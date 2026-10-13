def register(client, name, email):
    return client.post("/api/register", json={
        "full_name": name,
        "email": email,
        "password": "DemoPass123!",
    })


def login(client, email):
    response = client.post("/api/login", json={
        "email": email,
        "password": "DemoPass123!",
    })
    assert response.status_code == 200
    return response.get_json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"


def test_register_and_duplicate_email(client):
    first = register(client, "Demo One", "one@example.test")
    assert first.status_code == 201
    assert first.get_json()["balance"] == "0.00"

    duplicate = register(client, "Demo One", "ONE@example.test")
    assert duplicate.status_code == 409


def test_deposit_withdraw_and_insufficient_balance(client):
    register(client, "Demo One", "one@example.test")
    token = login(client, "one@example.test")

    deposit = client.post("/api/deposit", json={"amount": "1000.00"}, headers=auth(token))
    assert deposit.status_code == 201
    assert deposit.get_json()["balance"] == "1000.00"

    withdraw = client.post("/api/withdraw", json={"amount": "250.00"}, headers=auth(token))
    assert withdraw.status_code == 201
    assert withdraw.get_json()["balance"] == "750.00"

    too_much = client.post("/api/withdraw", json={"amount": "900.00"}, headers=auth(token))
    assert too_much.status_code == 400
    assert too_much.get_json()["error"] == "Insufficient balance."


def test_transfer_between_accounts(client):
    register(client, "Demo One", "one@example.test")
    register(client, "Demo Two", "two@example.test")
    token_one = login(client, "one@example.test")
    token_two = login(client, "two@example.test")

    account_two = client.get("/api/account", headers=auth(token_two)).get_json()
    client.post("/api/deposit", json={"amount": "500.00"}, headers=auth(token_one))

    transfer = client.post("/api/transfer", json={
        "to_account": account_two["account_number"],
        "amount": "125.00",
    }, headers=auth(token_one))
    assert transfer.status_code == 201
    assert transfer.get_json()["balance"] == "375.00"

    balance_two = client.get("/api/balance", headers=auth(token_two)).get_json()
    assert balance_two["balance"] == "125.00"


def test_invalid_amount_and_missing_token(client):
    register(client, "Demo One", "one@example.test")
    token = login(client, "one@example.test")

    invalid = client.post("/api/deposit", json={"amount": "-5"}, headers=auth(token))
    assert invalid.status_code == 400

    missing_token = client.get("/api/balance")
    assert missing_token.status_code == 401


def test_transaction_history(client):
    register(client, "Demo One", "one@example.test")
    token = login(client, "one@example.test")
    client.post("/api/deposit", json={"amount": "25.00"}, headers=auth(token))

    response = client.get("/api/transactions", headers=auth(token))
    assert response.status_code == 200
    body = response.get_json()
    assert body["count"] == 1
    assert body["transactions"][0]["type"] == "DEPOSIT"
