from logging import getLogger
from typing import Annotated, Dict, List, Optional

from bson.objectid import ObjectId
from core import storage
from core.conversion import convert_to_agent_out
from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from schemas.agent import Agent, AgentOut, AgentUpdate, Platform
from schemas.file import FileMetadata
from schemas.page import Page
from schemas.review import Review, ReviewIn, TargetType

router = APIRouter()


@router.get(path="/agents", response_model=Page[AgentOut])
def get_user_agents(
    cursor: Optional[str] = None,
    limit: int = 10,
):
    """Get all current active agents of a user"""
    logger = getLogger(__name__ + ".get_user_agents")
    try:
        filter = {}

        agents_page = storage.agents.get_page(
            filter, limit=limit, cursor=cursor
        )
        items = [convert_to_agent_out(item) for item in agents_page.items]
        agents_page.items = items

        return agents_page
    except HTTPException as ex:
        logger.exception(ex)
        raise ex
    except Exception as ex:
        logger.exception(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.get(path="/agents/{agent_id}", response_model=AgentOut)
def get_user_agent(
    agent_id: str,
):
    """Get agent for a user by its id"""
    logger = getLogger(__name__ + ".get_user_agent")
    try:

        agent = storage.agents.verify({"_id": agent_id})
        agent = convert_to_agent_out(agent)
        return agent
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.post("/agents", response_model=AgentOut)
async def new_agent(
    # supporting_documents: List[str] = []
    title: Annotated[str, Form(...)],
    category: Annotated[str, Form(...)],
    tagline: Annotated[str, Form(...)],
    provider: Annotated[str, Form(...)],
    pricing_model: Annotated[str, Form(...)],
    platform_type: Annotated[Platform, Form(...)],
    demo_available: Annotated[bool, Form(...)],
    description: Annotated[str, Form(...)],
    key_features: Annotated[List[str], Form(...)],
    integrations: Annotated[List[str], Form(...)],
    related_ai_solutions: Annotated[List[str], Form(...)],
    platform_file: UploadFile,
    thumbnail_image: UploadFile,
) -> Agent:
    f"""
    Adds a new agent for a logged in user

    platforms: {Platform.list()}
    """
    logger = getLogger(__name__ + ".new_agent")
    try:
        data = {
            "title": title,
            "category": category,
            "tagline": tagline,
            "provider": provider,
            "pricing_model": pricing_model,
            "platform_type": platform_type,
            "demo_available": demo_available,
            "description": description,
            "key_features": key_features,
            "integrations": integrations,
            "related_ai_solutions": related_ai_solutions,
        }
        data["rating"] = {"total_stars": 0, "review_count": 0}
        data["dependencies"] = []

        platform_file_id = storage.files.file_create_record(
            data=await platform_file.read(),
            file_data=FileMetadata(
                filename=platform_file.filename,
            ),
        )
        data["platform_file"] = platform_file_id

        thumbnail_image_id = storage.files.file_create_record(
            data=await thumbnail_image.read(),
            file_data=FileMetadata(
                filename=thumbnail_image.filename,
            ),
        )
        data["thumbnail_image"] = thumbnail_image_id

        agent_id = storage.agents.create(data=data)
        agent = storage.agents.verify({"_id": agent_id})
        return convert_to_agent_out(agent)
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.patch("/agents/{agent_id}/details", response_model=AgentOut)
async def update_agent_details(agent_id: str, data: AgentUpdate) -> AgentOut:
    f"""
    updates an agent's details

    platforms: {Platform.list()}
    """
    logger = getLogger(__name__ + ".update_agent_details")
    try:
        update = data.model_dump(exclude_unset=True, exclude_none=True)
        storage.agents.update({"_id": agent_id}, update=update)
        agent = storage.agents.verify({"_id": agent_id})
        return convert_to_agent_out(agent)
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.patch("/agents/{agent_id}/files", response_model=AgentOut)
async def update_agent_files(
    agent_id: str,
    platform_file: Optional[UploadFile] = None,
    thumbnail_image: Optional[UploadFile] = None,
) -> AgentOut:
    f"""
    Adds a new agent for a logged in user

    platforms: {Platform.list()}
    """
    logger = getLogger(__name__ + ".update_agent_files")
    try:
        agent = storage.agents.verify({"_id": agent_id})
        data = agent.model_dump()
        update = {}
        for file, key in [
            (platform_file, "platform_file"),
            (thumbnail_image, "thumbnail_image"),
        ]:
            if file is not None:
                file_id = storage.files.file_create_record(
                    data=await file.read(),
                    file_data=FileMetadata(
                        filename=file.filename,
                    ),
                )
                update[key] = file_id
                storage.files.file_delete_record({"_id": data[key]})

        storage.agents.update(filter={"_id": agent_id}, update=update)
        agent = storage.agents.verify({"_id": agent_id})
        return convert_to_agent_out(agent)
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.delete("/agents/{agent_id}", response_model=Dict[str, str])
def delete_agent(
    agent_id: str,
) -> JSONResponse:
    """Deletes a user's agent"""
    logger = getLogger(__name__ + ".delete_agent")
    try:
        storage.agents.verify({"_id": agent_id})
        storage.agents.delete({"_id": agent_id})

        message = {"message": "Agent deleted"}
        return JSONResponse(content=message)
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.post(path="/agents/{agent_id}/review", response_model=Review)
def review_agent(agent_id: str, input: ReviewIn):
    """Adds a review/ reaction to an agent"""
    logger = getLogger(__name__ + ".review_agent")
    try:

        storage.agents.verify({"_id": agent_id})
        data = {
            "target_type": TargetType.AGENT,
            "target_id": agent_id,
            "stars": input.stars,
            "description": input.description,
        }
        id = storage.reviews.create(data=data)

        update = {
            "$inc": {
                "rating.total_stars": input.stars,
                "rating.review_count": 1,
            }
        }
        storage.agents.advanced_update(filter={"_id": agent_id}, update=update)

        return storage.reviews.verify({"_id": id})
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))
