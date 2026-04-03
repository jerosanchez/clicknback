---
# template.md for add-migration
---

# Migration Template

```python
# alembic/versions/XXXX_add_<table>_table.py
from alembic import op
import sqlalchemy as sa

revision = 'XXXX'
down_revision = 'YYYY'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        '<table>',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

def downgrade() -> None:
    op.drop_table('<table>')
```
