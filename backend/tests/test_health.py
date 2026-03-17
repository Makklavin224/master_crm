import pytest


@pytest.mark.anyio
async def test_health_check(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


@pytest.mark.anyio
async def test_api_v1_prefix(client):
    """Health endpoint only works under /api/v1 prefix, not at root."""
    # /api/v1/health should work
    response = await client.get("/api/v1/health")
    assert response.status_code == 200

    # /health should NOT work (404)
    response = await client.get("/health")
    assert response.status_code == 404
