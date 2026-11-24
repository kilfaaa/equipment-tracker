from typing import Protocol, TypedDict, cast

from psycopg import Connection
from psycopg.errors import UniqueViolation
from psycopg.rows import DictRow
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.exceptions import ConflictError
from app.repositories.models import Employee


class EmployeeRow(TypedDict):
    id: int
    name: str
    email: str
    is_active: bool


class EmployeeRepositoryProtocol(Protocol):
    def get_by_id(self, employee_id: int) -> EmployeeRow | None: ...

    def get_by_email(self, email: str) -> EmployeeRow | None: ...

    def list_all(self) -> list[EmployeeRow]: ...

    def create(self, name: str, email: str) -> EmployeeRow: ...

    def get_for_update(self, employee_id: int) -> EmployeeRow | None: ...

    def deactivate(self, employee_id: int) -> EmployeeRow: ...


class EmployeeRepository:
    def __init__(self, conn: Connection[DictRow]) -> None:
        self.conn = conn

    def get_by_id(self, employee_id: int) -> EmployeeRow | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, is_active FROM employees WHERE id = %s",
                (employee_id,),
            )
            return cast(EmployeeRow | None, cur.fetchone())

    def get_by_email(self, email: str) -> EmployeeRow | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, is_active FROM employees WHERE email = %s",
                (email,),
            )
            return cast(EmployeeRow | None, cur.fetchone())

    def list_all(self) -> list[EmployeeRow]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, name, email, is_active FROM employees ORDER BY id")
            return cast(list[EmployeeRow], cur.fetchall())

    def get_for_update(self, employee_id: int) -> EmployeeRow | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, is_active FROM employees WHERE id = %s FOR UPDATE",
                (employee_id,),
            )
            return cast(EmployeeRow | None, cur.fetchone())

    def create(self, name: str, email: str) -> EmployeeRow:
        with self.conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO employees (name, email) VALUES (%s, %s) "
                    "RETURNING id, name, email, is_active",
                    (name, email),
                )
            except UniqueViolation as exc:
                raise ConflictError("Сотрудник с таким Email уже существует") from exc

            row = cur.fetchone()
            if row is None:
                raise RuntimeError("INSERT ... RETURNING не вернул строку")
            return cast(EmployeeRow, row)

    def deactivate(self, employee_id: int) -> EmployeeRow:
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE employees SET is_active = FALSE WHERE id = %s "
                "RETURNING id, name, email, is_active",
                (employee_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("UPDATE ... RETURNING не вернул строку")
            return cast(EmployeeRow, row)


class SqlAlchemyEmployeeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, employee_id: int) -> EmployeeRow | None:
        employee = self.session.get(Employee, employee_id)
        if employee is None:
            return None
        return self._to_row(employee)

    def get_by_email(self, email: str) -> EmployeeRow | None:
        stmt = select(Employee).where(Employee.email == email)
        employee = self.session.scalars(stmt).one_or_none()
        if employee is None:
            return None
        return self._to_row(employee)

    def list_all(self) -> list[EmployeeRow]:
        stmt = select(Employee).order_by(Employee.id)
        employees = self.session.scalars(stmt).all()
        return [self._to_row(employee) for employee in employees]

    def get_for_update(self, employee_id: int) -> EmployeeRow | None:
        stmt = (
            select(Employee)
            .where(Employee.id == employee_id)
            .with_for_update()
        )
        employee = self.session.scalars(stmt).one_or_none()
        if employee is None:
            return None
        return self._to_row(employee)


    def create(self, name: str, email: str) -> EmployeeRow:
        employee = Employee(name=name, email=email)
        self.session.add(employee)

        try:
            self.session.flush()
        except IntegrityError as exc:
            original = exc.orig
            if (
                    isinstance(original, UniqueViolation)
                    and original.diag.constraint_name == "employees_email_key"
            ):
                raise ConflictError("Сотрудник с таким Email уже существует") from exc
            raise

        return self._to_row(employee)

    def deactivate(self, employee_id: int) -> EmployeeRow:
        employee = self.session.get(Employee, employee_id)
        if employee is None:
            raise RuntimeError("UPDATE ... RETURNING не вернул строку")

        employee.is_active = False
        self.session.flush()
        return self._to_row(employee)

    @staticmethod
    def _to_row(employee: Employee) -> EmployeeRow:
        return {
            "id": employee.id,
            "name": employee.name,
            "email": employee.email,
            "is_active": employee.is_active,
        }