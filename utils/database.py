from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv() 

# Access the environment variables
test_mode = os.getenv("TEST", "True")


def connect_to_db() -> Dict[str, Any]:
    username = "Project-AI"
    pword = "m5vr23zThUdemscI"
    uri = f"mongodb+srv://{username}:{pword}@atlascluster.doihstd.mongodb.net/?appName=AtlasCluster"
    client = MongoClient(uri, server_api=ServerApi("1"))
    # Send a ping to confirm a successful connection
    try:
        client.admin.command("ping")
        print("Pinged your deployment. You successfully connected to MongoDB!")
        if test_mode:
            db = client["TestFruitfulVine"]
        else:
            db = client["FruitfulVine"]
        return {
            "admin_collection": db["Admin"],
            "blog_categories_collection": db["BlogCategories"],
            "blog_posts_collection": db["BlogPosts"],
            "products_collection": db["Products"]
        }
    except Exception as e:
        print(e)
        return {}
