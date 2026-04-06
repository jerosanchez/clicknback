from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from app.auth import policies
from app.auth.clients import UsersClientABC
from app.auth.exceptions import (
    InvalidRefreshTokenException,
    RefreshTokenAlreadyUsedException,
)
from app.auth.models import TokenPayload, TokenResponse
from app.auth.repositories import RefreshTokenRepositoryABC
from app.auth.token_provider import OAuth2TokenProviderABC
from app.core.logging import logger
from app.core.unit_of_work import UnitOfWorkABC


class AuthService:

    def __init__(
        self,
        users_client: UsersClientABC,
        token_provider: OAuth2TokenProviderABC,
        refresh_token_repository: RefreshTokenRepositoryABC,
        verify_password: Callable[[str, str], bool],
    ):
        self.users_client = users_client
        self.token_provider = token_provider
        self.refresh_token_repository = refresh_token_repository
        self.verify_password = verify_password

    async def login(
        self, login_data: dict[str, Any], uow: UnitOfWorkABC
    ) -> TokenResponse:
        """Authenticate user and return access and refresh tokens."""
        email: str = login_data["email"]
        password: str = login_data["password"]

        user = await self.users_client.get_user_by_email(uow.session, email)

        # Enforce business rules via policies
        policies.enforce_user_exists(user, email)
        policies.enforce_password_valid(
            self.verify_password(password, str(user.hashed_password))
        )

        # Create access token
        access_token = self.token_provider.create_access_token(
            payload=TokenPayload(user_id=str(user.id), user_role=str(user.role))
        )

        # Create refresh token
        now = datetime.now(timezone.utc)
        refresh_token = await self._create_refresh_token_record(str(user.id), now, uow)

        await uow.commit()

        logger.info("Login attempt successful.", extra={"email": email})
        return TokenResponse(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )

    async def refresh(self, refresh_token: str, uow: UnitOfWorkABC) -> TokenResponse:
        """Refresh expired access token using a refresh token.

        Implements single-use token rotation: each refresh generates a new access token
        and a new refresh token. The old refresh token is marked as used and cannot be
        reused, preventing token replay attacks.

        Args:
            refresh_token: The refresh token from the client
            uow: Unit of Work for managing the database transaction

        Returns:
            TokenResponse with new access_token and refresh_token

        Raises:
            InvalidRefreshTokenException: If token is invalid, expired, or already used
        """
        try:
            # Verify the refresh token JWT signature and expiration
            user_id = self.token_provider.verify_refresh_token(refresh_token)
            token_hash = self.token_provider.hash_refresh_token(refresh_token)

            # Look up the refresh token in the database
            stored_token = await self.refresh_token_repository.get_by_hash(
                uow.session, token_hash
            )

            now = datetime.now(timezone.utc)

            # Enforce business rules via policies
            policies.enforce_refresh_token_exists(stored_token, user_id)
            policies.enforce_refresh_token_not_expired(stored_token, now)
            policies.enforce_refresh_token_not_used(stored_token)

            # Mark the old token as used (enforce single-use)
            await self.refresh_token_repository.mark_as_used(
                uow.session, stored_token.id, now
            )

            # Fetch user to get their role
            user = await self.users_client.get_user_by_id(uow.session, user_id)
            policies.enforce_user_exists_for_refresh(user, user_id)

            # Generate new access token
            new_access_token = self.token_provider.create_access_token(
                payload=TokenPayload(user_id=user_id, user_role=str(user.role))
            )

            # Generate new refresh token (token rotation)
            new_refresh_token = await self._create_refresh_token_record(
                user_id, now, uow
            )

            await uow.commit()

            logger.info(
                "Token refresh successful.",
                extra={"user_id": user_id, "old_token_id": stored_token.id},
            )

            return TokenResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
            )

        except (InvalidRefreshTokenException, RefreshTokenAlreadyUsedException):
            raise
        except Exception as e:
            logger.error("Error during token refresh.", extra={"error": str(e)})
            raise InvalidRefreshTokenException("Token refresh failed.")

    async def _create_refresh_token_record(
        self, user_id: str, now: datetime, uow: UnitOfWorkABC
    ) -> str:
        """Create a new refresh token record and return the token string.

        Generates a new refresh token, hashes it, and persists the record to the
        database. The token is automatically marked with an expiration time based
        on the configured refresh TTL. Does not commit the transaction; the caller
        is responsible for calling uow.commit() when all changes are complete.

        Args:
            user_id: ID of the user to create the token for
            now: Current datetime (allows time freezing in tests)
            uow: Unit of Work for transaction management

        Returns:
            The generated refresh token string
        """
        refresh_token = self.token_provider.create_refresh_token(user_id)
        token_hash = self.token_provider.hash_refresh_token(refresh_token)
        expires_at = now + timedelta(minutes=self.token_provider.refresh_ttl_in_minutes)

        await self.refresh_token_repository.create(
            uow.session,
            user_id=user_id,
            token_hash=token_hash,
            issued_at=now,
            expires_at=expires_at,  # type: ignore
        )

        return refresh_token
