# Equipment Tracker

Equipment Tracker — API для учёта выдачи рабочего оборудования сотрудникам. Приложение хранит сотрудников, оборудование и историю выдач в PostgreSQL. API написан на FastAPI, для доступа к базе используется SQLAlchemy.

Правила выдачи:

- У предмета может быть только одна активная выдача.
- У сотрудника может быть не больше трёх активных выдач.
- Неактивному сотруднику нельзя выдать оборудование.
- Сотрудника с активными выдачами нельзя деактивировать.
- После возврата предмет можно выдать снова.

## Версии

- Python 3.14
- FastAPI, Pydantic, Uvicorn
- SQLAlchemy 2.1.9
- psycopg 3.3.6 (`psycopg-binary`, синхронный драйвер)
- PostgreSQL 18.6
- pytest, mypy

Точные версии библиотек зафиксированы в `requirements.txt`.

## Установка и запуск

Создайте виртуальное окружение и установите зависимости:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Для новой учебной базы создайте `equipment_tracker` и примените схему:

```bash
createdb equipment_tracker
psql -d equipment_tracker -f schema.sql
```

Укажите строку подключения в переменной окружения `DATABASE_URL`. Префикс `postgresql+psycopg://` указывает SQLAlchemy использовать PostgreSQL с драйвером `psycopg`. Подставьте имя пользователя и пароль своей локальной базы.

```bash
export DATABASE_URL="postgresql+psycopg://USER:PASSWORD@localhost:5432/equipment_tracker"
python -m uvicorn app.main:app --reload
```

При запуске через PyCharm можно задать `DATABASE_URL` в конфигурации запуска. Пароль хранится в локальной конфигурации, `.env` добавлен в `.gitignore`.

Интерактивная документация доступна в [Swagger UI](http://127.0.0.1:8000/docs). Маршрут `/health` проверяет, что API запущен. Для проверки подключения к базе используйте любой маршрут, который читает или записывает данные, например `GET /employees`.

## Маршруты

| Метод | Путь | Действие | Успех | Ошибки |
|---|---|---|---|---|
| GET | `/health` | Проверить, что API запущен | 200 | — |
| POST | `/employees` | Создать сотрудника | 201 | 409, 422 |
| GET | `/employees` | Получить список сотрудников | 200 | — |
| GET | `/employees/{id}` | Найти сотрудника | 200 | 404, 422 |
| PATCH | `/employees/{id}/deactivate` | Деактивировать сотрудника | 200 | 404, 409, 422 |
| POST | `/equipment` | Добавить предмет | 201 | 409, 422 |
| GET | `/equipment` | Получить список оборудования | 200 | — |
| GET | `/equipment/{id}` | Найти предмет | 200 | 404, 422 |
| POST | `/loans` | Выдать предмет сотруднику | 201 | 404, 409, 422 |
| GET | `/loans?active=true&employee_id=1` | Получить список выдач с необязательными фильтрами | 200 | 422 |
| GET | `/loans/{id}` | Найти выдачу | 200 | 404, 422 |
| POST | `/loans/{id}/return` | Вернуть предмет | 200 | 404, 409, 422 |

Ошибки `404` и `409` возвращаются в формате `{"detail": "текст"}`. Ошибки валидации (`422`) формирует FastAPI.

### Сценарий выдачи и возврата

1. Через `POST /employees` создайте сотрудника, например `{"name": "Иван", "email": "ivan@example.com"}`. Запомните его `id`.
2. Через `POST /equipment` добавьте предмет, например `{"name": "Ноутбук", "inventory_number": "INV-001"}`. Запомните `id` предмета.
3. Через `POST /loans` передайте оба ID, например `{"employee_id": 1, "equipment_id": 1}`. Ожидайте `201 Created`. У новой выдачи `returned_at` равен `null`.
4. Вызовите `GET /loans?active=true` и убедитесь, что выдача есть в списке активных.
5. Через `POST /loans/{id}/return` верните предмет. Используйте ID **выдачи** из шага 3. Ожидайте `200 OK` и заполненное поле `returned_at`.
6. Вызовите `GET /loans?active=false` и убедитесь, что выдача есть в списке завершённых.
7. Повторите `POST /loans` с тем же сотрудником и предметом. Должна появиться новая активная выдача с отдельным ID.

Пример ответа на создание выдачи:

```json
{
  "id": 1,
  "employee_id": 1,
  "equipment_id": 1,
  "issued_at": "2026-11-18T04:10:00.123456+03:00",
  "returned_at": null
}
```

## Устройство проекта

```text
app/
  main.py          приложение FastAPI, роутеры, обработчики ошибок, /health
  database.py      Engine и фабрика сессий SQLAlchemy
  dependencies.py  создание сервисов и граница транзакции
  exceptions.py    NotFoundError и ConflictError
  routers/         HTTP-маршруты и коды ответов
  schemas/         Pydantic-схемы запросов и ответов
  services/        бизнес-правила
  repositories/    протоколы и реализации доступа к данным
    models.py      ORM-модели Employee, Equipment и Loan
tests/
  fakes.py        тестовые репозитории в памяти
  conftest.py     фикстуры и подмены зависимостей FastAPI
  test_services/  тесты бизнес-правил
  test_api/       тесты HTTP-слоя
schema.sql        схема PostgreSQL
```

Роутер принимает HTTP-запрос и передаёт проверенные данные сервису. Сервис применяет бизнес-правила и вызывает методы репозиториев через `Protocol`. Репозитории выполняют запросы к базе и возвращают типизированные словари `EmployeeRow`, `EquipmentRow` и `LoanRow`. Обработчики в `main.py` преобразуют `NotFoundError` в `404`, а `ConflictError` — в `409`.

В `dependencies.py` приложение подключает `SqlAlchemyEmployeeRepository`, `SqlAlchemyEquipmentRepository` и `SqlAlchemyLoanRepository`. Старые реализации на прямом SQL сохранены в тех же файлах для сравнения. Общие протоколы позволяют сервисам работать с обеими реализациями и с тестовыми репозиториями.

ORM-модели описывают, как Python-объекты связаны с таблицами PostgreSQL. Pydantic-схемы описывают входные и выходные данные HTTP API. Метод `_to_row()` в каждом ORM-репозитории преобразует модель в словарь, который ожидает сервис.

### Граница транзакции

Для HTTP-запроса, которому нужна база, `get_session()` в `dependencies.py` открывает сессию через `session_factory.begin()`. Все репозитории, участвующие в операции, получают одну `Session`. При успешном выходе из контекстного менеджера SQLAlchemy выполняет `commit()`, при исключении — `rollback()`. В обоих случаях сессия закрывается. Благодаря `scope="function"` транзакция завершается до отправки HTTP-ответа.

При создании сотрудника или оборудования `flush()` отправляет вставку в PostgreSQL внутри открытой транзакции и позволяет сразу получить ID. При создании выдачи `session.scalars(stmt)` выполняет `INSERT ... RETURNING` и возвращает созданную запись. Фиксация транзакции в обоих случаях происходит в общей зависимости.

### Защита от гонок

- При выдаче и деактивации `SELECT ... FOR UPDATE` блокирует строку сотрудника. При возврате блокируется строка выдачи. Блокировки сохраняются до завершения общей транзакции.
- Частичный уникальный индекс `uq_loans_active_equipment` по `equipment_id` действует для строк с `returned_at IS NULL`. Он обеспечивает максимум одну активную выдачу на предмет. После возврата закрытая выдача выходит из индекса, сохраняясь в истории.
- Схема PostgreSQL задаёт обязательные поля, уникальность email и инвентарного номера, проверки непустых строк и времени возврата, а также внешние ключи с `ON DELETE RESTRICT`.

## Тесты

```bash
python -m mypy app tests --disallow-untyped-defs
python -m pytest -q
```

После подключения ORM выполнен `python -m pytest -q`. Результат — **82 passed**.

Сервисные тесты используют репозитории в памяти. API-тесты через `app.dependency_overrides` подставляют сервисы с этими репозиториями. Так проверяются бизнес-правила, валидация и HTTP-ответы. SQL-запросы, блокировки и откат дополнительно проверены вручную на PostgreSQL.

GitHub Actions запускает mypy и pytest при `push` и `pull request`. Конфигурация находится в `.github/workflows/tests.yml`.

## Ручные проверки на PostgreSQL

| Проверка | Результат |
|---|---|
| Создание сотрудника и оборудования через Swagger | `201 Created`, оба объекта получили ID |
| Выдача, возврат и повторная выдача | Первая выдача закрылась, повторная получила новый ID |
| Попытка выдать уже занятый предмет | `409 Conflict` |
| Повторный возврат закрытой выдачи | `409 Conflict` |
| Попытка выдать четвёртый свободный предмет сотруднику с тремя активными выдачами | `409 Conflict` |
| Деактивация сотрудника с активной выдачей | `409 Conflict` |
| Блокировка строки в двух подключениях | Второе подключение получило `55P03` при `FOR UPDATE NOWAIT`. После завершения первой транзакции повторный запрос смог взять блокировку |
| Вторая активная выдача того же предмета напрямую через SQL | PostgreSQL вернул `23505` и указал индекс `uq_loans_active_equipment` |
| Откат после успешного `flush()` | Вставка получила ID. После намеренного исключения поиск в новой сессии вернул `None` |

В предыдущей версии проекта также проверены сохранение данных после перезапуска API, ограничение `NOT NULL` на `issued_at`, уникальность email и инвентарного номера и конфликт при двух попытках создать сотрудника с одинаковым email.

### Как воспроизвести проверку отката

Запустите следующий Python-код с активным виртуальным окружением и `DATABASE_URL`, указывающим на учебную базу.

```python
from uuid import uuid4

from app.database import get_session_factory
from app.repositories.employees import SqlAlchemyEmployeeRepository


class RollbackDemo(Exception):
    pass


session_factory = get_session_factory()
email = f"rollback-{uuid4().hex}@example.com"

try:
    with session_factory.begin() as session:
        repo = SqlAlchemyEmployeeRepository(session)
        employee = repo.create("Rollback Demo", email)
        print("После flush() получен ID:", employee["id"])
        raise RollbackDemo()
except RollbackDemo:
    print("Транзакция завершилась откатом")

with session_factory() as session:
    repo = SqlAlchemyEmployeeRepository(session)
    employee = repo.get_by_email(email)
    print("Результат поиска в новой сессии:", employee)
    assert employee is None
```

`create()` выполняет `flush()`, поэтому база успевает выполнить `INSERT` и присвоить сотруднику ID. Исключение `RollbackDemo` выходит из блока `with`, и SQLAlchemy откатывает транзакцию. Последняя строка вывода — `Результат поиска в новой сессии: None`.

## Прямой SQL и ORM

В старом `get_by_email()` запрос выглядел так:

```sql
SELECT id, name, email, is_active
FROM employees
WHERE email = %s
```

Репозиторий выполнял его через `cursor.execute()`, а `fetchone()` возвращал словарь благодаря `dict_row` или `None`. В ORM-версии запрос строится на атрибутах модели:

```python
stmt = select(Employee).where(Employee.email == email)
employee = self.session.scalars(stmt).one_or_none()
```

`one_or_none()` возвращает `Employee` или `None`. Если сотрудник найден, `_to_row()` преобразует объект в `EmployeeRow`, который ожидает сервис.

Преимущество ORM — запросы можно строить из атрибутов модели и добавлять условия по мере необходимости. Компромисс — нужно понимать, когда SQLAlchemy отправит запрос в базу, какие объекты отслеживает `Session` и когда заканчивается транзакция.

## Как закрыты замечания предыдущей работы

- ID принимаются как строгие целые числа от `1` до `2147483647`. Значения `true`, `1.5`, `"1"` и числа вне диапазона дают `422`.
- Длины строк в схемах соответствуют ограничениям PostgreSQL.
- Время выдачи и возврата задаёт PostgreSQL через `now()`. Лишние поля в теле запроса отклоняются через `extra="forbid"`. Даты в ответах возвращаются в формате ISO 8601.
- В проекте используется типизация. Команда проверки — `python -m mypy app tests --disallow-untyped-defs`.

## Использование AI

В предыдущей версии проекта использовал Claude, а при переходе на SQLAlchemy — ChatGPT. Помощники объясняли слои приложения, `Protocol`, зависимости FastAPI, ORM, транзакции и блокировки. Также использовал их для разбора ошибок и примеров кода.

Результат проверял через pytest, Swagger и отдельные сценарии в PostgreSQL. Непонятные места разбирал до тех пор, пока не мог объяснить их на примере своего проекта.