import os

# Должно быть задано до импорта приложения: адрес БД читается при создании engine.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
