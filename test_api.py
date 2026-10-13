
import pytest
import app as api


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Для тестов используется отдельная временная база данных.
    monkeypatch.setattr(api, "DB_PATH", tmp_path / "test_users.db")
    api.init_db()

    api.app.config["TESTING"] = True

    with api.app.test_client() as client:
        yield client


def test_get_users_empty(client):
    response = client.get("/api/users")

    assert response.status_code == 200
    assert response.get_json() == []


def test_create_user(client):
    response = client.post(
        "/api/users",
        json={"name": "Ivan"}
    )

    assert response.status_code == 201
    assert response.get_json()["name"] == "Ivan"


def test_get_users_after_creation(client):
    client.post("/api/users", json={"name": "Ivan"})

    response = client.get("/api/users")

    assert response.status_code == 200
    assert len(response.get_json()) == 1
    assert response.get_json()[0]["name"] == "Ivan"


def test_delete_user(client):
    created = client.post("/api/users", json={"name": "Ivan"})
    user_id = created.get_json()["id"]

    response = client.delete(f"/api/users/{user_id}")

    assert response.status_code == 200

    users = client.get("/api/users").get_json()
    assert users == []


def test_delete_missing_user(client):
    response = client.delete("/api/users/99999")

    assert response.status_code == 404


def test_sql_injection_is_stored_as_plain_text(client):
    payload = "' OR 1=1 --"

    response = client.post(
        "/api/users",
        json={"name": payload}
    )

    assert response.status_code == 201
    assert response.get_json()["name"] == payload

    users = client.get("/api/users").get_json()
    assert len(users) == 1
    assert users[0]["name"] == payload


def test_xss_is_returned_as_json_text(client):
    payload = "<script>alert('XSS')</script>"

    response = client.post(
        "/api/users",
        json={"name": payload}
    )

    assert response.status_code == 201
    assert response.is_json
    assert response.get_json()["name"] == payload


def test_empty_name_is_rejected(client):
    response = client.post(
        "/api/users",
        json={"name": "   "}
    )

    assert response.status_code == 400


def test_missing_name_is_rejected(client):
    response = client.post("/api/users", json={})

    assert response.status_code == 400
