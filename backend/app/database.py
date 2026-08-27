import os
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("La variable DATABASE_URL est absente")


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_database_session() -> Generator[Session, None, None]:
    database_session = SessionLocal()

    try:
        yield database_session
    finally:
        database_session.close()


def check_database() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return True