from dataclasses import dataclass

import pytest

from app.exceptions import ConflictError, NotFoundError
from app.services.loans import LoanService
from tests.fakes import (
    FakeEmployeeRepository,
    FakeEquipmentRepository,
    FakeLoanRepository,
)


@dataclass
class LoanContext:
    service: LoanService
    employees: FakeEmployeeRepository
    equipment: FakeEquipmentRepository
    loans: FakeLoanRepository


@pytest.fixture
def ctx() -> LoanContext:
    employees = FakeEmployeeRepository()
    equipment = FakeEquipmentRepository()
    loans = FakeLoanRepository()
    employees.create("Иван", "ivan@example.com")
    equipment.create("Ноутбук", "INV-001")
    service = LoanService(loans, employees, equipment)
    return LoanContext(service, employees, equipment, loans)


def add_equipment(ctx: LoanContext, count: int) -> None:
    """Добавляет ещё `count` предметов (у них будут id 2, 3, ...)."""
    for number in range(2, count + 2):
        ctx.equipment.create(f"Предмет {number}", f"INV-{number:03d}")


def test_issue_loan_success(ctx: LoanContext) -> None:
    loan = ctx.service.issue_loan(1, 1)

    assert loan["id"] == 1
    assert loan["employee_id"] == 1
    assert loan["equipment_id"] == 1
    assert loan["returned_at"] is None
    assert len(ctx.loans.loans) == 1


def test_issue_loan_employee_not_found(ctx: LoanContext) -> None:
    with pytest.raises(NotFoundError):
        ctx.service.issue_loan(999, 1)

    assert ctx.loans.loans == []


def test_issue_loan_inactive_employee(ctx: LoanContext) -> None:
    ctx.employees.employees[0]["is_active"] = False

    with pytest.raises(ConflictError):
        ctx.service.issue_loan(1, 1)

    assert ctx.loans.loans == []


def test_issue_loan_equipment_not_found(ctx: LoanContext) -> None:
    with pytest.raises(NotFoundError):
        ctx.service.issue_loan(1, 999)

    assert ctx.loans.loans == []


def test_issue_loan_equipment_already_issued(ctx: LoanContext) -> None:
    ctx.service.issue_loan(1, 1)
    ctx.employees.create("Пётр", "petr@example.com")

    with pytest.raises(ConflictError):
        ctx.service.issue_loan(2, 1)

    assert len(ctx.loans.loans) == 1


def test_issue_loan_limit_third_allowed_fourth_forbidden(ctx: LoanContext) -> None:
    add_equipment(ctx, 3)

    ctx.service.issue_loan(1, 1)
    ctx.service.issue_loan(1, 2)
    third = ctx.service.issue_loan(1, 3)

    assert third["id"] == 3

    with pytest.raises(ConflictError):
        ctx.service.issue_loan(1, 4)

    assert len(ctx.loans.loans) == 3


def test_return_loan_success(ctx: LoanContext) -> None:
    loan = ctx.service.issue_loan(1, 1)

    returned = ctx.service.return_loan(loan["id"])

    assert returned["id"] == loan["id"]
    assert returned["returned_at"] is not None


def test_return_loan_not_found(ctx: LoanContext) -> None:
    with pytest.raises(NotFoundError):
        ctx.service.return_loan(999)


def test_return_loan_twice_keeps_first_return_time(ctx: LoanContext) -> None:
    loan = ctx.service.issue_loan(1, 1)
    first = ctx.service.return_loan(loan["id"])
    first_time = first["returned_at"]

    with pytest.raises(ConflictError):
        ctx.service.return_loan(loan["id"])

    assert ctx.loans.loans[0]["returned_at"] == first_time


def test_issue_again_after_return_to_same_employee(ctx: LoanContext) -> None:
    first = ctx.service.issue_loan(1, 1)
    ctx.service.return_loan(first["id"])

    second = ctx.service.issue_loan(1, 1)

    assert second["id"] == 2
    assert second["returned_at"] is None
    assert ctx.loans.count_active_by_employee(1) == 1


def test_issue_after_return_to_other_employee(ctx: LoanContext) -> None:
    ctx.employees.create("Пётр", "petr@example.com")
    first = ctx.service.issue_loan(1, 1)
    ctx.service.return_loan(first["id"])

    second = ctx.service.issue_loan(2, 1)

    assert second["employee_id"] == 2
    assert second["returned_at"] is None


def test_return_frees_slot_in_limit(ctx: LoanContext) -> None:
    add_equipment(ctx, 3)
    first = ctx.service.issue_loan(1, 1)
    ctx.service.issue_loan(1, 2)
    ctx.service.issue_loan(1, 3)

    with pytest.raises(ConflictError):
        ctx.service.issue_loan(1, 4)

    ctx.service.return_loan(first["id"])
    new_loan = ctx.service.issue_loan(1, 4)

    assert new_loan["equipment_id"] == 4
    assert ctx.loans.count_active_by_employee(1) == 3