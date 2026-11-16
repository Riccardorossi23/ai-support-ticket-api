from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL

# MODIFICATO: prima l'URL era scritto qui dentro, ora lo prendo da config.py.
# Cosi' quando migro a PostgreSQL cambio solo la variabile DATABASE_URL nel .env.

# "check_same_thread" e' un'opzione che esiste solo per SQLite: con PostgreSQL darebbe errore,
# quindi la passo soltanto quando il database e' SQLite.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
