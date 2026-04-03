---
# template.md for setup-http-request
---

# HTTP File Template

```yaml
### Comment describing endpoint and seed data
# This file tests the Purchase API endpoints
# Seed data: merchants (550e8400...) must exist in dev DB

### Variables
@baseUrl = http://localhost:8001/api/v1
@adminToken = <generate-via-login-request-below>
@userToken = <generate-via-login-request-below>
@merchantId = 550e8400-e29b-41d4-a716-446655440000
@userId = 11111111-1111-1111-1111-111111111111

### Login (Admin)
POST {{baseUrl}}/auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "admin123"
}

@adminToken = {{response.body.access_token}}

### Login (User)
POST {{baseUrl}}/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "user123"
}

@userToken = {{response.body.access_token}}

### Create Purchase
POST {{baseUrl}}/purchases
Authorization: Bearer {{userToken}}
Content-Type: application/json

{
  "merchant_id": "{{merchantId}}",
  "amount": "50.00",
  "currency": "EUR",
  "external_id": "ext-{{$uuid}}"
}

### List Purchases (Admin)
GET {{baseUrl}}/purchases?page=1&page_size=10
Authorization: Bearer {{adminToken}}
```
