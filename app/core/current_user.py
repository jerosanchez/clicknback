from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.exceptions import InvalidTokenException
from app.auth.token_provider import JwtOAuth2TokenProvider, OAuth2TokenProviderABC
from app.core.database import get_db
from app.core.logging import logger
from app.users.composition import get_user_repository
from app.users.models import User, UserRoleEnum
from app.users.repositories import UserRepositoryABC

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_token_provider() -> OAuth2TokenProviderABC:
    return JwtOAuth2TokenProvider()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    token_provider: OAuth2TokenProviderABC = Depends(get_token_provider),
    user_repository: UserRepositoryABC = Depends(get_user_repository),
) -> User:
    logger.debug("Verifying access token.", extra={"token": token})
    payload = token_provider.verify_access_token(token)

    user = user_repository.get_user_by_id(db, payload.user_id or "")

    # Very unlikely to happen, but if the user was deleted after the token was issued,
    # we should reject the token
    if not user:
        logger.debug(
            "Token valid but user not found.",
            extra={"user_id": payload.user_id},
        )
        raise InvalidTokenException()

    if user.active is False:
        logger.debug(
            "Token valid but user is inactive.",
            extra={"user_id": payload.user_id},
        )
        raise InvalidTokenException()

    return user


def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.role == UserRoleEnum.admin:
        logger.debug(
            "Token valid but user is not an admin.",
            extra={"user_id": current_user.id, "user_role": current_user.role.value},
        )
        raise InvalidTokenException()

    return current_user
