from typing import Any

from sqlalchemy.orm import Session

from app.auth.clients import UserClientABC
from app.auth.exceptions import UserNotFoundException
from app.auth.models import Token, TokenPayload


class AuthService:
    def __init__(self, user_client: UserClientABC):
        self.user_client = user_client

    def login(self, login_data: dict[str, Any], db: Session) -> Token:
        email = login_data["email"]
        user = self.user_client.get_user_by_email(db, email)

        if not user:
            raise UserNotFoundException(email)

        payload = TokenPayload(str(user.id))

        return Token(access_token=str(payload), token_type="bearer")
