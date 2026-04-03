---
name: add-migration
type: skill
description: Create and apply Alembic database migrations
---

# Skill: Add Migration

Create and apply a database migration using Alembic.

## One ORM Model at a Time

All ORM models live in `app/models.py`. Alembic reads this file to detect schema changes.

```python
# app/models.py
from app.purchases.models import Purchase
from app.merchants.models import Merchant
from app.wallets.models import Wallet
# Include ALL models so Alembic sees them
```

## Workflow

### Step 1: Modify ORM Model

Edit the model in its module (e.g., `app/purchases/models.py`).

### Step 2: Ensure Model is Imported in app/models.py

```python
# app/models.py
from app.<module>.models import <Entity>
```

### Step 3: Autogenerate Migration

```bash
alembic revision --autogenerate -m "descriptive change message"
```

This creates `alembic/versions/XXXX_descriptive_change_message.py`.

### Step 4: Inspect Migration

```bash
# View the generated upgrade() and downgrade() functions
cat alembic/versions/XXXX_descriptive_change_message.py
```

Verify:
- ✅ All changes are correct
- ✅ Reversibility: `downgrade()` properly reverses `upgrade()`
- ❌ Never manually add application logic to migrations

### Step 5: Test Migration

```bash
# Apply migration
alembic upgrade head

# Verify database schema
psql $DATABASE_URL -c "\d+ <table_name>"

# Downgrade to test reversibility
alembic downgrade -1

# Upgrade again
alembic upgrade head
```

### Step 6: Commit Migration File

Never edit an unreleased migration; if you made a mistake, create a new migration to fix it.

---
