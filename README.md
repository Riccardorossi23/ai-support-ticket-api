# AI Support Ticket API

API REST per gestire ticket di assistenza clienti. Progetto di consolidamento dopo il corso FastAPI:
CRUD, validazione, autenticazione JWT, ruoli, error handling e test automatici.

## Stack

- Python 3.13, FastAPI, Uvicorn
- SQLAlchemy 2.0 (SQLite ora, PostgreSQL in futuro)
- Pydantic v2 per la validazione
- PyJWT per i token, PBKDF2-SHA256 (libreria standard) per le password
- pytest + httpx per i test

## Struttura

```
app/
  main.py          avvio app, creazione tabelle, primo admin
  config.py        impostazioni lette da .env / variabili d'ambiente
  database.py      engine, sessione, Base
  models.py        tabelle Ticket e User
  schemas.py       modelli Pydantic (validazione e risposte)
  crud.py          funzioni di accesso al database
  security.py      hash password e JWT
  dependencies.py  get_current_user, require_admin
  routers/
    tickets.py     endpoint dei ticket
    users.py       registrazione, login, /users/me
tests/             test automatici
```

## Installazione

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Variabili d'ambiente

Copia `.env.example` in `.env` e compila i valori. Il file `.env` e' nel `.gitignore`: non va mai pubblicato.

| Variabile | Obbligatoria | Descrizione |
|---|---|---|
| `SECRET_KEY` | si | Chiave per firmare i JWT. Generala con `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | Durata del token (default 30) |
| `DATABASE_URL` | no | Default `sqlite:///./ticket.db` |
| `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` | no | Se presenti, il primo admin viene creato all'avvio |

## Avvio

```powershell
python -m uvicorn app.main:app --reload
```

Le tabelle vengono create automaticamente al primo avvio.
Se hai un vecchio `ticket.db` creato prima dell'aggiunta di `owner_id`, cancellalo: non uso migrazioni.

Swagger: http://127.0.0.1:8000/docs

## Endpoint

| Metodo | Percorso | Chi puo' usarlo | Descrizione |
|---|---|---|---|
| GET | `/health` | tutti | Stato del servizio |
| POST | `/users/register` | tutti | Registra un utente (sempre ruolo `user`) |
| POST | `/users/login` | tutti | Restituisce il token JWT |
| GET | `/users/me` | utente loggato | Dati dell'utente corrente |
| POST | `/tickets/` | utente loggato | Crea un ticket (il proprietario e' chi lo crea) |
| GET | `/tickets/` | utente loggato | Lista, con filtri `status`, `priority`, `category` anche combinati |
| GET | `/tickets/search?q=...` | utente loggato | Cerca in messaggio, nome cliente e categoria |
| GET | `/tickets/stats` | admin | `total`, `open`, `in_progress`, `closed`, `high_priority` |
| GET | `/tickets/{id}` | proprietario o admin | Dettaglio |
| PUT | `/tickets/{id}` | proprietario o admin | Modifica (lo `status` solo admin) |
| DELETE | `/tickets/{id}` | admin | Elimina |

Valori ammessi: category `pagamento | account | spedizione | altro`, priority `bassa | media | alta`,
status `aperto | in_lavorazione | chiuso`.

## Autenticazione e autorizzazione

1. Ci si registra con `POST /users/register`.
2. Con `POST /users/login` (email e password) si riceve un `access_token`.
3. Il token va inviato in ogni richiesta protetta: `Authorization: Bearer <token>`.
   In Swagger: bottone **Authorize** e incolla il token.

Le password sono salvate con PBKDF2-SHA256, salt casuale e 600000 iterazioni. Il token contiene solo l'id
utente e la scadenza: il ruolo viene riletto dal database a ogni richiesta.

### Cosa puo' fare ogni ruolo

**user**
- creare ticket
- vedere, cercare e modificare solo i propri ticket
- non puo' cambiare lo `status` di un ticket, non puo' cancellare, non vede le statistiche

**admin**
- tutto quello che fa un user, ma su tutti i ticket
- cambiare lo `status`, cancellare ticket, vedere le statistiche

Chi si registra e' sempre `user`. Il primo admin si crea con le variabili `ADMIN_*` del `.env`.

### Codici di errore

| Codice | Quando |
|---|---|
| 400 | `PUT` senza nessun campo da modificare |
| 401 | token mancante, non valido o scaduto; credenziali errate |
| 403 | ticket di un altro utente; azione riservata agli admin |
| 404 | ticket inesistente |
| 409 | username o email gia' registrati |
| 422 | dati non validi (email, lunghezze, valori non ammessi) |

## Test

```powershell
python -m pytest
```

I test usano un database SQLite in memoria, quindi non toccano `ticket.db`. Coprono: health, CRUD ticket,
ticket inesistente, filtri, ricerca, statistiche, registrazione, login, credenziali errate, autenticazione e autorizzazione.

## Esempi (PowerShell)

```powershell
# registrazione
Invoke-RestMethod -Method Post http://127.0.0.1:8000/users/register -ContentType "application/json" `
  -Body '{"username":"mario","email":"mario@example.com","password":"password123"}'

# login e salvataggio del token
$token = (Invoke-RestMethod -Method Post http://127.0.0.1:8000/users/login -ContentType "application/json" `
  -Body '{"email":"mario@example.com","password":"password123"}').access_token

# creazione ticket
Invoke-RestMethod -Method Post http://127.0.0.1:8000/tickets/ -ContentType "application/json" `
  -Headers @{Authorization="Bearer $token"} `
  -Body '{"customer_name":"Mario Rossi","email":"cliente@example.com","category":"pagamento","priority":"alta","message":"Non riesco a pagare"}'

# lista con filtri
Invoke-RestMethod "http://127.0.0.1:8000/tickets/?priority=alta&category=pagamento" -Headers @{Authorization="Bearer $token"}
```

## Possibili miglioramenti futuri

- Migrazione a PostgreSQL (basta cambiare `DATABASE_URL`) e uso di Alembic per le migrazioni
- Docker e docker-compose
- Paginazione della lista ticket e ordinamento
- Refresh token e logout
- Limite ai tentativi di login (rate limiting)
- Integrazione AI: classificazione automatica, priorita', riassunto e risposta suggerita
