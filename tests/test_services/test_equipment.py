import pytest

from app.exceptions import ConflictError, NotFoundError
from app.services.equipment import EquipmentService
from tests.fakes import FakeEquipmentRepository


def test_create_equipment() -> None:
    service = EquipmentService(FakeEquipmentRepository())

    item = service.create_equipment("Ноутбук", "INV-001")

    assert item["id"] == 1
    assert item["inventory_number"] == "INV-001"


def test_create_equipment_duplicate_inventory_number() -> None:
    service = EquipmentService(FakeEquipmentRepository())

    service.create_equipment("Ноутбук", "INV-001")

    with pytest.raises(ConflictError):
        service.create_equipment("Монитор", "INV-001")


def test_get_equipment_not_found() -> None:
    service = EquipmentService(FakeEquipmentRepository())

    with pytest.raises(NotFoundError):
        service.get_equipment(999)