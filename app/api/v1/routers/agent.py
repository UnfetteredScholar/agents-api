from logging import getLogger
from typing import Annotated, Dict, List, Optional

from bson.objectid import ObjectId
from core.storage import storage
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from schemas.agent import Agent, AgentBase, AgentOut, AgentUpdate, Platform
from schemas.file import FileCategory, FileMetadata
from schemas.page import Page
from schemas.review import Review, ReviewBase, ReviewIn, TargetType

router = APIRouter()


def convert_to_agent_out(agent_in: Agent) -> AgentOut:
    """Converts an agent to AgentOut"""
    logger = getLogger(__name__ + ".convert_to_agent_out")
    try:
        agent_out = AgentOut(**agent_in.model_dump())
        metadata = storage.file_get_record(
            {"agent_id": agent_in.id, "category": FileCategory.METADATA}
        )
        if metadata:
            agent_out.metadata = metadata

        logo = storage.file_get_record(
            {"agent_id": agent_in.id, "category": FileCategory.LOGO}
        )
        if logo:
            agent_out.logo = logo

        instructions = storage.file_get_record(
            {"agent_id": agent_in.id, "category": FileCategory.INSRUCTIONS}
        )
        if instructions:
            agent_out.instructions = instructions

        pa_web_agent_package = storage.file_get_record(
            {"agent_id": agent_in.id, "category": FileCategory.PA_WEB_AP}
        )
        if pa_web_agent_package:
            agent_out.pa_web_agent_package = pa_web_agent_package

        pa_web_agent_dependencies = storage.file_get_record(
            {"agent_id": agent_in.id, "category": FileCategory.PA_WEB_AD}
        )
        if pa_web_agent_dependencies:
            agent_out.pa_web_agent_dependencies = pa_web_agent_dependencies

        pa_desk_agent_package = storage.file_get_record(
            {"agent_id": agent_in.id, "category": FileCategory.PA_DESK_AP}
        )
        if pa_desk_agent_package:
            agent_out.pa_desk_agent_package = pa_desk_agent_package

        pa_desk_agent_dependencies = storage.file_get_record(
            {"agent_id": agent_in.id, "category": FileCategory.PA_DESK_AD}
        )
        if pa_desk_agent_dependencies:
            agent_out.pa_desk_agent_dependencies = pa_desk_agent_dependencies

        uipath_agent_package = storage.file_get_record(
            {"agent_id": agent_in.id, "category": FileCategory.UIPATH_AP}
        )
        if uipath_agent_package:
            agent_out.uipath_agent_package = uipath_agent_package

        uipath_agent_dependencies = storage.file_get_record(
            {"agent_id": agent_in.id, "category": FileCategory.UIPATH_AD}
        )
        if uipath_agent_dependencies:
            agent_out.uipath_agent_dependencies = uipath_agent_dependencies

        return agent_out

    except Exception as ex:
        logger.exception(ex)
        raise ex


@router.get(path="/agents", response_model=Page[AgentOut])
def get_user_agents(
    cursor: Optional[str] = None,
    limit: int = 10,
):
    """Get all current active agents of a user"""
    logger = getLogger(__name__ + ".get_user_agents")
    try:
        filter = {}
        if cursor:
            filter["_id"] = {"$gt": ObjectId(cursor)}

        agents = storage.agent_get_all_records(filter, limit=limit)
        agents = [convert_to_agent_out(agent) for agent in agents]
        item_count = len(agents)
        count_filter = filter.copy()
        if "_id" in count_filter:
            del count_filter["_id"]
        total_count = storage.agents_collection.count_documents(count_filter)
        next_cursor = None

        if item_count > 0:
            next_cursor = agents[-1].id

        agents_page = Page(
            items=agents,
            item_count=item_count,
            total_count=total_count,
            next_cursor=next_cursor,
        )

        return agents_page
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.get(path="/agents/{agent_id}", response_model=AgentOut)
def get_user_agent(
    agent_id: str,
):
    """Get agent for a user by its id"""
    logger = getLogger(__name__ + ".get_user_agent")
    try:

        agent = storage.agent_verify_record({"_id": agent_id})
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
    name: Annotated[str, Form(...)],
    description: Annotated[str, Form(...)],
    platforms: Annotated[
        List[str], Form(description=f"Options: {Platform.list()}")
    ],
    api_keys_required: Annotated[List[str], Form(...)],
    metadata: Optional[UploadFile] = None,
    logo: Optional[UploadFile] = None,
    instructions: Optional[UploadFile] = None,
    pa_web_agent_package: Optional[UploadFile] = None,
    pa_web_agent_dependencies: Optional[UploadFile] = None,
    pa_desk_agent_package: Optional[UploadFile] = None,
    pa_desk_agent_dependencies: Optional[UploadFile] = None,
    uipath_agent_package: Optional[UploadFile] = None,
    uipath_agent_dependencies: Optional[UploadFile] = None,
) -> AgentOut:
    f"""
    Adds a new agent for a logged in user

    platforms: {Platform.list()}
    """
    logger = getLogger(__name__ + ".new_agent")
    try:
        data = AgentBase(
            name=name,
            description=description,
            platforms=platforms,
            api_keys_required=api_keys_required,
        )

        agent_id = storage.agent_create_record(data)

        if metadata:
            storage.file_create_record(
                data=await metadata.read(),
                file_data=FileMetadata(
                    filename=metadata.filename,
                    agent_id=agent_id,
                    category=FileCategory.METADATA,
                    restrict_access=False,
                ),
            )
            logger.info(f"Added metadata file for agent({agent_id})")

        if logo:
            storage.file_create_record(
                data=await logo.read(),
                file_data=FileMetadata(
                    filename=logo.filename,
                    agent_id=agent_id,
                    category=FileCategory.LOGO,
                    restrict_access=False,
                ),
            )

            logger.info(f"Added logo file for agent({agent_id})")

        if instructions:
            storage.file_create_record(
                data=await instructions.read(),
                file_data=FileMetadata(
                    filename=instructions.filename,
                    agent_id=agent_id,
                    category=FileCategory.INSRUCTIONS,
                    restrict_access=False,
                ),
            )

            logger.info(f"Added intructions file for agent({agent_id})")

        if pa_web_agent_package:
            storage.file_create_record(
                data=await pa_web_agent_package.read(),
                file_data=FileMetadata(
                    filename=pa_web_agent_package.filename,
                    agent_id=agent_id,
                    category=FileCategory.PA_WEB_AP,
                    restrict_access=False,
                ),
            )

            logger.info(
                f"Added metadata power automate web agent package for agent({agent_id})"
            )

        if pa_web_agent_dependencies:
            storage.file_create_record(
                data=await pa_web_agent_dependencies.read(),
                file_data=FileMetadata(
                    filename=pa_web_agent_dependencies.filename,
                    agent_id=agent_id,
                    category=FileCategory.PA_WEB_AD,
                    restrict_access=False,
                ),
            )

            logger.info(
                f"Added power automate web dependencies file for agent({agent_id})"
            )

        if pa_desk_agent_package:
            storage.file_create_record(
                data=await pa_desk_agent_package.read(),
                file_data=FileMetadata(
                    filename=pa_desk_agent_package.filename,
                    agent_id=agent_id,
                    category=FileCategory.PA_DESK_AP,
                    restrict_access=False,
                ),
            )

            logger.info(
                f"Added metadata power automate desk agent package for agent({agent_id})"
            )

        if pa_desk_agent_dependencies:
            storage.file_create_record(
                data=await pa_desk_agent_dependencies.read(),
                file_data=FileMetadata(
                    filename=pa_desk_agent_dependencies.filename,
                    agent_id=agent_id,
                    category=FileCategory.PA_DESK_AD,
                    restrict_access=False,
                ),
            )

            logger.info(
                f"Added metadata power automate desk agent dependencies for agent({agent_id})"
            )

        if uipath_agent_package:
            storage.file_create_record(
                data=await uipath_agent_package.read(),
                file_data=FileMetadata(
                    filename=uipath_agent_package.filename,
                    agent_id=agent_id,
                    category=FileCategory.UIPATH_AP,
                    restrict_access=False,
                ),
            )

            logger.info(
                f"Added metadata uipath agent package for agent({agent_id})"
            )

        if uipath_agent_dependencies:
            storage.file_create_record(
                data=await uipath_agent_dependencies.read(),
                file_data=FileMetadata(
                    filename=uipath_agent_dependencies.filename,
                    agent_id=agent_id,
                    category=FileCategory.UIPATH_AD,
                    restrict_access=False,
                ),
            )
            logger.info(
                f"Added metadata uipath agent dependencies for agent({agent_id})"
            )

        agent = storage.agent_verify_record({"_id": agent_id})
        return convert_to_agent_out(agent)
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.patch("/agents/{agent_id}/details_update", response_model=AgentOut)
async def update_agent_details(agent_id: str, data: AgentUpdate) -> AgentOut:
    f"""
    updates an agent's details

    platforms: {Platform.list()}
    """
    logger = getLogger(__name__ + ".update_agent_details")
    try:
        update = data.model_dump(exclude_unset=True, exclude_none=True)
        storage.agent_update_record({"_id": agent_id}, update=update)
        agent = storage.agent_verify_record({"_id": agent_id})
        return convert_to_agent_out(agent)
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.patch("/agents/{agent_id}", response_model=AgentOut)
async def update_agent(
    agent_id: str,
    # name: Optional[str] = Form(default=None),
    # description: Optional[str] = Form(default=None),
    # platforms: Optional[List[str]] = Form(
    #     default=None, description=f"Options: {Platform.list()}"
    # ),
    # api_keys_required: Optional[List[str]] = Form(
    #     default=None, description=f"Options: {Platform.list()}"
    # ),
    metadata: Optional[UploadFile] = None,
    logo: Optional[UploadFile] = None,
    instructions: Optional[UploadFile] = None,
    pa_web_agent_package: Optional[UploadFile] = None,
    pa_web_agent_dependencies: Optional[UploadFile] = None,
    pa_desk_agent_package: Optional[UploadFile] = None,
    pa_desk_agent_dependencies: Optional[UploadFile] = None,
    uipath_agent_package: Optional[UploadFile] = None,
    uipath_agent_dependencies: Optional[UploadFile] = None,
) -> AgentOut:
    f"""
    Adds a new agent for a logged in user

    platforms: {Platform.list()}
    """
    logger = getLogger(__name__ + ".update_agent")
    try:
        agent = storage.agent_verify_record({"_id": agent_id})

        # update = {}
        # for k, v in [
        #     ("name", name),
        #     ("description", description),
        #     ("platforms", platforms),
        #     ("api_keys_required", api_keys_required),
        # ]:
        #     if v is not None and v is not [] and v != "":
        #         update[k] = v

        # storage.agent_update_record(filter={"_id": agent_id}, update=update)

        if metadata:
            try:
                storage.file_delete_record(
                    {"agent_id": agent_id, "category": FileCategory.METADATA}
                )
            except Exception:
                pass
            storage.file_create_record(
                data=await metadata.read(),
                file_data=FileMetadata(
                    filename=metadata.filename,
                    agent_id=agent_id,
                    category=FileCategory.METADATA,
                    restrict_access=False,
                ),
            )
            logger.info(f"Updated metadata file for agent({agent_id})")

        if logo:
            try:
                storage.file_delete_record(
                    {"agent_id": agent_id, "category": FileCategory.LOGO}
                )
            except Exception:
                pass
            storage.file_create_record(
                data=await logo.read(),
                file_data=FileMetadata(
                    filename=logo.filename,
                    agent_id=agent_id,
                    category=FileCategory.LOGO,
                    restrict_access=False,
                ),
            )

            logger.info(f"Updated logo file for agent({agent_id})")

        if instructions:
            try:
                storage.file_delete_record(
                    {
                        "agent_id": agent_id,
                        "category": FileCategory.INSRUCTIONS,
                    }
                )
            except Exception:
                pass
            storage.file_create_record(
                data=await instructions.read(),
                file_data=FileMetadata(
                    filename=instructions.filename,
                    agent_id=agent_id,
                    category=FileCategory.INSRUCTIONS,
                    restrict_access=False,
                ),
            )

            logger.info(f"Updated intructions file for agent({agent_id})")

        if pa_web_agent_package:
            try:
                storage.file_delete_record(
                    {"agent_id": agent_id, "category": FileCategory.PA_DESK_AP}
                )
            except Exception:
                pass
            storage.file_create_record(
                data=await pa_web_agent_package.read(),
                file_data=FileMetadata(
                    filename=pa_web_agent_package.filename,
                    agent_id=agent_id,
                    category=FileCategory.PA_WEB_AP,
                    restrict_access=False,
                ),
            )

            logger.info(
                f"Updated metadata power automate web agent package for agent({agent_id})"
            )

        if pa_web_agent_dependencies:
            try:
                storage.file_delete_record(
                    {"agent_id": agent_id, "category": FileCategory.PA_WEB_AD}
                )
            except Exception:
                pass
            storage.file_create_record(
                data=await pa_web_agent_dependencies.read(),
                file_data=FileMetadata(
                    filename=pa_web_agent_dependencies.filename,
                    agent_id=agent_id,
                    category=FileCategory.PA_WEB_AD,
                    restrict_access=False,
                ),
            )

            logger.info(
                f"Updated power automate web dependencies file for agent({agent_id})"
            )

        if pa_desk_agent_package:
            try:
                storage.file_delete_record(
                    {"agent_id": agent_id, "category": FileCategory.PA_DESK_AP}
                )
            except Exception:
                pass
            storage.file_create_record(
                data=await pa_desk_agent_package.read(),
                file_data=FileMetadata(
                    filename=pa_desk_agent_package.filename,
                    agent_id=agent_id,
                    category=FileCategory.PA_DESK_AP,
                    restrict_access=False,
                ),
            )

            logger.info(
                f"Updated metadata power automate desk agent package for agent({agent_id})"
            )

        if pa_desk_agent_dependencies:
            try:
                storage.file_delete_record(
                    {"agent_id": agent_id, "category": FileCategory.PA_DESK_AD}
                )
            except Exception:
                pass
            storage.file_create_record(
                data=await pa_desk_agent_dependencies.read(),
                file_data=FileMetadata(
                    filename=pa_desk_agent_dependencies.filename,
                    agent_id=agent_id,
                    category=FileCategory.PA_DESK_AD,
                    restrict_access=False,
                ),
            )

            logger.info(
                f"Updated metadata power automate desk agent dependencies for agent({agent_id})"
            )

        if uipath_agent_package:
            try:
                storage.file_delete_record(
                    {"agent_id": agent_id, "category": FileCategory.UIPATH_AP}
                )
            except Exception:
                pass
            storage.file_create_record(
                data=await uipath_agent_package.read(),
                file_data=FileMetadata(
                    filename=uipath_agent_package.filename,
                    agent_id=agent_id,
                    category=FileCategory.UIPATH_AP,
                    restrict_access=False,
                ),
            )

            logger.info(
                f"Updated metadata uipath agent package for agent({agent_id})"
            )

        if uipath_agent_dependencies:
            try:
                storage.file_delete_record(
                    {"agent_id": agent_id, "category": FileCategory.UIPATH_AD}
                )
            except Exception:
                pass
            storage.file_create_record(
                data=await uipath_agent_dependencies.read(),
                file_data=FileMetadata(
                    filename=uipath_agent_dependencies.filename,
                    agent_id=agent_id,
                    category=FileCategory.UIPATH_AD,
                    restrict_access=False,
                ),
            )
            logger.info(
                f"Updated metadata uipath agent dependencies for agent({agent_id})"
            )

        agent = storage.agent_verify_record({"_id": agent_id})
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
        storage.agent_delete_record({"_id": agent_id})
        message = {"message": "Agent deleted"}
        return JSONResponse(content=message)
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.post(path="/agents/{agent_id}/review", response_model=Review)
def review_agent(agent_id: str, data: ReviewIn):
    """Adds a review/ reaction to an agent"""
    logger = getLogger(__name__ + ".review_agent")
    try:

        storage.agent_verify_record({"_id": agent_id})

        id = storage.review_create_record(
            review_data=ReviewBase(
                reaction=data.reaction,
                target_id=agent_id,
                target_type=TargetType.AGENT,
                description=data.description,
            )
        )

        return storage.review_verify_record({"_id": id})
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))
