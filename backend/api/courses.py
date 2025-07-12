# backend/api/courses.py

from fastapi import APIRouter, Depends, Request
from ..services.supabase_client import supabase
from ..deps import get_current_user, User
from ..jinja_env import templates

router = APIRouter(prefix="/courses", tags=["courses"])

@router.get("")
async def list_courses(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    # fetch all courses (or filter by state, etc.)
    resp = await supabase.from_("courses").select("*").execute()
    courses = resp.data or []

    return templates.TemplateResponse(
        "courses.html",
        {"request": request, "courses": courses}
    )
