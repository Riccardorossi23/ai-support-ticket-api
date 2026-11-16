
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.crud import (
    create_ticket,
    delete_ticket,
    get_ticket,
    list_tickets,
    search_tickets,
    update_ticket,
)
from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models import Ticket, User
from app.schemas import (
    Category,
    Priority,
    TicketCreate,
    TicketResponse,
    TicketStatus,
    TicketUpdate,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])

# Regole di autorizzazione che ho scelto (le ho scritte anche nel README):
#  - user:  crea ticket, vede/cerca/modifica SOLO i suoi, ma non puo' cambiare lo status ne' cancellare
#  - admin: fa tutto su tutti i ticket (compreso cambiare status, cancellare e vedere le statistiche)


def _is_admin(user: User) -> bool:
    return user.role == "admin"


def _get_ticket_or_error(db: Session, ticket_id: int, current_user: User) -> Ticket:
    # 404 se il ticket non esiste, 403 se esiste ma e' di qualcun altro.
    ticket = get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if not _is_admin(current_user) and ticket.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only access your own tickets")
    return ticket


@router.post("/", response_model=TicketResponse, status_code=201)
def create(
    ticket: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Il proprietario e' sempre chi e' loggato, non lo decide il client.
    return create_ticket(db, ticket, owner_id=current_user.id)


@router.get("/", response_model=list[TicketResponse])
def get_all(
    status: TicketStatus | None = None,
    priority: Priority | None = None,
    category: Category | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # L'admin vede tutto (owner_id=None = nessun filtro), l'user solo i suoi.
    owner_id = None if _is_admin(current_user) else current_user.id
    return list_tickets(db, status, priority, category, owner_id)


@router.get("/search", response_model=list[TicketResponse])
def search(
    q: str = Query(min_length=2),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    owner_id = None if _is_admin(current_user) else current_user.id
    return search_tickets(db, q, owner_id)


@router.get("/stats")
def statistics(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return {
        "total": db.query(func.count(Ticket.id)).scalar() or 0,
        "open": db.query(func.count(Ticket.id)).filter(Ticket.status == "aperto").scalar() or 0,
        "in_progress": db.query(func.count(Ticket.id)).filter(Ticket.status == "in_lavorazione").scalar() or 0,
        "closed": db.query(func.count(Ticket.id)).filter(Ticket.status == "chiuso").scalar() or 0,
        "high_priority": db.query(func.count(Ticket.id)).filter(Ticket.priority == "alta").scalar() or 0,
    }


@router.get("/{ticket_id}", response_model=TicketResponse)
def get(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_ticket_or_error(db, ticket_id, current_user)


@router.put("/{ticket_id}", response_model=TicketResponse)
def update(
    ticket_id: int,
    ticket: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = _get_ticket_or_error(db, ticket_id, current_user)

    changes = ticket.model_dump(exclude_unset=True, exclude_none=True)
    # 400 se la richiesta non cambia niente (body vuoto).
    if not changes:
        raise HTTPException(status_code=400, detail="No fields to update")
    # Solo l'admin puo' cambiare lo status (un cliente non si chiude da solo il ticket).
    if "status" in changes and not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can change the ticket status")

    return update_ticket(db, obj, ticket)


# Solo l'admin puo' cancellare.
@router.delete("/{ticket_id}", status_code=204)
def delete(
    ticket_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    obj = get_ticket(db, ticket_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Ticket not found")
    delete_ticket(db, obj)
