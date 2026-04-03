---
name: setup-http-request
type: skill
description: Create HTTP request files for manual API testing
---

# Skill: Setup HTTP Request

Create `.http` files for manual API testing in VS Code or similar editors.

## File Structure

One file per endpoint:

```text
http/
  merchants/
    get-merchant.http
    list-merchants.http
    create-merchant.http
  purchases/
    create-purchase.http
    list-purchases.http
```

## File Contents

### Header & Variables

```yaml
@baseUrl = http://localhost:8001/api/v1
@adminToken = <placeholder_or_empty>
@userToken = <placeholder_or_empty>
@merchantId = 550e8400-e29b-41d4-a716-446655440000
```

### Helper Requests

Include token refresh requests that other requests can reuse:

```bash
### Refresh admin token
POST {{baseUrl}}/auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "admin123"
}

@adminToken = {{response.body.access_token}}

### List merchants (requires admin token)
GET {{baseUrl}}/merchants
Authorization: Bearer {{adminToken}}
```

### Request Examples

```bash
### Create a merchant
POST {{baseUrl}}/merchants
Authorization: Bearer {{adminToken}}
Content-Type: application/json

{
  "name": "Test Merchant",
  "default_cashback_percentage": 10.0,
  "active": true
}

### List merchants (paginated)
GET {{baseUrl}}/merchants?page=1&page_size=10&active=true
Authorization: Bearer {{adminToken}}
```

---
