import random
import string
from typing import Optional

import pytest

from app.users.exceptions import PasswordNotComplexEnoughException
from app.users.policies import enforce_password_complexity


def random_password(length: int = 12, chars: Optional[str] = None) -> str:
    if chars is None:
        if length < 8:
            raise ValueError(
                "Password length must be at least 8 to satisfy complexity requirements."
            )
        # Ensure at least one from each category
        password = [
            random.choice(string.ascii_uppercase),
            random.choice(string.ascii_lowercase),
            random.choice(string.digits),
            random.choice(string.punctuation),
        ]
        all_chars = string.ascii_letters + string.digits + string.punctuation
        password += [random.choice(all_chars) for _ in range(length - 4)]
        random.shuffle(password)

        return "".join(password)
    else:
        return "".join(random.choice(chars) for _ in range(length))


@pytest.mark.parametrize(
    "password",
    [
        "Abcdef1!",  # minimal valid
        random_password(16),  # random valid
        "A1b2c3d4!@#",  # valid with multiple specials
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
    with pytest.raises(PasswordNotComplexEnoughException) as exc:
        enforce_password_complexity(password)
    assert expected_message in str(exc.value)


def test_enforce_password_complexity_succeeds_on_complex_enough_passwords() -> None:
    password = "ValidPass1!"
    enforce_password_complexity(password)
    # No exception should be raised
