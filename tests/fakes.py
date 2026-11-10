from app.repositories.employees import EmployeeRow


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