
def test_create_blog_post(client, admin_token):
    payload = {
        "image_url": "https://example.com/image.jpg",
        "category_id": "cat-001",
        "category_name": "Tech",
        "post_title": "Test Blog Post",
        "short_title": "Test Blog",
        "body": "This is a test blog body",
        "iframe": ""
    }

    response = client.post(
        "/api/blog/",
        json=payload,
        headers={"token": admin_token}
    )

    assert response.status_code == 201
    assert response.json() == {"status": True}


def test_get_blog_posts(client):
    response = client.get("/api/blog/?page=1&limit=10")
    assert response.status_code == 200

    body = response.json()

    assert "current_page" in body
    assert "pages" in body
    assert "blogs" in body

    assert isinstance(body["blogs"], list)

def test_blog_post_schema(client):
    response = client.get("/api/blog/?page=1&limit=10")
    blogs = response.json()["blogs"]

    if not blogs:
        return  # allow empty DB

    blog = blogs[0]

    assert "_id" in blog
    assert isinstance(blog["_id"], str)

    assert "image_url" in blog
    assert "category_id" in blog
    assert "category_name" in blog
    assert "post_title" in blog
    assert "short_title" in blog
    assert "body" in blog
    assert "date" in blog
    assert "iframe" in blog

def test_get_last_blog_post(client):
    response = client.get("/api/get_last_post/")
    assert response.status_code == 200

    body = response.json()

    assert body["status"] is True
    assert "data" in body

    data = body["data"]

    assert "_id" in data
    assert "post_title" in data

def test_delete_blog_post(client, admin_token):
    # Create blog
    client.post(
        "/api/blog/",
        json={
            "image_url": "https://example.com/image.jpg",
            "category_id": "cat-del",
            "category_name": "Delete",
            "post_title": "Delete Me",
            "short_title": "Delete",
            "body": "This will be deleted",
            "iframe": ""
        },
        headers={"token": admin_token}
    )

    # Fetch blogs
    response = client.get("/api/blog/")
    blogs = response.json()["blogs"]

    assert len(blogs) > 0

    blog_id = blogs[0]["_id"]

    # Delete
    delete_response = client.delete(
        f"/api/blog/{blog_id}/",
        headers={"token": admin_token}
    )

    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": True}

    # Verify deletion
    remaining = client.get("/api/blog/").json()["blogs"]
    ids = [b["_id"] for b in remaining]

    assert blog_id not in ids
