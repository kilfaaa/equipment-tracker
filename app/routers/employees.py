from fastapi import APIRouter, status

from app.dependencies import EmployeeServiceDep
from app.schemas.employees import EmployeeCreate, EmployeeRead

router = APIRouter(prefix="/employees", tags=["employees"])


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(data: EmployeeCreate, service: EmployeeServiceDep):
    return service.create_employee(data.name, data.email)


@router.get("", response_model=list[EmployeeRead])
def list_employees(service: EmployeeServiceDep):
    return service.list_employees()


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(employee_id: int, service: EmployeeServiceDep):
    return service.get_employee(employee_id)