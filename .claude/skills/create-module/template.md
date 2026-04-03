---
# template.md for create-module
---

# Module Skeleton Template

```python
# app/<module>/__init__.py
# Empty file; marks package

# app/<module>/models.py
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from app.core.database import Base

class <Entity>(Base):
    __tablename__ = "<table_name>"
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(unique=True)
    active: Mapped[bool] = mapped_column(server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

# app/<module>/schemas.py
from pydantic import BaseModel

class <Entity>Out(BaseModel):
    id: str
    name: str
    model_config = {"from_attributes": True}

# app/<module>/repositories.py
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession

class <Entity>RepositoryABC(ABC):
    @abstractmethod
    async def add(self, db: AsyncSession, entity: <Entity>) -> <Entity>:
        pass

class <Entity>Repository(<Entity>RepositoryABC):
    async def add(self, db: AsyncSession, entity: <Entity>) -> <Entity>:
        db.add(entity)
        await db.flush()
        return entity

# app/<module>/services.py
class <Entity>Service:
    def __init__(self, repository: <Entity>RepositoryABC):
        self.repository = repository

# app/<module>/policies.py
# Empty, add functions as needed

# app/<module>/exceptions.py
class DomainException(Exception):
    pass

# app/<module>/errors.py
from enum import Enum

class ErrorCode(str, Enum):
    pass

# app/<module>/composition.py
from fastapi import Depends
from app.<module>.repositories import <Entity>Repository, <Entity>RepositoryABC

def get_<entity>_repository() -> <Entity>RepositoryABC:
    return <Entity>Repository()

def get_<entity>_service(
    repository: <Entity>RepositoryABC = Depends(get_<entity>_repository)
) -> <Entity>Service:
    return <Entity>Service(repository)

# app/<module>/api.py
from fastapi import APIRouter, Depends
from app.<module>.services import <Entity>Service
from app.<module>.composition import get_<entity>_service

router = APIRouter(prefix="/<entities>", tags=["<entities>"])

# Routes added here later
```
