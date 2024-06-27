from typing import List, Dict
from pydantic import BaseModel, Field


class FieldBase(BaseModel):
    name: str
    type: str
    constraints: Dict[str, int | str | bool | List[str]] = Field(default_factory=dict)
