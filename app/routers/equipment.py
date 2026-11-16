from fastapi import APIRouter, status

from app.dependencies import EquipmentServiceDep
from app.repositories.equipment import EquipmentRow
from app.schemas.equipment import EquipmentCreate, EquipmentRead

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.post(
    "",
    response_model=EquipmentRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Инвентарный номер уже существует"}},
)
def create_equipment(
    data: EquipmentCreate, service: EquipmentServiceDep
) -> EquipmentRow:
    return service.create_equipment(data.name, data.inventory_number)


@router.get("", response_model=list[EquipmentRead])
def list_equipment(service: EquipmentServiceDep) -> list[EquipmentRow]:
    return service.list_equipment()


@router.get(
    "/{equipment_id}",
    response_model=EquipmentRead,
    responses={404: {"description": "Оборудование не найдено"}},
)
def get_equipment(equipment_id: int, service: EquipmentServiceDep) -> EquipmentRow:
    return service.get_equipment(equipment_id)