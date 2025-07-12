# backend/main.py


from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from .jinja_env       import templates
from .api.auth        import router as auth_router
from .api.dashboard   import router as dashboard_router
from .api.ce          import router as ce_router
from .api.settings    import router as settings_router
from .api.report      import router as report_router
from .api.courses     import router as courses_router

# Determine project base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# 1) Instantiate the FastAPI app
app = FastAPI(redirect_slashes=False)

# 2) Mount static assets
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)

# 3) Make `now()` available in all Jinja templates
templates.env.globals["now"] = datetime.utcnow

# 4) Wire up routers
app.include_router(auth_router)        # /signup, /login, /logout
app.include_router(dashboard_router)   # /dashboard
app.include_router(ce_router)          # /ce/...
app.include_router(settings_router)    # /settings
app.include_router(report_router)      # /report...
app.include_router(courses_router)     # /courses

# 5) Root endpoint
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

# 6) Health check
@app.get("/alive")
async def alive():
    return {"status": "👍 alive!"}


#   python -m uvicorn backend.main:app --reload
