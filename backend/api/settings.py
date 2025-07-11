# backend/api/settings.py

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from backend.services.supabase_client import supabase
from backend.deps import get_current_user_id
from backend.jinja_env import templates

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("", response_class=templates.TemplateResponse)
async def view_settings(request: Request, user=Depends(get_current_user_id)):
    res = await supabase.table("states").select("code,name").execute()
    states = res.data or []
    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "user": user, "states": states}
    )

@router.post("", response_class=RedirectResponse)
async def update_settings(
    request: Request,
    password: str = Form(None),
    state: str = Form(...),
    user=Depends(get_current_user_id)
):
    update_data = {"state": state}
    # Update password if provided
    if password:
        await supabase.auth.api.update_user(
            user.session.access_token,
            {"password": password}
        )
    # Update user profile
    await supabase.table("users").update(update_data).eq("id", user.id).execute()
    return RedirectResponse(url="/settings", status_code=303)
