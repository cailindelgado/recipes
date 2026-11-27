import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = os.environ.get("SQLALCHEMY_DATABASE_URI") or (
    f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}/{os.environ['DB_NAME']}"
)

_pool_kwargs = (
    {"pool_size": 1, "max_overflow": 0}
    if not SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(SQLALCHEMY_DATABASE_URL, **_pool_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_reader_url = os.environ.get("SQLALCHEMY_DATABASE_URI")
if _reader_url:
    read_engine = create_engine(_reader_url, **_pool_kwargs)
    ReadSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=read_engine
    )
else:
    read_engine = engine
    ReadSessionLocal = SessionLocal

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
