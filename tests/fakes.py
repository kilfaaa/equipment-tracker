from app.repositories.employees import EmployeeRow
from app.repositories.equipment import EquipmentRow


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