"""Knowledge-base retrieval with BM25 ranking (no external search service needed)."""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .config import get_settings

STOPWORDS = set(
    "a an and are as at be but by can cannot do for from has have i if in into is it its my "
    "not of on or our so that the their them then there this to was we what when with you your".split()
)


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w[:-1] if w.endswith("s") and len(w) > 3 else w for w in words if w not in STOPWORDS]


@dataclass(frozen=True)
class Article:
    slug: str
    title: str
    category: str
    team: str
    body: str


def parse_article(path: Path) -> Article:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    meta: dict[str, str] = {}
    body = text
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if match:
        for line in match.group(1).splitlines():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
        body = match.group(2).strip()
    return Article(path.stem, meta.get("title", path.stem), meta.get("category", "general"),
                   meta.get("team", "service_desk"), body)


class KnowledgeBase:
    def __init__(self, articles: list[Article], k1: float = 1.5, b: float = 0.75):
        self.articles = articles
        self.k1, self.b = k1, b
        # Title words count twice: titles are the strongest signal.
        self.docs = [Counter(tokenize(a.title) * 2 + tokenize(a.body)) for a in articles]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_len = sum(self.lengths) / max(len(self.lengths), 1)
        df = Counter(term for d in self.docs for term in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    @classmethod
    def from_dir(cls, folder: Path) -> "KnowledgeBase":
        return cls([parse_article(p) for p in sorted(folder.glob("*.md"))])

    def score(self, query_terms: list[str], i: int) -> float:
        doc, length, total = self.docs[i], self.lengths[i], 0.0
        for term in query_terms:
            tf = doc.get(term, 0)
            if tf:
                norm = tf + self.k1 * (1 - self.b + self.b * length / self.avg_len)
                total += self.idf[term] * tf * (self.k1 + 1) / norm
        return total

    def search(self, query: str, k: int = 3) -> list[dict]:
        terms = tokenize(query)
        ranked = sorted(((self.score(terms, i), i) for i in range(len(self.articles))), reverse=True)
        results = []
        for score, i in ranked[:k]:
            if score <= 0:
                break
            a = self.articles[i]
            results.append({"article": a.slug, "title": a.title, "category": a.category,
                            "team": a.team, "score": round(score, 2), "content": a.body})
        return results


@lru_cache(maxsize=1)
def default_kb() -> KnowledgeBase:
    return KnowledgeBase.from_dir(get_settings().kb_dir)
