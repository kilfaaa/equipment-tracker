from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        CheckConstraint("btrim(name) <> ''", name="employees_name_check"),
        UniqueConstraint("email", name="employees_email_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))


class Equipment(Base):
    __tablename__ = "equipment"
    __table_args__ = (
        CheckConstraint("btrim(name) <> ''", name="equipment_name_check"),
        CheckConstraint(
            "btrim(inventory_number) <> ''", name="equipment_inventory_number_check"
        ),
        UniqueConstraint("inventory_number", name="equipment_inventory_number_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    inventory_number: Mapped[str] = mapped_column(String(50))


class Loan(Base):
    __tablename__ = "loans"
    __table_args__ = (
        CheckConstraint(
            "returned_at IS NULL OR returned_at >= issued_at", name="loans_check"
        ),
        Index(
            "uq_loans_active_equipment",
            "equipment_id",
            unique=True,
            postgresql_where=text("returned_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT")
    )
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="RESTRICT")
    )
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))