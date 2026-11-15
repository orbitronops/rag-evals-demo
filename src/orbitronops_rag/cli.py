"""CLI: python -m orbitronops_rag ask "question" | evals

Run from the repo root, no install needed (``src`` is put on sys.path).
No API key, no network, no cluster.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from a checkout without installing: `src` on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orbitronops_rag.answer import compose_answer  # noqa: E402
from orbitronops_rag.chunking import chunk_corpus, load_documents  # noqa: E402
from orbitronops_rag.evals import load_qa, run_evals  # noqa: E402
from orbitronops_rag.retrieval import Retriever  # noqa: E402


def _build_retriever(data_dir: str) -> Retriever:
    docs = load_documents(data_dir)
    if not docs:
        print(f"error: no documents found in {data_dir}", file=sys.stderr)
        raise SystemExit(2)
    return Retriever(chunk_corpus(docs))


def _render_answer_text(answer) -> str:
    if answer.abstained:
        return "I don't know from these documents."
    lines = [answer.text, "", "Sources:"]
    lines += [f"  - {citation}" for citation in answer.citations]
    lines.append(f"Confidence (retrieval signal only): {answer.confidence:.2f}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="orbitronops-rag",
        description="Deterministic RAG demo with evals (OrbitronOps demo).",
    )
    parser.add_argument("--data-dir", default="data", help="Corpus directory (default: data).")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=0.5)
    sub = parser.add_subparsers(dest="command", required=True)

    ask = sub.add_parser("ask", help="Ask one question of the corpus.")
    ask.add_argument("question", help="The question to answer.")
    ask.add_argument("--format", choices=["text", "json"], default="text")

    run = sub.add_parser("evals", help="Run the Q&A eval set and print scores.")
    run.add_argument("--qa-file", default="evals/qa.jsonl")
    run.add_argument("--format", choices=["text", "json"], default="text")

    args = parser.parse_args(argv)
    retriever = _build_retriever(args.data_dir)

    if args.command == "ask":
        retrieved = retriever.retrieve(args.question, top_k=args.top_k)
        answer = compose_answer(
            args.question, retrieved, threshold=args.threshold, top_k=args.top_k
        )
        if args.format == "json":
            print(json.dumps(answer.to_dict(), indent=2))
        else:
            print(_render_answer_text(answer))
        return 0

    if args.command == "evals":
        try:
            questions = load_qa(args.qa_file)
        except FileNotFoundError:
            print(f"error: file not found: {args.qa_file}", file=sys.stderr)
            return 2
        report = run_evals(
            questions, retriever, top_k=args.top_k, threshold=args.threshold
        )
        if args.format == "json":
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(f"Eval results — {report.total} questions "
                  f"({report.answerable} answerable, {report.unanswerable} unanswerable)")
            print(f"  Retrieval recall@3:            {report.retrieval_recall_at_3:.2f}")
            mean = report.mean_keyword_accuracy
            print(f"  Mean keyword accuracy:         {mean:.2f}" if mean is not None else "  Mean keyword accuracy:         n/a")
            print(f"  Abstention (unanswerable):     {report.abstention_rate_unanswerable:.2f}")
            print(f"  False abstention (answerable): {report.false_abstention_rate:.2f}")
            print("")
            for result in report.results:
                acc = f"{result.keyword_accuracy:.2f}" if result.keyword_accuracy is not None else "n/a"
                flag = "ABSTAINED" if result.abstained else "answered"
                print(f"  {result.question_id}: recall={result.recall_at_3:.0f} accuracy={acc} {flag} — {result.question}")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
