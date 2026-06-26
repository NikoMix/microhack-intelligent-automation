"""Tests for the BM25 local fallback retriever and tokenizer."""

from __future__ import annotations

from iauto_foundry_agent.documents import Document
from iauto_foundry_agent.retrieval.base import SearchHit, tokenize
from iauto_foundry_agent.retrieval.local import BM25LocalRetriever


def test_tokenize_lowercases_and_drops_stopwords() -> None:
    assert tokenize("How do I reset THE password?") == ["reset", "password"]


def test_tokenize_keeps_alphanumeric() -> None:
    assert tokenize("GlobalProtect vpn-2 client!") == ["globalprotect", "vpn", "2", "client"]


def test_search_ranks_relevant_document_first(
    local_retriever: BM25LocalRetriever,
) -> None:
    hits = local_retriever.search("how do I connect to the vpn", top_k=3)
    assert hits
    assert hits[0].document.id == "d1"
    assert isinstance(hits[0], SearchHit)
    assert hits[0].score > 0.0


def test_search_matches_password_topic(local_retriever: BM25LocalRetriever) -> None:
    hits = local_retriever.search("forgot my password reset", top_k=1)
    assert [h.document.id for h in hits] == ["d2"]


def test_search_respects_top_k(local_retriever: BM25LocalRetriever) -> None:
    hits = local_retriever.search("vpn password expenses", top_k=2)
    assert len(hits) <= 2


def test_search_empty_query_returns_nothing(local_retriever: BM25LocalRetriever) -> None:
    assert local_retriever.search("the and of", top_k=3) == []
    assert local_retriever.search("", top_k=3) == []


def test_search_non_positive_top_k(local_retriever: BM25LocalRetriever) -> None:
    assert local_retriever.search("vpn", top_k=0) == []


def test_empty_corpus_returns_nothing() -> None:
    retriever = BM25LocalRetriever([])
    assert retriever.search("anything", top_k=3) == []


def test_scores_are_sorted_descending(local_retriever: BM25LocalRetriever) -> None:
    hits = local_retriever.search("vpn password expenses receipts", top_k=5)
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_no_match_returns_empty(local_retriever: BM25LocalRetriever) -> None:
    assert local_retriever.search("zzzquux nonexistentterm", top_k=3) == []


def test_tie_break_is_deterministic() -> None:
    docs = [
        Document(id="a", title="apple", content="apple"),
        Document(id="b", title="apple", content="apple"),
    ]
    retriever = BM25LocalRetriever(docs)
    hits = retriever.search("apple", top_k=2)
    assert [h.document.id for h in hits] == ["a", "b"]


def test_from_path_loads_bundled_kb() -> None:
    retriever = BM25LocalRetriever.from_path()
    hits = retriever.search("connect to the vpn with globalprotect", top_k=1)
    assert hits
    assert "vpn" in hits[0].document.searchable_text.lower()
