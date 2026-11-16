#  Tutto cio' che riguarda la sicurezza sta qui: hash delle password e token JWT.
# Li tengo separati dai router cosi' i router restano corti e leggibili.
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app import config


# ---------- PASSWORD ----------
# Prima usavo SHA-256 "liscio": e' velocissimo, quindi chi ruba il database puo' provare
# miliardi di password al secondo, e senza salt due utenti con la stessa password avevano lo stesso hash.
# Adesso uso PBKDF2 (e' dentro hashlib, non serve installare niente) con un salt casuale per ogni
# utente e tanti giri, in modo da rendere ogni tentativo lento.
# Nel database salvo tutto in una stringa sola: algoritmo$giri$salt$hash


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), config.PASSWORD_ITERATIONS
    )
    return f"pbkdf2_sha256${config.PASSWORD_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    # Se nel database c'e' un hash vecchio (es. SHA-256 senza i "$") non crasho: dico solo "no".
    try:
        algorithm, iterations, salt, expected = stored_hash.split("$")
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations))
    # compare_digest invece di "==" per non far trapelare informazioni dal tempo di confronto.
    return hmac.compare_digest(digest.hex(), expected)


# ---------- JWT ----------
# Nel token metto solo l'id dell'utente ("sub") e la scadenza ("exp").
# Il ruolo NON lo metto: lo rileggo dal database a ogni richiesta, cosi' se tolgo i permessi
# a qualcuno hanno effetto subito e non quando scade il token.


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    # PyJWT vuole che "sub" sia una stringa, per questo str(user_id).
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """Restituisce l'id utente se il token e' valido, altrimenti None."""
    try:
        # Passo la lista degli algoritmi ammessi a mano: e' la protezione contro i token "alg: none".
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        # Token scaduto, firma sbagliata, formato strano: per me sono tutti "non valido".
        return None
