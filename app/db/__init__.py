"""SQLite persistence layer.

- models.py     : SQLAlchemy ORM table definitions.
- session.py    : engine/session management (get_session, get_db, init_db).
- repository.py : the only functions other packages should call — CRUD +
                   EnvironmentalState <-> ORM translation + merge-on-write.
"""
