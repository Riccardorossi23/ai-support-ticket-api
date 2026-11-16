# Qui ci sono le "dipendenze" di FastAPI che usano gli endpoint protetti:
#   get_current_user -> chi sta facendo la richiesta? (401 se non e' autenticato)
#   require_admin    -> e' un admin? (403 se non lo e')
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token

# Uso HTTPBearer: in Swagger compare il bottone "Authorize" dove incollo il token.
# auto_error=False perche' voglio decidere io il messaggio e il codice (401) quando manca il token.
bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise _unauthorized("Not authenticated")

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise _unauthorized("Invalid or expired token")

    # Anche con un token valido controllo che l'utente esista ancora (potrebbe essere stato cancellato).
    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized("User not found")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user
