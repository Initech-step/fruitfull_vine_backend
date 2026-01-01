from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv() 

# Access the environment variables
test_mode = os.getenv("TEST", True)
username = os.getenv("ATLAS_USERNAME")
pword = os.getenv("PWORD")
offline = os.getenv("OFFLINE_MODE", False)

def connect_to_db() -> Dict[str, Any]:
    uri = f"mongodb+srv://{username}:{pword}@atlascluster.doihstd.mongodb.net/?appName=AtlasCluster"
    client = MongoClient(uri, server_api=ServerApi("1"))
    # Send a ping to confirm a successful connection
    try:
        client.admin.command("ping")
        if test_mode:
            db = client["TestFruitfulVine"]
        else:
            db = client["FruitfulVine"]
        print("Connected to MongoDB successfully.")
        return {
            "admin_collection": db["Admin"],
            "categories_collection": db["Categories"],
            "blog_posts_collection": db["BlogPosts"],
            "products_collection": db["Products"],
            "contact_collection": db["Contacts"]
        }
    except Exception as e:
        print(e)
        print("\n Switched to OFFLINE_MODE due to database connection failure. \n")
        return {}
