FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY static ./static
COPY templates ./templates

# Запуск не от root; /data — папка для базы данных
RUN useradd --create-home appuser && mkdir /data && chown appuser /data
USER appuser

ENV DATABASE_URL=sqlite:////data/diary.db \
    PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 2 main:app"]
