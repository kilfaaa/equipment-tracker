from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends

from app.repositories.employees import SqlAlchemyEmployeeRepository
from app.repositories.equipment import SqlAlchemyEquipmentRepository
from app.repositories.loans import SqlAlchemyLoanRepository
from app.services.employees import EmployeeService
from app.services.equipment import EquipmentService

from sqlalchemy.orm import Session

from app.database import get_session_factory

from app.services.loans import LoanService

def get_session() -> Iterator[Session]:
    session_factory = get_session_factory()
    with session_factory.begin() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session, scope="function")]


def get_employee_service(session: SessionDep) -> EmployeeService:
    return EmployeeService(
        SqlAlchemyEmployeeRepository(session),
        SqlAlchemyLoanRepository(session),
    )


def get_equipment_service(session: SessionDep) -> EquipmentService:
    return EquipmentService(SqlAlchemyEquipmentRepository(session))


def get_loan_service(session: SessionDep) -> LoanService:
    return LoanService(
        SqlAlchemyLoanRepository(session),
        SqlAlchemyEmployeeRepository(session),
        SqlAlchemyEquipmentRepository(session),
    )


EmployeeServiceDep = Annotated[EmployeeService, Depends(get_employee_service)]
EquipmentServiceDep = Annotated[EquipmentService, Depends(get_equipment_service)]
LoanServiceDep = Annotated[LoanService, Depends(get_loan_service)]