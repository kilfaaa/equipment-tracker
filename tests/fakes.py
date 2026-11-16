from datetime import datetime, timezone

from app.repositories.employees import EmployeeRow
from app.repositories.equipment import EquipmentRow
from app.repositories.loans import LoanRow


class FakeEmployeeRepository:
    def __init__(self) -> None:
        self.employees: list[EmployeeRow] = []

    def get_by_id(self, employee_id: int) -> EmployeeRow | None:
        for employee in self.employees:
            if employee["id"] == employee_id:
                return employee
        return None

    def get_by_email(self, email: str) -> EmployeeRow | None:
        for employee in self.employees:
            if employee["email"] == email:
                return employee
        return None

    def list_all(self) -> list[EmployeeRow]:
        return self.employees

    def create(self, name: str, email: str) -> EmployeeRow:
        employee: EmployeeRow = {
            "id": len(self.employees) + 1,
            "name": name,
            "email": email,
            "is_active": True,
        }
        self.employees.append(employee)
        return employee

    def get_for_update(self, employee_id: int) -> EmployeeRow | None:
        return self.get_by_id(employee_id)


class FakeEquipmentRepository:
    def __init__(self) -> None:
        self.equipment: list[EquipmentRow] = []

    def get_by_id(self, equipment_id: int) -> EquipmentRow | None:
        for item in self.equipment:
            if item["id"] == equipment_id:
                return item
        return None

    def get_by_inventory_number(self, inventory_number: str) -> EquipmentRow | None:
        for item in self.equipment:
            if item["inventory_number"] == inventory_number:
                return item
        return None

    def list_all(self) -> list[EquipmentRow]:
        return self.equipment

    def create(self, name: str, inventory_number: str) -> EquipmentRow:
        item: EquipmentRow = {
            "id": len(self.equipment) + 1,
            "name": name,
            "inventory_number": inventory_number,
        }
        self.equipment.append(item)
        return item


class FakeLoanRepository:
    def __init__(self) -> None:
        self.loans: list[LoanRow] = []

    def create(self, employee_id: int, equipment_id: int) -> LoanRow:
        loan: LoanRow = {
            "id": len(self.loans) + 1,
            "employee_id": employee_id,
            "equipment_id": equipment_id,
            "issued_at": datetime.now(timezone.utc),
            "returned_at": None,
        }
        self.loans.append(loan)
        return loan

    def get_by_id(self, loan_id: int) -> LoanRow | None:
        for loan in self.loans:
            if loan["id"] == loan_id:
                return loan
        return None

    def get_for_update(self, loan_id: int) -> LoanRow | None:
        return self.get_by_id(loan_id)

    def list_all(
        self, active: bool | None = None, employee_id: int | None = None
    ) -> list[LoanRow]:
        result: list[LoanRow] = []
        for loan in self.loans:
            if active is True and loan["returned_at"] is not None:
                continue
            if active is False and loan["returned_at"] is None:
                continue
            if employee_id is not None and loan["employee_id"] != employee_id:
                continue
            result.append(loan)
        return result

    def get_active_by_equipment(self, equipment_id: int) -> LoanRow | None:
        for loan in self.loans:
            if loan["equipment_id"] == equipment_id and loan["returned_at"] is None:
                return loan
        return None

    def count_active_by_employee(self, employee_id: int) -> int:
        return sum(
            1
            for loan in self.loans
            if loan["employee_id"] == employee_id and loan["returned_at"] is None
        )

    def mark_returned(self, loan_id: int) -> LoanRow:
        loan = self.get_by_id(loan_id)
        if loan is None:
            raise RuntimeError("Выдача не найдена")
        loan["returned_at"] = datetime.now(timezone.utc)
        return loan