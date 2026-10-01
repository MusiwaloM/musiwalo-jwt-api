from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_successful_login():
    response = client.post(
        "/login",
        data={"username": "musiwalo", "password": "password123"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_protected_route_without_token():
    response = client.get("/protected-tenders")
    assert response.status_code == 401

def test_protected_route_with_token():
    # Log in first
    login_response = client.post(
        "/login",
        data={"username": "musiwalo", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Use the token to access the protected route
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/protected-tenders", headers=headers)
    
    assert response.status_code == 200