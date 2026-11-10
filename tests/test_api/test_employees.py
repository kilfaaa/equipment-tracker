import pytest
from fastapi.testclient import TestClient

from tests.fakes import FakeEmployeeRepository

ApiClient = tuple[TestClient, FakeEmployeeRepository]


def test_create_employee(api_client: ApiClient) -> None:
    client, repo = api_client

    response = client.post(
        "/employees", json={"name": "Иван", "email": "ivan@example.com"}
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "Иван",
        "email": "ivan@example.com",
        "is_active": True,
    }


def test_create_employee_normalizes_input(api_client: ApiClient) -> None:
    client, repo = api_client

    response = client.post(
        "/employees", json={"name": "  Иван  ", "email": "  IVAN@Example.COM "}
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Иван"
    assert response.json()["email"] == "ivan@example.com"


def test_list_employees(api_client: ApiClient) -> None:
    client, repo = api_client
    repo.create("Иван", "ivan@example.com")
    repo.create("Пётр", "petr@example.com")

    response = client.get("/employees")

    assert response.status_code == 200
    emails = [employee["email"] for employee in response.json()]
    assert emails == ["ivan@example.com", "petr@example.com"]


def test_get_employee(api_client: ApiClient) -> None:
    client, repo = api_client
    repo.create("Иван", "ivan@example.com")

    response = client.get("/employees/1")

    assert response.status_code == 200
    assert response.json()["email"] == "ivan@example.com"


def test_get_employee_not_found(api_client: ApiClient) -> None:
    client, repo = api_client

    response = client.get("/employees/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Сотрудник не найден"}


def test_get_employee_invalid_id(api_client: ApiClient) -> None:
    client, repo = api_client

    response = client.get("/employees/abc")

    assert response.status_code == 422


def test_create_employee_duplicate_email(api_client: ApiClient) -> None:
    client, repo = api_client
    payload = {"name": "Иван", "email": "ivan@example.com"}

    first = client.post("/employees", json=payload)
    second = client.post("/employees", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json() == {"detail": "Сотрудник с таким Email уже существует"}


@pytest.mark.parametrize("email", ["abc", "", "ivan@", "@example.com"])
def test_create_employee_invalid_email(api_client: ApiClient, email: str) -> None:
    client, repo = api_client

    response = client.post("/employees", json={"name": "Иван", "email": email})

    assert response.status_code == 422


def test_create_employee_extra_field(api_client: ApiClient) -> None:
    client, repo = api_client

    response = client.post(
        "/employees",
        json={"name": "Иван", "email": "ivan@example.com", "is_active": False},
    )

    assert response.status_code == 422