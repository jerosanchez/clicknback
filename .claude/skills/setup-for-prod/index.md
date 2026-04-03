---
name: setup-for-prod
type: skill
description: Production deployment and launch checklist
---

# Skill: Setup for Prod

Pre-production launch checklist. Ensure all systems are configured, tested, and ready.

## Pre-Deployment Checklist

### Code Quality

- [ ] `make lint && make test && make coverage && make security` all pass
- [ ] Coverage ≥ 85%
- [ ] No failing tests, no skipped tests
- [ ] All PRs reviewed and approved

### Configuration

- [ ] `.env.prod` has all required environment variables
- [ ] No hardcoded secrets in code
- [ ] Database connection string points to production DB
- [ ] Logging configured for production (rates, levels)
- [ ] CORS origins configured (not wildcard)

### Database

- [ ] Latest migrations applied: `alembic upgrade head`
- [ ] Backup taken before migration
- [ ] Database indexes created on foreign keys and search columns
- [ ] Connection pooling configured

### Deployment

- [ ] All dependencies installed and pinned in `requirements.txt`
- [ ] Application starts without errors
- [ ] Health check endpoint responds: `GET /health`
- [ ] API documentation available: `GET /docs`

### Security

- [ ] All passwords hashed (bcrypt + salt)
- [ ] JWT tokens signed with strong secret
- [ ] HTTPS enabled (TLS 1.3+)
- [ ] Rate limiting configured
- [ ] Input validation on all endpoints

### Monitoring & Observability

- [ ] Logging infrastructure configured
- [ ] Error alerting set up
- [ ] Database monitoring configured
- [ ] Application performance monitoring (APM) enabled

### Smoke Tests

After deployment, verify:

```bash
curl -X GET https://api.example.com/health  # 200
curl -X GET https://api.example.com/docs    # 200

# Auth endpoint
curl -X POST https://api.example.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'

# Verify database accessible
curl -X GET https://api.example.com/merchants \
  -H "Authorization: Bearer <admin_token>"
```

---
