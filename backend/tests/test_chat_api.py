"""POST /api/chat — grounded Q&A, no live model in CI."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _reading_body():
    response = client.post(
        "/api/reading",
        json={
            "full_name": "Ayush Mishra",
            "date_of_birth": "1995-08-15",
            "time_of_birth": "10:30",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_chat_without_a_key_returns_unavailable_not_500():
    body = _reading_body()
    response = client.post(
        "/api/chat",
        json={"message": "Why is leadership low?", "reading": body, "history": []},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "unavailable"
    assert isinstance(payload["reply"], str) and payload["reply"]


def test_empty_question_is_rejected():
    body = _reading_body()
    response = client.post(
        "/api/chat",
        json={"message": "   ", "reading": body},
    )
    assert response.status_code == 422
    assert response.json()["field"] == "message"
