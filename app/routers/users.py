from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import create_user, get_user_by_email
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import TokenResponse, UserCreate, UserLogin, UserResponse
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(User)
        .filter((User.username == user.username) | (User.email == user.email.lower()))
        .first()
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username or email already registered")
    # Il ruolo non lo prendo dalla richiesta: chi si registra e' sempre "user".
    return create_user(db, user.username, user.email, hash_password(user.password))


@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    # Stesso messaggio sia se l'email non esiste sia se la password e' sbagliata:
    # cosi' chi prova non capisce quali email sono registrate.
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # COMPLETATAMENTO CODICE: qui c'era il TODO del JWT. Ora il token e' vero.
    return {"access_token": create_access_token(db_user.id), "token_type": "bearer"}


# NUOVO ENDPOINT: restituisce l'utente a cui appartiene il token.
@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
