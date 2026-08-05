from app.services.ai_service import suggest_triage


def test_suggest_triage_uses_heuristics_when_ollama_unavailable() -> None:
    result = suggest_triage("My VPN is not connecting and I need access immediately")

    assert result["priority"] == "urgent"
    assert result["category"] == "access"
    assert "VPN" in result["short_summary"]
    assert result["recommended_agent"] == "access_management_agent"
    assert any("credentials" in step.lower() for step in result["next_steps"])
