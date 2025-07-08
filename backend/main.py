from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# import routers
from backend.api.auth import router as auth_router
from backend.api.dashboard import router as dashboard_router

from backend.ce import router as ce_router
app.include_router(ce_router)


BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI()


app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# wire routers
app.include_router(auth_router)       # /signup, /login
app.include_router(dashboard_router)  # /dashboard

# public root
@app.get("/", response_class=templates.TemplateResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {"request": request}
    )



@app.get("/alive")
async def alive():
    return {"status": "👍 alive!"}
