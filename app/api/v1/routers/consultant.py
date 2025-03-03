from logging import getLogger
from typing import Annotated, Dict, Optional

from core.storage import storage
from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from schemas.consultant import (
    Consultant,
    ConsultantBase,
    ConsultantOut,
    ConsultantUpdate,
)
from schemas.file import FileMetadata
from schemas.page import Page
from schemas.review import Review, ReviewBase, ReviewIn, TargetType

router = APIRouter()


def convert_to_consultant_out(input: Consultant) -> ConsultantOut:
    """Converts form Consultant to ConsultantOut"""
    profile_picture = storage.file_get_record(
        {"_id": input.profile_picture_id}
    )
    resume_file = storage.file_get_record({"_id": input.resume_file_id})
    data = input.model_dump()
    data["profile_picture"] = profile_picture
    data["resume_file"] = resume_file

    return ConsultantOut(**data)


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
        consultants_page = storage.consultant_get_page(
            filter, limit=limit, cursor=cursor
        )
        items = [
            convert_to_consultant_out(con) for con in consultants_page.items
        ]

        output = Page(
            items=items,
            item_count=consultants_page.item_count,
            next_cursor=consultants_page.next_cursor,
        )

        return output
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

        consultant = storage.consultant_verify_record({"_id": consultant_id})

        return convert_to_consultant_out(consultant)
    except Exception as ex:
        logger.error(ex)
        if type(ex) is not HTTPException:
            raise HTTPException(status_code=500, detail=str(ex))
        raise ex


@router.post("/consultants", response_model=ConsultantOut)
async def new_consultant(
    name: Annotated[str, Form(...)],
    description: Annotated[str, Form(...)],
    role: Annotated[str, Form(...)],
    expertise: Annotated[str, Form(...)],
    day_rate: Annotated[float, Form(...)],
    profile_picture: UploadFile,
    resume_file: UploadFile,
) -> ConsultantOut:
    """
    Adds a new human consultant
    """
    logger = getLogger(__name__ + ".new_consultant")
    try:

        profile_picture_id = storage.file_create_record(
            data=await profile_picture.read(),
            file_data=FileMetadata(
                filename=profile_picture.filename,
                restrict_access=False,
            ),
        )

        resume_file_id = storage.file_create_record(
            data=await resume_file.read(),
            file_data=FileMetadata(
                filename=resume_file.filename,
                restrict_access=False,
            ),
        )

        data = ConsultantBase(
            profile_picture_id=profile_picture_id,
            name=name,
            role=role,
            description=description,
            resume_file_id=resume_file_id,
            expertise=expertise,
            day_rate=day_rate,
        )

        id = storage.consultant_create_record(data)

        consultant = storage.consultant_verify_record({"_id": id})
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

        storage.consultant_update_record(
            filter={"_id": consultant_id},
            update=update,
        )

        return convert_to_consultant_out(
            storage.consultant_verify_record({"_id": consultant_id})
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
    profile_picture: Optional[UploadFile] = None,
    resume_file: Optional[UploadFile] = None,
) -> JSONResponse:
    """Updates a consultant"""
    logger = getLogger(__name__ + ".update_consultant")
    try:
        update = {}
        if profile_picture:
            profile_picture_id = storage.file_create_record(
                data=await profile_picture.read(),
                file_data=FileMetadata(
                    filename=profile_picture.filename,
                    restrict_access=False,
                ),
            )
            update["profile_picture_id"] = profile_picture_id
        if resume_file:
            resume_file_id = storage.file_create_record(
                data=await resume_file.read(),
                file_data=FileMetadata(
                    filename=resume_file.filename,
                    restrict_access=False,
                ),
            )
            update["resume_file_id"] = resume_file_id

        storage.consultant_update_record(
            filter={"_id": consultant_id},
            update=update,
        )

        return convert_to_consultant_out(
            storage.consultant_verify_record({"_id": consultant_id})
        )
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

        storage.consultant_delete_record({"_id": consultant_id})
        message = {"message": "Consultant deleted"}
        return JSONResponse(content=message)
    except Exception as ex:
        logger.error(ex)
        if type(ex) is not HTTPException:
            raise HTTPException(status_code=500, detail=str(ex))
        raise ex


@router.post(path="/consultants/{consultant_id}/review", response_model=Review)
def review_consultant(consultant_id: str, data: ReviewIn):
    """Adds a review/ reaction to an consultant"""
    logger = getLogger(__name__ + ".review_consultant")
    try:

        storage.consultant_verify_record({"_id": consultant_id})

        id = storage.review_create_record(
            review_data=ReviewBase(
                reaction=data.reaction,
                target_id=consultant_id,
                target_type=TargetType.CONSULTANT,
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
