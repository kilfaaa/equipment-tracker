from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_employee_service
from app.main import app
from app.services.employees import EmployeeService
from tests.fakes import FakeEmployeeRepository


@pytest.fixture
def api_client() -> Iterator[tuple[TestClient, FakeEmployeeRepository]]:
    repo = FakeEmployeeRepository()
    app.dependency_overrides[get_employee_service] = lambda: EmployeeService(repo)
    client = TestClient(app)
    yield client, repo
    app.dependency_overrides.clear()