from eval.retrieval import retrieval_hit_rate
from eval.synthetic import build_dataset


def test_synthetic_dataset_has_unique_paraphrased_cases_and_hard_examples() -> None:
    dataset = build_dataset()
    texts = {ticket.text.lower() for ticket in dataset}

    assert len(dataset) >= 120
    assert len(texts) == len(dataset)
    assert any("phishing" in text for text in texts)
    assert any("ignore" in text or "override" in text for text in texts)
    assert any("not sure" in text or "vague" in text for text in texts)
    assert any("and" in text and "outlook" in text.lower() for text in texts)


def test_retrieval_report_uses_held_out_questions() -> None:
    report = retrieval_hit_rate()

    assert report["question_count"] >= 8
    assert 0.0 <= report["hit_rate_at_3"] <= 1.0
    assert report["hits"] <= report["question_count"]
    assert report["hits"] == 5
