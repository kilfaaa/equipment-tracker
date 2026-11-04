class NotFoundError(Exception):
    """Объект не найден (позже станет 404)."""


class ConflictError(Exception):
    """Действие конфликтует с текущим состоянием (позже станет 409)."""