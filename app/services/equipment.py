from app.exceptions import ConflictError, NotFoundError
from app.repositories.equipment import EquipmentRepositoryProtocol, EquipmentRow


class EquipmentService:
    def __init__(self, equipment_repo: EquipmentRepositoryProtocol) -> None:
        self.equipment_repo = equipment_repo

    def get_equipment(self, equipment_id: int) -> EquipmentRow:
        equipment = self.equipment_repo.get_by_id(equipment_id)
        if equipment is None:
            raise NotFoundError("Оборудование не найдено")
        return equipment

    def list_equipment(self) -> list[EquipmentRow]:
        return self.equipment_repo.list_all()

    def create_equipment(self, name: str, inventory_number: str) -> EquipmentRow:
        existing = self.equipment_repo.get_by_inventory_number(inventory_number)
        if existing is not None:
            raise ConflictError("Оборудование с таким инвентарным номером уже существует")
        return self.equipment_repo.create(name, inventory_number)