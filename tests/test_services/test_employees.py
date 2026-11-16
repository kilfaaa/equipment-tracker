import pytest

from app.exceptions import ConflictError, NotFoundError
from app.services.employees import EmployeeService
from tests.fakes import FakeEmployeeRepository, FakeLoanRepository


def test_create_employee() -> None:
    repo = FakeEmployeeRepository()
    service = EmployeeService(repo, FakeLoanRepository())

    employee = service.create_employee("Иван", "ivan@example.com")

    assert employee["id"] == 1
    assert employee["email"] == "ivan@example.com"


def test_create_employee_duplicate_email() -> None:
    repo = FakeEmployeeRepository()
    service = EmployeeService(repo, FakeLoanRepository())

    service.create_employee("Иван", "ivan@example.com")

    with pytest.raises(ConflictError):
        service.create_employee("Пётр", "ivan@example.com")


def test_get_employee_not_found() -> None:
    repo = FakeEmployeeRepository()
    service = EmployeeService(repo, FakeLoanRepository())

    with pytest.raises(NotFoundError):
        service.get_employee(999)


def test_deactivate_employee_success() -> None:
    employees = FakeEmployeeRepository()
    service = EmployeeService(employees, FakeLoanRepository())
    employees.create("Иван", "ivan@example.com")

    result = service.deactivate_employee(1)

    assert result["is_active"] is False
    assert employees.employees[0]["is_active"] is False


def test_deactivate_employee_twice_returns_current_state() -> None:
    employees = FakeEmployeeRepository()
    service = EmployeeService(employees, FakeLoanRepository())
    employees.create("Иван", "ivan@example.com")

    service.deactivate_employee(1)
    again = service.deactivate_employee(1)

    assert again["is_active"] is False


def test_deactivate_employee_with_active_loan_forbidden() -> None:
    employees = FakeEmployeeRepository()
    loans = FakeLoanRepository()
    service = EmployeeService(employees, loans)
    employees.create("Иван", "ivan@example.com")
    loans.create(1, 1)

    with pytest.raises(ConflictError):
        service.deactivate_employee(1)

    assert employees.employees[0]["is_active"] is True


def test_deactivate_employee_after_return_allowed() -> None:
    employees = FakeEmployeeRepository()
    loans = FakeLoanRepository()
    service = EmployeeService(employees, loans)
    employees.create("Иван", "ivan@example.com")
    loan = loans.create(1, 1)
    loans.mark_returned(loan["id"])

    result = service.deactivate_employee(1)

    assert result["is_active"] is False


def test_deactivate_employee_not_found() -> None:
    service = EmployeeService(FakeEmployeeRepository(), FakeLoanRepository())

    with pytest.raises(NotFoundError):
        service.deactivate_employee(999)