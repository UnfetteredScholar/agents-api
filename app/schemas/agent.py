from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import AliasChoices, BaseModel, Field
from schemas.base import PyObjectID
from schemas.file import File

AgentstrKey = Literal[
    "metadata",
    "logo",
    "instructions",
    "pa_web_agent_package",
    "pa_web_agent_dependencies",
    "pa_desk_agent_package",
    "pa_desk_agent_dependencies",
    "uipath_agent_package",
    "uipath_agent_dependencies",
]


class Platform(str, Enum):
    PA_WEB = "Power Automate Web"
    PA_DESK = "Power Automate Desktop"
    UIPATH = "UiPath"
    PYTHON = "Python"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class AgentData(BaseModel):
    agent_package_id: Optional[str] = None
    agent_dependencies_id: Optional[str] = None


class AgentBase(BaseModel):
    name: str
    description: str
    platforms: List[Platform]
    api_keys_required: List[str]


class Agent(AgentBase):
    id: PyObjectID = Field(validation_alias=AliasChoices("_id", "id"))
    date_created: datetime
    date_modified: datetime


class AgentOut(Agent):
    metadata: Optional[File] = None
    logo: Optional[File] = None
    instructions: Optional[File] = None
    pa_web_agent_package: Optional[File] = None
    pa_web_agent_dependencies: Optional[File] = None
    pa_desk_agent_package: Optional[File] = None
    pa_desk_agent_dependencies: Optional[File] = None
    uipath_agent_package: Optional[File] = None
    uipath_agent_dependencies: Optional[File] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    platforms: Optional[List[Platform]] = None
    api_keys_required: Optional[List[str]] = None
