from typing import Any, Callable

from sqlalchemy.orm import Session

from app.auth.clients import UsersClientABC
from app.auth.exceptions import PasswordVerificationException, UserNotFoundException
from app.auth.models import Token, TokenPayload
from app.auth.providers import OAuth2TokenProviderABC


class AuthService:

    def __init__(
        self,
        users_client: UsersClientABC,
        token_provider: OAuth2TokenProviderABC,
        verify_password: Callable[[str, str], bool],
    ):
        self.users_client = users_client
        self.token_provider = token_provider
        self.verify_password = verify_password

    def login(self, login_data: dict[str, Any], db: Session) -> Token:
        email: str = login_data["email"]
        password: str = login_data["password"]

        user = self.users_client.get_user_by_email(db, email)

        if not user:
            raise UserNotFoundException(email)

        if not self.verify_password(password, str(user.hashed_password)):
            raise PasswordVerificationException()

        access_token = self.token_provider.create_access_token(
            payload=TokenPayload(user_id=str(user.id), user_role=str(user.role))
        )

        return Token(access_token=access_token, token_type="bearer")
