from fastapi.testclient import TestClient

from app import app


client = TestClient(app)
TEST_TOKEN = "t7t7PWOxi='D0ov9iG&L+.I{K!x~8g0zr^M3v_P;g(vt,mX_Bg"


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    print(response.json())


def test_create_category():
    payload = {
        "name": "TEST_CATEGORY",
        "description": "Created by TestClient"
    }

    response = client.post(
        "/api/category/",
        json=payload,
        headers={"token": TEST_TOKEN}
    )

    assert response.status_code == 201
    assert response.json() == {"status": True}


def test_get_categories():
    response = client.get("/api/category/")

    assert response.status_code == 200

    body = response.json()
    assert body["status"] is True
    assert isinstance(body["data"], list)


def test_delete_category():
    # 1. Create category
    create_response = client.post(
        "/api/category/",
        json={
            "name": "TEST_DELETE_CATEGORY",
            "description": "Will be deleted"
        },
        headers={"token": TEST_TOKEN}
    )

    assert create_response.status_code == 201

    # 2. Fetch categories to get ID
    get_response = client.get("/api/category/")
    categories = get_response.json()["data"]
    first_category_id = categories[0]['_id']

    # 3. Delete category
    delete_response = client.delete(
        f"/api/category/{first_category_id}/",
        headers={"token": TEST_TOKEN}
    )

    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": True}

    # 4. Verify deletion
    verify_response = client.get("/api/category/")
    ids = [c['_id'] for c in verify_response.json()["data"]]
    assert first_category_id not in ids
