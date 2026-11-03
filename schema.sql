CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL CHECK (btrim(name) <> ''),
    email VARCHAR(254) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE equipment (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL CHECK (btrim(name) <> ''),
    inventory_number VARCHAR(50) NOT NULL UNIQUE CHECK (btrim(inventory_number) <> '')
);

CREATE TABLE loans (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees (id) ON DELETE RESTRICT,
    equipment_id INTEGER NOT NULL REFERENCES equipment (id) ON DELETE RESTRICT,
    issued_at TIMESTAMPTZ NOT NULL,
    returned_at TIMESTAMPTZ,
    CHECK (returned_at IS NULL OR returned_at >= issued_at)
);

CREATE UNIQUE INDEX uq_loans_active_equipment
ON loans (equipment_id)
WHERE returned_at IS NULL;
