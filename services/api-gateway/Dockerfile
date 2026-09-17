FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY services/api-gateway/pyproject.toml ./
COPY services/api-gateway/app ./app
RUN pip install --no-cache-dir .
RUN useradd --create-home cityos
USER cityos
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

