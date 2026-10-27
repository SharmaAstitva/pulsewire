"""Stage 2: story clustering.

Different outlets publish the same story under different URLs, so URL hashing
alone is not enough. We compare normalised title tokens (Jaccard similarity)
against stories from the last 48 hours. The threshold is deliberately
conservative: merging two different stories is worse than showing one twice."""
import re

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "of", "to", "in", "on", "for", "with", "at",
    "by", "from", "as", "is", "are", "was", "were", "be", "been", "it", "its", "this",
    "that", "after", "over", "into", "says", "said", "say", "new", "how", "why", "what",
    "who", "will", "has", "have", "had", "not", "no", "up", "out", "amid", "about", "than",
    "more", "us", "uk", "s", "his", "her", "their", "they", "he", "she", "we", "you",
}
SIMILARITY_THRESHOLD = 0.5
MIN_TOKENS = 3


def title_tokens(title: str) -> frozenset[str]:
    words = re.findall(r"[a-z0-9]+", title.lower())
    return frozenset(_stem(w) for w in words if w not in STOPWORDS and len(w) > 1)


def _stem(word: str) -> str:
    # Tiny suffix stripper so "strikes"/"strike" and "elected"/"elect" match.
    for suffix in ("ing", "ed", "s"):
        if len(word) > len(suffix) + 3 and word.endswith(suffix) and not word.endswith("ss"):
            return word[: -len(suffix)]
    return word


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class StoryClusterer:
    """Holds canonical stories and finds a match for new titles."""

    def __init__(self, threshold: float = SIMILARITY_THRESHOLD):
        self.threshold = threshold
        self._stories: list[tuple[object, frozenset[str]]] = []

    def add(self, story, title: str) -> None:
        tokens = title_tokens(title)
        if len(tokens) >= MIN_TOKENS:
            self._stories.append((story, tokens))

    def match(self, title: str):
        tokens = title_tokens(title)
        if len(tokens) < MIN_TOKENS:
            return None
        best, best_score = None, 0.0
        for story, story_tokens in self._stories:
            score = jaccard(tokens, story_tokens)
            if score > best_score:
                best, best_score = story, score
        return best if best_score >= self.threshold else None
