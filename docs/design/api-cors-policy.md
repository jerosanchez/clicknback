# API CORS Policy

## Quick Reference (TL;DR)

**For Web Apps:**
- Add your origin to `CORS_ALLOWED_ORIGINS` environment variable
- Browser will automatically send `Origin` header; server will respond with `Access-Control-Allow-Origin`
- If origin not allowed, you'll see CORS error in browser console

**For Mobile Apps:**
- CORS does not apply (native apps don't enforce it)
- Just send JWT bearer token in `Authorization` header
- Use HTTPS only in production

**For New Origins:**
- Create GitHub issue labeled `feature:cors-new-origin`
- Include origin, business context, expected traffic
- Follow security review process (see "Requesting New Origins" section below)

---

## Overview

ClickNBack enforces a strict Cross-Origin Resource Sharing (CORS) policy to protect the API while enabling legitimate clients (web applications and mobile apps) to access resources securely.

**Key principle**: CORS is a **browser security mechanism**. Native mobile apps (iOS, Android) do not enforce it; they are considered equivalent to server-to-server requests. Web applications running in browsers must comply with CORS rules.

---

## How CORS Works

### For Web Applications

Web browsers enforce the **Same-Origin Policy** — JavaScript code can only make HTTP requests to the same origin (protocol + domain + port) from which the page was loaded. To allow cross-origin requests, the server sends CORS headers:

1. Browser makes a request to `https://api.clicknback.com/api/v1/purchases`
2. Request includes the `Origin: https://app.clicknback.com` header
3. Server responds with `Access-Control-Allow-Origin: https://app.clicknback.com`
4. Browser sees the matching origin and allows the response to reach JavaScript

If the origin is not allowed, the browser blocks the response and logs a CORS error in the console.

### For Mobile Apps (iOS, Android)

**Native mobile apps do not enforce CORS.** They are not constrained by the Same-Origin Policy. A mobile app can make HTTP requests to any domain without CORS preflight or origin headers.

Instead, mobile apps rely on:

- **Authentication tokens** (Bearer JWT) — proves the app is authorized to call the API
- **HTTPS** — encrypts the request in transit
- **API versioning and rate limiting** — protects the API from abuse
- **Server-side authorization** — checks permissions inside the API (which role can access which resources)

**Important**: The absence of CORS does not mean the API is unprotected. Security comes from authentication, authorization, and rate limiting.

---

## Allowed Origins

### Production Environment

| Origin | Type | Use Case |
|--------|------|----------|
| `https://clicknback.com` | Primary domain | Official web dashboard |
| `https://app.clicknback.com` | Subdomain | Customer-facing web app |
| `https://admin.clicknback.com` | Subdomain | Partner admin portal |

### Staging Environment

| Origin | Type | Use Case |
|--------|------|----------|
| `https://staging.clicknback.com` | Staging domain | Staging web app |
| `http://localhost:*` | Wildcard port | Local development on `localhost` |
| `http://127.0.0.1:*` | Wildcard port | Local development on `127.0.0.1` |

### Never use wildcard origins in production

A wildcard CORS origin (`Access-Control-Allow-Origin: *`) means **any website** can make requests to the API on behalf of users. This is dangerous if the API has side effects (which ClickNBack does — purchases, payouts, wallet updates).

**Always use an explicit allowlist.**

---

## HTTP Methods and Headers

### Allowed Methods

The API accepts the following HTTP methods:

```text
GET, POST, PUT, PATCH, DELETE, OPTIONS
```

- `OPTIONS` is used for preflight requests (automatic; no direct calls)
- `GET` retrieves resources (read-only)
- `POST` creates resources
- `PUT` / `PATCH` update resources
- `DELETE` destroys resources

### Allowed Headers

The following request headers are permitted:

```text
Content-Type, Authorization, Accept, Accept-Language, User-Agent
```

- `Content-Type` — specifies request body format (usually `application/json`)
- `Authorization` — carries the JWT bearer token
- `Accept` — specifies response format (usually `application/json`)
- `Accept-Language` — indicates preferred language
- `User-Agent` — identifies the client application

### Credentials

The CORS policy allows credentials (cookies, authorization headers):

```text
Access-Control-Allow-Credentials: true
```

This means the browser will include cookies and the `Authorization` header in cross-origin requests. Credentials are required for stateful sessions and token-based auth.

---

## Preflight Requests

When a web browser makes a "complex" request (anything other than `GET`, `HEAD`, or `POST` with simple headers), it first sends an automatic preflight request using the `OPTIONS` method:

### Example: Web App Updating a Purchase

#### Browser sends a preflight request

```http
OPTIONS /api/v1/purchases/123 HTTP/1.1
Origin: https://app.clicknback.com
Access-Control-Request-Method: PATCH
Access-Control-Request-Headers: Content-Type, Authorization
```

#### Server responds with allowed methods and headers

```http
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://app.clicknback.com
Access-Control-Allow-Methods: GET, POST, PATCH, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 86400
```

#### Browser sends the actual request (if preflight succeeded)

```http
PATCH /api/v1/purchases/123 HTTP/1.1
Origin: https://app.clicknback.com
Authorization: Bearer <jwt-token>
Content-Type: application/json

{
  "status": "confirmed"
}
```

#### Server responds with endpoint response

```http
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://app.clicknback.com
Content-Type: application/json

{
  "id": "...",
  "status": "confirmed"
}
```

`Access-Control-Max-Age: 86400` tells the browser to cache the preflight result for 24 hours, avoiding repeated preflight requests.

---

## Requesting New Origins

### Process

To request a new origin (e.g., a partner's web application), follow these steps:

1. **Document the request**:
   - Partner name and website
   - Origin (e.g., `https://partner-app.example.com`)
   - Expected traffic volume
   - Business justification

2. **Create a GitHub issue** labeled `feature:cors-new-origin`:
   - Title: `[CORS] Allow origin https://partner-app.example.com`
   - Description: Include the business context

3. **Security review**:
   - Verify the origin is HTTPS (except for localhost in dev)
   - Confirm the partner organization owns the domain
   - Check for any known security risks

4. **Update the configuration** (see Configuration section below)

5. **Test the preflight requests** (see Testing section below)

6. **Deploy to staging**, verify, then promote to production

---

## Configuration

### Environment Variables

The CORS policy is configured via environment variables. Set them in `.env` or your deployment environment:

```bash
# Comma-separated list of allowed origins (no spaces)
CORS_ALLOWED_ORIGINS=https://app.clicknback.com,https://admin.clicknback.com

# Optional: regex pattern for development (localhost with any port)
CORS_ALLOW_ORIGIN_REGEX=http://localhost(:\d+)?
```

### Default Values

**Development** (`.env` file):

```bash
CORS_ALLOWED_ORIGINS=https://clicknback.com
CORS_ALLOW_ORIGIN_REGEX=http://localhost(:\d+)?
```

**Staging**:

```bash
CORS_ALLOWED_ORIGINS=https://staging.clicknback.com
CORS_ALLOW_ORIGIN_REGEX=http://localhost(:\d+)?
```

**Production**:

```bash
CORS_ALLOWED_ORIGINS=https://clicknback.com,https://app.clicknback.com,https://admin.clicknback.com
```

### Code Configuration

The `CORSMiddleware` in `app/main.py` is configured as follows:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,         # explicit list
    allow_origin_regex=settings.cors_allow_origin_regex,  # regex for dev
    allow_credentials=True,                               # allow Authorization headers
    allow_methods=["*"],                                  # all standard HTTP methods
    allow_headers=["*"],                                  # all standard headers
)
```

---

## Local Development Setup

### Configure Your `.env` for Testing

During local development, you need to allow requests from your development servers (typically running on `localhost` with various ports). The recommended approach is to use **both** explicit origins and a regex pattern:

**In your `.env` file:**

```bash
CORS_ALLOWED_ORIGINS=https://clicknback.com
CORS_ALLOW_ORIGIN_REGEX=http://localhost(:\d+)?|http://127.0.0.1(:\d+)?
```

This configuration allows:

- ✅ Production domain: `https://clicknback.com`
- ✅ Any localhost port: `http://localhost:3000`, `http://localhost:8000`, `http://localhost:5173`, etc.
- ✅ Any `127.0.0.1` port: `http://127.0.0.1:3000`, etc.

### Alternative: Explicit Localhost Origins

If you prefer to be more restrictive and only allow specific development servers, list them explicitly:

```bash
CORS_ALLOWED_ORIGINS=https://clicknback.com,http://localhost:3000,http://localhost:8000
```

Choose whichever approach matches your development workflow.

### Testing Your Configuration

After setting `.env`, restart the development server:

```bash
make dev  # or: make up && make dev
```

Then test from your web app (see "Testing CORS Configuration" section below for examples).

**Note**: `.env` is **gitignored** and never committed. Each developer can have their own local CORS settings without affecting others. Production uses VPS environment variables (never a `.env` file from the repository).

---

## Testing CORS Configuration

### Manual Test: Preflight Request

Use `curl` to test a preflight request:

```bash
curl -X OPTIONS https://api.clicknback.com/api/v1/purchases \
  -H "Origin: https://app.clicknback.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type, Authorization" \
  -v
```

**Expected response** (HTTP 200):

```text
Access-Control-Allow-Origin: https://app.clicknback.com
Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 86400
```

### Manual Test: Simple Request

```bash
curl -X GET https://api.clicknback.com/api/v1/merchants \
  -H "Origin: https://app.clicknback.com" \
  -H "Authorization: Bearer <valid-jwt-token>" \
  -v
```

**Expected response** (HTTP 200):

```text
Access-Control-Allow-Origin: https://app.clicknback.com
Content-Type: application/json
[...]
```

### Browser Test: Web App Integration

In your web application's browser console (F12), make a fetch request:

```javascript
fetch('https://api.clicknback.com/api/v1/merchants', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer <valid-jwt-token>',
    'Content-Type': 'application/json',
  },
  credentials: 'include', // include cookies
})
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('CORS error:', error));
```

If CORS is misconfigured, you will see an error in the browser console like:

```text
Access to XMLHttpRequest at 'https://api.clicknback.com/...' from origin 'https://app.clicknback.com' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

### Mobile App Test: HTTP Request

Native mobile apps do not enforce CORS, so they will succeed regardless of CORS headers. However, verify the request is properly authenticated:

**iOS (Swift)**:

```swift
var request = URLRequest(url: URL(string: "https://api.clicknback.com/api/v1/merchants")!)
request.httpMethod = "GET"
request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")

URLSession.shared.dataTask(with: request) { data, response, error in
    if let data = data {
        let merchants = try? JSONDecoder().decode([Merchant].self, from: data)
        print(merchants ?? [])
    }
}.resume()
```

**Android (Kotlin)**:

```kotlin
val request = Request.Builder()
    .url("https://api.clicknback.com/api/v1/merchants")
    .addHeader("Authorization", "Bearer $jwtToken")
    .build()

client.newCall(request).enqueue(object : Callback {
    override fun onResponse(call: Call, response: Response) {
        val merchants = Json.decodeFromString<List<Merchant>>(response.body?.string() ?: "[]")
        println(merchants)
    }
    override fun onFailure(call: Call, exception: IOException) {
        exception.printStackTrace()
    }
})
```

---

## Common Issues and Debugging

### Issue: "No 'Access-Control-Allow-Origin' header"

**Cause**: The request origin is not in the allowed list.

**Fix**:

1. Check the `Origin` header in the request
2. Verify it matches an entry in `CORS_ALLOWED_ORIGINS`
3. If it's a new partner, follow the "Requesting New Origins" process

### Issue: Preflight Request Succeeds, Actual Request Fails

**Cause**: The `Authorization` header or request method is not allowed.

**Fix**:

1. Verify `Authorization` is in `CORS_ALLOW_HEADERS`
2. Verify the HTTP method (`PATCH`, `DELETE`, etc.) is in `CORS_ALLOW_METHODS`
3. Check server logs for the actual error (often not a CORS issue)

### Issue: Mobile App Makes Requests Successfully, But Browser App Fails

**Cause**: Browsers enforce CORS; mobile apps do not.

**Fix**:

1. Check the browser's Development Tools → Network tab
2. Look for the preflight request (`OPTIONS`)
3. Verify the response includes correct `Access-Control-*` headers
4. If origin not in list, request it via GitHub

### Issue: CORS Works in Staging, But Not Production

**Cause**: Production and staging have different `CORS_ALLOWED_ORIGINS` values.

**Fix**:

1. Verify the production `CORS_ALLOWED_ORIGINS` environment variable is set
2. Confirm it includes the partner's origin
3. Redeploy the configuration

---

## Security Considerations

### 1. Never Use Wildcard Origins in Production

```text
❌ WRONG (production)
Access-Control-Allow-Origin: *

✅ CORRECT
Access-Control-Allow-Origin: https://app.clicknback.com
```

A wildcard origin exposes your API to **any website**, enabling credential theft and data exfiltration.

### 2. Always Use HTTPS

```text
❌ WRONG
http://app.example.com  (no SSL/TLS)

✅ CORRECT
https://app.example.com  (SSL/TLS encrypted)
```

CORS headers are only sent over HTTPS to prevent interception.

### 3. Require Authentication

CORS does not provide authentication. Always require valid JWT tokens or API keys, even for read-only endpoints:

```python
@router.get("/merchants")
async def list_merchants(current_user: User = Depends(get_current_user)):
    # CORS allows the request to reach here, but the endpoint still
    # checks that the user is authenticated
    return merchants
```

### 4. Use CORS for Browsers, Not APIs

If you're building backend-to-backend (API-to-API) communication, CORS is not the right tool:

- Use mutual TLS (mTLS) or VPN
- Use service accounts with API keys
- Firewall rules (IP allowlist)

---

## Related Documentation

- [Security Strategy](security-strategy.md) — authentication, authorization, data protection
- [Error Handling Strategy](error-handling-strategy.md) — how CORS errors are reported
- [Deployment Plan](deployment-plan.md) — environment-specific configuration

---
