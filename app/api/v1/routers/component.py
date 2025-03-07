from logging import getLogger
from typing import Annotated, Dict, Optional

from core import storage
from core.conversion import convert_to_component_out
from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from schemas.component import Component, ComponentUpdate
from schemas.file import FileMetadata
from schemas.page import Page

router = APIRouter()


@router.get(path="/components", response_model=Page[Component])
def get_components(
    cursor: Optional[str] = None,
    limit: int = 10,
):
    """Get all current active components of a user"""
    logger = getLogger(__name__ + ".get_components")
    try:
        filter = {}
        components_page = storage.components.get_page(
            filter, limit=limit, cursor=cursor
        )
        items = [
            convert_to_component_out(item) for item in components_page.items
        ]
        components_page.items = items

        return components_page
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.get(path="/components/{component_id}", response_model=Component)
def get_component(
    component_id: str,
):
    """Get component for a user by its id"""
    logger = getLogger(__name__ + ".get_component")
    try:

        component = storage.components.get({"_id": component_id})
        return convert_to_component_out(component)
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.post("/components", response_model=Component)
async def new_component(
    name: Annotated[str, Form(...)],
    description: Annotated[str, Form(...)],
    price: Annotated[float, Form(...)],
    dependency_file: UploadFile,
    logo: UploadFile,
) -> Component:
    """
    Adds a new component for a logged in user
    """
    logger = getLogger(__name__ + ".new_component")
    ids = []
    try:
        data = {"name": name, "description": description, "price": price}
        logo_id = storage.files.file_create_record(
            data=await logo.read(),
            file_data=FileMetadata(
                filename=logo.filename,
            ),
        )
        data["logo"] = logo_id
        ids.append(logo_id)

        dependency_file_id = storage.files.file_create_record(
            data=await dependency_file.read(),
            file_data=FileMetadata(
                filename=dependency_file.filename,
            ),
        )

        data["dependency_file"] = dependency_file_id
        ids.append(dependency_file)

        component_id = storage.components.create(data=data)
        component = storage.components.verify({"_id": component_id})
        return convert_to_component_out(component)
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.patch(
    "/components/{component_id}/details_update", response_model=Component
)
async def update_component_details(
    component_id: str, data: ComponentUpdate
) -> Component:
    """
    updates an component's details
    """
    logger = getLogger(__name__ + ".update_component_details")
    try:
        update = data.model_dump(exclude_unset=True, exclude_none=True)
        storage.components.update({"_id": component_id}, update=update)
        component = storage.components.verify({"_id": component_id})
        return convert_to_component_out(component)
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.patch("/components/{component_id}/files", response_model=Component)
async def update_component_files(
    component_id: str,
    dependency_file: Optional[UploadFile] = None,
    logo: Optional[UploadFile] = None,
) -> Component:
    """
    Update component's files
    """
    logger = getLogger(__name__ + ".update_component_files")
    try:
        component = storage.components.verify({"_id": component_id})
        update = {}
        if logo:
            storage.files.file_delete_record(
                {
                    "_id": component.logo,
                }
            )

            logo_id = storage.files.file_create_record(
                data=await logo.read(),
                file_data=FileMetadata(
                    filename=logo.filename,
                ),
            )
            update["logo"] = logo_id
            logger.info(f"Updated logo file for component({component_id})")

        if dependency_file:
            storage.files.file_delete_record(
                {
                    "_id": component.dependency_file,
                }
            )

            dependency_file_id = storage.files.file_create_record(
                data=await dependency_file.read(),
                file_data=FileMetadata(
                    filename=dependency_file.filename,
                ),
            )
            update["dependency_file"] = dependency_file_id
            logger.info(f"Updated logo file for component({component_id})")

        updated_component = storage.components.update(
            filter={"_id": component_id}, update=update
        )

        return convert_to_component_out(updated_component)
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.delete("/components/{component_id}", response_model=Dict[str, str])
def delete_component(
    component_id: str,
) -> JSONResponse:
    """Deletes a user's component"""
    logger = getLogger(__name__ + ".delete_component")
    try:
        component = storage.components.verify({"_id": component_id})
        ids = [component.logo, component.dependency_file]

        for id in ids:
            try:
                storage.files.file_delete_record({"_id": id})
            except Exception:
                pass

        storage.components.delete({"_id": component_id})
        message = {"message": "Component deleted"}
        return JSONResponse(content=message)
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))
