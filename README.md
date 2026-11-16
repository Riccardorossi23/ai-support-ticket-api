# API per la gestione dei ticket di assistenza

API REST per la gestione dei ticket di assistenza clienti.

Questo progetto è stato realizzato come progetto di consolidamento dopo
aver completato un corso su FastAPI. Si concentra sullo sviluppo backend
con FastAPI, SQLAlchemy, Pydantic, autenticazione, autorizzazione,
validazione, gestione degli errori e test automatizzati.

## Funzionalità

-   API RESTful realizzata con FastAPI
-   Operazioni CRUD per i ticket di assistenza
-   Registrazione e accesso degli utenti
-   Autenticazione basata su JWT
-   Autorizzazione basata sui ruoli (`user` / `admin`)
-   Hash delle password con PBKDF2-SHA256
-   Validazione delle richieste e delle risposte con Pydantic v2
-   Filtri e ricerca dei ticket
-   Statistiche sui ticket per gli amministratori
-   Test automatizzati con pytest e httpx
-   Database SQLite con SQLAlchemy 2.0
-   Configurazione tramite variabili d'ambiente
-   Creazione automatica del primo amministratore

## Tecnologie utilizzate

-   Python 3.13
-   FastAPI
-   Uvicorn
-   SQLAlchemy 2.0
-   SQLite
-   Pydantic v2
-   PyJWT
-   PBKDF2-SHA256
-   pytest
-   httpx

## Struttura del progetto

``` text
app/
├── main.py
├── config.py
├── database.py
├── models.py
├── schemas.py
├── crud.py
├── security.py
├── dependencies.py
└── routers/
    ├── tickets.py
    └── users.py

tests/
└── ...

.env.example
requirements.txt
```

## Installazione

Clona il repository:

``` powershell
git clone https://github.com/Riccardorossi23/ai-support-ticket-api.git
cd ai-support-ticket-api
```

Crea e attiva un ambiente virtuale:

``` powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Installa le dipendenze:

``` powershell
python -m pip install -r requirements.txt
```

## Variabili d'ambiente

Copia il file `.env.example` in `.env` e configura i valori.

Il file `.env` è incluso in \`.gitignore e non deve mai essere caricato
su GitHub.

  ---------------------------------------------------------------------------------
  Variabile                       Obbligatoria            Descrizione
  ------------------------------- ----------------------- -------------------------
  `SECRET_KEY`                    Sì                      Chiave segreta utilizzata
                                                          per firmare i token JWT

  `ACCESS_TOKEN_EXPIRE_MINUTES`   No                      Durata del token.
                                                          Predefinita: `30`

  `DATABASE_URL`                  No                      URL del database.
                                                          Predefinito:
                                                          `sqlite:///./ticket.db`

  `ADMIN_USERNAME`                No                      Nome utente del primo
                                                          amministratore

  `ADMIN_EMAIL`                   No                      Email del primo
                                                          amministratore

  `ADMIN_PASSWORD`                No                      Password del primo
                                                          amministratore
  ---------------------------------------------------------------------------------

Genera una `SECRET_KEY` sicura con:

``` powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Se le variabili `ADMIN_*` sono configurate, il primo amministratore
viene creato automaticamente all'avvio dell'applicazione.

## Avvio dell'API

Avvia il server di sviluppo:

``` powershell
python -m uvicorn app.main:app --reload
```

API:

``` text
http://127.0.0.1:8000
```

Documentazione Swagger:

``` text
http://127.0.0.1:8000/docs
```

Le tabelle del database vengono create automaticamente all'avvio
dell'applicazione.

> Al momento il progetto non utilizza migrazioni del database. Se è
> stato creato un vecchio file `ticket.db` prima dell'aggiunta del campo
> `owner_id`, eliminalo e riavvia l'applicazione.

## Endpoint

  -------------------------------------------------------------------------------
  Metodo            Endpoint                  Accesso           Descrizione
  ----------------- ------------------------- ----------------- -----------------
  GET               `/health`                 Pubblico          Verifica dello
                                                                stato del
                                                                servizio

  POST              `/users/register`         Pubblico          Registra un nuovo
                                                                utente

  POST              `/users/login`            Pubblico          Effettua
                                                                l'accesso e
                                                                restituisce un
                                                                JWT

  GET               `/users/me`               Autenticato       Restituisce le
                                                                informazioni
                                                                dell'utente
                                                                corrente

  POST              `/tickets/`               Autenticato       Crea un ticket

  GET               `/tickets/`               Autenticato       Elenca i ticket
                                                                con filtri
                                                                opzionali

  GET               `/tickets/search?q=...`   Autenticato       Cerca i ticket

  GET               `/tickets/stats`          Admin             Restituisce le
                                                                statistiche dei
                                                                ticket

  GET               `/tickets/{id}`           Proprietario /    Restituisce un
                                              Admin             ticket

  PUT               `/tickets/{id}`           Proprietario /    Modifica un
                                              Admin             ticket

  DELETE            `/tickets/{id}`           Admin             Elimina un ticket
  -------------------------------------------------------------------------------

### Filtri dei ticket

L'endpoint per l'elenco dei ticket supporta i seguenti filtri:

-   `status`
-   `priority`
-   `category`

È possibile combinare più filtri.

### Valori consentiti

Categoria:

``` text
pagamento
account
spedizione
altro
```

Priorità:

``` text
bassa
media
alta
```

Stato:

``` text
aperto
in_lavorazione
chiuso
```

## Autenticazione e autorizzazione

Flusso di autenticazione:

1.  Registrati con `POST /users/register`.
2.  Effettua l'accesso con `POST /users/login`.
3.  L'API restituisce un `access_token`.
4.  Invia il token nelle richieste protette:

``` text
Authorization: Bearer <token>
```

In Swagger, utilizza il pulsante **Authorize** e inserisci il token.

### Sicurezza delle password

Le password vengono memorizzate utilizzando PBKDF2-SHA256, con un salt
casuale e 600.000 iterazioni.

Il JWT contiene l'ID dell'utente e la data di scadenza. Il ruolo
dell'utente viene letto dal database a ogni richiesta autenticata.

### Ruolo utente

Un utente standard (`user`) può:

-   creare ticket
-   elencare i ticket
-   cercare i ticket
-   visualizzare i propri ticket
-   modificare i propri ticket

Un utente standard non può:

-   modificare lo stato dei ticket
-   eliminare ticket
-   accedere alle statistiche
-   accedere ai ticket di altri utenti

### Ruolo amministratore

Un amministratore (`admin`) può:

-   eseguire tutte le operazioni disponibili agli utenti standard
-   accedere a tutti i ticket
-   modificare lo stato dei ticket
-   eliminare ticket
-   accedere alle statistiche dei ticket

Gli utenti registrati tramite `/users/register` ricevono sempre il ruolo
`user`.

Il primo amministratore può essere creato utilizzando le variabili
d'ambiente `ADMIN_*`.

## Codici di stato HTTP

  Codice   Significato
  -------- --------------------------------------------------------------
  `400`    Richiesta non valida, ad esempio una modifica senza campi
  `401`    Token mancante, non valido o scaduto; credenziali non valide
  `403`    Accesso negato
  `404`    Risorsa non trovata
  `409`    Nome utente o email già registrati
  `422`    Errore di validazione

## Test

Esegui la suite di test:

``` powershell
python -m pytest
```

I test utilizzano un database SQLite in memoria, quindi non modificano
il database di sviluppo `ticket.db`.

La suite di test copre:

-   endpoint di controllo dello stato (`health`)
-   operazioni CRUD sui ticket
-   ticket inesistenti
-   filtri dei ticket
-   ricerca dei ticket
-   statistiche dei ticket
-   registrazione degli utenti
-   accesso
-   credenziali non valide
-   autenticazione
-   autorizzazione

## Esempi con PowerShell

### Registrare un utente

``` powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/users/register `
  -ContentType "application/json" `
  -Body '{"username":"mario","email":"mario@example.com","password":"password123"}'
```

### Effettuare l'accesso e salvare il token

``` powershell
$token = (Invoke-RestMethod -Method Post http://127.0.0.1:8000/users/login `
  -ContentType "application/json" `
  -Body '{"email":"mario@example.com","password":"password123"}').access_token
```

### Creare un ticket

``` powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/tickets/ `
  -ContentType "application/json" `
  -Headers @{Authorization="Bearer $token"} `
  -Body '{"customer_name":"Mario Rossi","email":"cliente@example.com","category":"pagamento","priority":"alta","message":"Non riesco a pagare"}'
```

### Elencare i ticket con filtri

``` powershell
Invoke-RestMethod "http://127.0.0.1:8000/tickets/?priority=alta&category=pagamento" `
  -Headers @{Authorization="Bearer $token"}
```

## Miglioramenti futuri

-   Migrazione a PostgreSQL
-   Alembic per le migrazioni del database
-   Docker e Docker Compose
-   Paginazione e ordinamento
-   Refresh token e logout
-   Limitazione della frequenza dei tentativi di accesso
-   Classificazione dei ticket tramite IA
-   Rilevamento automatico della priorità
-   Riepilogo dei ticket
-   Suggerimenti per le risposte ai clienti

## Obiettivo del progetto

L'obiettivo di questo progetto era consolidare i concetti di FastAPI
realizzando un'applicazione backend completa, anziché una raccolta di
esercizi isolati.

Il progetto combina:

``` text
FastAPI
   ↓
Validazione con Pydantic
   ↓
Autenticazione / Autorizzazione
   ↓
SQLAlchemy
   ↓
SQLite
   ↓
CRUD + Ricerca + Filtri + Statistiche
   ↓
Test automatizzati
```

## Autore

**Riccardo Rossi**
