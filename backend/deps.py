# backend/deps.py

import json
from fastapi import HTTPException, Request
from backend.services.supabase_client import supabase

async def get_current_user_id(request: Request) -> str:
    # 1. Grab the cookie
    sb_token = request.cookies.get("sb_token")
    if not sb_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # 2. Parse out tokens
    try:
        data = json.loads(sb_token)
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
    except (ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid auth cookie")

    # 3. Set session
    supabase.auth.set_session(access_token, refresh_token)

    # 4. Fetch user
    user_resp = supabase.auth.get_user()
    user = getattr(user_resp, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return user.id
