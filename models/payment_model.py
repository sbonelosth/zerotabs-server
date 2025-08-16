from utils.couchbase_client import CouchbaseClient
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
scope = os.getenv("COUCHBASE_SCOPE", "appdata")
collection_name = "payments"

class PaymentModel:
    def __init__(self):
        self.db = CouchbaseClient().get_collection(scope, collection_name)

    def create_payment(self, payment_data: dict):
        self.db.upsert(key=payment_data.get("payment_id"), value=payment_data)
        return {"message": "Payment created successfully"}

    def get_payment(self, payment_id: str) -> dict:
        return self.db.get(payment_id).content_as[dict]

# Test
if __name__ == "__main__":
    m = PaymentModel()
    test_payment = {
        "payment_id": "pay_001",
        "session_id": "sess_001",
        "vendor_id": "vendor_001",
        "total_amount": 120.50,
        "currency": "USD",
        "participants": [
            {"user_id": "user_001", "amount": 40.17},
            {"user_id": "user_002", "amount": 40.17},
            {"user_id": "user_003", "amount": 40.16}
        ],
        "payment_status": "processing",
        "processed_at": datetime.now(timezone.utc).isoformat()
    }
    print(m.create_payment(test_payment))
    print(m.get_payment("pay_001"))
