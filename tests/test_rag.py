"""Tests for the RAG demo. Run: python -m pytest -q"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from orbitronops_rag.answer import compose_answer
from orbitronops_rag.chunking import chunk_corpus, chunk_document, load_documents
from orbitronops_rag.evals import keyword_accuracy, load_qa, run_evals
from orbitronops_rag.models import Document
from orbitronops_rag.retrieval import Retriever

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
QA_FILE = Path(__file__).resolve().parents[1] / "evals" / "qa.jsonl"


def _retriever() -> Retriever:
    return Retriever(chunk_corpus(load_documents(DATA_DIR)))


def test_chunking_splits_on_headings():
    doc = Document(
        source="data/test.md", title="Test Doc",
        text="# One\n\nFirst paragraph.\n\n# Two\n\nSecond paragraph.\n",
    )
    chunks = chunk_document(doc)
    assert len(chunks) >= 2
    assert any(c.title == "One" for c in chunks)
    assert any(c.title == "Two" for c in chunks)


def test_chunking_keeps_long_documents_bounded():
    doc = Document(source="data/test.md", title="Long", text="word " * 500)
    chunks = chunk_document(doc, max_chars=200)
    assert all(len(c.text) <= 200 for c in chunks)
    assert len(chunks) > 1


def test_corpus_loads_four_documents():
    docs = load_documents(DATA_DIR)
    assert len(docs) == 4
    assert all(doc.text for doc in docs)


def test_retrieval_returns_relevant_doc_first():
    retriever = _retriever()
    results = retriever.retrieve("How do I deploy checkout-api?", top_k=3)
    assert results
    assert results[0].chunk.source == "data/runbook-deploy.md"


def test_retrieval_memory_limit_doc_first():
    retriever = _retriever()
    results = retriever.retrieve("What is the memory limit for checkout-api?", top_k=3)
    assert results
    assert results[0].chunk.source == "data/product-checkout.md"


def test_abstention_on_unrelated_question():
    retriever = _retriever()
    retrieved = retriever.retrieve("What is the capital of France?", top_k=3)
    answer = compose_answer("What is the capital of France?", retrieved)
    assert answer.abstained is True
    assert "don't know" in answer.text.lower()
    assert answer.citations == []


def test_abstention_on_unanswerable_corpus_question():
    retriever = _retriever()
    retrieved = retriever.retrieve("What is the refund policy for customers?", top_k=3)
    answer = compose_answer("What is the refund policy for customers?", retrieved)
    assert answer.abstained is True


def test_answer_has_citation_and_source_text():
    retriever = _retriever()
    retrieved = retriever.retrieve("How do I deploy checkout-api?", top_k=3)
    answer = compose_answer("How do I deploy checkout-api?", retrieved)
    assert answer.abstained is False
    assert answer.citations
    assert "kubectl" in answer.text
    assert any("runbook-deploy.md" in c for c in answer.citations)


def test_empty_query_abstains():
    retriever = _retriever()
    answer = compose_answer("", retriever.retrieve("", top_k=3))
    assert answer.abstained is True


def test_json_output_is_valid():
    retriever = _retriever()
    retrieved = retriever.retrieve("What database does checkout-api use?", top_k=3)
    answer = compose_answer("What database does checkout-api use?", retrieved)
    data = json.loads(json.dumps(answer.to_dict()))
    assert data["question"]
    assert "answer" in data
    assert isinstance(data["citations"], list)
    assert data["abstained"] is False


def test_keyword_accuracy_is_a_fraction():
    assert keyword_accuracy("kubectl apply and rollout status", ["kubectl apply", "rollout status"]) == 1.0
    assert keyword_accuracy("nothing relevant here", ["kubectl apply"]) == 0.0
    assert keyword_accuracy("anything", []) is None


def test_evals_harness_computes_recall():
    retriever = _retriever()
    questions = load_qa(QA_FILE)
    assert len(questions) == 10
    report = run_evals(questions, retriever)
    assert report.total == 10
    assert report.answerable == 8
    assert report.unanswerable == 2
    assert report.retrieval_recall_at_3 >= 0.75
    assert report.abstention_rate_unanswerable == 1.0
    assert report.false_abstention_rate == 0.0


def test_no_answer_invents_citations():
    retriever = _retriever()
    retrieved = retriever.retrieve("How can we reduce cloud costs?", top_k=3)
    answer = compose_answer("How can we reduce cloud costs?", retrieved)
    sources = {c.source for c in chunk_corpus(load_documents(DATA_DIR))}
    for citation in answer.citations:
        assert any(citation.startswith(source) for source in sources)
