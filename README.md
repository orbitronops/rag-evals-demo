# OrbitronOps RAG + Evals Demo

> **A small, honest RAG demo with an evaluation harness.** It answers questions
> only from a small set of sample documents, cites its sources, and says
> "I don't know from these documents" when the corpus cannot answer.

[![CI](https://github.com/orbitronops/rag-evals-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/orbitronops/rag-evals-demo/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: Demo](https://img.shields.io/badge/status-demo%20%E2%80%94%20not%20client%20work-lightgrey.svg)](#status)

**By [OrbitronOps](https://www.orbitronops.com)** — Production AI Infrastructure on Kubernetes.
North Vancouver, BC · Canada Remote / BC Hybrid

---

## What this proves

A buyer doesn't have to take our word for it. They can run this in 2 minutes:

```bash
git clone https://github.com/orbitronops/rag-evals-demo.git
cd rag-evals-demo
pip install -e .
python -m orbitronops_rag ask "How do I deploy checkout-api?"
python -m orbitronops_rag evals
```

And get a cited answer like this:

```
To deploy checkout-api, run `kubectl apply -f k8s/checkout-api.yaml -n prod`
from the release branch, then watch the rollout with
`kubectl rollout status deployment/checkout-api -n prod`. A deployment is
only complete when the rollout reports success and the readiness probe is
passing.

Sources:
  - data/runbook-deploy.md#Deploying checkout-api
  - data/runbook-deploy.md#Approval
  - data/product-checkout.md#What checkout-api does
Confidence (retrieval signal only): 1.00
```

And an unanswerable question gets an honest abstention, not a guess:

```
$ python -m orbitronops_rag ask "What is the capital of France?"

I don't know from these documents.
```

No API key needed. No embeddings service. No cluster. No cloud bill.

## How retrieval works

1. **Chunking** — each document in `data/` is split on headings and blank lines into chunks of at most 900 characters, keeping the heading as context.
2. **Retrieval** — a deterministic TF-IDF-style keyword index scores chunks by IDF-weighted query-term overlap, normalised by chunk length. Same corpus + same question = same ranking, every time.
3. **Answer** — the answer is extractive: the best sentences from the top 3 retrieved chunks, with citations naming the source file and section. Nothing is generated beyond those chunks.
4. **Abstention** — if no chunk scores above the threshold, the answer is "I don't know from these documents." No citations, confidence 0.0.

An LLM explainer is a pluggable interface (`answer.LLMExplainer`) — optional, off by default, bring your own key. It may only reword an answer that already exists; it can never add facts or execute actions. It is not implemented in v0.1.0.

## Eval results

Measured with `python -m orbitronops_rag evals` on the 10-question set in `evals/qa.jsonl` (8 answerable, 2 unanswerable). See [`docs/EVALS.md`](docs/EVALS.md) for what each number means — and what it does not.

| Metric | Score |
|---|---|
| Retrieval recall@3 | 1.00 |
| Mean keyword accuracy (proxy) | 1.00 |
| Abstention rate — unanswerable | 1.00 |
| False abstention rate — answerable | 0.00 |

Per-question detail is in [`examples/sample-qa.txt`](examples/sample-qa.txt). A perfect score on 10 questions is a smoke test, not a benchmark — the point is that the harness is visible and repeatable: add questions, re-run, watch the numbers move.

## Quickstart

**Requirements:** Python 3.10+ only. No dependencies for the demo.

```bash
# 1. Clone
git clone https://github.com/orbitronops/rag-evals-demo.git
cd rag-evals-demo

# 2. Install (editable, no dependencies)
pip install -e .

# 3. Ask a question
python -m orbitronops_rag ask "How do I deploy checkout-api?"
python -m orbitronops_rag ask "What is the memory limit for checkout-api?"
python -m orbitronops_rag ask "What is the capital of France?"

# 4. Run the evals
python -m orbitronops_rag evals

# 5. Run the tests
python -m pytest -q
```

Without installing, run with `PYTHONPATH=src` instead, e.g. `PYTHONPATH=src python -m orbitronops_rag ask "..."`. JSON output is available with `--format json` on both `ask` and `evals`.

### Try your own documents

Add a Markdown file to `data/` and ask about it — it is indexed automatically. Add a question to `evals/qa.jsonl` with its `expected_source` and `expected_keywords` (or `answerable: false` for an abstention test), then re-run `evals`.

## Limitations — read before judging the scores

- **Small, fictional corpus** — 4 short documents about a made-up company ("Acme Retail"). No real client data, no real internal documents.
- **Keyword retrieval, not semantic** — it fails on synonyms and paraphrase ("how do I ship it?" vs "deploy"). A production system would add embeddings; this demo keeps the keyword retriever as the no-key fallback.
- **Keyword accuracy is a proxy** — it checks that expected facts appear in the answer; it is not human judgement of correctness, completeness, or wording.
- **10 questions is a smoke test** — not a dataset, not a benchmark.
- **Extractive answers can be wordy** — an answer may include extra sentences from a retrieved chunk that are true but not asked for. That is the trade-off of grounding: the answer never invents, but it is not yet summarised.

## Project layout

```
.
├── src/orbitronops_rag/     # the demo: chunking, retrieval, answers, evals, CLI
│   ├── models.py            # Document / Chunk / Answer / EvalReport dataclasses
│   ├── chunking.py          # heading-aware chunking (≤900 chars)
│   ├── retrieval.py         # TF-IDF-style keyword retriever
│   ├── answer.py            # extractive, cited answers + abstention (+ LLM interface)
│   ├── evals.py             # recall@3, keyword accuracy, abstention rates
│   └── cli.py               # `ask` and `evals` commands
├── data/                    # fictional sample corpus (4 documents)
├── evals/qa.jsonl           # 10 eval questions (8 answerable, 2 abstention tests)
├── examples/sample-qa.txt   # actual output from a sample run
├── tests/                   # 13 tests for chunking, retrieval, answers, evals
├── docs/
│   ├── ARCHITECTURE.md      # design, flow, extension points
│   ├── SECURITY.md          # what the demo can / cannot do
│   └── EVALS.md             # how the scores are computed, what they mean
├── .github/workflows/ci.yml # lint + tests + demo smoke test on every push
├── Dockerfile               # run the demo in a container, no local Python needed
└── pyproject.toml
```

## Status

**Demo — not client work.**

OrbitronOps has not yet delivered a client RAG system. This repository is a working prototype built to show how we build one: grounded answers, citations, honest abstention, and a measured eval harness a client would actually get.

If you want this wired to *your* documents, with embeddings, access control, and human-graded evals, talk to us: [orbitronops.com](https://www.orbitronops.com) · [LinkedIn](https://www.linkedin.com/company/orbitronops/)

## Roadmap

- [x] Deterministic keyword retrieval + cited extractive answers + abstention
- [x] Eval harness: recall@3, keyword accuracy, abstention rates
- [ ] Embeddings retriever behind the same interface (keyword stays as no-key fallback)
- [ ] Optional LLM explainer / summariser (pluggable, off by default)
- [ ] Human-graded evals on a real corpus, with an LLM judge as a second opinion
- [ ] Access control and document permissions for multi-team corpora

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and PRs welcome — please keep the grounded-answers rule intact: no invented content, no dropped abstention.

## License

MIT — see [LICENSE](LICENSE).
