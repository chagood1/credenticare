# backend/api/settings.py

from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import RedirectResponse
from ..services.supabase_client import supabase
from ..deps import get_current_user, User
from ..jinja_env import templates
import json

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("")
async def view_settings(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    # Fetch list of US states for dropdown
    states_res = await supabase.table("states").select("code,name").execute()
    states = states_res.data or []
    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "user": current_user, "states": states}
    )

@router.post("")
async def update_settings(
    request: Request,
    state: str = Form(...),
    password: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    # Update user profile in Supabase
    update_data = {"state": state}
    try:
        # Update password if provided
        if password:
            session = request.cookies.get("sb_token")
            if not session:
                raise HTTPException(401, "Not authenticated")
            token_data = json.loads(session)
            supabase.auth.set_session(
                token_data["access_token"],
                token_data["refresh_token"]
            )
            await supabase.auth.api.update_user(
                token_data["access_token"],
                {"password": password}
            )

        # Update user state flag
        await supabase.table("users").update(update_data).eq("id", current_user.id).execute()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {e}")

    return RedirectResponse(url="/settings", status_code=303)
