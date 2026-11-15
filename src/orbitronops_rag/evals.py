"""Evaluation harness: retrieval recall, keyword accuracy, abstention.

Metrics are deliberately simple and labelled as proxies in docs/EVALS.md:
keyword accuracy is *not* human judgement of correctness — it is the share
of the question's expected keywords that appear in the answer text.
"""
from __future__ import annotations

import json
from pathlib import Path

from orbitronops_rag.answer import compose_answer
from orbitronops_rag.models import EvalQuestion, EvalReport, EvalResult
from orbitronops_rag.retrieval import Retriever


def load_qa(path: str | Path) -> list[EvalQuestion]:
    questions: list[EvalQuestion] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        questions.append(
            EvalQuestion(
                id=str(data["id"]),
                question=str(data["question"]),
                expected_source=str(data.get("expected_source", "")),
                expected_keywords=[str(k) for k in data.get("expected_keywords", [])],
                answerable=bool(data.get("answerable", True)),
            )
        )
    return questions


def keyword_accuracy(answer_text: str, expected_keywords: list[str]) -> float | None:
    """Share of expected keywords present in the answer (case-insensitive)."""
    if not expected_keywords:
        return None
    lowered = answer_text.lower()
    hits = sum(1 for keyword in expected_keywords if keyword.lower() in lowered)
    return hits / len(expected_keywords)


def run_evals(
    questions: list[EvalQuestion],
    retriever: Retriever,
    top_k: int = 3,
    threshold: float = 0.5,
) -> EvalReport:
    results: list[EvalResult] = []
    for question in questions:
        retrieved = retriever.retrieve(question.question, top_k=top_k)
        answer = compose_answer(
            question.question, retrieved, threshold=threshold, top_k=top_k
        )
        sources = [r.chunk.source for r in retrieved]
        if question.answerable and question.expected_source:
            recall = 1.0 if question.expected_source in sources else 0.0
        else:
            recall = 0.0  # not applicable for unanswerable questions
        accuracy = None
        if question.answerable and not answer.abstained:
            accuracy = keyword_accuracy(answer.text, question.expected_keywords)
        results.append(
            EvalResult(
                question_id=question.id,
                question=question.question,
                answerable=question.answerable,
                abstained=answer.abstained,
                recall_at_3=recall,
                keyword_accuracy=accuracy,
                retrieved_sources=sources,
            )
        )

    answerable = [r for r in results if r.answerable]
    unanswerable = [r for r in results if not r.answerable]
    recalls = [r.recall_at_3 for r in answerable]
    accuracies = [r.keyword_accuracy for r in answerable if r.keyword_accuracy is not None]
    report = EvalReport(
        total=len(results),
        answerable=len(answerable),
        unanswerable=len(unanswerable),
        retrieval_recall_at_3=(sum(recalls) / len(recalls) if recalls else 0.0),
        mean_keyword_accuracy=(sum(accuracies) / len(accuracies) if accuracies else None),
        abstention_rate_unanswerable=(
            sum(1 for r in unanswerable if r.abstained) / len(unanswerable)
            if unanswerable
            else 0.0
        ),
        false_abstention_rate=(
            sum(1 for r in answerable if r.abstained) / len(answerable)
            if answerable
            else 0.0
        ),
        results=results,
    )
    return report
