# Architecture

## Design goals

1. **A stranger can run it in 2 minutes** — no API key, no embeddings service, no cluster, no cloud bill.
2. **Deterministic** — same corpus + same question = same ranking, same answer, same eval scores. No hidden randomness in the demo path.
3. **Grounded by construction** — the answer is built only from retrieved chunks. If nothing relevant is retrieved, the answer is an abstention, not a guess.

## Flow

```
data/*.md
  → chunking.load_documents() / chunk_corpus()   # heading-aware chunks, ≤900 chars
  → retrieval.Retriever                          # TF-IDF-style keyword index
  → retrieval.retrieve(question, top_k=3)        # ranked chunks
  → answer.compose_answer()                      # extractive sentences + citations,
                                                 # or "I don't know from these documents."
  → CLI renders text or JSON
```

Evals run the same path over `evals/qa.jsonl`:

```
evals/qa.jsonl
  → evals.run_evals()   # recall@3, keyword accuracy, abstention rates
  → EvalReport          # text table or JSON
```

## Extension points

| Want to add… | Where |
|---|---|
| A new document | A new `*.md` file in `data/` — it is indexed automatically |
| A better retriever | A new class with the same `retrieve(query, top_k)` shape, swapped in `cli._build_retriever()` |
| Real embeddings | A new `retrieval.py` backend behind the same interface; keep the keyword retriever as the no-key fallback |
| An LLM explainer | Implement `answer.LLMExplainer.reword()` — it may only reword an existing answer using its cited chunks, never add facts |
| More eval questions | A new line in `evals/qa.jsonl` with `expected_source` and `expected_keywords` (or `answerable: false` for abstention tests) |
| A live corpus | A loader that reads from a docs site or wiki instead of `data/`; keep the fictional corpus as the default demo |

## What this is not (yet)

- Not a production RAG system — the corpus is 4 short fictional documents, and retrieval is keyword-based, not semantic.
- Not a chatbot — it answers one question at a time from the corpus; it has no memory or conversation state.
- Not a client delivery — see README Status. It is a prototype that shows how OrbitronOps builds: grounded answers, citations, and measured evals.
