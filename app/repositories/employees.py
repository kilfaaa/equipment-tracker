from typing import Any, Protocol

from psycopg import Connection
from psycopg.rows import DictRow

EmployeeRow = dict[str, Any]


class EmployeeRepositoryProtocol(Protocol):
    def get_by_id(self, employee_id: int) -> EmployeeRow | None: ...

    def get_by_email(self, email: str) -> EmployeeRow | None: ...

    def list_all(self) -> list[EmployeeRow]: ...

    def create(self, name: str, email: str) -> EmployeeRow: ...


class EmployeeRepository:
    def __init__(self, conn: Connection[DictRow]) -> None:
        self.conn = conn

    def get_by_id(self, employee_id: int) -> EmployeeRow | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, is_active FROM employees WHERE id = %s",
                (employee_id,),
            )
            return cur.fetchone()

    def get_by_email(self, email: str) -> EmployeeRow | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, is_active FROM employees WHERE email = %s",
                (email,),
            )
            return cur.fetchone()

    def list_all(self) -> list[EmployeeRow]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, name, email, is_active FROM employees ORDER BY id")
            return cur.fetchall()

    def get_for_update(self, employee_id: int) -> EmployeeRow | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, is_active FROM employees WHERE id = %s FOR UPDATE",
                (employee_id,),
            )
            return cur.fetchone()

    def create(self, name: str, email: str) -> EmployeeRow:
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO employees (name, email) VALUES (%s, %s) "
                "RETURNING id, name, email, is_active",
                (name, email),
            )
            row: EmployeeRow | None = cur.fetchone()
            if row is None:
                raise RuntimeError("INSERT ... RETURNING не вернул строку")
            return row