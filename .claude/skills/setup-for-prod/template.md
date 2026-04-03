---
# template.md for setup-for-prod
---

# Environment Variables Template

```bash
# .env.prod
DATABASE_URL=postgresql+asyncpg://user:password@prod-db:5432/clicknback
JWT_SECRET=<generate-with-secrets.token_urlsafe(32)>
JWT_ALGORITHM=HS256
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://app.example.com,https://www.example.com
```

# Pre-Launch Steps

```bash
# 1. Pull latest code
git checkout main
git pull

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run all quality gates
make lint && make test && make coverage && make security

# 4. Apply migrations
export DATABASE_URL="<production_db_url>"
alembic upgrade head

# 5. Start application
uvicorn app.main:app --host 0.0.0.0 --port 8001

# 6. Verify health
curl http://localhost:8001/health
```
