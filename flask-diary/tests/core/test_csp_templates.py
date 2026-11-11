"""Защита от возврата встроенного кода: он нарушил бы строгую политику CSP."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2] / 'diary'
TEMPLATES = sorted((ROOT / 'templates').rglob('*.html'))

FORBIDDEN = {
    'встроенный обработчик (onclick=, onsubmit=…)': re.compile(r'\son[a-z]+\s*=', re.IGNORECASE),
    'встроенный стиль (style="…")': re.compile(r'\sstyle\s*=', re.IGNORECASE),
    'тег <style>': re.compile(r'<style\b', re.IGNORECASE),
    'встроенный скрипт (<script> без src)': re.compile(r'<script\b(?![^>]*\bsrc=)', re.IGNORECASE),
    'адрес javascript:': re.compile(r'javascript:', re.IGNORECASE),
}


def test_templates_were_found():
    assert len(TEMPLATES) >= 10


@pytest.mark.parametrize('template', TEMPLATES, ids=lambda path: path.relative_to(ROOT).as_posix())
def test_template_has_no_inline_code(template):
    text = template.read_text(encoding='utf-8')

    found = [name for name, pattern in FORBIDDEN.items() if pattern.search(text)]

    assert not found, f'{template.name}: {found}'


@pytest.mark.parametrize(
    'script', sorted((ROOT / 'static' / 'js').glob('*.js')), ids=lambda p: p.name
)
def test_scripts_avoid_dangerous_apis(script):
    text = script.read_text(encoding='utf-8')

    for dangerous in ('eval(', 'innerHTML', 'document.write', 'new Function'):
        assert dangerous not in text, f'{script.name}: {dangerous}'
