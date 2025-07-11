# backend/api/ce.py

import json
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from datetime import date, datetime, timedelta
from typing import List
from pathlib import Path

from backend.services.supabase_client import supabase
from backend.deps import get_current_user_id
from backend.jinja_env import templates

router = APIRouter(prefix="/ce", tags=["ce"])


# Pydantic models
class CERecordIn(BaseModel):
    course_id: str = Field(..., description="UUID of the course")
    date_completed: date = Field(..., description="Date when CE was completed")
    hours_earned: int = Field(..., gt=0, description="Number of hours earned")
    notes: str = Field(None, description="Optional notes")


class CERecordOut(CERecordIn):
    id: str
    user_id: str


# List user-specific CE records
@router.get("/records", response_model=List[CERecordOut])
async def list_records(user_id: str = Depends(get_current_user_id)):
    res = (
        supabase
        .table("ce_records")
        .select("*")
        .eq("user_id", user_id)
        # .order("date_completed", {"ascending": False})
        .execute()
    )
    if hasattr(res, "error") and res.error:
        raise HTTPException(status_code=500, detail=res.error.message)
    return res.data


# Create a new CE record
@router.post("/records", response_model=CERecordOut)
async def create_record(rec: CERecordIn, user_id: str = Depends(get_current_user_id)):
    payload = rec.dict()
    payload["user_id"] = user_id
    res = (
        supabase
        .table("ce_records")
        .insert(payload)
        .single()
        .execute()
    )
    if res.error:
        raise HTTPException(status_code=500, detail=res.error.message)
    return res.data


# Compute CE status for the user
@router.get("/status")
async def ce_status(user_id: str = Depends(get_current_user_id)):
    # Fetch global CE requirement (allowing zero rows)
    req_resp = (
        supabase
        .table("ce_requirements")
        .select("*")
        .maybe_single()
        .execute()
    )
    if req_resp is None:
        raise HTTPException(status_code=500, detail="Invalid Supabase response")
    if hasattr(req_resp, "error") and req_resp.error:
        raise HTTPException(status_code=500, detail=req_resp.error.message)
    if req_resp.data is None:
        raise HTTPException(status_code=404, detail="No CE requirement configured")

    req = req_resp.data
    required_hours = req["required_hours"]
    renewal_interval_days = req["renewal_interval_days"]

    # Sum this user’s CE records
    recs_resp = (
        supabase
        .table("ce_records")
        .select("hours_earned,date_completed")
        .eq("user_id", user_id)
        .execute()
    )
    if hasattr(recs_resp, "error") and recs_resp.error:
        raise HTTPException(status_code=500, detail=recs_resp.error.message)

    records = recs_resp.data or []
    hours_completed = sum(r["hours_earned"] for r in records)

    # Compute next renewal date
    latest = max(
        (datetime.fromisoformat(r["date_completed"]) for r in records),
        default=datetime.utcnow()
    )
    next_renewal = (latest + timedelta(days=renewal_interval_days)).date()

    return {
        "required_hours": required_hours,
        "hours_completed": hours_completed,
        "hours_remaining": max(0, required_hours - hours_completed),
        "next_renewal_date": str(next_renewal),
    }


# Render upload form
@router.get("/records/upload")
async def upload_ce_form(request: Request, user_id: str = Depends(get_current_user_id)):
    # NOTE: changed 'name' → 'course_title'
    courses_resp = supabase.table("courses").select("*").execute()
    courses = courses_resp.data or []
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "courses": courses,
        "error": None
    })


# Process upload submission
@router.post("/records/upload")
async def upload_ce_submit(
    request: Request,
    course_id: str = Form(...),
    date_completed: date = Form(...),
    hours_earned: int = Form(...),
    notes: str = Form(""),
    user_id: str = Depends(get_current_user_id)
):
    payload = {
        "course_id": course_id,
        "date_completed": date_completed,
        "hours_earned": hours_earned,
        "notes": notes,
        "user_id": user_id
    }
    res = supabase.table("ce_records").insert(payload).execute()
    if res.error:
        # NOTE: also updated here
        courses = supabase.table("courses").select("id,course_title").execute().data or []
        return templates.TemplateResponse("upload.html", {
            "request": request,
            "courses": courses,
            "error": res.error.message
        }, status_code=400)

    return RedirectResponse(url="/dashboard", status_code=303)
