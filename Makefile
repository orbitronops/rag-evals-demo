.PHONY: demo test lint clean

demo:
	python -m orbitronops_rag ask "How do I deploy checkout-api?"
	python -m orbitronops_rag evals

test:
	python -m pytest -q || python -m unittest discover -s tests -v

lint:
	python -m compileall -q src tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
