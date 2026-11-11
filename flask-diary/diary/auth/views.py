"""Страницы регистрации, входа и выхода."""
import math

from flask import (
    Blueprint, current_app, flash, make_response, redirect,
    render_template, request, url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from ..core.errors import render_error
from ..extensions import login_manager
from ..logging_setup import safe_text
from . import services
from .validation import validate_password, validate_username

bp = Blueprint('auth', __name__)


@login_manager.user_loader
def load_user(user_id):
    return services.get_user(int(user_id))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        raw_username = request.form.get('username', '')
        password = request.form.get('password', '')

        if not raw_username.strip() or not password:
            flash('Заполните все поля', 'error')
            return redirect(url_for('auth.register'))

        username, error = validate_username(raw_username)
        if error is None:
            error = validate_password(password)
        if error:
            flash(error, 'error')
            return render_template('auth/register.html', username=raw_username), 400

        if services.find_user(username):
            flash('Такой пользователь уже существует', 'error')
            return redirect(url_for('auth.register'))

        user = services.create_user(username, password)
        current_app.logger.info('register ok user_id=%s ip=%s', user.id, request.remote_addr)
        flash('Регистрация прошла успешно! Теперь войдите.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@bp.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        ip = request.remote_addr or 'unknown'

        retry_after = services.login_retry_after(ip, username)
        if retry_after:
            current_app.logger.warning(
                'login blocked username=%r ip=%s retry_after=%ss',
                safe_text(username or ''), ip, retry_after,
            )
            minutes = max(1, math.ceil(retry_after / 60))
            body, code = render_error(
                429,
                'Слишком много попыток входа',
                f'Подождите {minutes} мин. и повторите попытку.',
            )
            response = make_response(body, code)
            response.headers['Retry-After'] = str(retry_after)
            return response

        user = services.find_user(username)
        if user and user.check_password(password):
            services.clear_failed_logins(ip, username)
            login_user(user)
            current_app.logger.info('login ok user_id=%s ip=%s', user.id, ip)
            return redirect(url_for('cards.index'))

        services.record_failed_login(ip, username)
        current_app.logger.warning(
            'login failed username=%r ip=%s', safe_text(username or ''), ip,
        )
        flash('Неверный логин или пароль', 'error')
        return redirect(url_for('auth.login'))

    return render_template('auth/login.html')


@bp.route('/logout/', methods=['POST'])
@login_required
def logout():
    current_app.logger.info('logout user_id=%s', current_user.id)
    logout_user()
    return redirect(url_for('core.home'))
