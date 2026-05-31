import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the app directory to the system path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app"))

from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_upload_invalid_file_type():
    # Attempt to upload a non-PDF file
    response = client.post(
        "/upload/test_session_123",
        files={"file": ("test.txt", b"dummy content", "text/plain")}
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_ask_without_upload():
    # Should say no documents found since session is empty
    response = client.post(
        "/ask",
        json={"question": "What is AI?", "session_id": "empty_session_456"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "No documents found" in data["answer"]
    assert len(data["sources"]) == 0
