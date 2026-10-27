import json

import httpx
import pytest

from app import config
from pipeline import enrich
from pipeline.enrich import (
    GroqSummaries,
    LiteProcessor,
    TransformersProcessor,
    extractive_summary,
    get_processor,
)


def test_lite_topic_classification():
    p = LiteProcessor()
    tech = p.process("Nvidia launches new AI chip", "The chip targets data centres.")
    assert tech.topic_primary == "Technology"
    assert p.process("India win cricket final", "The team won the match.").topic_primary == "Sports"


def test_lite_sentiment_has_three_classes():
    p = LiteProcessor()
    assert p.sentiment("Floods killed dozens, officials warn of crisis")[0] == "negative"
    assert p.sentiment("Team wins award after record success")[0] == "positive"
    assert p.sentiment("The committee met on Tuesday")[0] == "neutral"


def test_topic_scores_are_probabilities():
    scores = LiteProcessor().classify("Stock markets rise", "Shares and earnings")
    assert abs(sum(scores.values()) - 1) < 0.01


def test_extractive_summary_limits_length():
    text = "First sentence here. Second one follows. " * 20
    summary = extractive_summary(text, max_chars=60)
    assert summary.startswith("First sentence here.") and len(summary) <= 60
    assert extractive_summary("") is None


# ---------------------------------------------------------------- AI backends

LONG_TEXT = "The central bank raised interest rates again on Thursday. " * 10


def make_transformers(summary="Model summary.", label="LABEL_1", score=0.88):
    """TransformersProcessor with the HuggingFace pipelines replaced by stubs."""
    processor = TransformersProcessor.__new__(TransformersProcessor)
    processor._summarizer = lambda text, **kw: [{"summary_text": f" {summary} "}]
    processor._sentiment = lambda text, **kw: [{"label": label, "score": score}]
    processor._classifier = lambda text, labels, **kw: {
        "labels": ["Finance", "Politics", "World News"], "scores": [0.7, 0.2, 0.1]}
    return processor


def test_transformers_maps_model_labels():
    result = make_transformers(label="LABEL_0").process("Rates rise", LONG_TEXT)
    assert result.sentiment == "negative"
    assert make_transformers(label="positive").sentiment("x") == ("positive", 0.88)
    assert result.topic_primary == "Finance" and result.topic_secondary == "Politics"


def test_transformers_only_summarises_long_text():
    processor = make_transformers()
    assert processor.summarize("t", LONG_TEXT) == "Model summary."
    assert processor.summarize("t", "Short blurb. Already a summary.") == "Short blurb. Already a summary."


def groq_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_groq_replaces_summary():
    def handler(request):
        body = json.loads(request.content)
        assert request.headers["Authorization"] == "Bearer key"
        assert body["model"] == "test-model"
        return httpx.Response(200, json={"choices": [{"message": {"content": " LLM summary. "}}]})

    wrapper = GroqSummaries(LiteProcessor(), "key", "test-model")
    wrapper._client = groq_client(handler)
    assert wrapper.process("Rates rise", LONG_TEXT).summary == "LLM summary."
    assert wrapper.name == "lite+groq"


def test_groq_failure_keeps_fallback_summary():
    wrapper = GroqSummaries(LiteProcessor(), "key", "m")
    wrapper._client = groq_client(lambda request: httpx.Response(500))
    result = wrapper.process("Rates rise", LONG_TEXT)
    assert result.summary.startswith("The central bank raised")


def test_groq_skips_short_text():
    def handler(request):
        raise AssertionError("should not call the API for short text")

    wrapper = GroqSummaries(LiteProcessor(), "key", "m")
    wrapper._client = groq_client(handler)
    assert wrapper.process("t", "Short text.").summary == "Short text."


def test_get_processor_selection(monkeypatch):
    monkeypatch.setattr(config, "GROQ_API_KEY", "")
    assert get_processor("lite").name == "lite"
    with pytest.raises(ValueError):
        get_processor("gpt-9000")
    monkeypatch.setattr(config, "GROQ_API_KEY", "key")
    assert get_processor("lite").name == "lite+groq"


def test_get_processor_falls_back_when_models_cannot_load(monkeypatch):
    monkeypatch.setattr(config, "GROQ_API_KEY", "")

    def broken():
        raise ImportError("no torch")

    monkeypatch.setattr(enrich, "TransformersProcessor", broken)
    assert get_processor("transformers").name == "lite"
