"""
Integration tests for the authentication flow.

These tests verify that the FastAPI backend correctly:
  - Validates Entra ID (Azure AD) tokens via MSAL
  - Issues / refreshes sessions
  - Rejects invalid or expired tokens
  - Creates a user record on first login (JIT provisioning)

Prerequisites:
  - A running API server (or use pytest-asyncio with an ASGI test client)
  - TEST_ENTRA_TOKEN env var set to a valid short-lived dev token

Run with:
    pytest tests/integration/test_auth.py -v
"""

import os
import pytest

# ---------------------
# TODO: Import once the API is wired up.
# from httpx import AsyncClient
# from app.main import app
# ---------------------


@pytest.fixture
def test_token() -> str:
    """Return a test Entra ID token from the environment."""
    token = os.getenv("TEST_ENTRA_TOKEN", "")
    if not token:
        pytest.skip("TEST_ENTRA_TOKEN not set — skipping auth integration tests.")
    return token


class TestTokenValidation:
    """Tests that the /auth/me endpoint validates tokens correctly."""

    def test_placeholder_passes(self):
        """Placeholder — replace with real HTTP calls once API is running."""
        assert True

    @pytest.mark.skip(reason="API not yet implemented")
    @pytest.mark.asyncio
    async def test_valid_token_returns_200(self, test_token):
        """A valid Entra ID token should return HTTP 200 with user info."""
        # async with AsyncClient(app=app, base_url="http://test") as client:
        #     resp = await client.get(
        #         "/auth/me",
        #         headers={"Authorization": f"Bearer {test_token}"},
        #     )
        # assert resp.status_code == 200
        # assert "id" in resp.json()
        pass

    @pytest.mark.skip(reason="API not yet implemented")
    @pytest.mark.asyncio
    async def test_missing_token_returns_401(self):
        """Missing Authorization header should return HTTP 401."""
        pass

    @pytest.mark.skip(reason="API not yet implemented")
    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self):
        """A malformed or expired token should return HTTP 401."""
        pass

    @pytest.mark.skip(reason="API not yet implemented")
    @pytest.mark.asyncio
    async def test_wrong_audience_returns_401(self):
        """A token issued for a different app should be rejected."""
        pass


class TestJITProvisioning:
    """Tests that a new user is created in the DB on first authenticated request."""

    def test_placeholder_passes(self):
        assert True

    @pytest.mark.skip(reason="API not yet implemented")
    @pytest.mark.asyncio
    async def test_first_login_creates_user_record(self, test_token):
        """
        After the first successful auth call, a users row should exist
        with the matching entra_id and default plan = 'free'.
        """
        pass

    @pytest.mark.skip(reason="API not yet implemented")
    @pytest.mark.asyncio
    async def test_second_login_does_not_duplicate_user(self, test_token):
        """Subsequent logins with the same token must not create duplicate rows."""
        pass


class TestSession:
    """Tests for session / cookie behaviour (if applicable)."""

    def test_placeholder_passes(self):
        assert True

    @pytest.mark.skip(reason="API not yet implemented")
    @pytest.mark.asyncio
    async def test_logout_invalidates_session(self, test_token):
        pass
