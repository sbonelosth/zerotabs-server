# seed_data.py
from models import VendorModel, SessionModel, BillModel, SplitModel, PaymentModel

def seed_vendors():
    vendor_model = VendorModel()
    test_vendor = {
        "vendor_id": "vendor_001",
        "name": "Pizza Palace",
        "type": "Restaurant",
        "kyc_verified": True,
        "contact_info": {"phone": "1234567890", "email": "contact@pizzapalace.com"},
        "payment_account": {"bank": "Chase", "account_number": "12345678"},
        "created_at": "2025-08-16T12:00:00Z"
    }
    vendor_model.create_vendor(test_vendor)
    print("✅ Inserted vendor")

def seed_sessions():
    session_model = SessionModel()
    test_session = {
        "session_id": "session_001",
        "vendor_id": "vendor_001",
        "created_by": "alice",
        "status": "open",
        "created_at": "2025-08-16T12:05:00Z",
        "participants": ["alice", "bob", "charlie"]
    }
    session_model.create_session(test_session)
    print("✅ Inserted session")

def seed_bills():
    bill_model = BillModel()
    test_bill = {
        "bill_id": "bill_001",
        "session_id": "session_001",
        "vendor_id": "vendor_001",
        "total_amount": 45.50,
        "currency": "USD",
        "items": [
            {"name": "Pizza", "price": 20.00},
            {"name": "Pasta", "price": 15.50},
            {"name": "Drinks", "price": 10.00}
        ],
        "ai_validation": True,
        "created_at": "2025-08-16T12:10:00Z"
    }
    bill_model.create_bill(test_bill)
    print("✅ Inserted bill")

def seed_splits():
    split_model = SplitModel()
    test_split = {
        "split_id": "split_001",
        "bill_id": "bill_001",
        "user_id": "bob",
        "amount": 15.17,
        "items": ["Pizza"],
        "approval_status": "pending",
        "approved_at": None
    }
    split_model.create_split(test_split)
    print("✅ Inserted split")

def seed_payments():
    payment_model = PaymentModel()
    test_payment = {
        "payment_id": "payment_001",
        "session_id": "session_001",
        "vendor_id": "vendor_001",
        "total_amount": 45.50,
        "currency": "USD",
        "participants": ["alice", "bob", "charlie"],
        "payment_status": "processing",
        "processed_at": None
    }
    payment_model.create_payment(test_payment)
    print("✅ Inserted payment")

if __name__ == "__main__":
    print("🌱 Seeding mock data into Couchbase...")
    seed_vendors()
    seed_sessions()
    seed_bills()
    seed_splits()
    seed_payments()
    print("🎉 Done seeding!")
