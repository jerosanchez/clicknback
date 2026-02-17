# ADR 008: JWT-Based Stateless Authentication

## Status

Accepted

## Context

ClickNBack is an API-first backend serving multiple clients (web, mobile, third-party integrations). All require scalable, stateless authentication.

### Authentication Approaches

#### Option 1: Session-Based (Traditional)

```python
# User logs in → Server creates session → Session ID in cookie
@app.post("/login")
def login(email: str, password: str, db: Session):
    user = verify_credentials(email, password, db)
    session_id = create_session(user.id, db)  # Stored in DB
    return {"session_id": session_id}  # Return to client

# Each request checks session in DB
@app.get("/dashboard")
def get_dashboard(session_id: str, db: Session):
    user = db.query(Session).filter(Session.id == session_id).user  # DB lookup
    return {...}
```

- ✅ Revocation is immediate (delete session from DB)
- ✅ Simple to understand
- ❌ Requires DB lookup on every request
- ❌ Doesn't scale well (session state is shared)
- ❌ Mobile clients struggle with cookies
- ❌ Third-party integrations need token-based auth anyway

#### Option 2: JWT (JSON Web Tokens)

```python
# User logs in → Server returns signed JWT
@app.post("/login")
def login(email: str, password: str):
    user = verify_credentials(email, password)
    token = jwt.encode({"user_id": user.id, "role": user.role, "exp": ...})
    return {"access_token": token}

# Each request validates token signature (no DB lookup)
@app.get("/dashboard")
def get_dashboard(token: str):
    payload = jwt.decode(token)  # Validates signature, expiration
    user_id = payload["user_id"]  # No DB needed
    return {...}
```

- ✅ Stateless (no session storage)
- ✅ O(1) validation (cryptographic signature check)
- ✅ Scales horizontally (any server can validate any token)
- ✅ API-native (fits REST patterns)
- ✅ Mobile and third-party friendly
- ❌ Revocation delayed until expiration
- ❌ Token size larger than session ID

#### Option 3: PASETO (Platform-Agnostic Security Tokens)

```python
# Similar to JWT but with different design
import paseto

token = paseto.create(
    version="v4",  # Latest version
    purpose="public",
    payload={"user_id": user.id, "role": user.role},
    key=secret_key
)
# Validates like JWT but with opinionated security
payload = paseto.parse(token, key=secret_key)
```

- ✅ Simpler security model (no algorithm confusion attacks)
- ✅ Smaller library surface (less to go wrong)
- ❌ Newer, less widely adopted
- ❌ Less tooling and integrations
- ❌ Fewer SDKs across languages

---

## Decision

Use **JWT-based stateless authentication** for ClickNBack.

### Why JWT

1. **Scalability:** Stateless tokens mean horizontal scaling is trivial; any server validates any token
2. **API-native:** JWT is the standard for REST APIs, especially with third-party integrations and webhooks
3. **Mobile-friendly:** Clients store tokens locally; no cookie infrastructure needed
4. **Industry standard:** JWT is widely understood by engineers, employers, and partners
5. **Mature ecosystem:** Extensive libraries, tools, and best practices across all languages
6. **No DB overhead:** Token validation is O(1)—cryptographic check, not database query

Compared to alternatives:

- **Sessions:** Require shared state (hard to scale), don't work well for mobile/third-party
- **PASETO:** Newer, safer design but less adoption; JWT risk mitigated by architecture choices

### Token Design

**Lifetime and Revocation:**

- Tokens expire in 15-30 minutes, limiting damage from leaked tokens
- Password changes immediately invalidate all prior tokens via issued-at (iat) check
- Clients with old tokens are rejected; no database lookup needed for revocation
- Refresh tokens (future enhancement) allow obtaining new access tokens without re-authenticating

**Token Claims:**

- `user_id`: Identifies the requester
- `role`: User or Admin, used for authorization checks at HTTP layer
- `exp`: Expiration timestamp (seconds since epoch)
- `iat`: Issued-at timestamp; password changes increment user's iat, invalidating prior tokens

**Stateless Validation:**

- Token signature is validated cryptographically (no database required)
- Claims are parsed and trusted (signature proves authenticity)
- Authorization checks happen at endpoint layer before business logic runs

**Signing Algorithm:**

- HS256 (HMAC-SHA256) for single-server deployments
- RS256 (RSA) if multiple independent auth servers needed (future)
- Always validate signature and expiration on every request

---

## Consequences

- ✅ Horizontal scaling: Any server instance validates any token cryptographically
- ✅ Stateless: No session storage or shared state required
- ✅ Fast validation: O(1) signature check, no database lookups
- ✅ Mobile-friendly: Standard bearer token in Authorization header
- ✅ Third-party integration: Standard authentication mechanism
- ✅ Industry standard: Familiar to engineers and easy to document
- ⚠️ Revocation delayed until expiration (mitigated by short lifetime + issued-at strategy)
- ⚠️ Token size slightly larger than session IDs (negligible; ~500 bytes)
- ⚠️ Leaked token remains valid until expiration (mitigated by HTTPS-only transport + short lifetime)

## Alternatives Considered

- **Session-based auth:** Immediate revocation but requires session storage and database lookups; doesn't scale well; poor mobile support
- **PASETO:** Slightly safer token format but immature ecosystem and poor adoption; JWT risks are mitigated by design choices (short lifetime, issued-at revocation)

## Rationale

JWT aligns with ClickNBack's architectural goals and deployment model:

**Stateless by Design:**
ClickNBack is designed as a modular monolith (ADR 001) with horizontal scaling in mind. JWT enables stateless deployment—each server instance independently validates tokens without shared session storage. This eliminates synchronization complexity and allows true horizontal scaling without coordinating session state.

**Financial System Constraints:**
ClickNBack handles cashback transactions and wallet balances. Stateless authentication means authorization decisions (who is requesting, what role do they have) are purely cryptographic and deterministic. This fits financial systems where correctness and auditability are paramount—every authorization decision is reproducible by any server with the signing key.

**Token Lifetime as Security Trade-off:**
Delayed revocation until token expiration is acceptable because:

1. Short lifetime (15-30 minutes) limits exposure from leaked tokens
2. Issued-at checks provide immediate password-change revocation without DB queries
3. Financial transactions are reversible; a compromised token for 30 minutes is recoverable via audit and transaction reversal
4. The operational simplicity (no revocation DB queries) outweighs the marginal risk

**API-First Architecture:**
ClickNBack serves web, mobile, and third-party integrations. Bearer tokens in Authorization headers are the standard across all clients and reduce complexity compared to managing cookies, session storage, and platform-specific authentication methods. This supports the modular, domain-driven architecture where each endpoint is independently deployable.

**Future Extensibility:**
JWT's cryptographic design supports future enhancements (RS256 for multiple auth servers, refresh token rotation, scoped tokens for fine-grained permissions) without breaking the authentication layer.
