from utils.couchbase_client import CouchbaseClient
import os
import uuid
from datetime import datetime

scope = os.getenv("COUCHBASE_SCOPE")
collection_name = "splits"

class SplitModel:
    def __init__(self):
        self.db = CouchbaseClient().get_collection(scope, collection_name)

    def create_split(self, bill_id: str, user_id: str, amount: float, auto_generated=True):
        split_id = str(uuid.uuid4())
        split = {
            "split_id": split_id,
            "bill_id": bill_id,
            "user_id": user_id,
            "amount": amount,
            "items": [],  # later AI assigns items
            "approval_status": "pending",
            "auto_generated": auto_generated,
            "approved_at": None,
            "created_at": datetime.utcnow().isoformat()
        }
        self.db.upsert(key=split_id, value=split)
        return split

    def get_splits_for_bill(self, bill_id: str):
        # naive query (better: N1QL later)
        return [row for row in self.db.get_all() if row["bill_id"] == bill_id]
