from typing import List
from pydantic import BaseModel


class GenericLoginConfig(BaseModel):
    card_color: str
    card_title: str
    header_text: str
    corner_radius: int
    logo_placement: str
    paragraph_text: str
    card_text_color: str
    background_color: str
    paragraph_text_color: str


class LoginConfig(BaseModel):
    landing_url: str
