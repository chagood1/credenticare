# backend/api/auth.py

import json
from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import RedirectResponse
from gotrue.errors import AuthApiError
from backend.services.supabase_client import supabase
from backend.jinja_env import templates

router = APIRouter()


def _set_token_cookie(resp: RedirectResponse, token_data: dict) -> None:
    """
    Store both access_token and refresh_token together
    in the sb_token cookie as a JSON string.
    """
    resp.set_cookie(
        key="sb_token",
        value=json.dumps(token_data),
        httponly=True,
        max_age=7 * 24 * 3600,
        secure=False,  # flip to True in production over HTTPS
        samesite="lax",
    )


# ─── SIGNUP ─────────────────────────────────────────────────────

@router.get("/signup")
async def signup_get(request: Request):
    return templates.TemplateResponse(
        "signup.html",
        {"request": request, "error": None},
        status_code=200
    )


@router.post("/signup")
async def signup_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    try:
        supabase.auth.sign_up({"email": email, "password": password})
        return RedirectResponse(url="/login", status_code=303)

    except AuthApiError as e:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": str(e)},
            status_code=200
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Signup failed unexpectedly."
        )


# ─── LOGIN ──────────────────────────────────────────────────────

@router.get("/login")
async def login_get(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None},
        status_code=200
    )


@router.post("/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        session = res.session

        if not session or not session.access_token or not session.refresh_token:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Invalid credentials."},
                status_code=200
            )

        token_payload = {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token
        }
        resp = RedirectResponse(url="/dashboard", status_code=303)
        _set_token_cookie(resp, token_payload)
        return resp

    except AuthApiError as e:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": str(e)},
            status_code=200
        )
    except Exception:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "An unexpected error occurred."},
            status_code=200
        )


# ─── LOGOUT ─────────────────────────────────────────────────────

@router.get("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie("sb_token")
    return resp
