from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import AliasChoices, BaseModel, Field
from schemas.base import PyObjectID


class Reaction(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    LOVE = "love"


class TargetType(str, Enum):
    AGENT = "agent"
    CONSULTANT = "consultant"


class ReviewIn(BaseModel):
    reaction: Reaction
    description: Optional[str] = None


class ReviewBase(BaseModel):
    reaction: Reaction
    # user_id: str
    target_id: str
    target_type: TargetType
    description: Optional[str] = None


class Review(ReviewBase):
    id: PyObjectID = Field(validation_alias=AliasChoices("_id", "id"))
    date_created: datetime
    date_modified: datetime


class ReviewMetrics(BaseModel):
    like: int = 0
    dislike: int = 0
    love: int = 0
