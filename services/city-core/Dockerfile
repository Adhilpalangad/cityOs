FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY services/city-core/pyproject.toml ./
COPY services/city-core/app ./app
RUN pip install --no-cache-dir .
RUN useradd --create-home cityos
USER cityos
EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
