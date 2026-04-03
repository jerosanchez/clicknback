---
# template.md for write-unit-tests
---

# Pytest Fixtures Template

```python
# tests/unit/conftest.py (shared across all tests)
@pytest.fixture
def merchant_factory() -> Callable[..., Merchant]:
    """Factory: creates Merchant instances for testing."""
    def _create(**kwargs) -> Merchant:
        return Merchant(
            id=kwargs.get("id", str(uuid.uuid4())),
            name=kwargs.get("name", "Test Merchant"),
            default_cashback_percentage=kwargs.get("default_cashback_percentage", 10.0),
            active=kwargs.get("active", True),
        )
    return _create
```

# Policy Test Template

```python
# tests/unit/<module>/test_<module>_policies.py
import pytest
from decimal import Decimal
from app.<module>.policies import enforce_cashback_percentage_validity

def test_enforce_cashback_percentage_raises_on_too_high():
    # Arrange
    invalid_percentage = Decimal("150")
    
    # Act & Assert
    with pytest.raises(ValueError):
        enforce_cashback_percentage_validity(invalid_percentage)

def test_enforce_cashback_percentage_returns_none_on_valid():
    # Arrange
    valid_percentage = Decimal("50")
    
    # Act
    result = enforce_cashback_percentage_validity(valid_percentage)
    
    # Assert
    assert result is None
```

# Service Test Template (Write Operation)

```python
# tests/unit/<module>/test_<module>_services.py
from unittest.mock import create_autospec, Mock
import pytest
from app.<module>.repositories import MerchantRepositoryABC
from app.<module>.services import MerchantService
from app.<module>.exceptions import MerchantNameAlreadyExistsException

def _make_uow() -> Mock:
    uow = Mock()
    uow.session = AsyncMock()
    uow.commit = AsyncMock()
    return uow

@pytest.mark.asyncio
async def test_create_merchant_returns_created_merchant_on_success(merchant_factory):
    # Arrange
    repository = create_autospec(MerchantRepositoryABC)
    service = MerchantService(repository)
    uow = _make_uow()
    
    expected_merchant = merchant_factory(name="Acme")
    repository.add_merchant.return_value = expected_merchant
    repository.get_merchant_by_name.return_value = None  # Uniqueness check passes
    
    merchant_data = {"name": "Acme", "default_cashback_percentage": 10, "active": True}
    
    # Act
    result = await service.create_merchant(merchant_data, uow)
    
    # Assert
    assert result.name == "Acme"
    uow.commit.assert_called_once()

@pytest.mark.asyncio
async def test_create_merchant_raises_on_name_already_exists(merchant_factory):
    # Arrange
    repository = create_autospec(MerchantRepositoryABC)
    service = MerchantService(repository)
    uow = _make_uow()
    
    existing = merchant_factory(name="Acme")
    repository.get_merchant_by_name.return_value = existing  # Uniqueness check fails
    
    merchant_data = {"name": "Acme", "default_cashback_percentage": 10, "active": True}
    
    # Act & Assert
    with pytest.raises(MerchantNameAlreadyExistsException):
        await service.create_merchant(merchant_data, uow)
    
    uow.commit.assert_not_called()
```

# API Test Template

```python
# tests/unit/<module>/test_<module>_api.py
from fastapi.testclient import TestClient
from unittest.mock import create_autospec
import pytest
from app.main import app
from app.<module>.services import MerchantService
from app.<module>.schemas import MerchantOut
from app.<module>.composition import get_merchant_service

@pytest.fixture
def client_with_mock_service(merchant_factory):
    """Override the service dependency."""
    service = create_autospec(MerchantService)
    app.dependency_overrides[get_merchant_service] = lambda: service
    client = TestClient(app)
    yield client, service
    app.dependency_overrides.clear()

def test_create_merchant_returns_201_on_success(client_with_mock_service, merchant_factory):
    # Arrange
    client, service = client_with_mock_service
    merchant = merchant_factory(name="Acme", id="uuid-1")
    service.create_merchant.return_value = merchant
    
    # Act
    response = client.post(
        "/merchants",
        json={"name": "Acme", "default_cashback_percentage": 10, "active": True}
    )
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme"
    assert data["id"] == "uuid-1"
    assert data["active"] is True

def test_list_merchants_returns_paginated_response(client_with_mock_service, merchant_factory):
    # Arrange
    client, service = client_with_mock_service
    merchants = [merchant_factory(name=f"Merchant {i}") for i in range(3)]
    service.list_merchants.return_value = (merchants, 3)
    
    # Act
    response = client.get("/merchants?page=1&page_size=10")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 3
    assert data["page"] == 1
```
