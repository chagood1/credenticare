# backend/deps.py

import json
from fastapi import HTTPException, Request, Depends, status
from pydantic import BaseModel
from backend.services.supabase_client import supabase

class User(BaseModel):
    id: str
    email: str
    state: str
    is_pro: bool = False

async def get_current_user_id(request: Request) -> User:
    sb_token = request.cookies.get("sb_token")
    if not sb_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if sb_token.startswith('"') and sb_token.endswith('"'):
        sb_token = sb_token[1:-1]
    try:
        session = json.loads(sb_token)
        access_token = session["access_token"]
        refresh_token = session["refresh_token"]
    except (ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth cookie")
    supabase.auth.set_session(access_token, refresh_token)
    user_resp = supabase.auth.get_user()
    auth_user = getattr(user_resp, "user", None)
    if not auth_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    return auth_user

async def get_current_user(auth_user=Depends(get_current_user_id)) -> User:
    # extract fields from GoTrue user
    user_id = auth_user.id
    email = auth_user.email
    state = auth_user.user_metadata.get("state", "") if hasattr(auth_user, 'user_metadata') else ""
    # Fetch pro flag from Postgres
    res = await supabase.table("users") \
        .select("is_pro") \
        .eq("id", user_id) \
        .single() \
        .execute()
    is_pro = res.data.get("is_pro", False) if res.data else False
    return User(id=user_id, email=email, state=state, is_pro=is_pro)



    #           python -m uvicorn backend.main:app --reload
