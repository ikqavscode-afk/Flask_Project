"""Точка входа: gunicorn main:app, flask --app main ..., python main.py."""

import os

from diary import create_app

app = create_app()

# Запуск для разработки (в продакшене используется gunicorn)
if __name__ == "__main__":  # pragma: no cover
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
