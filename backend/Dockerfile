FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything needed
COPY backend/ ./backend/
COPY pipeline/ ./pipeline/
COPY data/ ./data/
COPY front/ ./front/

WORKDIR /app/backend

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn invision.wsgi:application --bind 0.0.0.0:$PORT --workers 2"]
