"""Tests for the local triage engine."""
import asyncio
import json
import logging

import httpx
from app.core.config import settings
from app.services import ai_service


def _mock_ollama(monkeypatch, response: str | None = None, error: Exception | None = None):
    async_client = httpx.AsyncClient
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if error is not None:
            raise error
        return httpx.Response(200, json={"response": response})

    def make_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return async_client(*args, **kwargs)

    monkeypatch.setattr(ai_service.httpx, "AsyncClient", make_client)
    return requests


def _fallback_response(monkeypatch) -> None:
    _mock_ollama(monkeypatch, error=httpx.ConnectError("Ollama is unavailable"))


def test_suggest_triage_vpn_urgent_classifies_as_p2_network(monkeypatch) -> None:
    _fallback_response(monkeypatch)
    result = asyncio.run(ai_service.suggest_triage("My VPN is not connecting and I need access immediately"))

    assert result["severity"] in ("P1", "P2")
    assert result["priority"] in ("urgent", "high")
    assert result["category"] == "network"
    assert "recommended_agent" not in result
    assert isinstance(result["next_steps"], list)
    assert len(result["next_steps"]) > 0
    assert isinstance(result["diagnostic_trail"], list)
    assert len(result["diagnostic_trail"]) > 0


def test_suggest_triage_outage_classifies_as_p1(monkeypatch) -> None:
    _fallback_response(monkeypatch)
    result = asyncio.run(ai_service.suggest_triage("Production server outage — the whole team is blocked"))

    assert result["severity"] == "P1"
    assert result["priority"] == "urgent"
    assert result["requires_escalation"] is True
    assert "recommended_agent" not in result


def test_suggest_triage_password_reset_classifies_access(monkeypatch) -> None:
    _fallback_response(monkeypatch)
    result = asyncio.run(ai_service.suggest_triage("I forgot my password and my account is locked"))

    assert result["category"] == "access"
    assert "recommended_agent" not in result
    assert result["severity"] in ("P3", "P4")


def test_suggest_triage_low_severity_request(monkeypatch) -> None:
    _fallback_response(monkeypatch)
    result = asyncio.run(ai_service.suggest_triage("How do I change my email signature in Outlook?"))

    assert result["severity"] == "P4"
    assert result["priority"] == "low"
    assert result["requires_escalation"] is False


def test_suggest_triage_extracts_assets(monkeypatch) -> None:
    _fallback_response(monkeypatch)
    result = asyncio.run(
        ai_service.suggest_triage("Laptop ASSET-12345 won't connect to wifi, IP 10.0.1.50 is unreachable")
    )

    assets = result.get("affected_assets", [])
    asset_str = " ".join(assets)
    assert "ASSET-12345" in asset_str
    assert "10.0.1.50" in asset_str


def test_suggest_triage_diagnostic_trail_structure(monkeypatch) -> None:
    _fallback_response(monkeypatch)
    result = asyncio.run(ai_service.suggest_triage("Cannot install Excel update on my laptop"))

    trail = result.get("diagnostic_trail", [])
    assert len(trail) >= 4
    assert trail[0]["action"] == "Intent Recognition"
    assert "step" in trail[0]
    assert "timestamp" in trail[0]


def test_suggest_triage_uses_validated_ollama_json(monkeypatch, caplog) -> None:
    caplog.set_level(logging.INFO, logger=ai_service.__name__)
    response = json.dumps(
        {
            "priority": "high",
            "category": "software",
            "short_summary": "Payroll app crashes",
            "next_steps": ["Restart the app"],
        }
    )
    requests = _mock_ollama(monkeypatch, response=response)

    result = asyncio.run(ai_service.suggest_triage("The payroll app crashes when I open it"))

    assert result["category"] == "software"
    assert result["priority"] == "high"
    assert "recommended_agent" not in result
    assert result["next_steps"] == ["Restart the app"]
    assert "diagnostic_trail" in result
    assert "Triage used validated Ollama response" in caplog.text

    request = requests[0]
    assert str(request.url) == f"{settings.ollama_base_url}/api/generate"
    payload = json.loads(request.content)
    assert payload["stream"] is False
    assert payload["format"] == "json"
    assert payload["options"] == {"temperature": settings.ollama_temperature, "num_predict": 512}
    assert "temperature" not in payload
    assert "max_tokens" not in payload


def test_suggest_triage_invalid_json_falls_back(monkeypatch, caplog) -> None:
    _mock_ollama(monkeypatch, response="not valid JSON")

    result = asyncio.run(ai_service.suggest_triage("Excel app crashes after update"))

    assert result["category"] == "software"
    assert "heuristic fallback" in caplog.text


def test_suggest_triage_timeout_falls_back(monkeypatch) -> None:
    _mock_ollama(monkeypatch, error=httpx.ReadTimeout("Ollama request timed out"))

    result = asyncio.run(ai_service.suggest_triage("VPN is not connecting and I need access immediately"))

    assert result["category"] == "network"
    assert result["severity"] in ("P1", "P2")
    assert result["priority"] in ("urgent", "high")


def test_suggest_triage_invalid_enum_falls_back(monkeypatch) -> None:
    response = json.dumps(
        {
            "priority": "high",
            "category": "payroll",
            "short_summary": "Payroll app issue",
            "next_steps": ["Retry"],
        }
    )
    _mock_ollama(monkeypatch, response=response)

    result = asyncio.run(ai_service.suggest_triage("Excel crashes after update"))

    assert result["category"] == "software"
    assert result["priority"] == "low"


def test_suggest_triage_security_incident_escalates(monkeypatch) -> None:
    _fallback_response(monkeypatch)
    result = asyncio.run(ai_service.suggest_triage("Suspected phishing email received with malware attachment"))

    assert result["category"] == "security"
    assert result["severity"] in {"P1", "P2"}
    assert result["requires_escalation"] is True
    assert isinstance(result["next_steps"], list)

    result2 = asyncio.run(
        ai_service.suggest_triage("Data breach confirmed — customer data may be compromised")
    )
    assert result2["severity"] == "P1"
    assert result2["requires_escalation"] is True


def test_keyword_rules_use_word_boundaries_and_issue_categories() -> None:
    assert ai_service._classify_severity("The download folder is missing") != "P1"
    assert ai_service._classify_category("The rollout plan is ready") != "network"
    assert ai_service._classify_category("Wi-Fi keeps disconnecting") == "network"
    assert ai_service._classify_category("Outlook is crashing") == "email"
    assert ai_service._classify_category("My account is locked") == "access"


def test_security_keywords_escalate_sensitive_incidents() -> None:
    for text in (
        "I clicked a suspicious link",
        "I entered my password on an unknown page",
        "A company device was lost",
        "My laptop was stolen",
        "Malware was detected",
        "My account is compromised",
    ):
        assert ai_service._classify_category(text) == "security"
        assert ai_service._classify_severity(text) in {"P1", "P2"}
