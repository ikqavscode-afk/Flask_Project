<p align="center">
  <img src="flask-diary/static/img/logo.webp" alt="RAY" width="96" height="96">
</p>

# Flask_Project

[![Tests](https://github.com/ikqavscode-afk/Flask_Project/actions/workflows/tests.yml/badge.svg)](https://github.com/ikqavscode-afk/Flask_Project/actions/workflows/tests.yml)

<p align="center">
  <img src="flask-notes-blog/static/img/specialization.webp" alt="QA Engineering &amp; Python Development" width="420">
</p>

Сборник проектов на Python: веб-приложения на Flask, алгоритмы и консольное приложение на ООП.

## Как это выглядит

<p>
  <img src="docs/screenshots/diary-cards.webp" alt="Flask Diary: список карточек с поиском и пагинацией" width="64%">
  <img src="docs/screenshots/diary-mobile.webp" alt="Flask Diary на экране телефона" width="24%">
</p>

Больше снимков — в [описании Flask Diary](flask-diary/README.md#скриншоты).

## Проекты

### [Flask Diary](flask-diary/)
Дневник с карточками: регистрация, вход через Flask-Login, защищённые страницы, создание и просмотр карточек.
**Стек:** Flask, Flask-Login, Flask-SQLAlchemy, SQLite, Jinja2, CSS, pytest.

### [Flask Notes Blog](flask-notes-blog/)
Блог с заметками: регистрация и вход, хеширование паролей, токены сессии, миграции базы данных.
**Стек:** Flask, Flask-SQLAlchemy, Flask-Migrate (Alembic), SQLite, pytest.

### [Algorithms: динамическое программирование](algorithms-dp/)
Рюкзак 0/1, наибольшая общая подпоследовательность, разбиения числа, алгоритм Флойда–Уоршелла, размен монет, редакционное расстояние. Восстановление самого ответа, докстринги со сложностью, тесты со сверкой с полным перебором.
**Стек:** Python, pytest.

### [CLI Shop](cli-shop/)
Консольный симулятор магазина: каталог, корзина и четыре собственные реализации сортировки с пошаговым выводом.
**Стек:** Python, ООП, pytest.

## Быстрый старт

Инструкции по запуску и тестам находятся в README каждого проекта.

Тесты запускаются автоматически через GitHub Actions при каждом push (см. значок выше).

## Заметки по проектам

Как устроено приложение и как его расширять: [архитектура](docs/architecture.md).

Решения, трудности и возможные улучшения: [Flask Diary](docs/flask-diary.md), [Notes Blog](docs/flask-notes-blog.md), [CLI Shop](docs/cli-shop.md), [Algorithms](docs/algorithms-dp.md).

## Структура репозитория

```
Flask_Project/
├── flask-diary/
├── flask-notes-blog/
├── algorithms-dp/
├── cli-shop/
├── docs/
└── .github/workflows/tests.yml
```
