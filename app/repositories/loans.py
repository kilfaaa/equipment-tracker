from datetime import datetime
from typing import Protocol, TypedDict, cast

from psycopg import Connection
from psycopg.rows import DictRow

from psycopg.errors import UniqueViolation

from app.exceptions import ConflictError

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update, insert
from app.repositories.models import Loan
from sqlalchemy.exc import IntegrityError


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

class SqlAlchemyLoanRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, loan_id: int) -> LoanRow | None:
        loan = self.session.get(Loan, loan_id)
        if loan is None:
            return None
        return self._to_row(loan)

    def get_active_by_equipment(self, equipment_id: int) -> LoanRow | None:
        stmt = select(Loan).where(
            Loan.equipment_id == equipment_id,
            Loan.returned_at.is_(None),
        )
        loan = self.session.scalars(stmt).one_or_none()
        if loan is None:
            return None
        return self._to_row(loan)


    def count_active_by_employee(self, employee_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Loan)
            .where(
                Loan.employee_id == employee_id,
                Loan.returned_at.is_(None),
            )
        )
        return self.session.execute(stmt).scalar_one()


    def get_for_update(self, loan_id: int) -> LoanRow | None:
        stmt = (
            select(Loan)
            .where(Loan.id == loan_id)
            .with_for_update()
        )
        loan = self.session.scalars(stmt).one_or_none()
        if loan is None:
            return None
        return self._to_row(loan)


    def mark_returned(self, loan_id: int) -> LoanRow:
        stmt = (
            update(Loan)
            .where(Loan.id == loan_id)
            .values(returned_at=func.now())
            .returning(Loan)
        )
        loan = self.session.scalars(stmt).one_or_none()
        if loan is None:
            raise RuntimeError("UPDATE ... RETURNING не вернул строку")
        return self._to_row(loan)


    def list_all(
            self, active: bool | None = None, employee_id: int | None = None
    ) -> list[LoanRow]:
        stmt = select(Loan).order_by(Loan.id)

        if active is True:
            stmt = stmt.where(Loan.returned_at.is_(None))
        elif active is False:
            stmt = stmt.where(Loan.returned_at.is_not(None))

        if employee_id is not None:
            stmt = stmt.where(Loan.employee_id == employee_id)

        loans = self.session.scalars(stmt).all()
        return [self._to_row(loan) for loan in loans]


    def create(self, employee_id: int, equipment_id: int) -> LoanRow:
        stmt = (
            insert(Loan)
            .values(
                employee_id=employee_id,
                equipment_id=equipment_id,
                issued_at=func.now(),
            )
            .returning(Loan)
        )

        try:
            loan = self.session.scalars(stmt).one_or_none()
        except IntegrityError as exc:
            original = exc.orig
            if (
                    isinstance(original, UniqueViolation)
                    and original.diag.constraint_name == "uq_loans_active_equipment"
            ):
                raise ConflictError("Оборудование уже выдано") from exc
            raise

        if loan is None:
            raise RuntimeError("INSERT ... RETURNING не вернул строку")

        return self._to_row(loan)


    @staticmethod
    def _to_row(loan: Loan) -> LoanRow:
        return {
            "id": loan.id,
            "employee_id": loan.employee_id,
            "equipment_id": loan.equipment_id,
            "issued_at": loan.issued_at,
            "returned_at": loan.returned_at,
        }