from pydantic import BaseModel

class User(BaseModel):
    id: str
    email: str
    state: str
    is_pro: bool = False
