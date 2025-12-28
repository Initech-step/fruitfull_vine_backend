

def test_create_blog_post(client, admin_token):
    payload = {
        "image_url": "https://example.com/image.jpg",
        "category_id": "cat-001",
        "category_name": "Tech",
        "post_title": "Test Blog Post",
        "short_title": "Test Blog",
        "body": "This is a test blog body",
        "iframe": "www.whatever.com"
    }

    response = client.post(
        "/api/blog/",
        json=payload,
        headers={"token": admin_token}
    )

    assert response.status_code == 201
    assert response.json() == {"status": True}

def test_get_blog_posts(client, test_blog_posts_setup):
    response = client.get("/api/blog/?page=1&limit=15")
    assert response.status_code == 200

    body = response.json()

    assert "current_page" in body
    assert "pages" in body
    assert "blogs" in body
    assert isinstance(body["blogs"], list)

def test_blog_post_schema(client, test_blog_posts_setup):
    response = client.get("/api/blog/?page=1&limit=15")
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

def test_get_single_blog_post(client, test_blog_posts_setup):
    response = client.get(f"/api/blog/{test_blog_posts_setup[0]}/")
    assert response.status_code == 200

    body = response.json()
    assert "_id" in body
    assert isinstance(body["_id"], str)

    assert "image_url" in body
    assert "category_id" in body
    assert "category_name" in body
    assert "post_title" in body
    assert "short_title" in body
    assert "body" in body
    assert "date" in body
    assert "iframe" in body

def test_get_last_blog_post(client, test_blog_posts_setup):
    response = client.get("/api/get_last_post/")
    assert response.status_code == 200

    body = response.json()
    assert "_id" in body
    assert isinstance(body["_id"], str)
    assert "image_url" in body
    assert "category_id" in body
    assert "category_name" in body
    assert "post_title" in body
    assert "short_title" in body
    assert "body" in body
    assert "date" in body
    assert "iframe" in body

def test_delete_blog_post(client, admin_token, test_blog_posts_setup):
    # Delete
    delete_response = client.delete(
        f"/api/blog/{test_blog_posts_setup[0]}/",
        headers={"token": admin_token}
    )

    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": True}

# get blog posts by category
def test_get_blog_posts_by_category(client, test_blog_posts_setup):
    response = client.get("/api/blog/?page=1&limit=15&category_id=cat1/")
    assert response.status_code == 200

    body = response.json()

    assert "current_page" in body
    assert "pages" in body
    assert "blogs" in body
    assert isinstance(body["blogs"], list)

    for blog in body["blogs"]:
        assert blog["category_id"].lower() == "cat1"

