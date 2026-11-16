import pytest
from fastapi.testclient import TestClient

from tests.fakes import FakeEquipmentRepository

ApiClient = tuple[TestClient, FakeEquipmentRepository]


def test_create_equipment_normalizes_input(equipment_api_client: ApiClient) -> None:
    client, repo = equipment_api_client

    response = client.post(
        "/equipment", json={"name": "  Ноутбук ", "inventory_number": " inv-001 "}
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "Ноутбук",
        "inventory_number": "INV-001",
    }


def test_list_equipment(equipment_api_client: ApiClient) -> None:
    client, repo = equipment_api_client
    repo.create("Ноутбук", "INV-001")
    repo.create("Монитор", "INV-002")

    response = client.get("/equipment")

    assert response.status_code == 200
    numbers = [item["inventory_number"] for item in response.json()]
    assert numbers == ["INV-001", "INV-002"]


def test_list_equipment_empty(equipment_api_client: ApiClient) -> None:
    client, repo = equipment_api_client

    response = client.get("/equipment")

    assert response.status_code == 200
    assert response.json() == []


def test_get_equipment(equipment_api_client: ApiClient) -> None:
    client, repo = equipment_api_client
    repo.create("Ноутбук", "INV-001")

    response = client.get("/equipment/1")

    assert response.status_code == 200
    assert response.json()["inventory_number"] == "INV-001"


def test_get_equipment_not_found(equipment_api_client: ApiClient) -> None:
    client, repo = equipment_api_client

    response = client.get("/equipment/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Оборудование не найдено"}


def test_create_equipment_duplicate_inventory_number(
    equipment_api_client: ApiClient,
) -> None:
    client, repo = equipment_api_client
    payload = {"name": "Ноутбук", "inventory_number": "INV-001"}

    first = client.post("/equipment", json=payload)
    second = client.post("/equipment", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "", "inventory_number": "INV-001"},
        {"name": "   ", "inventory_number": "INV-001"},
        {"name": "Ноутбук", "inventory_number": ""},
        {"name": "Н" * 101, "inventory_number": "INV-001"},
        {"name": "Ноутбук", "inventory_number": "N" * 51},
        {"name": "Ноутбук"},
        {"name": "Ноутбук", "inventory_number": "INV-001", "id": 5},
    ],
)
def test_create_equipment_invalid_payload(
    equipment_api_client: ApiClient, payload: dict[str, object]
) -> None:
    client, repo = equipment_api_client

    response = client.post("/equipment", json=payload)

    assert response.status_code == 422