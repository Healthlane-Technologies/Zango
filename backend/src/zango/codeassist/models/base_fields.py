from typing import List, Dict
from pydantic import BaseModel


class FieldBase(BaseModel):
    name: str
    type: str
    constraints: Dict[str, int | str | bool | List[str]]
