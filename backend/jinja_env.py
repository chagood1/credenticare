from pathlib import Path
from fastapi.templating import Jinja2Templates
from datetime import datetime

# point at project root’s templates folder
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# make now() available in all templates
templates.env.globals["now"] = datetime.utcnow
