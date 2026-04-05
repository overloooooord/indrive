FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY pipeline/ ./pipeline/
COPY data/ ./data/
COPY front/ ./front/
# NLP package (essay analysis, shared with bot)
COPY bot/nlp/ ./backend/nlp/

# NLP model will be lazy-loaded at first request (no HuggingFace auth needed at build)
ENV MODEL_CACHE_DIR=/app/nlp_model_cache

WORKDIR /app/backend

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn invision.wsgi:application --bind 0.0.0.0:$PORT --workers 2"]
