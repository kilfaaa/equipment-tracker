from datetime import datetime
from typing import Protocol, TypedDict, cast

from psycopg import Connection
from psycopg.rows import DictRow

from psycopg.errors import UniqueViolation

from app.exceptions import ConflictError


class LoanRow(TypedDict):
    id: int
    employee_id: int
    equipment_id: int
    issued_at: datetime
    returned_at: datetime | None


class LoanRepositoryProtocol(Protocol):
    def create(self, employee_id: int, equipment_id: int) -> LoanRow: ...

    def get_by_id(self, loan_id: int) -> LoanRow | None: ...

    def get_for_update(self, loan_id: int) -> LoanRow | None: ...

    def list_all(
        self, active: bool | None = None, employee_id: int | None = None
    ) -> list[LoanRow]: ...

    def get_active_by_equipment(self, equipment_id: int) -> LoanRow | None: ...

    def count_active_by_employee(self, employee_id: int) -> int: ...

    def mark_returned(self, loan_id: int) -> LoanRow: ...


class LoanRepository:
    def __init__(self, conn: Connection[DictRow]) -> None:
        self.conn = conn

    def create(self, employee_id: int, equipment_id: int) -> LoanRow:
        with self.conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO loans (employee_id, equipment_id, issued_at) "
                    "VALUES (%s, %s, now()) "
                    "RETURNING id, employee_id, equipment_id, issued_at, returned_at",
                    (employee_id, equipment_id),
                )
            except UniqueViolation as exc:
                raise ConflictError("Оборудование уже выдано") from exc
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("INSERT ... RETURNING не вернул строку")
            return cast(LoanRow, row)

    def get_by_id(self, loan_id: int) -> LoanRow | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, employee_id, equipment_id, issued_at, returned_at "
                "FROM loans WHERE id = %s",
                (loan_id,),
            )
            return cast(LoanRow | None, cur.fetchone())

    def get_for_update(self, loan_id: int) -> LoanRow | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, employee_id, equipment_id, issued_at, returned_at "
                "FROM loans WHERE id = %s FOR UPDATE",
                (loan_id,),
            )
            return cast(LoanRow | None, cur.fetchone())

    def list_all(
        self, active: bool | None = None, employee_id: int | None = None
    ) -> list[LoanRow]:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, employee_id, equipment_id, issued_at, returned_at "
                "FROM loans "
                "WHERE (%(active)s::boolean IS NULL "
                "       OR (returned_at IS NULL) = %(active)s::boolean) "
                "AND (%(employee_id)s::integer IS NULL "
                "     OR employee_id = %(employee_id)s::integer) "
                "ORDER BY id",
                {"active": active, "employee_id": employee_id},
            )
            return cast(list[LoanRow], cur.fetchall())

    def get_active_by_equipment(self, equipment_id: int) -> LoanRow | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, employee_id, equipment_id, issued_at, returned_at "
                "FROM loans WHERE equipment_id = %s AND returned_at IS NULL",
                (equipment_id,),
            )
            return cast(LoanRow | None, cur.fetchone())

    def count_active_by_employee(self, employee_id: int) -> int:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) AS total FROM loans "
                "WHERE employee_id = %s AND returned_at IS NULL",
                (employee_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("count(*) не вернул строку")
            return int(row["total"])

    def mark_returned(self, loan_id: int) -> LoanRow:
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE loans SET returned_at = now() WHERE id = %s "
                "RETURNING id, employee_id, equipment_id, issued_at, returned_at",
                (loan_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("UPDATE ... RETURNING не вернул строку")
            return cast(LoanRow, row)