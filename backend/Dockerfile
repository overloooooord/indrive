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

# Pre-download ONNX model into image so first request isn't slow
ENV MODEL_CACHE_DIR=/app/nlp_model_cache
RUN python -c "\
import os; os.makedirs('/app/nlp_model_cache', exist_ok=True); \
import sys; sys.path.insert(0, '/app/backend'); \
from nlp.nlp_model import _load_model; \
_load_model(); \
print('NLP model cached successfully')"

WORKDIR /app/backend

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn invision.wsgi:application --bind 0.0.0.0:$PORT --workers 2"]
