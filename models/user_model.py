from utils.couchbase_client import CouchbaseClient
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
scope = os.getenv("COUCHBASE_SCOPE", "appdata")
collection_name = "users"

class UserModel:
    def __init__(self):
        self.db = CouchbaseClient().get_collection(scope, collection_name)

    def create_user(self, user_data: dict):
        self.db.upsert(key=user_data.get("user_id"), value=user_data)
        return {"message": "User created successfully"}

    def get_user(self, user_id: str) -> dict:
        return self.db.get(user_id).content_as[dict]

# Test
if __name__ == "__main__":
    m = UserModel()
    test_user = {
        "user_id": "user_001",
        "full_name": "Alice Moyo",
        "email": "alice@example.com",
        "phone": "0123456789",
        "kyc_verified": False,
        "payment_method": {"type": "visa", "last4": "8675"},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    print(m.create_user(test_user))
    print(m.get_user("user_001"))
