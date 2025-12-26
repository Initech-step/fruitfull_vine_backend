
def test_root(client):
    response = client.get("/")
    assert response.status_code == 200


def test_create_category(client, admin_token):
    response = client.post(
        "/api/category/",
        json={
            "name": "TEST_CATEGORY",
            "description": "Created by TestClient"
        },
        headers={"token": admin_token}
    )

    assert response.status_code == 201
    assert response.json() == {"status": True}


def test_get_categories(client):
    response = client.get("/api/category/")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] is True
    assert body["data"] == []


def test_delete_category(client, admin_token):
    # create
    client.post(
        "/api/category/",
        json={
            "name": "TEST_DELETE_CATEGORY",
            "description": "Will be deleted"
        },
        headers={"token": admin_token}
    )

    # fetch
    categories = client.get("/api/category/").json()["data"]
    assert len(categories) == 1

    category_id = categories[0]["_id"]

    # delete
    delete_response = client.delete(
        f"/api/category/{category_id}/",
        headers={"token": admin_token}
    )

    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": True}

    # verify
    remaining = client.get("/api/category/").json()["data"]
    assert remaining == []
