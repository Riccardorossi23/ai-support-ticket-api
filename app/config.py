# Qui raccolgo tutte le impostazioni che leggo dall'ambiente (o dal file .env).
# L'idea e' che nel codice non ci sia nessun segreto scritto a mano: la specifica lo vieta
# e comunque se carico il progetto su GitHub non voglio regalare la chiave a nessuno.
import os

from dotenv import load_dotenv

# Legge il file .env (se esiste) e mette i valori nelle variabili d'ambiente.
# Se una variabile e' gia' impostata dal sistema NON viene sovrascritta: mi serve nei test.
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ticket.db")

# La chiave segreta non ha un valore di default di proposito: se me ne dimentico
# preferisco che l'app non parta, invece di partire con una chiave debole e uguale per tutti.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY mancante. Copia .env.example in .env e inserisci una chiave "
        "(puoi generarla con: python -c \"import secrets; print(secrets.token_hex(32))\")."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Numero di giri dell'hash delle password. 600000 e' il valore consigliato da OWASP per PBKDF2-SHA256.
# Lo rendo configurabile solo per poterlo abbassare nei test e non farli durare una vita.
PASSWORD_ITERATIONS = int(os.getenv("PASSWORD_ITERATIONS", "600000"))

# Dati del primo admin (opzionali).
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
