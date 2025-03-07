from datetime import datetime
from typing import List, Optional

from pydantic import AliasChoices, BaseModel, Field
from schemas.base import PyObjectID
from schemas.document import Document
from schemas.review import ReviewMetrics


class Consultant(BaseModel):
    id: PyObjectID = Field(validation_alias=AliasChoices("_id", "id"))
    title: str
    category: str
    tagline: str
    thumbnail_image: str  # File
    provider: str
    description: str
    services_offered: List[str]
    industries_served: List[str]
    day_rate: float
    related_services: List[str]
    resume_upload: str  # File
    rating: ReviewMetrics
    date_created: datetime
    date_modified: datetime


class ConsultantOut(BaseModel):
    id: PyObjectID = Field(validation_alias=AliasChoices("_id", "id"))
    title: str
    category: str
    tagline: str
    thumbnail_image: str  # File
    provider: str
    description: str
    services_offered: List[str]
    industries_served: List[str]
    day_rate: float
    related_services: List[str]
    resume_upload: str  # File
    rating: ReviewMetrics
    supporting_documents: List[Document]

    date_created: datetime
    date_modified: datetime


class ConsultantUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    tagline: Optional[str] = None
    provider: Optional[str] = None
    description: Optional[str] = None
    services_offered: Optional[List[str]] = None
    industries_served: Optional[List[str]] = None
    day_rate: Optional[float] = None
    related_services: Optional[List[str]] = None
