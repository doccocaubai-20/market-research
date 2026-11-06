"""Select web passages for the analysis agents using in-memory BM25."""

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from math import log1p
from xml.sax.saxutils import escape


PASSAGE_WORDS = 150
PASSAGE_OVERLAP = 25
MAX_PASSAGES = 6
MAX_PASSAGES_PER_URL = 2
MAX_CONTEXT_CHARS = 6_000
K1 = 1.2
B = 0.75

ROLE_FOCUS = {
    "trend": "xu hướng tiêu dùng nhu cầu hành vi mua hàng tăng trưởng dự báo",
    "competitor": "đối thủ doanh nghiệp thương hiệu thị phần chiến lược mở rộng",
}


@dataclass(frozen=True)
class Passage:
    id: str
    url: str
    title: str
    text: str
    source_type: str


def _tokenize(text: str) -> list[str]:
    # Compare accented and unaccented Vietnamese while preserving the original excerpt.
    normalized = unicodedata.normalize("NFD", text.casefold()).replace("đ", "d")
    folded = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.findall(r"[^\W_]+", folded)


def _split_sources(sources: list[dict]) -> list[Passage]:
    passages = []
    seen_urls = set()
    for source in sources:
        if not isinstance(source, dict):
            continue
        url = source.get("link") or source.get("url")
        text = source.get("snippet")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            continue
        if url in seen_urls or not isinstance(text, str) or not text.strip():
            continue

        seen_urls.add(url)
        title = source.get("title") or ""
        is_crawled = source.get("is_deep_crawled")
        source_type = "website" if is_crawled else "search_snippet"
        if is_crawled is None:
            source_type = "cached_excerpt"

        words = text.split()
        step = PASSAGE_WORDS - PASSAGE_OVERLAP
        for start in range(0, len(words), step):
            end = start + PASSAGE_WORDS
            passages.append(Passage(
                id=f"E{len(passages) + 1:03d}",
                url=url,
                title=title,
                text=" ".join(words[start:end]),
                source_type=source_type,
            ))
            if end >= len(words):
                break
    return passages


def retrieve_evidence(topic: str, sources: list[dict]) -> dict[str, list[Passage]]:
    """Rank source passages per role. An empty dict means no usable source text."""
    passages = _split_sources(sources)
    if not passages:
        return {}

    term_counts = [Counter(_tokenize(passage.text)) for passage in passages]
    lengths = [sum(counts.values()) for counts in term_counts]
    average_length = sum(lengths) / len(passages) or 1

    document_frequency = Counter()
    for counts in term_counts:
        document_frequency.update(counts.keys())

    selected = {}
    for role, focus in ROLE_FOCUS.items():
        query_terms = dict.fromkeys(_tokenize(f"{topic} {focus}"))
        weights = {}
        for term in query_terms:
            frequency = document_frequency[term]
            if frequency:
                weights[term] = log1p((len(passages) - frequency + 0.5) / (frequency + 0.5))

        scores = []
        for passage, counts, length in zip(passages, term_counts, lengths):
            normalization = K1 * (1 - B + B * length / average_length)
            score = sum(
                weight * counts[term] * (K1 + 1) / (counts[term] + normalization)
                for term, weight in weights.items()
                if term in counts
            )
            if score > 0:
                scores.append((score, passage))

        ranked = sorted(scores, key=lambda item: item[0], reverse=True)
        selected[role] = _select_within_budget(ranked)
    return selected


def _select_within_budget(ranked: list[tuple[float, Passage]]) -> list[Passage]:
    selected = []
    by_url = Counter()
    used_chars = 0
    for _, passage in ranked:
        if by_url[passage.url] >= MAX_PASSAGES_PER_URL:
            continue
        block_chars = len(_format_passage(passage)) + bool(selected)
        if used_chars + block_chars > MAX_CONTEXT_CHARS:
            continue
        selected.append(passage)
        by_url[passage.url] += 1
        used_chars += block_chars
        if len(selected) == MAX_PASSAGES:
            break
    return selected


def format_evidence(passages: list[Passage]) -> str:
    return "\n".join(_format_passage(passage) for passage in passages)


def _format_passage(passage: Passage) -> str:
    return (
        f'<passage id="{passage.id}" type="{passage.source_type}">\n'
        f"<title>{escape(passage.title)}</title>\n"
        f"<url>{escape(passage.url)}</url>\n"
        f"<excerpt>{escape(passage.text)}</excerpt>\n"
        "</passage>"
    )
