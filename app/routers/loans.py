from fastapi import APIRouter, status

from app.dependencies import LoanServiceDep
from app.repositories.loans import LoanRow
from app.schemas.loans import LoanCreate, LoanRead

router = APIRouter(prefix="/loans", tags=["loans"])


@router.post(
    "",
    response_model=LoanRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"description": "Сотрудник или оборудование не найдены"},
        409: {"description": "Сотрудник неактивен, предмет выдан или лимит исчерпан"},
    },
)
def issue_loan(data: LoanCreate, service: LoanServiceDep) -> LoanRow:
    return service.issue_loan(data.employee_id, data.equipment_id)


@router.get("", response_model=list[LoanRead])
def list_loans(
    service: LoanServiceDep,
    active: bool | None = None,
    employee_id: int | None = None,
) -> list[LoanRow]:
    return service.list_loans(active=active, employee_id=employee_id)


@router.get(
    "/{loan_id}",
    response_model=LoanRead,
    responses={404: {"description": "Выдача не найдена"}},
)
def get_loan(loan_id: int, service: LoanServiceDep) -> LoanRow:
    return service.get_loan(loan_id)


@router.post(
    "/{loan_id}/return",
    response_model=LoanRead,
    responses={
        404: {"description": "Выдача не найдена"},
        409: {"description": "Выдача уже возвращена"},
    },
)
def return_loan(loan_id: int, service: LoanServiceDep) -> LoanRow:
    return service.return_loan(loan_id)