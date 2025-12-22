from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from typing import Dict, Any


def connect_to_db() -> Dict[str, Any]:
    username = "Project-AI"
    pword = "m5vr23zThUdemscI"
    uri = f"mongodb+srv://{username}:{pword}@atlascluster.doihstd.mongodb.net/?appName=AtlasCluster"
    client = MongoClient(uri, server_api=ServerApi("1"))
    # Send a ping to confirm a successful connection
    try:
        client.admin.command("ping")
        print("Pinged your deployment. You successfully connected to MongoDB!")
        db = client["FruitfulVine"]
        return {
            "admin_collection": db["Admin"],
        }
    except Exception as e:
        print(e)
        return {}
