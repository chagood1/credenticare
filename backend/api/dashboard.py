# backend/api/dashboard.py

import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends, HTTPException
from backend.jinja_env import templates
from backend.deps import get_current_user_id
from backend.services.supabase_client import supabase

router = APIRouter()

@router.get("/dashboard")
async def dashboard(request: Request, user_id: str = Depends(get_current_user_id)):
    # 1. Fetch global CE requirement (allow zero rows)
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
    renewal_days = req["renewal_interval_days"]

    # 2. Fetch and sum user CE records
    recs_resp = (
        supabase
        .table("ce_records")
        .select("hours_earned,date_completed")
        .eq("user_id", user_id)
        .execute()
    )
    if recs_resp is None:
        raise HTTPException(status_code=500, detail="Invalid Supabase response")
    if hasattr(recs_resp, "error") and recs_resp.error:
        raise HTTPException(status_code=500, detail=recs_resp.error.message)

    records = recs_resp.data or []
    hours_completed = sum(r["hours_earned"] for r in records)
    hours_remaining = max(0, required_hours - hours_completed)

    # 3. Compute next renewal date
    latest = max(
        (datetime.fromisoformat(r["date_completed"]) for r in records),
        default=datetime.utcnow()
    )
    next_renewal = (latest + timedelta(days=renewal_days)).date()

    # 4. Fetch full record list for display
    full_resp = (
        supabase
        .table("ce_records")
        .select("*")
        .eq("user_id", user_id)
        # .order("date_completed", {"ascending": False})
        .execute()
    )
    if full_resp is None:
        raise HTTPException(status_code=500, detail="Invalid Supabase response")
    if hasattr(full_resp, "error") and full_resp.error:
        raise HTTPException(status_code=500, detail=full_resp.error.message)

    full_records = full_resp.data or []

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "status": {
                "required_hours": required_hours,
                "hours_completed": hours_completed,
                "hours_remaining": hours_remaining,
                "next_renewal": str(next_renewal),
            },
            "records": full_records,
        }
    )
