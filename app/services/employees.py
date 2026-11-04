from app.exceptions import NotFoundError, ConflictError


class EmployeeService:
    def __init__(self, employee_repo):
        self.employee_repo = employee_repo

    def get_employee(self, employee_id):
        employee = self.employee_repo.get_by_id(employee_id)
        if employee is None:
            raise NotFoundError("Сотрудник не найден")
        return employee

    def list_employees(self):
        return self.employee_repo.list_all()

    def create_employee(self, name, email):
        existing = self.employee_repo.get_by_email(email)
        if existing is not None:
            raise ConflictError("Сотрудник с таким Email уже существует")
        return self.employee_repo.create(name, email)