import uuid
from datetime import datetime, UTC
import os
from utils.couchbase_client import CouchbaseClient

scope = os.getenv("COUCHBASE_SCOPE", "appdata")

class AISplitService:
    def __init__(self):
        self.split_db = CouchbaseClient().get_collection(scope, "splits")
        self.session_db = CouchbaseClient().get_collection(scope, "bill_sessions")

    def auto_generate(self, bill_id: str, total_amount: float, session_id: str = None):
        """
        Auto-generate splits using participants from the bill_session.
        If no session_id is passed, we try to resolve it from Couchbase later.
        """
        participants = []

        # If session_id is provided, pull participants
        if session_id:
            try:
                session = self.session_db.get(session_id).content_as[dict]
                participants = session.get("participants", [])
            except Exception:
                pass  # fallback to empty

        # Fallback: if no participants found, assign dummy
        if not participants:
            participants = ["alice", "bob", "charlie"]

        # Even split
        share = round(total_amount / len(participants), 2)

        splits = []
        for user_id in participants:
            split = {
                "split_id": str(uuid.uuid4()),
                "bill_id": bill_id,
                "user_id": user_id,
                "amount": share,
                "items": [],  # AI could later map items
                "approval_status": "pending",
                "created_at": datetime.now(UTC).isoformat()
            }
            self.split_db.upsert(split["split_id"], split)
            splits.append(split)

        return splits

    def manual_create(self, bill_id: str, splits_data: list[dict]):
        """
        Store manually created splits.
        """
        saved_splits = []
        for split in splits_data:
            split_doc = {
                "split_id": str(uuid.uuid4()),
                "bill_id": bill_id,
                "user_id": split["user_id"],
                "amount": split["amount"],
                "items": split.get("items", []),
                "approval_status": "pending",
                "created_at": datetime.now(UTC).isoformat()
            }
            self.split_db.upsert(split_doc["split_id"], split_doc)
            saved_splits.append(split_doc)

        return saved_splits
