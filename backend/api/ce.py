# backend/api/ce.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from datetime import date
from typing import List
from backend.services.supabase_client import supabase

router = APIRouter(prefix="/ce", tags=["ce"])

class CERecordIn(BaseModel):
    course_id: str = Field(..., description="UUID of the course")
    date_completed: date = Field(..., description="Date when CE was completed")
    hours_earned: int = Field(..., gt=0, description="Number of hours earned")
    notes: str = Field(None, description="Optional notes")

class CERecordOut(CERecordIn):
    id: str
    user_id: str

@router.get("/records", response_model=List[CERecordOut])
async def list_records():
    # Fetch only this user’s CE records
    user_id = supabase.auth.api.get_user().id
    res = supabase.table("ce_records").select("*").eq("user_id", user_id).execute()
    return res.data

@router.post("/records", response_model=CERecordOut)
async def create_record(rec: CERecordIn):
    user_id = supabase.auth.api.get_user().id
    payload = rec.dict()
    payload["user_id"] = user_id
    res = supabase.table("ce_records").insert(payload).single().execute()
    return res.data

@router.get("/status")
async def ce_status():
    # ⚠️ placeholder: replace with your actual logic
    return {"status": "stub"}
