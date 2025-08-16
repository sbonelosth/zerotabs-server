from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

from utils.couchbase_client import CouchbaseClient
from services.bill_service import BillService
from services.ai_service import AISplitService  # AI & manual split logic

router = APIRouter(prefix="/bills", tags=["Bills"])

scope = os.getenv("COUCHBASE_SCOPE", "appdata")
collection_name = "bills"
db = CouchbaseClient().get_collection(scope, collection_name)

# =====================
# Schemas
# =====================
class BillItem(BaseModel):
    name: str
    price: float
    quantity: int = 1

class BillCreate(BaseModel):
    session_id: str
    vendor_id: str
    total_amount: float
    currency: str
    items: list[BillItem]
    manual_split: bool = False

# =====================
# Routes
# =====================
bill_service = BillService()
split_service = AISplitService()

@router.post("/create")
def create_bill(bill_data: BillCreate):
    """
    Create a bill and auto-generate splits unless manual_split is True.
    """
    bill = bill_service.create_bill(bill_data.dict())

    if not bill_data.manual_split:
        # Default → AI auto-generate splits
        splits = split_service.auto_generate(
            bill_id=bill["bill_id"], 
            total_amount=bill["total_amount"],
            session_id=bill["session_id"]   # ✅ added
        )

        return {
            "bill": bill,
            "splits": splits,
            "message": "Bill created with AI-generated splits"
        }

    return {
        "bill": bill,
        "message": "Bill created, waiting for manual splits"
    }

@router.get("/{bill_id}")
def get_bill(bill_id: str):
    try:
        result = db.get(bill_id)
        return result.content_as[dict]
    except Exception:
        raise HTTPException(status_code=404, detail="Bill not found")

@router.get("/session/{session_id}")
def list_bills_for_session(session_id: str):
    from couchbase.options import QueryOptions
    query = f"""
        SELECT b.* 
        FROM `{db._bucket.name}`.`{scope}`.`{collection_name}` b 
        WHERE b.session_id = $1
    """
    rows = db._scope.bucket.cluster.query(query, QueryOptions(positional_parameters=[session_id]))
    return [row for row in rows]
