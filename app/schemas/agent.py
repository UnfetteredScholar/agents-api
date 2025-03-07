from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import AliasChoices, BaseModel, Field
from schemas.base import PyObjectID
from schemas.component import Component
from schemas.document import Document
from schemas.review import ReviewMetrics


class Platform(str, Enum):
    PA_WEB = "Power Automate Web"
    PA_DESK = "Power Automate Desktop"
    UIPATH = "UiPath"
    PYTHON = "Python"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class Agent(BaseModel):
    id: PyObjectID = Field(validation_alias=AliasChoices("_id", "id"))
    title: str
    category: str
    tagline: str
    thumbnail_image: str
    rating: ReviewMetrics
    provider: str
    description: str
    key_features: List[str]
    integrations: List[str]
    pricing_model: str
    demo_available: bool
    related_ai_solutions: List[str]
    platform_type: Platform
    platform_file: str

    dependencies: List[str]
    # supporting_documents: List[str] = []

    date_created: datetime
    date_modified: datetime


class AgentOut(BaseModel):
    id: PyObjectID = Field(validation_alias=AliasChoices("_id", "id"))
    title: str
    category: str
    tagline: str
    thumbnail_image: str
    rating: ReviewMetrics
    provider: str
    description: str
    key_features: List[str]
    integrations: List[str]
    pricing_model: str
    demo_available: bool
    related_ai_solutions: List[str]
    platform_type: Platform
    platform_file: str

    dependencies: List[Component]
    supporting_documents: List[Document]

    date_created: datetime
    date_modified: datetime


class AgentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    tagline: Optional[str] = None
    provider: Optional[str] = None
    description: Optional[str] = None
    key_features: Optional[List[str]] = None
    integrations: Optional[List[str]] = None
    pricing_model: Optional[str] = None
    demo_available: Optional[bool] = None
    related_ai_solutions: Optional[List[str]] = None
    platform_type: Optional[Platform] = None

    dependencies: Optional[List[str]] = None
