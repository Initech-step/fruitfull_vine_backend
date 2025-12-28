# tests/conftest.py
from fastapi.testclient import TestClient
from app import app
import pytest
from pymongo import MongoClient
from utils.database import connect_to_db


@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def admin_token():
    return "t7t7PWOxi='D0ov9iG&L+.I{K!x~8g0zr^M3v_P;g(vt,mX_Bg"

@pytest.fixture(scope="function")
def test_blog_posts_setup():
    db = connect_to_db()
    blog_posts_collection = db["blog_posts_collection"]
    # Insert test blog posts
    test_posts = [
        {
            "image_url": "https://example.com/image1.jpg",
            "category_id": "cat1",
            "category_name": "Category 1",
            "post_title": "Test Blog Post 1",
            "short_title": "Test Blog 1",
            "body": "This is the body of test blog post 1",
            "date": "2024-01-01",
            "iframe": "www.example1.com"
        },
        {
            "image_url": "https://example.com/image1.jpg",
            "category_id": "Cat2",
            "category_name": "Category 2",
            "post_title": "Test Blog Post 2",
            "short_title": "Test Blog 2",
            "body": "This is the body of test blog post 2",
            "date": "2024-01-01",
            "iframe": "www.example1.com"
        },
    ]
    blog_posts_collection.insert_many(test_posts)
    
    # get blog posts and yield their IDs for tests
    blog_posts = list(blog_posts_collection.find({}))
    store_ids = [str(post["_id"]) for post in blog_posts]

    yield store_ids

@pytest.fixture(scope="function")
def test_products_setup():
    db = connect_to_db()
    products_collection = db["products_collection"]
    # Insert test products
    test_products = [
        {
            "image_url": "https://example.com/product1.jpg",
            "category_id": "prodcat1",
            "category_name": "Product Category 1",
            "product_name": "Test Product 1",
            "short_description": "Short description of Test Product 1",
            "body": "This is the body of test product 1",
            "iframe": "www.product1.com"
        },
        {
            "image_url": "https://example.com/product2.jpg",
            "category_id": "prodcat2",
            "category_name": "Product Category 2",
            "product_name": "Test Product 2",
            "short_description": "Short description of Test Product 2",
            "body": "This is the body of test product 2",
            "iframe": "www.product2.com"
        },
    ]
    products_collection.insert_many(test_products)
    
    # get products and yield their IDs for tests
    products = list(products_collection.find({}))
    product_ids = [str(product["_id"]) for product in products]

    yield product_ids

@pytest.fixture(scope="function")
def test_contact():
    db = connect_to_db()
    contact_collection = db["contact_collection"]
    # Insert a test contact
    test_contact = {
        "name": "Single User",
        "email": "single@example.com",
        "message": "Single fetch test",
        "phone_number": "+2349282892"
    }
    contact_collection.insert_one(test_contact)

    # get the contact and yield its ID for tests
    contacts = list(contact_collection.find({}))
    contact_ids = [str(contact["_id"]) for contact in contacts]

    yield contact_ids

@pytest.fixture(autouse=True)
def clean_collections():
    db = connect_to_db()
    collections = [
        db["categories_collection"],
        db["blog_posts_collection"],
        db["products_collection"],
        db["contact_collection"]
    ]

    # before each test
    for c in collections:
        c.delete_many({})

    yield

    # after each test
    for c in collections:
        c.delete_many({})
