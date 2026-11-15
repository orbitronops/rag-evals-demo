FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY data ./data
COPY evals ./evals
RUN pip install --no-cache-dir -e .
ENTRYPOINT ["python", "-m", "orbitronops_rag"]
CMD ["ask", "How do I deploy checkout-api?"]
