from fastapi.testclient import TestClient
import pytest
from api import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200


def test_chat_pusty_message():
    r = client.post("/chat", json={"message": ""})
    assert r.status_code == 422


@pytest.mark.wymaga_ollamy
def test_chat_zwraca_klucze():
    r = client.post("/chat", json={"message": "jak zmienić hasło"})
    assert r.status_code == 200
    dane = r.json()
    assert "agent" in dane
    assert "answer" in dane
    assert "sources" in dane
    assert "citations" in dane