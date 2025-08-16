from utils.couchbase_client import CouchbaseClient
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
scope = os.getenv("COUCHBASE_SCOPE", "appdata")
collection_name = "sessions"

class SessionModel:
    def __init__(self):
        self.db = CouchbaseClient().get_collection(scope, collection_name)

    def create_session(self, session_data: dict):
        self.db.upsert(key=session_data.get("session_id"), value=session_data)
        return {"message": "Session created successfully"}

    def get_session(self, session_id: str) -> dict:
        return self.db.get(session_id).content_as[dict]

# Test
if __name__ == "__main__":
    m = SessionModel()
    test_session = {
        "session_id": "sess_001",
        "vendor_id": "vendor_001",
        "created_by": "user_001",
        "status": "active",
        "participants": ["user_001", "user_002", "user_003"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    print(m.create_session(test_session))
    print(m.get_session("sess_001"))
