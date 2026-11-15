# Security

## What the demo can do

- Read the Markdown files you give it in `data/`.
- Print an answer (text or JSON) built from those files.
- Print eval scores for `evals/qa.jsonl`.

## What the demo cannot do

- It has no network access in the demo path.
- It cannot run shell commands, call an LLM, or execute any action.
- It stores no credentials. There is no place to put a token or API key in the demo.
- The optional `LLMExplainer` interface is not implemented in v0.1.0 — there is no code path that sends your documents anywhere.

## Grounded answers, not guesses

Every `Answer` is either:

- built only from retrieved chunks, with citations naming the source file and section, or
- an abstention: `"I don't know from these documents."`, with no citations and confidence 0.0.

That is the safety rule for a RAG system in a regulated team: a wrong confident answer is worse than an honest "I don't know".

## Reporting a problem

Open an issue in this repo. Do not include real customer data, real internal documents, or secrets in any issue, example, or eval question.
