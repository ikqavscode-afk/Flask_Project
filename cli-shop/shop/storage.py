"""Сохранение и загрузка каталога в JSON-файл."""

import json
from pathlib import Path

from .models import Catalog, Product


def save_catalog(catalog, path):
    """Записывает каталог в JSON (создаёт папки, если их нет)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [product.to_dict() for product in catalog.get_list()]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_catalog(path):
    """Читает каталог из JSON.

    Возвращает None, если файла нет. Если файл повреждён или имеет
    неверный формат, выбрасывает ValueError.
    """
    path = Path(path)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        catalog = Catalog()
        for item in data:
            catalog.add_product(Product(**item))
        return catalog
    except (json.JSONDecodeError, TypeError, AttributeError) as error:
        raise ValueError(f"Некорректный файл каталога: {path}") from error
