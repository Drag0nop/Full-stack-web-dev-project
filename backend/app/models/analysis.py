from pydantic import BaseModel
from datetime import datetime


class Analysis(BaseModel):
    user_email: str
    code: str
    result: dict
    created_at: datetime = datetime.utcnow()