class EmployeeRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_by_id(self, employee_id):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, is_active FROM employees WHERE id = %s",
                (employee_id,),
            )
            return cur.fetchone()

    def get_by_email(self, email):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, is_active FROM employees WHERE email = %s",
                (email,),
            )
            return cur.fetchone()

    def list_all(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, name, email, is_active FROM employees ORDER BY id")
            return cur.fetchall()

    def get_for_update(self, employee_id):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, is_active FROM employees WHERE id = %s FOR UPDATE",
                (employee_id,),
            )
            return cur.fetchone()

    def create(self, name, email):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO employees (name, email) VALUES (%s, %s) "
                "RETURNING id, name, email, is_active",
                (name, email),
            )
            return cur.fetchone()