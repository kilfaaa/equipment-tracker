class FakeEmployeeRepository:
    def __init__(self):
        self.employees = []

    def get_by_id(self, employee_id):
        for employee in self.employees:
            if employee["id"] == employee_id:
                return employee
        return None

    def get_by_email(self, email):
        for employee in self.employees:
            if employee["email"] == email:
                return employee
        return None

    def list_all(self):
        return self.employees

    def create(self, name, email):
        employee = {
            "id": len(self.employees)+1,
            "name": name,
            "email": email,
            "is_active": True,
        }
        self.employees.append(employee)
        return employee


