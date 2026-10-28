from app.services.calibration import calibration_report, calibrate_triage


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


def test_calibration_report_tracks_safety_metrics() -> None:
    report = calibration_report([
        {"confidence": 0.9, "predicted": "P1", "actual": "P1", "abstain": False, "requires_escalation": True},
        {"confidence": 0.6, "predicted": "P4", "actual": "P1", "abstain": True, "requires_escalation": True},
        {"confidence": 0.8, "predicted": "P4", "actual": "P4", "abstain": False, "requires_escalation": False},
    ])

    assert report["safe_abstain_rate"] > 0
    assert "reliability_curve" in report
