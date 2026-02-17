# Reverse purchase

**Endpoint:** `PATCH /purchases/{id}/reverse`

**Roles:** Admin

## Success Response

**Status:** 200 OK

```json
{
  "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "reversed",
  "cashback_amount": 0
}
```
