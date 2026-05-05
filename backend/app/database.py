from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from .config import settings

# psycopg3 driver
db_url = settings.database_url.replace("postgresql://", "postgresql+psycopg://", 1) \
    if settings.database_url.startswith("postgresql://") and "+psycopg" not in settings.database_url \
    else settings.database_url

engine = create_engine(db_url, pool_pre_ping=True, pool_size=10, max_overflow=20, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base = declarative_base()


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
