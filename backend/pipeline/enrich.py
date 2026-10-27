"""Stage 3: AI enrichment (summary, sentiment, topics).

Two interchangeable backends:
  * "transformers" - local HuggingFace models, used by the scheduled pipeline
  * "lite"         - fast rule-based fallback with no ML dependencies, used for
                     tests, quick local runs and as a safety net if models fail
If GROQ_API_KEY is set, summaries come from an LLM via Groq instead."""
import json
import logging
import math
import re
from dataclasses import dataclass, field

import httpx

from app import config
from pipeline.clean import split_sentences

log = logging.getLogger("pulsewire.enrich")


@dataclass
class Enrichment:
    summary: str | None
    sentiment: str
    sentiment_score: float
    topic_primary: str
    topic_secondary: str | None
    topic_scores: dict[str, float] = field(default_factory=dict)


def extractive_summary(text: str, max_chars: int = 320) -> str | None:
    sentences = split_sentences(text)
    if not sentences:
        return None
    summary = ""
    for sentence in sentences[:3]:
        if summary and len(summary) + len(sentence) > max_chars:
            break
        summary = f"{summary} {sentence}".strip()
    return summary[:max_chars]


# ---------------------------------------------------------------- lite backend
TOPIC_KEYWORDS = {
    "Technology": "ai artificial intelligence software app apple google microsoft meta openai chip chips "
                  "semiconductor startup tech cyber hack hackers data smartphone iphone android robot "
                  "computing cloud internet crypto bitcoin gadget nvidia amazon tesla",
    "Finance": "market markets stock stocks shares economy economic inflation bank banks rate rates "
               "investor investors earnings profit revenue trade tariff tariffs gdp currency rupee dollar "
               "sensex nifty ipo fund oil prices price business company companies deal",
    "Politics": "election elections minister government parliament president senate congress vote "
                "voters party policy law bill campaign prime opposition modi biden trump court ruling",
    "Science": "science scientists research study space nasa isro planet climate species fossil "
               "physics astronomers discovery universe telescope environment energy",
    "Health": "health hospital doctors disease virus vaccine cancer patients medical drug drugs "
              "mental covid outbreak who treatment nutrition diet",
    "Sports": "match cricket football soccer tennis olympic olympics league cup tournament player "
              "players team coach win wins goal score ipl fifa nba championship",
    "Entertainment": "film movie music album actor actress celebrity box office netflix series "
                     "show festival bollywood hollywood singer award awards",
    "World News": "war ukraine russia china israel gaza iran attack military killed troops border "
                  "refugees protest united nations un summit embassy",
}
_TOPIC_SETS = {topic: set(words.split()) for topic, words in TOPIC_KEYWORDS.items()}

POSITIVE = set(
    "win wins won success successful growth gain gains rise rises surge record breakthrough boost "
    "improve improves improved recovery celebrate celebrates hope hopeful best launch launches "
    "approve approved agreement peace award awarded rescue saved strong profit innovative".split()
)
NEGATIVE = set(
    "war attack attacks killed kill dead death deaths crash crisis fall falls fell drop drops loss "
    "losses fear fears warn warns warning threat collapse fraud scandal lawsuit sued protest "
    "injured disaster flood floods fire fires shooting arrest arrested ban cuts layoffs decline "
    "recession conflict violence outbreak fails failure hack breach".split()
)


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


class LiteProcessor:
    name = "lite"

    def classify(self, title: str, text: str) -> dict[str, float]:
        words = _words(title) * 2 + _words(text)  # title counts double
        raw = {topic: sum(w in vocab for w in words) for topic, vocab in _TOPIC_SETS.items()}
        if not any(raw.values()):
            raw["World News"] = 1
        exps = {t: math.exp(v) for t, v in raw.items()}
        total = sum(exps.values())
        return dict(sorted(((t, round(v / total, 4)) for t, v in exps.items()),
                           key=lambda kv: kv[1], reverse=True))

    def sentiment(self, text: str) -> tuple[str, float]:
        words = _words(text)
        pos = sum(w in POSITIVE for w in words)
        neg = sum(w in NEGATIVE for w in words)
        polarity = (pos - neg) / (pos + neg + 2)
        if polarity > 0.15:
            label = "positive"
        elif polarity < -0.15:
            label = "negative"
        else:
            label = "neutral"
        return label, round(min(0.99, 0.5 + abs(polarity) / 2), 4)

    def summarize(self, title: str, text: str) -> str | None:
        return extractive_summary(text)

    def process(self, title: str, text: str) -> Enrichment:
        scores = self.classify(title, text)
        topics = list(scores)
        label, score = self.sentiment(f"{title}. {text}")
        return Enrichment(
            summary=self.summarize(title, text),
            sentiment=label,
            sentiment_score=score,
            topic_primary=topics[0],
            topic_secondary=topics[1] if len(topics) > 1 else None,
            topic_scores=dict(list(scores.items())[:3]),
        )


# -------------------------------------------------------- transformers backend
SENTIMENT_LABELS = {"label_0": "negative", "label_1": "neutral", "label_2": "positive"}


class TransformersProcessor(LiteProcessor):
    """Local HuggingFace models, CPU only. Loaded lazily, once per run."""

    name = "transformers"
    SUMMARY_MODEL = "t5-small"
    # 3-class model, so "neutral" is a real prediction (SST-2 models only
    # output positive/negative).
    SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    TOPIC_MODEL = "typeform/distilbart-mnli-12-3"

    def __init__(self):
        from transformers import pipeline  # imported here: heavy, optional

        log.info("Loading HuggingFace models (first run downloads them)…")
        self._summarizer = pipeline("summarization", model=self.SUMMARY_MODEL, device=-1)
        self._sentiment = pipeline("sentiment-analysis", model=self.SENTIMENT_MODEL, device=-1)
        self._classifier = pipeline("zero-shot-classification", model=self.TOPIC_MODEL, device=-1)

    def classify(self, title: str, text: str) -> dict[str, float]:
        result = self._classifier(f"{title}. {text[:600]}", config.TOPICS, multi_label=False)
        pairs = zip(result["labels"], result["scores"], strict=True)
        return {label: round(score, 4) for label, score in pairs}

    def sentiment(self, text: str) -> tuple[str, float]:
        result = self._sentiment(text[:1000], truncation=True)[0]
        label = result["label"].lower()
        return SENTIMENT_LABELS.get(label, label), round(float(result["score"]), 4)

    def summarize(self, title: str, text: str) -> str | None:
        if len(text) < 400:  # short RSS blurbs are already summaries
            return extractive_summary(text)
        out = self._summarizer(text[:2000], max_length=80, min_length=25, do_sample=False, truncation=True)
        return out[0]["summary_text"].strip()


# ----------------------------------------------------------- optional Groq LLM
class GroqSummaries:
    """Wraps another processor and replaces its summaries with LLM output."""

    def __init__(self, inner, api_key: str, model: str):
        self.inner, self.api_key, self.model = inner, api_key, model
        self.name = f"{inner.name}+groq"
        self._client = httpx.Client(timeout=30)

    def process(self, title: str, text: str) -> Enrichment:
        enrichment = self.inner.process(title, text)
        if len(text) >= 200:
            try:
                enrichment.summary = self._summarize(title, text) or enrichment.summary
            except Exception as exc:
                log.warning("Groq summary failed, keeping fallback: %s", exc)
        return enrichment

    def _summarize(self, title: str, text: str) -> str | None:
        response = self._client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "temperature": 0.2,
                "max_tokens": 160,
                "messages": [
                    {"role": "system", "content": "You summarise news articles in 2-3 neutral, factual "
                                                  "sentences. Use only facts in the text. No preamble."},
                    {"role": "user", "content": f"Title: {title}\n\n{text[:3000]}"},
                ],
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()


def get_processor(name: str | None = None):
    name = (name or config.AI_BACKEND).lower()
    processor = LiteProcessor()
    if name == "transformers":
        try:
            processor = TransformersProcessor()
        except Exception as exc:
            log.error("Could not load transformers backend, falling back to lite: %s", exc)
    elif name != "lite":
        raise ValueError(f"Unknown AI backend: {name}")
    if config.GROQ_API_KEY:
        return GroqSummaries(processor, config.GROQ_API_KEY, config.GROQ_MODEL)
    return processor


def scores_json(enrichment: Enrichment) -> str:
    return json.dumps(enrichment.topic_scores)
