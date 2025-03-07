from datetime import datetime
from typing import Optional

from pydantic import AliasChoices, BaseModel, Field
from schemas.base import PyObjectID


class DocumentBase(BaseModel):
    name: str
    description: str


class Document(DocumentBase):
    id: PyObjectID = Field(validation_alias=AliasChoices("_id", "id"))
    owner_id: str
    # user_id: str
    document_file: str  # File
    date_created: datetime
    date_modified: datetime


class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# class DocumentOut(DocumentBase):
#     id: PyObjectID = Field(validation_alias=AliasChoices("_id", "id"))
#     dependency_file: File
#     logo: File
#     date_created: datetime
#     date_modified: datetime
