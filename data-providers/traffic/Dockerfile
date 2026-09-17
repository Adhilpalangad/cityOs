FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY data-providers/traffic/pyproject.toml ./
COPY data-providers/traffic/main.py ./
RUN pip install --no-cache-dir .
RUN useradd --create-home cityos
USER cityos
EXPOSE 8010
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
