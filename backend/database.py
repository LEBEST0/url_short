from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # requis pour SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True, nullable=False)
    original = Column(String(2048), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    clicks = Column(Integer, default=0)


def init_db():
    """Crée les tables si elles n'existent pas encore."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dépendance FastAPI : fournit une session DB et la ferme après usage."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
