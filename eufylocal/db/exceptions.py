from typing import Any


class DbError(Exception):
    pass


class DbEntityNotFoundError(DbError):
    def __init__(self, entity: Any):
        self.entity = entity
        super().__init__(f"Entity not found: #{entity}")


class DbInvalidEntityError(DbError):
    def __init__(self, entity: Any):
        super().__init__(f"Invalid entity: #{entity}")


class DbIntegrityError(DbError):
    def __init__(self, entity: Any):
        super().__init__(f"Invalid entity: #{entity}")
