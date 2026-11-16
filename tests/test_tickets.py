from tests.conftest import ticket_payload


def _create(client, headers, **override):
    r = client.post("/tickets/", json=ticket_payload(**override), headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


# ---------- autenticazione ----------

def test_tickets_require_authentication(client):
    assert client.get("/tickets/").status_code == 401
    assert client.post("/tickets/", json=ticket_payload()).status_code == 401


# ---------- CRUD ----------

def test_create_ticket(client, user_headers):
    ticket = _create(client, user_headers)
    assert ticket["status"] == "aperto"
    assert ticket["id"] > 0


def test_create_ticket_validation_returns_422(client, user_headers):
    r = client.post("/tickets/", json=ticket_payload(email="xxx", category="boh", message="no"), headers=user_headers)
    assert r.status_code == 422


def test_same_email_can_open_two_tickets(client, user_headers):
    _create(client, user_headers)
    _create(client, user_headers)  # prima falliva per via dell'unique sull'email


def test_get_ticket(client, user_headers):
    ticket = _create(client, user_headers)
    r = client.get(f"/tickets/{ticket['id']}", headers=user_headers)
    assert r.status_code == 200
    assert r.json()["id"] == ticket["id"]


def test_get_nonexistent_ticket_returns_404(client, user_headers):
    assert client.get("/tickets/9999", headers=user_headers).status_code == 404


def test_update_ticket(client, user_headers):
    ticket = _create(client, user_headers)
    r = client.put(f"/tickets/{ticket['id']}", json={"message": "Messaggio aggiornato"}, headers=user_headers)
    assert r.status_code == 200
    assert r.json()["message"] == "Messaggio aggiornato"


def test_update_with_empty_body_returns_400(client, user_headers):
    ticket = _create(client, user_headers)
    assert client.put(f"/tickets/{ticket['id']}", json={}, headers=user_headers).status_code == 400


def test_update_nonexistent_ticket_returns_404(client, user_headers):
    assert client.put("/tickets/9999", json={"message": "ciao ciao"}, headers=user_headers).status_code == 404


def test_admin_deletes_ticket(client, user_headers, admin_headers):
    ticket = _create(client, user_headers)
    assert client.delete(f"/tickets/{ticket['id']}", headers=admin_headers).status_code == 204
    assert client.get(f"/tickets/{ticket['id']}", headers=admin_headers).status_code == 404


def test_delete_nonexistent_ticket_returns_404(client, admin_headers):
    assert client.delete("/tickets/9999", headers=admin_headers).status_code == 404


# ---------- filtri e ricerca ----------

def test_filters_alone_and_combined(client, user_headers):
    _create(client, user_headers, category="pagamento", priority="alta")
    _create(client, user_headers, category="pagamento", priority="bassa")
    _create(client, user_headers, category="account", priority="alta")

    assert len(client.get("/tickets/?priority=alta", headers=user_headers).json()) == 2
    assert len(client.get("/tickets/?category=pagamento", headers=user_headers).json()) == 2
    assert len(client.get("/tickets/?category=pagamento&priority=alta", headers=user_headers).json()) == 1
    assert len(client.get("/tickets/?status=chiuso", headers=user_headers).json()) == 0


def test_filter_with_invalid_value_returns_422(client, user_headers):
    assert client.get("/tickets/?priority=urgentissima", headers=user_headers).status_code == 422


def test_search_in_message(client, user_headers):
    _create(client, user_headers, message="La spedizione e' in ritardo")
    _create(client, user_headers, message="Password dimenticata")
    r = client.get("/tickets/search?q=spedizione", headers=user_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_search_query_too_short_returns_422(client, user_headers):
    assert client.get("/tickets/search?q=a", headers=user_headers).status_code == 422


# ---------- statistiche ----------

def test_stats_as_admin(client, user_headers, admin_headers):
    t1 = _create(client, user_headers, priority="alta")
    _create(client, user_headers, priority="bassa")
    client.put(f"/tickets/{t1['id']}", json={"status": "in_lavorazione"}, headers=admin_headers)

    r = client.get("/tickets/stats", headers=admin_headers)
    assert r.status_code == 200
    assert r.json() == {"total": 2, "open": 1, "in_progress": 1, "closed": 0, "high_priority": 1}


def test_stats_as_user_returns_403(client, user_headers):
    assert client.get("/tickets/stats", headers=user_headers).status_code == 403


# ---------- autorizzazione ----------

def test_user_sees_only_own_tickets(client, user_headers, other_headers, admin_headers):
    _create(client, user_headers)
    _create(client, other_headers)
    assert len(client.get("/tickets/", headers=user_headers).json()) == 1
    assert len(client.get("/tickets/", headers=admin_headers).json()) == 2


def test_user_cannot_access_other_users_ticket(client, user_headers, other_headers):
    ticket = _create(client, user_headers)
    url = f"/tickets/{ticket['id']}"
    assert client.get(url, headers=other_headers).status_code == 403
    assert client.put(url, json={"message": "provo a modificare"}, headers=other_headers).status_code == 403


def test_admin_can_access_any_ticket(client, user_headers, admin_headers):
    ticket = _create(client, user_headers)
    assert client.get(f"/tickets/{ticket['id']}", headers=admin_headers).status_code == 200


def test_user_cannot_change_status(client, user_headers):
    ticket = _create(client, user_headers)
    r = client.put(f"/tickets/{ticket['id']}", json={"status": "chiuso"}, headers=user_headers)
    assert r.status_code == 403


def test_admin_can_change_status(client, user_headers, admin_headers):
    ticket = _create(client, user_headers)
    r = client.put(f"/tickets/{ticket['id']}", json={"status": "chiuso"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "chiuso"


def test_user_cannot_delete_ticket(client, user_headers):
    ticket = _create(client, user_headers)
    assert client.delete(f"/tickets/{ticket['id']}", headers=user_headers).status_code == 403
