---
# template.md for write-integration-tests
---

# Integration Test Template

```python
# tests/integration/<module>/test_<module>_<endpoint>.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_merchant_happy_path(admin_http_client: AsyncClient):
    """Create merchant successfully and verify persistence."""
    # Arrange
    merchant_data = {
        "name": "Test Merchant",
        "default_cashback_percentage": 12.5,
        "active": True
    }
    
    # Act
    response = await admin_http_client.post("/merchants", json=merchant_data)
    
    # Assert HTTP response
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Merchant"
    assert data["default_cashback_percentage"] == 12.5
    merchant_id = data["id"]
    
    # Verify database persistence
    verify_response = await admin_http_client.get(f"/merchants/{merchant_id}")
    assert verify_response.status_code == 200
    assert verify_response.json()["name"] == "Test Merchant"

@pytest.mark.asyncio
async def test_create_merchant_requires_admin(user_http_client: AsyncClient):
    """Non-admin users cannot create merchants."""
    # Arrange
    merchant_data = {
        "name": "Test Merchant",
        "default_cashback_percentage": 12.5,
        "active": True
    }
    
    # Act
    response = await user_http_client.post("/merchants", json=merchant_data)
    
    # Assert
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_create_merchant_validates_percentage(admin_http_client: AsyncClient):
    """Invalid percentage is rejected."""
    # Arrange
    merchant_data = {
        "name": "Test Merchant",
        "default_cashback_percentage": 150,  # Invalid: > 100
        "active": True
    }
    
    # Act
    response = await admin_http_client.post("/merchants", json=merchant_data)
    
    # Assert
    assert response.status_code == 422
    assert "cashback_percentage" in response.json()["detail"][0]["loc"]
```
