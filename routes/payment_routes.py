from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import os
import uuid

from utils.couchbase_client import CouchbaseClient

router = APIRouter(prefix="/payments", tags=["Payments"])

scope = os.getenv("COUCHBASE_SCOPE", "appdata")
collection_name = "payments"
db = CouchbaseClient().get_collection(scope, collection_name)


# =====================
# Schemas
# =====================
class PaymentParticipant(BaseModel):
    user_id: str
    amount: float


class PaymentCreate(BaseModel):
    session_id: str
    vendor_id: str
    total_amount: float
    currency: str
    participants: list[PaymentParticipant]


# =====================
# Routes
# =====================

@router.post("/create")
def create_payment(req: PaymentCreate):
    payment_id = f"payment::{uuid.uuid4()}"

    new_payment = {
        "payment_id": payment_id,
        "session_id": req.session_id,
        "vendor_id": req.vendor_id,
        "total_amount": req.total_amount,
        "currency": req.currency,
        "participants": [p.dict() for p in req.participants],
        "payment_status": "pending",
        "processed_at": None,
        "created_at": datetime.utcnow().isoformat()
    }

    db.upsert(payment_id, new_payment)
    return {"message": "Payment created", "payment": new_payment}


@router.post("/{payment_id}/process")
def process_payment(payment_id: str):
    try:
        result = db.get(payment_id)
        payment = result.content_as[dict]

        # Simulate payment success
        payment["payment_status"] = "processed"
        payment["processed_at"] = datetime.utcnow().isoformat()

        db.upsert(payment_id, payment)
        return {"message": "Payment processed successfully", "payment": payment}

    except Exception:
        raise HTTPException(status_code=404, detail="Payment not found")


@router.get("/session/{session_id}")
def list_payments_for_session(session_id: str):
    from couchbase.options import QueryOptions
    query = f"SELECT p.* FROM `{db._bucket.name}`.`{scope}`.`{collection_name}` p WHERE p.session_id = $1"
    rows = db._scope.bucket.cluster.query(query, QueryOptions(positional_parameters=[session_id]))
    return [row for row in rows]
