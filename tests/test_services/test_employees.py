import pytest

from app.exceptions import ConflictError, NotFoundError
from app.services.employees import EmployeeService
from tests.fakes import FakeEmployeeRepository


def test_create_employee() -> None:
    repo = FakeEmployeeRepository()
    service = EmployeeService(repo)

    employee = service.create_employee("Иван", "ivan@example.com")

    assert employee["id"] == 1
    assert employee["email"] == "ivan@example.com"


def test_create_employee_duplicate_email() -> None:
    repo = FakeEmployeeRepository()
    service = EmployeeService(repo)

    service.create_employee("Иван", "ivan@example.com")

    with pytest.raises(ConflictError):
        service.create_employee("Пётр", "ivan@example.com")


def test_get_employee_not_found() -> None:
    repo = FakeEmployeeRepository()
    service = EmployeeService(repo)

    with pytest.raises(NotFoundError):
        service.get_employee(999)