from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Ticket, User
from app.schemas import TicketCreate, TicketUpdate


def _value(x):
    # I filtri mi arrivano come Enum (es. Priority.ALTA) ma nel database ho le stringhe ("alta").
    # Questa piccola funzione prende il valore se e' un Enum, altrimenti lascia com'e'.
    return getattr(x, "value", x)


# ---------- TICKET ----------


def create_ticket(db: Session, ticket: TicketCreate, owner_id: int):
    # MODIFICATO: ora serve anche owner_id, cioe' l'utente loggato che crea il ticket.
    # mode="json" trasforma gli Enum in semplici stringhe: SQLite le accetta lo stesso,
    # ma PostgreSQL (dove migrero') no, quindi meglio sistemarlo subito.
    obj = Ticket(**ticket.model_dump(mode="json"), owner_id=owner_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_ticket(db: Session, ticket_id: int):
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()


def list_tickets(db: Session, status=None, priority=None, category=None, owner_id=None):
    q = db.query(Ticket)
    # NUOVO: se passo owner_id vedo solo i ticket di quell'utente (lo uso per i normali "user").
    if owner_id is not None:
        q = q.filter(Ticket.owner_id == owner_id)
    if status:
        q = q.filter(Ticket.status == _value(status))
    if priority:
        q = q.filter(Ticket.priority == _value(priority))
    if category:
        q = q.filter(Ticket.category == _value(category))
    return q.all()


def search_tickets(db: Session, qtext: str, owner_id=None):
    p = f"%{qtext}%"
    q = db.query(Ticket).filter(
        or_(
            Ticket.message.ilike(p),
            Ticket.customer_name.ilike(p),
            Ticket.category.ilike(p),
        )
    )
    # Stessa logica di list_tickets: un user cerca solo tra i suoi ticket.
    if owner_id is not None:
        q = q.filter(Ticket.owner_id == owner_id)
    return q.all()


def update_ticket(db: Session, ticket, data: TicketUpdate):
    # exclude_none: se qualcuno manda "message": null non lo scrivo nel database
    # (la colonna non accetta null e avrei un errore 500).
    changes = data.model_dump(mode="json", exclude_unset=True, exclude_none=True)
    for field, value in changes.items():
        setattr(ticket, field, value)
    db.commit()
    db.refresh(ticket)
    return ticket


def delete_ticket(db: Session, ticket):
    db.delete(ticket)
    db.commit()


# ---------- UTENTI ----------


def get_user_by_email(db: Session, email: str):
    # NUOVO: la uso in login e in registrazione. Metto l'email in minuscolo
    # cosi' "Mario@x.it" e "mario@x.it" sono lo stesso utente.
    return db.query(User).filter(User.email == email.lower()).first()


def create_user(db: Session, username: str, email: str, hashed_password: str, role: str = "user"):
    obj = User(username=username, email=email.lower(), hashed_password=hashed_password, role=role)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
