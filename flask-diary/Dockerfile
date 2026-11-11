FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./
COPY diary ./diary
COPY migrations ./migrations

# Запуск не от root; /data — папка для базы данных
RUN useradd --create-home appuser && mkdir /data && chown appuser /data
USER appuser

ENV APP_ENV=production \
    DATABASE_URL=sqlite:////data/diary.db \
    PORT=8000

EXPOSE 8000

# Контейнер считается здоровым, если /health отвечает 200
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT', '8000'), timeout=3)"

# Сначала применяем миграции базы, затем запускаем сервер
CMD ["sh", "-c", "flask --app main db upgrade && gunicorn --bind 0.0.0.0:${PORT} --workers 2 --access-logfile - --access-logformat '%(h)s \"%(m)s %(U)s\" %(s)s %(b)s %(L)s' main:app"]
