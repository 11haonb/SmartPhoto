import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        with patch("app.core.database.engine") as mock_engine, \
             patch("app.core.sms.get_redis", new_callable=AsyncMock) as mock_redis:
            mock_conn = AsyncMock()
            mock_engine.connect.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_engine.connect.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_redis.return_value.ping = AsyncMock()

            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data


class TestAuthRoutes:
    @pytest.mark.asyncio
    async def test_send_code_validates_phone(self, client):
        response = await client.post(
            "/api/v1/auth/send-code",
            json={"phone": "123"},  # invalid phone
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_validates_phone(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={"phone": "123", "code": "123456"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_validates_code(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={"phone": "13800138000", "code": ""},
        )
        assert response.status_code == 422


class TestPhotosRoutes:
    @pytest.mark.asyncio
    async def test_upload_requires_auth(self, client):
        response = await client.post("/api/v1/photos/upload")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_batch_requires_auth(self, client):
        response = await client.post(
            "/api/v1/photos/batch",
            json={"total_photos": 5},
        )
        assert response.status_code in (401, 403)


class TestOrganizeRoutes:
    @pytest.mark.asyncio
    async def test_start_requires_auth(self, client):
        response = await client.post(
            "/api/v1/organize/start",
            json={"batch_id": "00000000-0000-0000-0000-000000000000"},
        )
        assert response.status_code in (401, 403)


class TestSettingsRoutes:
    @pytest.mark.asyncio
    async def test_get_providers_no_auth_needed(self, client):
        response = await client.get("/api/v1/settings/ai-providers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        providers = [p["provider"] for p in data]
        assert "local" in providers
        assert "claude" in providers
