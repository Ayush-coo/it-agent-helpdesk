from app.services.incident_simulator import simulate_incident_detection


def test_replay_simulator_reports_detector_metrics_without_a_baseline() -> None:
    report = simulate_incident_detection(
        seed=11,
        normal_tickets=30,
        outage_scenarios=3,
        burst_size=4,
    )

    assert report["ticket_count"] == 42
    assert report["detector"]["actual"] == 3
    assert 0 <= report["detector"]["precision"] <= 1
    assert 0 <= report["detector"]["recall"] <= 1
    assert "naive_keyword_baseline" not in report
