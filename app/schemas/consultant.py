from datetime import datetime
from typing import Optional

from pydantic import AliasChoices, BaseModel, Field
from schemas.base import PyObjectID
from schemas.file import File
from schemas.review import ReviewMetrics


class ConsultantBase(BaseModel):
    profile_picture_id: str
    name: str
    role: str
    description: str
    resume_file_id: str
    expertise: str
    day_rate: float
    # Review: Dislike, Like, Love


class Consultant(ConsultantBase):
    id: PyObjectID = Field(validation_alias=AliasChoices("_id", "id"))
    review_metrics: ReviewMetrics = ReviewMetrics()
    date_created: datetime
    date_modified: datetime


class ConsultantOut(BaseModel):
    id: PyObjectID = Field(validation_alias=AliasChoices("_id", "id"))
    profile_picture: File
    name: str
    role: str
    description: str
    resume_file: File
    expertise: str
    day_rate: float
    review_metrics: ReviewMetrics = ReviewMetrics()
    date_created: datetime
    date_modified: datetime


class ConsultantUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    expertise: Optional[str] = None
    day_rate: Optional[float] = None
