
def test_create_contact(client):
    response = client.post(
        "/api/contact/",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "message": "Hello from tests",
            "phone_number": "+2349282892"
        }
    )

    assert response.status_code == 201
    assert response.json() == {"status": True}

def test_get_all_contacts(client, test_contact):
    response = client.get("/api/contact/")
    assert response.status_code == 200

    body = response.json()["contacts"]
    assert isinstance(body, list)

    if body:
        contact = body[0]
        assert "_id" in contact
        assert "name" in contact
        assert "email" in contact
        assert "message" in contact

def test_get_one_contact(client, test_contact):
    response = client.get(f"/api/contact/{test_contact[0]}/")
    assert response.status_code == 200

    contact = response.json()
    assert contact["_id"] == test_contact[0]

def test_delete_contact(client, admin_token, test_contact):
    response = client.delete(
        f"/api/contact/{test_contact[0]}/",
        headers={"token": admin_token}
    )
    assert response.status_code == 200
    assert response.json() == {"status": True}
