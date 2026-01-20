import os

def test_create_product(client, admin_token):
    # Open the test image file
    current_dir = os.path.dirname(__file__)
    file_path1 = os.path.join(current_dir, "test.jpg")
    file_path2 = os.path.join(current_dir, "test2.png")

    with open(file_path1, "rb") as img1, open(file_path2, "rb") as img2:
        
        payload = {
            "category_id": "prodcat1",
            "category_name": "Tech",
            "product_name": "Test Product",
            "short_description": "Test Product",
            "body": "This is a test product body",
            "draft": "false",  # Form data sends booleans as strings
        }
        
        files = [
            ("images", ("test.jpg", img1, "image/jpeg")),
            ("images", ("test2.png", img2, "image/png"))
        ]
        
        response = client.post(
            "/api/product/",
            data=payload,
            files=files,
            headers={"token": admin_token}
        )

    assert response.status_code == 201
    assert response.json() == {"status": True}


def test_get_products(client, test_products_setup):
    response = client.get("/api/products/?page=1&limit=15")
    assert response.status_code == 200

    body = response.json()

    assert "current_page" in body
    assert "pages" in body
    assert "products" in body
    assert isinstance(body["products"], list)


def test_get_products_by_category(client, test_products_setup):
    response = client.get("/api/products/?page=1&limit=15&category_id=prodcat1/")
    assert response.status_code == 200

    body = response.json()

    assert "current_page" in body
    assert "pages" in body
    assert "products" in body
    assert isinstance(body["products"], list)

    for product in body["products"]:
        assert product["category_id"].lower() == "prodcat1"


def test_product_schema(client, test_products_setup):
    response = client.get(f"/api/product/{test_products_setup[0]}/")
    product = response.json()
    if not product:
        return  # allow empty DB

    assert "_id" in product
    assert isinstance(product["_id"], str)

    assert "category_id" in product
    assert "category_name" in product
    assert "product_name" in product
    assert "short_description" in product
    assert "date" in product


def test_get_last_product(client, test_products_setup):
    response = client.get("/api/get_last_product/")
    assert response.status_code == 200

    body = response.json()
    assert "_id" in body
    assert isinstance(body["_id"], str)
    assert "category_id" in body
    assert "category_name" in body
    assert "product_name" in body
    assert "short_description" in body
    assert "body" in body
    assert "date" in body


def test_delete_product(client, admin_token, test_products_setup):
    # Delete
    delete_response = client.delete(
        f"/api/product/{test_products_setup[0]}/", headers={"token": admin_token}
    )

    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": True}
