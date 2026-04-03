---
name: write-e2e-tests
type: skill
description: Write end-to-end tests using full Docker Compose stack
---

# Skill: Write E2E Tests

Write end-to-end tests that exercise full HTTP flows against a complete Docker Compose stack.

## When to Write E2E Tests

- For critical user workflows (e.g., "register → make purchase → request payout")
- AFTER unit and integration tests pass
- Sparingly: E2E tests are slow (5–30s per test)

## Setup

E2E tests require a running Docker Compose stack:

```bash
docker-compose -f docker-compose.e2e.yml up -d
export E2E_BASE_URL="http://localhost:8001/api/v1"
make test-e2e
```

## Test Structure

```python
# tests/e2e/test_purchase_workflow.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_user_workflow_register_purchase_withdraw():
    """End-to-end: User registers, makes purchase, requests payout."""
    async with AsyncClient(base_url="http://localhost:8001/api/v1") as client:
        # 1. Register user
        register_response = await client.post(
            "/auth/register",
            json={"email": "e2e@test.com", "password": "secure123"}
        )
        assert register_response.status_code == 201
        user_token = register_response.json()["token"]
        
        # 2. Create authenticated client
        client.headers["Authorization"] = f"Bearer {user_token}"
        
        # 3. Submit purchase
        purchase_response = await client.post(
            "/purchases",
            json={
                "merchant_id": "<known_merchant_id>",
                "amount": "100.00",
                "currency": "EUR",
                "external_id": "e2e-001"
            }
        )
        assert purchase_response.status_code == 201
        
        # 4. Verify wallet updated
        wallet_response = await client.get("/users/me/wallet")
        assert wallet_response.json()["pending"] == "10.00"  # 10% cashback
        
        # 5. Request payout
        payout_response = await client.post(
            "/payouts",
            json={"amount": "10.00"}
        )
        assert payout_response.status_code == 201
```

---
