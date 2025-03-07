from datetime import datetime

# from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from schemas.base import PyObjectID

# class FileCategory(str, Enum):
#     LOGO = "logo"
#     METADATA = "metadata"
#     INSRUCTIONS = "instructions"
#     PA_WEB_AP = "pa_web_agent_package"
#     PA_WEB_AD = "pa_web_agent_dependencies"
#     PA_DESK_AP = "pa_desk_agent_package"
#     PA_DESK_AD = "pa_desk_agent_dependencies"
#     UIPATH_AP = "uipath_agent_package"
#     UIPATH_AD = "uipath_agent_dependencies"


class FileMetadata(BaseModel):
    filename: str
    # user_id: str
    # group: Optional[str] = None


class FileUpdate(BaseModel):
    filename: Optional[str] = None
    # group: Optional[str] = None


class File(BaseModel):
    id: PyObjectID = Field(validation_alias="_id")
    gridfs_id: str
    filename: str
    # user_id: str
    # group: Optional[str] = None
    download_link: Optional[str] = None
    date_created: datetime
    date_modified: datetime
