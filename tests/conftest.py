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


@pytest.fixture(autouse=True)
def clean_collections():
    db = connect_to_db()
    collections = [
        db["blog_categories_collection"],
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
