---
# template.md for write-e2e-tests
---

# E2E Test Template

```python
# tests/e2e/test_<workflow>.py
import pytest
from httpx import AsyncClient
import os

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8001/api/v1")

@pytest.mark.asyncio
async def test_complete_purchase_workflow():
    """Full flow: user auth → purchase → wallet update → payout request."""
    async with AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # Step 1: Authenticate
        auth_resp = await client.post(
            "/auth/register",
            json={"email": "e2e_test@example.com", "password": "test123!"}
        )
        assert auth_resp.status_code == 201
        user_token = auth_resp.json()["access_token"]
        
        # Step 2: Set up authenticated client
        client.headers.update({"Authorization": f"Bearer {user_token}"})
        
        # Step 3: Create purchase
        purchase_data = {
            "merchant_id": "550e8400-e29b-41d4-a716-446655440000",  # Seed data
            "amount": "50.00",
            "currency": "EUR",
            "external_id": f"e2e-{uuid.uuid4()}"
        }
        purchase_resp = await client.post("/purchases", json=purchase_data)
        assert purchase_resp.status_code == 201
        purchase = purchase_resp.json()
        assert purchase["status"] == "pending"
        
        # Step 4: Wait for background job (confirm purchase)
        await asyncio.sleep(2)  # Give job time to run
        
        # Step 5: Verify wallet updated
        wallet_resp = await client.get("/users/me/wallet")
        assert wallet_resp.status_code == 200
        wallet = wallet_resp.json()
        assert wallet["available"] > 0  # Cashback moved from pending
        
        # Step 6: Request payout
        payout_resp = await client.post(
            "/payouts",
            json={"amount": wallet["available"]}
        )
        assert payout_resp.status_code == 201
        assert payout_resp.json()["status"] == "pending"
```
