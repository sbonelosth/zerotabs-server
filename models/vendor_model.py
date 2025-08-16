from utils.couchbase_client import CouchbaseClient
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
scope = os.getenv("COUCHBASE_SCOPE", "appdata")
collection_name = "vendors"

class VendorModel:
    def __init__(self):
        self.db = CouchbaseClient().get_collection(scope, collection_name)

    def create_vendor(self, vendor_data: dict):
        self.db.upsert(key=vendor_data.get("vendor_id"), value=vendor_data)
        return {"message": "Vendor created successfully"}

    def get_vendor(self, vendor_id: str) -> dict:
        return self.db.get(vendor_id).content_as[dict]

# Test
if __name__ == "__main__":
    m = VendorModel()
    test_vendor = {
        "vendor_id": "vendor_001",
        "name": "Pasta Palace",
        "type": "restaurant",
        "kyc_verified": True,
        "contact_info": {"email": "pasta@example.com", "phone": "0112345678"},
        "payment_account": {"scheme": "bet-pay", "merchant_ref": "mp_12345"},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    print(m.create_vendor(test_vendor))
    print(m.get_vendor("vendor_001"))
