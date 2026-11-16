from fastapi import APIRouter, status

from app.dependencies import EmployeeServiceDep
from app.repositories.employees import EmployeeRow
from app.schemas.employees import EmployeeCreate, EmployeeRead

router = APIRouter(prefix="/employees", tags=["employees"])


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(data: EmployeeCreate, service: EmployeeServiceDep) -> EmployeeRow:
    return service.create_employee(data.name, data.email)


@router.get("", response_model=list[EmployeeRead])
def list_employees(service: EmployeeServiceDep) -> list[EmployeeRow]:
    return service.list_employees()


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(employee_id: int, service: EmployeeServiceDep) -> EmployeeRow:
    return service.get_employee(employee_id)


@router.patch(
    "/{employee_id}/deactivate",
    response_model=EmployeeRead,
    responses={
        404: {"description": "Сотрудник не найден"},
        409: {"description": "У сотрудника есть активные выдачи"},
    },
)
def deactivate_employee(employee_id: int, service: EmployeeServiceDep) -> EmployeeRow:
    return service.deactivate_employee(employee_id)