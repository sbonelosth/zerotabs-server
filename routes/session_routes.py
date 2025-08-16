from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import os
import uuid

from utils.couchbase_client import CouchbaseClient

router = APIRouter(prefix="/sessions", tags=["Bill Sessions"])

scope = os.getenv("COUCHBASE_SCOPE", "appdata")
collection_name = "bill_sessions"
db = CouchbaseClient().get_collection(scope, collection_name)


# =====================
# Schemas
# =====================
class SessionCreate(BaseModel):
    vendor_id: str
    session_name: str
    created_by: str  # user_id of session creator


class JoinSession(BaseModel):
    session_id: str
    user_id: str


# =====================
# Routes
# =====================

@router.post("/create")
def create_session(req: SessionCreate):
    session_id = f"session::{uuid.uuid4()}"
    new_session = {
        "session_id": session_id,
        "session_name": req.session_name,
        "vendor_id": req.vendor_id,
        "created_by": req.created_by,
        "status": "open",
        "participants": [req.created_by],
        "created_at": datetime.utcnow().isoformat()
    }

    db.upsert(session_id, new_session)
    return {"message": "Session created", "session": new_session}


@router.post("/join")
def join_session(req: JoinSession):
    try:
        result = db.get(req.session_id)
        session = result.content_as[dict]
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["status"] != "open":
        raise HTTPException(status_code=400, detail="Session is closed")

    if req.user_id not in session["participants"]:
        session["participants"].append(req.user_id)
        db.upsert(req.session_id, session)

    return {"message": "Joined session", "session": session}


@router.get("/{session_id}")
def get_session(session_id: str):
    try:
        result = db.get(session_id)
        return result.content_as[dict]
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/")
def list_sessions():
    # NOTE: N1QL query since sessions are multiple docs
    from couchbase.options import QueryOptions
    query = f"SELECT s.* FROM `{db._bucket.name}`.`{scope}`.`{collection_name}` s"
    rows = db._scope.bucket.cluster.query(query, QueryOptions())
    return [row for row in rows]
