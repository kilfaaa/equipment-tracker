from typing import Protocol, TypedDict, cast

from psycopg import Connection
from psycopg.errors import UniqueViolation
from psycopg.rows import DictRow
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions import ConflictError
from app.repositories.models import Equipment


class EquipmentRow(TypedDict):
    id: int
    name: str
    inventory_number: str


class EquipmentRepositoryProtocol(Protocol):
    def get_by_id(self, equipment_id: int) -> EquipmentRow | None: ...

    def get_by_inventory_number(self, inventory_number: str) -> EquipmentRow | None: ...

    def list_all(self) -> list[EquipmentRow]: ...

    def create(self, name: str, inventory_number: str) -> EquipmentRow: ...


class EquipmentRepository:
    def __init__(self, conn: Connection[DictRow]) -> None:
        self.conn = conn

    def get_by_id(self, equipment_id: int) -> EquipmentRow | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, inventory_number FROM equipment WHERE id = %s",
                (equipment_id,),
            )
            return cast(EquipmentRow | None, cur.fetchone())

    def get_by_inventory_number(self, inventory_number: str) -> EquipmentRow | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, inventory_number FROM equipment "
                "WHERE inventory_number = %s",
                (inventory_number,),
            )
            return cast(EquipmentRow | None, cur.fetchone())

    def list_all(self) -> list[EquipmentRow]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, name, inventory_number FROM equipment ORDER BY id")
            return cast(list[EquipmentRow], cur.fetchall())

    def create(self, name: str, inventory_number: str) -> EquipmentRow:
        with self.conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO equipment (name, inventory_number) VALUES (%s, %s) "
                    "RETURNING id, name, inventory_number",
                    (name, inventory_number),
                )
            except UniqueViolation as exc:
                raise ConflictError(
                    "Оборудование с таким инвентарным номером уже существует"
                ) from exc

            row = cur.fetchone()
            if row is None:
                raise RuntimeError("INSERT ... RETURNING не вернул строку")
            return cast(EquipmentRow, row)


class SqlAlchemyEquipmentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, equipment_id: int) -> EquipmentRow | None:
        equipment = self.session.get(Equipment, equipment_id)
        if equipment is None:
            return None
        return self._to_row(equipment)

    def get_by_inventory_number(self, inventory_number: str) -> EquipmentRow | None:
        stmt = select(Equipment).where(Equipment.inventory_number == inventory_number)
        equipment = self.session.scalars(stmt).one_or_none()
        if equipment is None:
            return None
        return self._to_row(equipment)

    def list_all(self) -> list[EquipmentRow]:
        stmt = select(Equipment).order_by(Equipment.id)
        equipment_items = self.session.scalars(stmt).all()
        return [self._to_row(equipment) for equipment in equipment_items]

    def create(self, name: str, inventory_number: str) -> EquipmentRow:
        equipment = Equipment(name=name, inventory_number=inventory_number)
        self.session.add(equipment)

        try:
            self.session.flush()
        except IntegrityError as exc:
            original = exc.orig
            if (
                isinstance(original, UniqueViolation)
                and original.diag.constraint_name == "equipment_inventory_number_key"
            ):
                raise ConflictError(
                    "Оборудование с таким инвентарным номером уже существует"
                ) from exc
            raise

        return self._to_row(equipment)

    @staticmethod
    def _to_row(equipment: Equipment) -> EquipmentRow:
        return {
            "id": equipment.id,
            "name": equipment.name,
            "inventory_number": equipment.inventory_number,
        }