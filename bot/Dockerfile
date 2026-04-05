FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ ./bot/
COPY pipeline/nlp/ ./pipeline/nlp/

WORKDIR /app/bot

CMD ["python", "bot.py"]
