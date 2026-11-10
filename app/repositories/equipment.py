from typing import Any, Protocol

from psycopg import Connection
from psycopg.rows import DictRow

EquipmentRow = dict[str, Any]


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
            return cur.fetchone()

    def get_by_inventory_number(self, inventory_number: str) -> EquipmentRow | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, inventory_number FROM equipment "
                "WHERE inventory_number = %s",
                (inventory_number,),
            )
            return cur.fetchone()

    def list_all(self) -> list[EquipmentRow]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, name, inventory_number FROM equipment ORDER BY id")
            return cur.fetchall()

    def create(self, name: str, inventory_number: str) -> EquipmentRow:
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO equipment (name, inventory_number) VALUES (%s, %s) "
                "RETURNING id, name, inventory_number",
                (name, inventory_number),
            )
            row: EquipmentRow | None = cur.fetchone()
            if row is None:
                raise RuntimeError("INSERT ... RETURNING не вернул строку")
            return row