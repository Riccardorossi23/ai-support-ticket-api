from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utc_now() -> datetime:
    # datetime.utcnow() e' deprecato da Python 3.12, quindi uso questa versione.
    # Tolgo il fuso perche' la colonna DateTime e' "naive": salvo comunque sempre l'ora UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(100))
    # CORRETTO: avevo messo unique=True sull'email, ma cosi' un cliente non poteva aprire due ticket.
    email: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))
    priority: Mapped[str] = mapped_column(String(20))
    # CORRETTO: il default era "open", ma gli stati ammessi sono aperto / in_lavorazione / chiuso.
    status: Mapped[str] = mapped_column(String(20), default="aperto")
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now)
    # NUOVO: di chi e' il ticket. Mi serve per l'autorizzazione: un user vede solo i suoi.
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    # Ruoli possibili: "user" (default) e "admin".
    role: Mapped[str] = mapped_column(String(20), default="user")
