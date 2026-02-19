from fastapi import HTTPException, status

from app.core.errors.builders import (
    authentication_error,
    business_rule_violation_error,
    forbidden_error,
    internal_server_error,
    unprocessable_entity_error,
    validation_error,
)
from app.core.errors.codes import ErrorCode


def test_validation_error():
    # Arrange
    error_code = "VALIDATION_FAILED"
    message = "Invalid input"
    details = [{"field": "email", "error": "required"}]

    # Act
    exc = validation_error(error_code, message, details)

    # Assert
    assert exc.status_code == status.HTTP_400_BAD_REQUEST
    detail = exc.detail  # type: ignore[attr-defined]
    assert detail["error"]["code"] == error_code  # type: ignore[index]
    assert detail["error"]["message"] == message  # type: ignore[index]
    assert detail["error"]["details"]["violations"] == details  # type: ignore[index]


def test_authentication_error():
    # Arrange
    message = "Unauthorized"
    details = {"reason": "token expired"}

    # Act
    exc = authentication_error(message, details)

    # Assert
    assert isinstance(exc, HTTPException)
    assert exc.status_code == status.HTTP_401_UNAUTHORIZED
    detail = exc.detail  # type: ignore[attr-defined]
    assert detail["error"]["code"] == ErrorCode.INVALID_CREDENTIALS  # type: ignore[index]
    assert detail["error"]["message"] == message  # type: ignore[index]
    assert detail["error"]["details"] == details  # type: ignore[index]


def test_forbidden_error():
    # Arrange
    message = "Forbidden"
    details = {"reason": "no access"}

    # Act
    exc = forbidden_error(message, details)

    # Assert
    assert isinstance(exc, HTTPException)
    assert exc.status_code == status.HTTP_403_FORBIDDEN
    detail = exc.detail  # type: ignore[attr-defined]
    assert detail["error"]["code"] == ErrorCode.FORBIDDEN  # type: ignore[index]
    assert detail["error"]["message"] == message  # type: ignore[index]
    assert detail["error"]["details"] == details  # type: ignore[index]


def test_business_rule_violation_error():
    # Arrange
    error_code = "CONFLICT"
    message = "Business rule violated"
    details = {"rule": "unique email"}

    # Act
    exc = business_rule_violation_error(error_code, message, details)

    # Assert
    assert isinstance(exc, HTTPException)
    assert exc.status_code == status.HTTP_409_CONFLICT
    detail = exc.detail  # type: ignore[attr-defined]
    assert detail["error"]["code"] == error_code  # type: ignore[index]
    assert detail["error"]["message"] == message  # type: ignore[index]
    assert detail["error"]["details"] == details  # type: ignore[index]


def test_unprocessable_entity_error():
    # Arrange
    error_code = "UNPROCESSABLE"
    message = "Cannot process"
    details = {"field": "age"}

    # Act
    exc = unprocessable_entity_error(error_code, message, details)

    # Assert
    assert isinstance(exc, HTTPException)
    assert exc.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    detail = exc.detail  # type: ignore[attr-defined]
    assert detail["error"]["code"] == error_code  # type: ignore[index]
    assert detail["error"]["message"] == message  # type: ignore[index]
    assert detail["error"]["details"] == details  # type: ignore[index]


def test_internal_server_error():
    # Arrange
    message = "Server error"
    details = {"request_id": "123", "timestamp": "2026-02-18T00:00:00"}

    # Act
    exc = internal_server_error(message, details)

    # Assert
    assert isinstance(exc, HTTPException)
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = exc.detail  # type: ignore[attr-defined]
    assert detail["error"]["code"] == ErrorCode.INTERNAL_SERVER_ERROR  # type: ignore[index]
    assert detail["error"]["message"] == message  # type: ignore[index]
    assert detail["error"]["details"] == details  # type: ignore[index]


def test_internal_server_error_default_details():
    # Arrange

    # Act
    exc = internal_server_error()

    # Assert
    assert isinstance(exc, HTTPException)
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = exc.detail  # type: ignore[attr-defined]
    assert detail["error"]["code"] == ErrorCode.INTERNAL_SERVER_ERROR  # type: ignore[index]
    assert detail["error"]["message"] == "An unexpected error occurred. Our team has been notified. Please retry later."  # type: ignore[index]
    assert "request_id" in detail["error"]["details"]  # type: ignore[index]
    assert "timestamp" in detail["error"]["details"]  # type: ignore[index]
