
def test_create_contact(client):
    response = client.post(
        "/api/contact/",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "message": "Hello from tests"
        }
    )

    assert response.status_code == 201
    assert response.json() == {"status": True}

def test_get_all_contacts(client):
    response = client.get("/api/contact/")
    assert response.status_code == 200

    body = response.json()
    assert isinstance(body, list)

    if body:
        contact = body[0]
        assert "_id" in contact
        assert "name" in contact
        assert "email" in contact
        assert "message" in contact
        assert "created_at" in contact

def test_get_one_contact(client):
    # Create contact first
    client.post(
        "/api/contact/",
        json={
            "name": "Single User",
            "email": "single@example.com",
            "message": "Single fetch test"
        }
    )

    # Fetch all
    all_contacts = client.get("/api/contact/").json()
    contact_id = all_contacts[0]["_id"]

    # Fetch one
    response = client.get(f"/api/contact/{contact_id}/")
    assert response.status_code == 200

    contact = response.json()
    assert contact["_id"] == contact_id
    assert contact["name"] == "Single User"
