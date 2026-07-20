from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# DATABASE_URL = "postgresql://postgres:your_password@localhost:5432/aurfx"
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/aurumfx"
# DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@127.0.0.1:5432/aurfx"



engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()