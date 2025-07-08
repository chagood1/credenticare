from pathlib import Path
from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from gotrue.errors import AuthApiError
from backend.services.supabase_client import supabase

# point at project-root templates folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


def _set_token_cookie(resp: RedirectResponse, token: str) -> None:
    resp.set_cookie(
        key="sb_token",
        value=token,
        httponly=True,
        max_age=7 * 24 * 3600,
        secure=False,  # flip to True in production over HTTPS
        samesite="lax",
    )


# ─── SIGNUP ─────────────────────────────────────────────────────

@router.get("/signup")
async def signup_get(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request, "error": None}, status_code=200)


@router.post("/signup")
async def signup_post(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        # 1. Create the user
        supabase.auth.sign_up({"email": email, "password": password})
        # 2. Redirect new users to the login page
        return RedirectResponse(url="/login", status_code=303)

    except AuthApiError as e:
        # Show any Supabase error (e.g. email already in use)
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": str(e)},
            status_code=200
        )
    except Exception:
        # Unexpected failure
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Signup failed unexpectedly.")


# ─── LOGIN ──────────────────────────────────────────────────────

@router.get("/login")
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None}, status_code=200)


@router.post("/login")
async def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        session = res.session

        if not session or not session.access_token:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Invalid credentials."},
                status_code=200
            )

        # on success, set cookie and redirect
        resp = RedirectResponse(url="/dashboard", status_code=303)
        _set_token_cookie(resp, session.access_token)
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
