from app.services.calibration import (
    ABSTAIN_THRESHOLD,
    calibrate_triage,
    calibration_report,
    fit_abstain_threshold,
)


def test_triage_returns_evidence_and_calibrated_abstention_fields() -> None:
    result = calibrate_triage(
        "Unclear problem",
        {"category": "general", "severity": "P4", "short_summary": ""},
    )

    assert "confidence" in result
    assert "evidence" in result
    assert "abstain_threshold" in result
    assert result["abstain"] is True
    assert result["requires_escalation"] is True
    assert result["confidence"] == 0.7


def test_evidence_count_does_not_inflate_confidence() -> None:
    result = calibrate_triage(
        "VPN network Wi-Fi internet DNS outage everyone",
        {"category": "network", "severity": "P1", "confidence": 0.61},
    )

    assert result["confidence"] == 0.61


def test_rules_disagreement_forces_abstention() -> None:
    result = calibrate_triage(
        "Wi-Fi is unavailable",
        {"category": "software", "severity": "P4"},
        rules_disagree=True,
    )

    assert result["abstain"] is True
    assert result["rules_disagree"] is True
    assert "disagrees" in result["abstention_reason"]


def test_abstain_threshold_is_selected_from_labelled_validation_set() -> None:
    assert ABSTAIN_THRESHOLD == fit_abstain_threshold()
    assert ABSTAIN_THRESHOLD == 0.7


def test_calibration_report_tracks_safety_metrics() -> None:
    report = calibration_report([
        {"confidence": 0.9, "predicted": "P1", "actual": "P1", "abstain": False, "requires_escalation": True},
        {"confidence": 0.6, "predicted": "P4", "actual": "P1", "abstain": True, "requires_escalation": True},
        {"confidence": 0.8, "predicted": "P4", "actual": "P4", "abstain": False, "requires_escalation": False},
    ])

    assert report["safe_abstain_rate"] > 0
    assert "reliability_curve" in report
