import pytest

from diary.cards.validation import validate_card


def test_card_valid_is_trimmed():
    data, errors = validate_card("  Заголовок ", " под ", "  текст\n")

    assert errors == []
    assert data == {"title": "Заголовок", "subtitle": "под", "text": "текст"}


def test_card_subtitle_is_optional():
    data, errors = validate_card("T", None, "x")

    assert errors == []
    assert data["subtitle"] == ""


@pytest.mark.parametrize(
    ("title", "subtitle", "text", "fragment"),
    [
        ("", "", "x", "Заголовок не может быть пустым"),
        ("   ", "", "x", "Заголовок не может быть пустым"),
        ("t" * 101, "", "x", "Заголовок не длиннее 100"),
        ("t", "s" * 101, "x", "Подзаголовок не длиннее 100"),
        ("t", "", "", "Текст не может быть пустым"),
        ("t", "", "   ", "Текст не может быть пустым"),
        ("t", "", "x" * 5001, "Текст не длиннее 5000"),
    ],
)
def test_card_invalid(title, subtitle, text, fragment):
    _, errors = validate_card(title, subtitle, text)

    assert any(fragment in e for e in errors)


def test_card_boundary_lengths_are_valid():
    _, errors = validate_card("t" * 100, "s" * 100, "x" * 5000)

    assert errors == []


def test_card_collects_all_errors():
    _, errors = validate_card("", "s" * 101, "")

    assert len(errors) == 3
