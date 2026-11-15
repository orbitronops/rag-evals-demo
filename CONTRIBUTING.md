# Contributing

Thanks for looking at this OrbitronOps demo.

## Ground rules

1. **Answers stay grounded.** No PR may let the answerer invent content beyond the retrieved chunks, or drop the abstention rule. The tests in `tests/test_rag.py` enforce this.
2. **No fake client claims.** Do not add a case study, logo, or testimonial for work that did not happen. This is a demo prototype, and the corpus documents are fictional.
3. **Every new eval question needs an expected source.** Add it to `evals/qa.jsonl`, and say in the PR whether it is answerable or an abstention test.

## Running it locally

```bash
python -m orbitronops_rag ask "How do I deploy checkout-api?"
python -m orbitronops_rag evals
python -m pytest -q
```
