# backend/api/dashboard.py

from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    # if you need to pull user info from the cookie, do it here
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request},
        status_code=200
    )
