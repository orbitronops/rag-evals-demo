# Evals — how the scores are computed, and what they mean

Run them with:

```bash
python -m orbitronops_rag evals
python -m orbitronops_rag evals --format json
```

The eval set is `evals/qa.jsonl`: 10 questions, 8 answerable and 2 unanswerable.
Each answerable question names the document the answer should come from
(`expected_source`) and the key facts the answer should contain
(`expected_keywords`).

## The four numbers

### Retrieval recall@3

Share of answerable questions whose expected source document appears in the
top 3 retrieved chunks. 1.0 means the retriever found the right document
every time; 0.0 means it never did. This measures retrieval only — it says
nothing about whether the composed answer was good.

### Mean keyword accuracy

For each answerable question that was actually answered, the share of its
expected keywords that appear in the answer text. Averaged over those
questions. **This is a proxy, not human judgement.** It checks that the
expected facts are present; it does not check that the answer is complete,
well worded, or free of extra wrong claims. A real client eval would add
human grading or an LLM judge — both are out of scope for this demo, and
neither would be run on a 10-question set and called a result.

### Abstention rate (unanswerable)

Share of unanswerable questions where the demo correctly said
"I don't know from these documents." 1.0 is the target: guessing at a
question the corpus cannot answer is the failure this demo is built to
avoid.

### False abstention rate

Share of answerable questions where the demo wrongly abstained. 0.0 is the
target: abstaining on a question the corpus *can* answer is also a failure,
just a quieter one.

## What the numbers do not mean

- They do not prove the demo would work on a real corpus. The corpus here
  is 4 short fictional documents; a real corpus is thousands of pages, with
  duplicates, stale pages, and contradictory answers.
- They do not prove keyword retrieval is good enough in general. Keyword
  retrieval fails on synonyms and paraphrase ("how do I ship it?" vs
  "deploy") — that is exactly why a production system would add embeddings.
- They are not a benchmark. 10 questions is a smoke test, not a dataset.
  The point of the harness is that the *method* is visible and repeatable:
  add questions, re-run, watch the numbers move.
