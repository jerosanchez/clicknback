---
# template.md for build-feature skill
# Contains annotated code templates for schemas, exceptions, policies, repos, services, api
---

# Template: Schema Definition

```python
# app/<module>/schemas.py
from decimal import Decimal
from pydantic import BaseModel, field_validator

class MerchantCreate(BaseModel):
    name: str
    default_cashback_percentage: float
    active: bool = True

    @field_validator("default_cashback_percentage")
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        if not 0 <= v <= 100:
            raise ValueError("Percentage must be between 0 and 100")
        return v

class MerchantUpdate(BaseModel):
    name: str | None = None
    default_cashback_percentage: float | None = None
    active: bool | None = None

class MerchantOut(BaseModel):
    id: str
    name: str
    default_cashback_percentage: float
    active: bool
    created_at: str
    
    model_config = {"from_attributes": True}

class PaginatedMerchantOut(BaseModel):
    items: list[MerchantOut]
    total: int
    page: int
    page_size: int
```

# Template: Exception & Error Code

```python
# app/<module>/exceptions.py
class DomainException(Exception):
    pass

class MerchantNotFoundException(DomainException):
    def __init__(self, merchant_id: str):
        self.merchant_id = merchant_id
        super().__init__(f"Merchant {merchant_id} not found")

class MerchantNameAlreadyExistsException(DomainException):
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Merchant with name '{name}' already exists")

# app/<module>/errors.py
from enum import Enum

class ErrorCode(str, Enum):
    MERCHANT_NOT_FOUND = "MERCHANT_NOT_FOUND"
    MERCHANT_NAME_ALREADY_EXISTS = "MERCHANT_NAME_ALREADY_EXISTS"
    INVALID_CASHBACK_PERCENTAGE = "INVALID_CASHBACK_PERCENTAGE"
```

# Template: Policy Function

```python
# app/<module>/policies.py
from decimal import Decimal

def enforce_cashback_percentage_validity(percentage: Decimal) -> None:
    """Raise exception if percentage is invalid; return None if valid."""
    if not (Decimal("0") <= percentage <= Decimal("100")):
        raise ValueError("Percentage must be between 0 and 100")
```

# Template: Repository

```python
# app/<module>/repositories.py
from abc import ABC, abstractmethod
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.<module>.models import Merchant

class MerchantRepositoryABC(ABC):
    @abstractmethod
    async def add_merchant(self, db: AsyncSession, merchant: Merchant) -> Merchant:
        pass

    @abstractmethod
    async def get_merchant_by_id(self, db: AsyncSession, merchant_id: str) -> Merchant | None:
        pass

    @abstractmethod
    async def get_merchant_by_name(self, db: AsyncSession, name: str) -> Merchant | None:
        pass

    @abstractmethod
    async def list_merchants(
        self,
        db: AsyncSession,
        page: int,
        page_size: int,
        active: bool | None = None,
    ) -> tuple[list[Merchant], int]:
        pass

class MerchantRepository(MerchantRepositoryABC):
    async def add_merchant(self, db: AsyncSession, merchant: Merchant) -> Merchant:
        db.add(merchant)
        await db.flush()
        return merchant

    async def get_merchant_by_id(self, db: AsyncSession, merchant_id: str) -> Merchant | None:
        query = select(Merchant).where(Merchant.id == merchant_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def list_merchants(
        self,
        db: AsyncSession,
        page: int,
        page_size: int,
        active: bool | None = None,
    ) -> tuple[list[Merchant], int]:
        query = select(Merchant)
        if active is not None:
            query = query.where(Merchant.active == active)
        
        total_query = select(func.count()).select_from(Merchant)
        if active is not None:
            total_query = total_query.where(Merchant.active == active)
        
        total = (await db.execute(total_query)).scalar()
        items = (await db.execute(
            query.offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
        
        return items, total
```

# Template: Service

```python
# app/<module>/services.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.unit_of_work import UnitOfWorkABC
from app.<module>.repositories import MerchantRepositoryABC
from app.<module>.policies import enforce_cashback_percentage_validity
from app.<module>.exceptions import MerchantNotFoundException

class MerchantService:
    def __init__(self, repository: MerchantRepositoryABC):
        self.repository = repository

    async def create_merchant(
        self,
        merchant_data: dict[str, Any],
        uow: UnitOfWorkABC,
    ) -> Merchant:
        # Validate
        enforce_cashback_percentage_validity(
            Decimal(str(merchant_data["default_cashback_percentage"]))
        )
        
        # Check uniqueness
        existing = await self.repository.get_merchant_by_name(
            uow.session, merchant_data["name"]
        )
        if existing:
            raise MerchantNameAlreadyExistsException(merchant_data["name"])
        
        # Create & persist
        merchant = Merchant(**merchant_data)
        result = await self.repository.add_merchant(uow.session, merchant)
        await uow.commit()
        
        return result

    async def list_merchants(
        self,
        page: int,
        page_size: int,
        active: bool | None,
        db: AsyncSession,
    ) -> tuple[list[Merchant], int]:
        # Read-only: no UoW needed
        return await self.repository.list_merchants(db, page, page_size, active)
```

# Template: API Route

```python
# app/<module>/api.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.unit_of_work import UnitOfWorkABC
from app.<module>.composition import get_merchant_service, get_unit_of_work
from app.<module>.services import MerchantService
from app.<module>.schemas import MerchantCreate, MerchantOut, PaginatedMerchantOut
from app.<module>.exceptions import MerchantNotFoundException
from app.<module>.errors import ErrorCode
from app.core.errors.builders import not_found_error, validation_error

router = APIRouter(prefix="/merchants", tags=["merchants"])

@router.post("/", response_model=MerchantOut, status_code=201)
async def create_merchant(
    merchant_in: MerchantCreate,
    service: MerchantService = Depends(get_merchant_service),
    uow: UnitOfWorkABC = Depends(get_unit_of_work),
) -> MerchantOut:
    try:
        merchant = await service.create_merchant(merchant_in.model_dump(), uow)
        return MerchantOut.model_validate(merchant)
    except MerchantNameAlreadyExistsException as e:
        raise validation_error(
            ErrorCode.MERCHANT_NAME_ALREADY_EXISTS,
            f"Merchant '{e.name}' already exists",
        )

@router.get("/", response_model=PaginatedMerchantOut)
async def list_merchants(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    active: bool | None = Query(None),
    service: MerchantService = Depends(get_merchant_service),
    db: AsyncSession = Depends(get_async_db),
) -> PaginatedMerchantOut:
    items, total = await service.list_merchants(page, page_size, active, db)
    return PaginatedMerchantOut(
        items=[MerchantOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
```
