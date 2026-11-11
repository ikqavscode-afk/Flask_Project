import pytest

from diary.auth.validation import validate_password, validate_username


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("alice", "alice"),
        ("  alice  ", "alice"),
        ("иван_1", "иван_1"),
        ("a.b-c_d", "a.b-c_d"),
        ("abc", "abc"),
        ("a" * 50, "a" * 50),
    ],
)
def test_username_valid(raw, expected):
    username, error = validate_username(raw)

    assert error is None
    assert username == expected


@pytest.mark.parametrize(
    "raw",
    ["ab", "a" * 51, "", None, "  ab  ", "bad name", "john!", "<script>", "a@b"],
)
def test_username_invalid(raw):
    _, error = validate_username(raw)

    assert error is not None


@pytest.mark.parametrize("raw", ["12345678", "a" * 128, " pass word ", "Пароль-123"])
def test_password_valid(raw):
    assert validate_password(raw) is None


@pytest.mark.parametrize("raw", ["1234567", "a" * 129, "        ", "", None])
def test_password_invalid(raw):
    assert validate_password(raw) is not None
