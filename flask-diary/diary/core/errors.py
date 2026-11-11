"""Страницы ошибок.

Страница ошибки не зависит от базы данных и сессии, а текст ошибки
и пользовательский ввод на ней не показываются.
"""

from http import HTTPStatus

from flask import current_app, render_template, request
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import HTTPException

ERROR_PAGES = {
    400: (
        'Некорректный запрос',
        'Не удалось обработать запрос. Обновите страницу и повторите действие.',
    ),
    404: ('Страница не найдена', 'Такой страницы нет. Проверьте адрес или вернитесь на главную.'),
    405: ('Действие не поддерживается', 'Это действие нельзя выполнить таким способом.'),
    413: ('Слишком большой запрос', 'Отправленные данные превышают допустимый размер.'),
    429: ('Слишком много попыток', 'Подождите немного и повторите действие.'),
    500: ('Внутренняя ошибка сервера', 'Что-то пошло не так. Попробуйте повторить действие позже.'),
}
DEFAULT_ERROR_PAGE = ('Ошибка', 'Не удалось выполнить запрос.')


def render_error(code, title, message):
    return render_template('errors/error.html', code=code, title=title, message=message), code


def handle_csrf_error(error):
    current_app.logger.warning('csrf rejected ip=%s', request.remote_addr)
    return render_error(
        400,
        'Сессия устарела',
        'Форма была отправлена с устаревшей страницы. Обновите страницу и повторите действие.',
    )


def handle_http_error(error):
    # перенаправления (3xx) пропускаем как есть
    if error.code is None or error.code < HTTPStatus.BAD_REQUEST:
        return error
    title, message = ERROR_PAGES.get(error.code, DEFAULT_ERROR_PAGE)
    return render_error(error.code, title, message)


def register_error_handlers(app):
    app.register_error_handler(CSRFError, handle_csrf_error)
    app.register_error_handler(HTTPException, handle_http_error)
