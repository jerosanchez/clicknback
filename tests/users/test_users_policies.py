import pytest

from app.users.exceptions import PasswordNotComplexEnoughException
from app.users.policies import enforce_password_complexity

_MINIMAL_VALID_PASSWORD = "Abcdef1!"
_TYPICAL_VALID_PASSWORD = "ValidPass1!"
_COMPLEX_VALID_PASSWORD = "A1b2c3d4!@#"


@pytest.mark.parametrize(
    "password",
    [
        _MINIMAL_VALID_PASSWORD,
        _TYPICAL_VALID_PASSWORD,
        _COMPLEX_VALID_PASSWORD,
    ],
)
def test_enforce_password_complexity_accepts_valid(password: str) -> None:
    # Should not raise
    enforce_password_complexity(password)


@pytest.mark.parametrize(
    "password,expected_message",
    [
        ("Ab1!", "at least 8 characters"),
        ("abcdefgh1!", "one uppercase"),
        ("ABCDEFGH1!", "one lowercase"),
        ("Abcdefgh!", "one digit"),
        ("Abcdefgh1", "one special character"),
    ],
)
def test_enforce_password_complexity_rejects_invalid(
    password: str, expected_message: str
) -> None:
    # Act & Assert
    with pytest.raises(PasswordNotComplexEnoughException) as exc:
        enforce_password_complexity(password)
    assert expected_message in str(exc.value)
