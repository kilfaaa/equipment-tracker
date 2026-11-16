from app.repositories.equipment import EquipmentRepository
from app.services.equipment import EquipmentService

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from psycopg import Connection
from psycopg.rows import DictRow

from app.database import get_connection
from app.repositories.employees import EmployeeRepository
from app.services.employees import EmployeeService


def get_conn() -> Iterator[Connection[DictRow]]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


ConnDep = Annotated[Connection[DictRow], Depends(get_conn, scope="function")]


def get_employee_service(conn: ConnDep) -> EmployeeService:
    return EmployeeService(EmployeeRepository(conn))


EmployeeServiceDep = Annotated[EmployeeService, Depends(get_employee_service)]


def get_equipment_service(conn: ConnDep) -> EquipmentService:
    return EquipmentService(EquipmentRepository(conn))


EquipmentServiceDep = Annotated[EquipmentService, Depends(get_equipment_service)]