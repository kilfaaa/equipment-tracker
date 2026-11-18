from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import ApiWorld


def prepare(world: ApiWorld, equipment_count: int = 1) -> None:
    world.employees.create("Иван", "ivan@example.com")
    for number in range(1, equipment_count + 1):
        world.equipment.create(f"Предмет {number}", f"INV-{number:03d}")


def issue(world: ApiWorld, employee_id: int, equipment_id: int) -> dict[str, Any]:
    response = world.client.post(
        "/loans", json={"employee_id": employee_id, "equipment_id": equipment_id}
    )
    assert response.status_code == 201
    result: dict[str, Any] = response.json()
    return result


def prepare_for_filters(world: ApiWorld) -> None:
    prepare(world, equipment_count=3)
    world.employees.create("Пётр", "petr@example.com")
    issue(world, 1, 1)
    issue(world, 2, 2)
    issue(world, 1, 3)
    assert world.client.post("/loans/2/return").status_code == 200


def ids(response_json: list[dict[str, Any]]) -> list[int]:
    return [loan["id"] for loan in response_json]


def test_issue_loan(world: ApiWorld) -> None:
    prepare(world)

    response = world.client.post("/loans", json={"employee_id": 1, "equipment_id": 1})

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["employee_id"] == 1
    assert body["equipment_id"] == 1
    assert body["returned_at"] is None
    assert body["issued_at"] is not None


@pytest.mark.parametrize(
    ("employee_id", "equipment_id"),
    [(999, 1), (1, 999)],
)
def test_issue_loan_not_found(
    world: ApiWorld, employee_id: int, equipment_id: int
) -> None:
    prepare(world)

    response = world.client.post(
        "/loans", json={"employee_id": employee_id, "equipment_id": equipment_id}
    )

    assert response.status_code == 404
    assert world.loans.loans == []


def test_issue_loan_inactive_employee(world: ApiWorld) -> None:
    prepare(world)
    world.employees.employees[0]["is_active"] = False

    response = world.client.post("/loans", json={"employee_id": 1, "equipment_id": 1})

    assert response.status_code == 409
    assert world.loans.loans == []


def test_issue_loan_equipment_already_issued(world: ApiWorld) -> None:
    prepare(world)
    world.employees.create("Пётр", "petr@example.com")
    issue(world, 1, 1)

    response = world.client.post("/loans", json={"employee_id": 2, "equipment_id": 1})

    assert response.status_code == 409
    assert len(world.loans.loans) == 1


def test_issue_loan_limit(world: ApiWorld) -> None:
    prepare(world, equipment_count=4)
    issue(world, 1, 1)
    issue(world, 1, 2)
    issue(world, 1, 3)

    response = world.client.post("/loans", json={"employee_id": 1, "equipment_id": 4})

    assert response.status_code == 409
    assert len(world.loans.loans) == 3


@pytest.mark.parametrize(
    "payload",
    [
        {"employee_id": True, "equipment_id": 1},
        {"employee_id": 1.5, "equipment_id": 1},
        {"employee_id": "1", "equipment_id": 1},
        {"employee_id": 0, "equipment_id": 1},
        {"employee_id": -1, "equipment_id": 1},
        {"employee_id": 2147483648, "equipment_id": 1},
        {"employee_id": 1},
        {"employee_id": 1, "equipment_id": 1, "issued_at": "2026-01-01T00:00:00Z"},
    ],
)
def test_issue_loan_invalid_payload(world: ApiWorld, payload: dict[str, Any]) -> None:
    prepare(world)

    response = world.client.post("/loans", json=payload)

    assert response.status_code == 422
    assert world.loans.loans == []


def test_list_loans_empty(world: ApiWorld) -> None:
    response = world.client.get("/loans")

    assert response.status_code == 200
    assert response.json() == []


def test_list_loans_ordered_by_id(world: ApiWorld) -> None:
    prepare_for_filters(world)

    response = world.client.get("/loans")

    assert response.status_code == 200
    assert ids(response.json()) == [1, 2, 3]


def test_list_loans_active_true(world: ApiWorld) -> None:
    prepare_for_filters(world)

    response = world.client.get("/loans", params={"active": "true"})

    assert ids(response.json()) == [1, 3]


def test_list_loans_active_false(world: ApiWorld) -> None:
    prepare_for_filters(world)

    response = world.client.get("/loans", params={"active": "false"})

    assert ids(response.json()) == [2]


def test_list_loans_by_employee(world: ApiWorld) -> None:
    prepare_for_filters(world)

    response = world.client.get("/loans", params={"employee_id": 1})

    assert ids(response.json()) == [1, 3]


def test_list_loans_both_filters(world: ApiWorld) -> None:
    prepare_for_filters(world)

    returned_of_employee_2 = world.client.get(
        "/loans", params={"employee_id": 2, "active": "false"}
    )
    returned_of_employee_1 = world.client.get(
        "/loans", params={"employee_id": 1, "active": "false"}
    )

    assert ids(returned_of_employee_2.json()) == [2]
    assert returned_of_employee_1.json() == []


def test_list_loans_unknown_employee_returns_empty(world: ApiWorld) -> None:
    prepare_for_filters(world)

    response = world.client.get("/loans", params={"employee_id": 999})

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("params", [{"active": "abc"}, {"employee_id": "abc"}])
def test_list_loans_invalid_filters(world: ApiWorld, params: dict[str, str]) -> None:
    response = world.client.get("/loans", params=params)

    assert response.status_code == 422


def test_get_loan(world: ApiWorld) -> None:
    prepare(world)
    issue(world, 1, 1)

    response = world.client.get("/loans/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_loan_not_found(world: ApiWorld) -> None:
    response = world.client.get("/loans/999")

    assert response.status_code == 404


def test_get_loan_invalid_id(world: ApiWorld) -> None:
    response = world.client.get("/loans/abc")

    assert response.status_code == 422


def test_return_loan(world: ApiWorld) -> None:
    prepare(world)
    issue(world, 1, 1)

    response = world.client.post("/loans/1/return")

    assert response.status_code == 200
    assert response.json()["returned_at"] is not None


def test_return_loan_twice(world: ApiWorld) -> None:
    prepare(world)
    issue(world, 1, 1)
    first = world.client.post("/loans/1/return")

    second = world.client.post("/loans/1/return")

    assert second.status_code == 409
    assert world.loans.loans[0]["returned_at"] is not None
    assert first.json()["returned_at"] is not None


def test_return_loan_not_found(world: ApiWorld) -> None:
    response = world.client.post("/loans/999/return")

    assert response.status_code == 404


def test_deactivate_employee(world: ApiWorld) -> None:
    prepare(world)

    response = world.client.patch("/employees/1/deactivate")

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_deactivate_employee_twice(world: ApiWorld) -> None:
    prepare(world)
    world.client.patch("/employees/1/deactivate")

    response = world.client.patch("/employees/1/deactivate")

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_deactivate_employee_with_active_loan(world: ApiWorld) -> None:
    prepare(world)
    issue(world, 1, 1)

    response = world.client.patch("/employees/1/deactivate")

    assert response.status_code == 409
    assert world.employees.employees[0]["is_active"] is True


def test_deactivate_employee_not_found(world: ApiWorld) -> None:
    response = world.client.patch("/employees/999/deactivate")

    assert response.status_code == 404


def test_health_works_without_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
