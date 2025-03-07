from logging import getLogger
from typing import Annotated, Dict, List, Optional

from core import storage
from core.conversion import convert_to_consultant_out
from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from schemas.consultant import Consultant, ConsultantOut, ConsultantUpdate
from schemas.file import FileMetadata
from schemas.page import Page
from schemas.review import Review, ReviewBase, ReviewIn, TargetType

router = APIRouter()


@router.get(
    path="/consultants",
    response_model=Page[ConsultantOut],
)
def get_consultants(
    cursor: Optional[str] = None,
    limit: int = 10,
):
    """Gets available consultants"""
    logger = getLogger(__name__ + ".get_consultants")
    try:
        filter = {}
        consultants_page = storage.consultants.get_page(
            filter, limit=limit, cursor=cursor
        )
        items = [
            convert_to_consultant_out(con) for con in consultants_page.items
        ]

        consultants_page.items = items
        return consultants_page
    except Exception as ex:
        logger.error(ex)
        if type(ex) is not HTTPException:
            raise HTTPException(status_code=500, detail=str(ex))
        raise ex


@router.get(
    path="/consultants/{consultant_id}",
    response_model=ConsultantOut,
)
def get_user_consultant(
    consultant_id: str,
):
    """Get consultant for a user by its id"""
    logger = getLogger(__name__ + ".get_user_consultant")
    try:

        consultant = storage.consultants.verify({"_id": consultant_id})

        return convert_to_consultant_out(consultant)
    except Exception as ex:
        logger.error(ex)
        if type(ex) is not HTTPException:
            raise HTTPException(status_code=500, detail=str(ex))
        raise ex


@router.post("/consultants", response_model=ConsultantOut)
async def new_consultant(
    # rating: ReviewMetrics
    title: Annotated[str, Form(...)],
    category: Annotated[str, Form(...)],
    tagline: Annotated[str, Form(...)],
    provider: Annotated[str, Form(...)],
    description: Annotated[str, Form(...)],
    services_offered: Annotated[List[str], Form(...)],
    industries_served: Annotated[List[str], Form(...)],
    related_services: Annotated[List[str], Form(...)],
    day_rate: Annotated[float, Form(...)],
    thumbnail_image: UploadFile,
    resume_upload: UploadFile,
) -> ConsultantOut:
    """
    Adds a new human consultant
    """
    logger = getLogger(__name__ + ".new_consultant")
    try:

        data = {
            "title": title,
            "category": category,
            "tagline": tagline,
            "provider": provider,
            "services_offered": services_offered,
            "industries_served": industries_served,
            "related_services": related_services,
            "description": description,
            "day_rate": day_rate,
        }
        data["rating"] = {"total_stars": 0, "review_count": 0}
        data["dependencies"] = []

        resume_upload_id = storage.files.file_create_record(
            data=await resume_upload.read(),
            file_data=FileMetadata(
                filename=resume_upload.filename,
            ),
        )
        data["resume_upload"] = resume_upload_id

        thumbnail_image_id = storage.files.file_create_record(
            data=await thumbnail_image.read(),
            file_data=FileMetadata(
                filename=thumbnail_image.filename,
            ),
        )
        data["thumbnail_image"] = thumbnail_image_id

        id = storage.consultants.create(data=data)
        consultant = storage.consultants.verify({"_id": id})
        return convert_to_consultant_out(consultant)
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.patch(
    "/consultants/{consultant_id}/details",
    response_model=ConsultantOut,
)
def update_consultant(
    consultant_id: str,
    data: ConsultantUpdate,
) -> JSONResponse:
    """Updates a consultant"""
    logger = getLogger(__name__ + ".update_consultant")
    try:
        update = data.model_dump(exclude_unset=True, exclude_none=True)

        storage.consultants.update(
            filter={"_id": consultant_id},
            update=update,
        )

        return convert_to_consultant_out(
            storage.consultants.verify({"_id": consultant_id})
        )
    except Exception as ex:
        logger.error(ex)
        if type(ex) is not HTTPException:
            raise HTTPException(status_code=500, detail=str(ex))
        raise ex


@router.patch(
    "/consultants/{consultant_id}/files",
    response_model=ConsultantOut,
)
async def update_consultant_files(
    consultant_id: str,
    thumbnail_image: Optional[UploadFile] = None,
    resume_upload: Optional[UploadFile] = None,
) -> JSONResponse:
    """Updates a consultant"""
    logger = getLogger(__name__ + ".update_consultant")
    try:
        consultant = storage.consultants.verify({"_id": consultant_id})
        update = {}
        data = consultant.model_dump()
        for file, key in [
            (resume_upload, "resume_upload"),
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

        storage.consultants.update(
            filter={"_id": consultant_id}, update=update
        )
        consultant = storage.consultants.verify({"_id": consultant_id})
        return convert_to_consultant_out(consultant)
    except Exception as ex:
        logger.error(ex)
        if type(ex) is not HTTPException:
            raise HTTPException(status_code=500, detail=str(ex))
        raise ex


@router.delete(
    "/consultants/{consultant_id}",
    response_model=Dict[str, str],
)
def delete_consultant(
    consultant_id: str,
) -> JSONResponse:
    """Deletes a user's consultant"""
    logger = getLogger(__name__ + ".delete_consultant")
    try:
        storage.consultants.delete({"_id": consultant_id})
        message = {"message": "Consultant deleted"}
        return JSONResponse(content=message)
    except Exception as ex:
        logger.error(ex)
        if type(ex) is not HTTPException:
            raise HTTPException(status_code=500, detail=str(ex))
        raise ex


@router.post(path="/consultants/{consultant_id}/review", response_model=Review)
def review_consultant(consultant_id: str, input: ReviewIn):
    """Adds a review/ reaction to an consultant"""
    logger = getLogger(__name__ + ".review_consultant")
    try:

        storage.consultants.verify({"_id": consultant_id})
        data = {
            "target_type": TargetType.CONSULTANT,
            "target_id": consultant_id,
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
        storage.consultants.advanced_update(
            filter={"_id": consultant_id}, update=update
        )

        return storage.reviews.verify({"_id": id})
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))
