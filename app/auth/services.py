from typing import Any

from sqlalchemy.orm import Session

from app.auth.clients import UserClientABC
from app.auth.exceptions import UserNotFoundException
from app.auth.models import Token, TokenPayload
from app.auth.providers import OAuth2TokenProviderABC


class AuthService:
    def __init__(
        self,
        users_client: UserClientABC,
        token_provider: OAuth2TokenProviderABC,
    ):
        self.users_client = users_client
        self.token_provider = token_provider

    def login(self, login_data: dict[str, Any], db: Session) -> Token:
        email = login_data["email"]
        user = self.users_client.get_user_by_email(db, email)

        if not user:
            raise UserNotFoundException(email)

        access_token = self.token_provider.create_access_token(
            payload=TokenPayload(user_id=str(user.id))
        )

        return Token(access_token=access_token, token_type="bearer")
