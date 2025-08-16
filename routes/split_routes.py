from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from utils.couchbase_client import CouchbaseClient
from services.ai_service import AISplitService
from datetime import datetime, UTC

router = APIRouter(prefix="/splits", tags=["Splits"])

scope = os.getenv("COUCHBASE_SCOPE", "appdata")
collection_name = "splits"
db = CouchbaseClient().get_collection(scope, collection_name)

split_service = AISplitService()

# =====================
# Schemas
# =====================
class ManualSplit(BaseModel):
    user_id: str
    amount: float
    items: list[dict] = []


class ApproveSplit(BaseModel):
    user_id: str  # who is approving


# =====================
# Routes
# =====================

@router.get("/bill/{bill_id}")
def get_splits_for_bill(bill_id: str):
    """
    Get all splits for a given bill.
    """
    from couchbase.options import QueryOptions
    query = f"SELECT s.* FROM `{db._bucket.name}`.`{scope}`.`{collection_name}` s WHERE s.bill_id = $1"
    rows = db._scope.bucket.cluster.query(query, QueryOptions(positional_parameters=[bill_id]))
    return [row for row in rows]


@router.post("/manual/{bill_id}")
def create_manual_splits(bill_id: str, splits: list[ManualSplit]):
    """
    Create manual splits for a bill.
    """
    saved_splits = split_service.manual_create(bill_id, [s.dict() for s in splits])
    return {
        "bill_id": bill_id,
        "splits": saved_splits,
        "message": "Manual splits created"
    }


@router.post("/{split_id}/approve")
def approve_split(split_id: str, data: ApproveSplit):
    """
    Approve a split for a user.
    """
    try:
        split_doc = db.get(split_id).content_as[dict]

        if split_doc["user_id"] != data.user_id:
            raise HTTPException(status_code=403, detail="User does not own this split")

        split_doc["approval_status"] = "approved"
        split_doc["approved_at"] = datetime.now(UTC).isoformat()

        db.upsert(split_id, split_doc)
        return {
            "split": split_doc,
            "message": "Split approved successfully"
        }

    except Exception:
        raise HTTPException(status_code=404, detail="Split not found")
