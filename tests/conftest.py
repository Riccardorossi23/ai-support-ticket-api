# NUOVO FILE. Qui metto le cose che servono a tutti i test (fixture di pytest).
import os

# Queste due righe devono stare PRIMA di importare l'app, perche' config.py legge l'ambiente quando viene importato.
os.environ.setdefault("SECRET_KEY", "chiave-usata-solo-nei-test-" + "x" * 40)
os.environ.setdefault("PASSWORD_ITERATIONS", "1000")  # hash veloce, i test non devono durare minuti

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import User
from app.security import hash_password

PASSWORD = "password123"


@pytest.fixture()
def db_session():
    # Database SQLite in memoria, nuovo per ogni test: non sporco il mio ticket.db
    # e ogni test parte da zero, quindi non dipende da quelli prima.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def client(db_session):
    # Dico a FastAPI di usare il database di test al posto di quello vero.
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _login(client, email, password=PASSWORD):
    r = client.post("/users/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def user_headers(client):
    client.post("/users/register", json={"username": "mario", "email": "mario@example.com", "password": PASSWORD})
    return _login(client, "mario@example.com")


@pytest.fixture()
def other_headers(client):
    # Un secondo utente normale, serve per provare che non puo' toccare i ticket del primo.
    client.post("/users/register", json={"username": "luisa", "email": "luisa@example.com", "password": PASSWORD})
    return _login(client, "luisa@example.com")


@pytest.fixture()
def admin_headers(client, db_session):
    # L'admin non si puo' creare dall'API (e' voluto), quindi lo inserisco direttamente nel database.
    db_session.add(
        User(username="admin", email="admin@example.com", hashed_password=hash_password(PASSWORD), role="admin")
    )
    db_session.commit()
    return _login(client, "admin@example.com")


def ticket_payload(**override):
    data = {
        "customer_name": "Mario Rossi",
        "email": "cliente@example.com",
        "category": "pagamento",
        "priority": "alta",
        "message": "Non riesco a pagare l'ordine",
    }
    data.update(override)
    return data
