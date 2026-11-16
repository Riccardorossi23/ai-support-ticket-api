from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import config
from app.crud import create_user, get_user_by_email
from app.database import Base, SessionLocal, engine
from app.routers import tickets, users
from app.security import hash_password


# MODIFICATO: prima non creavo mai le tabelle e al primo avvio usciva "no such table".
# Le creo qui, all'avvio dell'app (e non appena importo il file) cosi' i test non toccano il database vero.
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _create_first_admin()
    yield


def _create_first_admin():
    # NUOVO: dato che dalla registrazione si diventa sempre "user", qualcuno deve pur essere admin.
    # Se nel .env ho messo i dati dell'admin lo creo al primo avvio (se non esiste gia').
    if not (config.ADMIN_USERNAME and config.ADMIN_EMAIL and config.ADMIN_PASSWORD):
        return
    db = SessionLocal()
    try:
        if get_user_by_email(db, config.ADMIN_EMAIL) is None:
            create_user(
                db,
                config.ADMIN_USERNAME,
                config.ADMIN_EMAIL,
                hash_password(config.ADMIN_PASSWORD),
                role="admin",
            )
    finally:
        db.close()


app = FastAPI(title="AI Support Ticket API", version="1.0.0", lifespan=lifespan)

app.include_router(tickets.router)
app.include_router(users.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
