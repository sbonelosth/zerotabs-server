from utils.couchbase_client import CouchbaseClient
import os
from datetime import datetime
import uuid

scope = os.getenv("COUCHBASE_SCOPE")
collection_name = "bills"

class BillModel:
    def __init__(self):
        self.db = CouchbaseClient().get_collection(scope, collection_name)

    def create_bill(self, bill_data: dict):
        bill_id = str(uuid.uuid4())
        bill = {
            "bill_id": bill_id,
            "session_id": bill_data.get("session_id"),
            "vendor_id": bill_data.get("vendor_id"),
            "total_amount": bill_data.get("total_amount"),
            "currency": bill_data.get("currency", "USD"),
            "items": bill_data.get("items", []),
            "ai_validation": False,
            "created_at": datetime.utcnow().isoformat()
        }
        self.db.upsert(key=bill_id, value=bill)
        return bill

    def get_bill(self, bill_id: str):
        return self.db.get(bill_id).content_as[dict]
