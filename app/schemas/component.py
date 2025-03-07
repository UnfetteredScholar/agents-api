from datetime import datetime
from typing import Optional

from pydantic import AliasChoices, BaseModel, Field
from schemas.base import PyObjectID


class ComponentBase(BaseModel):
    name: str
    description: str
    price: float


class Component(ComponentBase):
    id: PyObjectID = Field(validation_alias=AliasChoices("_id", "id"))
    # user_id: str
    dependency_file: str  # File
    logo: str  # File
    date_created: datetime
    date_modified: datetime


class ComponentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None


# class ComponentOut(ComponentBase):
#     id: PyObjectID = Field(validation_alias=AliasChoices("_id", "id"))
#     dependency_file: File
#     logo: File
#     date_created: datetime
#     date_modified: datetime
