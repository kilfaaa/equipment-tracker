from typing import Protocol, TypedDict, cast

from psycopg import Connection
from psycopg.rows import DictRow


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
            cur.execute(
                "INSERT INTO employees (name, email) VALUES (%s, %s) "
                "RETURNING id, name, email, is_active",
                (name, email),
            )
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