from typing import List
from pydantic import BaseModel


class Child(BaseModel):
    url: str
    name: str
    icon: str | None = None


class MenuItem(BaseModel):
    url: str = ""
    icon: str | None = None
    name: str
    children: List[Child] | None = None


class Color(BaseModel):
    accent: str = "#DDE2E5"
    header: str = "#FFFFFF"
    primary: str = "#DDE2E5"
    sidebar: str = "#E1D6AE"
    secondary: str = "#E1D6AE"
    background: str = "#FFFFFF"
    typography: str = "#212429"
    headerBorder: str = "#DDE2E5"


class ConfigItem(BaseModel):
    color: Color = Color()


class Frame(BaseModel):
    menu: List[MenuItem]
    config: ConfigItem = ConfigItem()
    login_url: str | None = None
    display_edit_profile: bool = True
    allow_change_password: bool = True
    display_change_password: bool = True
