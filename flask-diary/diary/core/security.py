"""Заголовки безопасности для всех ответов.

Политика содержимого (CSP) строгая: разрешены только свои скрипты, стили и картинки,
встроенного кода нет. Поэтому в шаблонах нельзя использовать ``onclick=``,
``style=``, ``<script>`` без ``src`` и ``<style>``: подключайте файлы из ``static/``.
"""

from flask import request

CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        "img-src 'self' data:",
        "style-src 'self'",
        "script-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)

STATIC_HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}

# Год. Без includeSubDomains: домен может обслуживать и другие поддомены.
HSTS = "max-age=31536000"


def add_security_headers(response):
    headers = response.headers
    for name, value in STATIC_HEADERS.items():
        headers.setdefault(name, value)

    # HSTS отправляется только по HTTPS (за прокси схема берётся из X-Forwarded-Proto)
    if request.is_secure:
        headers.setdefault("Strict-Transport-Security", HSTS)

    # Страницы приложения содержат личные данные: не кэшируем их ни в браузере, ни в прокси
    # (иначе кнопка «Назад» после выхода показала бы чужие карточки). Статику не трогаем.
    if request.endpoint != "static":
        headers.setdefault("Cache-Control", "no-store")

    return response


def register_security_headers(app):
    app.after_request(add_security_headers)
