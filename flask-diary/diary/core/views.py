"""Общие страницы: главная и проверка работоспособности."""
from flask import Blueprint, jsonify, render_template
from sqlalchemy import text

from ..extensions import db

bp = Blueprint('core', __name__)


@bp.route('/home')
def home():
    return render_template('core/home.html')


@bp.route('/health')
def health():
    """Проверка работоспособности для хостинга и мониторинга.

    Доступна без входа. Возвращает 200, если база отвечает, иначе 503.
    Подробности ошибки наружу не отдаются.
    """
    try:
        db.session.execute(text('SELECT 1'))
        status, code = 'ok', 200
    except Exception:
        db.session.rollback()
        status, code = 'error', 503

    response = jsonify(status=status)
    response.status_code = code
    response.headers['Cache-Control'] = 'no-store'
    return response
