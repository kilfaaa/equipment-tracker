from app.exceptions import ConflictError, NotFoundError
from app.repositories.employees import EmployeeRepositoryProtocol
from app.repositories.equipment import EquipmentRepositoryProtocol
from app.repositories.loans import LoanRepositoryProtocol, LoanRow

MAX_ACTIVE_LOANS = 3


class LoanService:
    def __init__(
        self,
        loan_repo: LoanRepositoryProtocol,
        employee_repo: EmployeeRepositoryProtocol,
        equipment_repo: EquipmentRepositoryProtocol,
    ) -> None:
        self.loan_repo = loan_repo
        self.employee_repo = employee_repo
        self.equipment_repo = equipment_repo

    def issue_loan(self, employee_id: int, equipment_id: int) -> LoanRow:
        employee = self.employee_repo.get_for_update(employee_id)
        if employee is None:
            raise NotFoundError("Сотрудник не найден")
        if not employee["is_active"]:
            raise ConflictError("Сотрудник неактивен")

        equipment = self.equipment_repo.get_by_id(equipment_id)
        if equipment is None:
            raise NotFoundError("Оборудование не найдено")
        if self.loan_repo.get_active_by_equipment(equipment_id) is not None:
            raise ConflictError("Оборудование уже выдано")

        if self.loan_repo.count_active_by_employee(employee_id) >= MAX_ACTIVE_LOANS:
            raise ConflictError("У сотрудника уже три активные выдачи")

        return self.loan_repo.create(employee_id, equipment_id)

    def return_loan(self, loan_id: int) -> LoanRow:
        loan = self.loan_repo.get_for_update(loan_id)
        if loan is None:
            raise NotFoundError("Выдача не найдена")
        if loan["returned_at"] is not None:
            raise ConflictError("Выдача уже возвращена")
        return self.loan_repo.mark_returned(loan_id)

    def get_loan(self, loan_id: int) -> LoanRow:
        loan = self.loan_repo.get_by_id(loan_id)
        if loan is None:
            raise NotFoundError("Выдача не найдена")
        return loan

    def list_loans(
        self, active: bool | None = None, employee_id: int | None = None
    ) -> list[LoanRow]:
        return self.loan_repo.list_all(active=active, employee_id=employee_id)