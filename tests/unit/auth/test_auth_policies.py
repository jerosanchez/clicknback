from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from app.auth import policies
from app.auth.exceptions import (
    InvalidRefreshTokenException,
    PasswordVerificationException,
    RefreshTokenAlreadyUsedException,
    UserNotFoundException,
)

# ──────────────────────────────────────────────────────────────────────────────
# enforce_user_exists
# ──────────────────────────────────────────────────────────────────────────────


def test_enforce_user_exists_raises_on_none() -> None:
    # Act & Assert
    with pytest.raises(UserNotFoundException):
        policies.enforce_user_exists(None, "alice@example.com")


def test_enforce_user_exists_logs_warning_on_none() -> None:
    # Arrange
    email = "alice@example.com"

    # Act & Assert
    with patch("app.auth.policies.logger") as mock_logger:
        with pytest.raises(UserNotFoundException):
            policies.enforce_user_exists(None, email)
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert "enumeration attack" in call_args[0][0].lower()
        assert call_args[1]["extra"]["email"] == email


def test_enforce_user_exists_passes_on_user_found() -> None:
    # Arrange
    user = Mock()

    # Act & Assert (no exception should be raised)
    policies.enforce_user_exists(user, "alice@example.com")


# ──────────────────────────────────────────────────────────────────────────────
# enforce_password_valid
# ──────────────────────────────────────────────────────────────────────────────


def test_enforce_password_valid_raises_on_false() -> None:
    # Act & Assert
    with pytest.raises(PasswordVerificationException):
        policies.enforce_password_valid(False)


def test_enforce_password_valid_logs_warning_on_false() -> None:
    # Act & Assert
    with patch("app.auth.policies.logger") as mock_logger:
        with pytest.raises(PasswordVerificationException):
            policies.enforce_password_valid(False)
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert "brute force" in call_args[0][0].lower()


def test_enforce_password_valid_passes_on_true() -> None:
    # Act & Assert (no exception should be raised)
    policies.enforce_password_valid(True)


# ──────────────────────────────────────────────────────────────────────────────
# enforce_refresh_token_exists
# ──────────────────────────────────────────────────────────────────────────────


def test_enforce_refresh_token_exists_raises_on_none() -> None:
    # Act & Assert
    with pytest.raises(InvalidRefreshTokenException):
        policies.enforce_refresh_token_exists(None, "user-123")


def test_enforce_refresh_token_exists_logs_warning_on_none() -> None:
    # Arrange
    user_id = "user-123"

    # Act & Assert
    with patch("app.auth.policies.logger") as mock_logger:
        with pytest.raises(InvalidRefreshTokenException):
            policies.enforce_refresh_token_exists(None, user_id)
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert (
            "tampering" in call_args[0][0].lower()
            or "attack" in call_args[0][0].lower()
        )
        assert call_args[1]["extra"]["user_id"] == user_id


def test_enforce_refresh_token_exists_passes_on_token_found() -> None:
    # Arrange
    token = Mock()

    # Act & Assert (no exception should be raised)
    policies.enforce_refresh_token_exists(token, "user-123")


# ──────────────────────────────────────────────────────────────────────────────
# enforce_refresh_token_not_expired
# ──────────────────────────────────────────────────────────────────────────────


def test_enforce_refresh_token_not_expired_raises_on_expired() -> None:
    # Arrange
    token = Mock()
    token.is_expired.return_value = True
    token.id = "token-123"
    now = datetime.now(timezone.utc)

    # Act & Assert
    with pytest.raises(InvalidRefreshTokenException):
        policies.enforce_refresh_token_not_expired(token, now)


def test_enforce_refresh_token_not_expired_logs_warning_on_expired() -> None:
    # Arrange
    token = Mock()
    token.is_expired.return_value = True
    token.id = "token-123"
    now = datetime.now(timezone.utc)

    # Act & Assert
    with patch("app.auth.policies.logger") as mock_logger:
        with pytest.raises(InvalidRefreshTokenException):
            policies.enforce_refresh_token_not_expired(token, now)
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert "expired" in call_args[0][0].lower()
        assert call_args[1]["extra"]["token_id"] == "token-123"


def test_enforce_refresh_token_not_expired_passes_on_valid() -> None:
    # Arrange
    token = Mock()
    token.is_expired.return_value = False
    now = datetime.now(timezone.utc)

    # Act & Assert (no exception should be raised)
    policies.enforce_refresh_token_not_expired(token, now)


# ──────────────────────────────────────────────────────────────────────────────
# enforce_refresh_token_not_used
# ──────────────────────────────────────────────────────────────────────────────


def test_enforce_refresh_token_not_used_raises_on_used() -> None:
    # Arrange
    token = Mock()
    token.id = "token-123"
    token.is_used.return_value = True

    # Act & Assert
    with pytest.raises(RefreshTokenAlreadyUsedException):
        policies.enforce_refresh_token_not_used(token)


def test_enforce_refresh_token_not_used_logs_warning_on_used() -> None:
    # Arrange
    token = Mock()
    token.id = "token-123"
    token.is_used.return_value = True

    # Act & Assert
    with patch("app.auth.policies.logger") as mock_logger:
        with pytest.raises(RefreshTokenAlreadyUsedException):
            policies.enforce_refresh_token_not_used(token)
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert "replay attack" in call_args[0][0].lower()
        assert call_args[1]["extra"]["token_id"] == "token-123"


def test_enforce_refresh_token_not_used_passes_on_not_used() -> None:
    # Arrange
    token = Mock()
    token.is_used.return_value = False

    # Act & Assert (no exception should be raised)
    policies.enforce_refresh_token_not_used(token)


# ──────────────────────────────────────────────────────────────────────────────
# enforce_user_exists_for_refresh
# ──────────────────────────────────────────────────────────────────────────────


def test_enforce_user_exists_for_refresh_raises_on_none() -> None:
    # Act & Assert
    with pytest.raises(InvalidRefreshTokenException):
        policies.enforce_user_exists_for_refresh(None, "user-123")


def test_enforce_user_exists_for_refresh_logs_error_on_none() -> None:
    # Arrange
    user_id = "user-123"

    # Act & Assert
    with patch("app.auth.policies.logger") as mock_logger:
        with pytest.raises(InvalidRefreshTokenException):
            policies.enforce_user_exists_for_refresh(None, user_id)
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "not found" in call_args[0][0].lower()
        assert call_args[1]["extra"]["user_id"] == user_id


def test_enforce_user_exists_for_refresh_passes_on_user_found() -> None:
    # Arrange
    user = Mock()

    # Act & Assert (no exception should be raised)
    policies.enforce_user_exists_for_refresh(user, "user-123")
