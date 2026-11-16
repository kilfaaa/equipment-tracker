from app.exceptions import ConflictError, NotFoundError
from app.repositories.employees import EmployeeRepositoryProtocol, EmployeeRow
from app.repositories.loans import LoanRepositoryProtocol


class EmployeeService:
    def __init__(
        self,
        employee_repo: EmployeeRepositoryProtocol,
        loan_repo: LoanRepositoryProtocol,
    ) -> None:
        self.employee_repo = employee_repo
        self.loan_repo = loan_repo

    def get_employee(self, employee_id: int) -> EmployeeRow:
        employee = self.employee_repo.get_by_id(employee_id)
        if employee is None:
            raise NotFoundError("Сотрудник не найден")
        return employee

    def list_employees(self) -> list[EmployeeRow]:
        return self.employee_repo.list_all()

    def create_employee(self, name: str, email: str) -> EmployeeRow:
        existing = self.employee_repo.get_by_email(email)
        if existing is not None:
            raise ConflictError("Сотрудник с таким Email уже существует")
        return self.employee_repo.create(name, email)

    def deactivate_employee(self, employee_id: int) -> EmployeeRow:
        employee = self.employee_repo.get_for_update(employee_id)
        if employee is None:
            raise NotFoundError("Сотрудник не найден")
        if not employee["is_active"]:
            return employee
        if self.loan_repo.count_active_by_employee(employee_id) > 0:
            raise ConflictError("У сотрудника есть активные выдачи")
        return self.employee_repo.deactivate(employee_id)