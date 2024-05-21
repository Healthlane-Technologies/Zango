from typing import List, Optional
from pydantic import BaseModel


class Permission(BaseModel):
    name: str
    type: str


class Statement(BaseModel):
    permissions: List[Permission]


class Policy(BaseModel):
    name: str
    description: Optional[str] = None
    statement: Statement


class Policies(BaseModel):
    policies: List[Policy]
