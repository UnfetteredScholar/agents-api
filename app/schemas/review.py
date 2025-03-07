from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import AliasChoices, BaseModel, Field, computed_field
from schemas.base import PyObjectID


class TargetType(str, Enum):
    AGENT = "agent"
    CONSULTANT = "consultant"


class ReviewIn(BaseModel):
    stars: int = Field(ge=0, le=5)
    description: Optional[str] = None


class ReviewBase(BaseModel):
    stars: int = Field(ge=0, le=5)
    target_id: str
    target_type: TargetType
    description: Optional[str] = None


class Review(ReviewBase):
    id: PyObjectID = Field(validation_alias=AliasChoices("_id", "id"))
    date_created: datetime
    date_modified: datetime


class ReviewMetrics(BaseModel):
    total_stars: int
    review_count: int

    @computed_field
    @property
    def stars(self) -> float:
        if self.review_count > 0:
            return float(self.total_stars) / float(self.review_count)
        else:
            return 0
