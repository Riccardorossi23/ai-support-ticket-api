from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class Category(str, Enum):
    PAGAMENTO = "pagamento"
    ACCOUNT = "account"
    SPEDIZIONE = "spedizione"
    ALTRO = "altro"


class Priority(str, Enum):
    BASSA = "bassa"
    MEDIA = "media"
    ALTA = "alta"


class TicketStatus(str, Enum):
    APERTO = "aperto"
    IN_LAVORAZIONE = "in_lavorazione"
    CHIUSO = "chiuso"


class TicketCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    category: Category
    priority: Priority
    message: str = Field(min_length=5, max_length=2000)


class TicketUpdate(BaseModel):
    customer_name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    category: Category | None = None
    priority: Priority | None = None
    status: TicketStatus | None = None
    message: str | None = Field(default=None, min_length=5, max_length=2000)


class TicketResponse(TicketCreate):
    id: int
    status: TicketStatus
    created_at: datetime
    # NUOVO: mostro anche chi e' il proprietario del ticket.
    owner_id: int


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    # Alzato da 6 a 8 caratteri. Il ruolo NON e' qui di proposito: nessuno si puo' auto-assegnare "admin".
    password: str = Field(min_length=8, max_length=100)


# NUOVO: per il login servono solo email e password. Prima usavo UserCreate,
# che pretendeva anche lo username senza che servisse a niente.
class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=100)


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
