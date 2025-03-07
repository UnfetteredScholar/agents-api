from logging import getLogger
from typing import Annotated, Dict, Optional

from core import storage
from core.conversion import convert_to_document_out
from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from schemas.document import Document, DocumentUpdate
from schemas.file import FileMetadata
from schemas.page import Page

router = APIRouter()


# @router.get(path="/documents", response_model=Page[Document])
# def get_documents(
#     cursor: Optional[str] = None,
#     limit: int = 10,
# ):
#     """Get all current active documents of a user"""
#     logger = getLogger(__name__ + ".get_documents")
#     try:
#         filter = {}
#         documents_page = storage.documents.get_page(
#             filter, limit=limit, cursor=cursor
#         )
#         items = [
#             convert_to_document_out(item) for item in documents_page.items
#         ]
#         documents_page.items = items

#         return documents_page
#     except HTTPException as ex:
#         logger.error(ex)
#         raise ex
#     except Exception as ex:
#         logger.error(ex)
#         raise HTTPException(status_code=500, detail=str(ex))


# @router.get(path="/documents/{document_id}", response_model=Document)
# def get_document(
#     document_id: str,
# ):
#     """Get document for a user by its id"""
#     logger = getLogger(__name__ + ".get_document")
#     try:

#         document = storage.documents.get({"_id": document_id})
#         return convert_to_document_out(document)
#     except HTTPException as ex:
#         logger.error(ex)
#         raise ex
#     except Exception as ex:
#         logger.error(ex)
#         raise HTTPException(status_code=500, detail=str(ex))


@router.post("/documents", response_model=Document)
async def new_document(
    agent_or_consultant_id: Annotated[str, Form(...)],
    name: Annotated[str, Form(...)],
    description: Annotated[str, Form(...)],
    document_file: UploadFile,
) -> Document:
    """
    Adds supporting documents to an agent or consultant
    """
    logger = getLogger(__name__ + ".new_document")
    ids = []
    try:
        filter = {"_id": agent_or_consultant_id}
        if not storage.agents.get(filter) and not storage.consultants.get(
            filter
        ):
            raise HTTPException(
                status_code=404, detail="Agent/ Consultant not found"
            )

        data = {
            "name": name,
            "description": description,
            "owner_id": agent_or_consultant_id,
        }
        document_file_id = storage.files.file_create_record(
            data=await document_file.read(),
            file_data=FileMetadata(
                filename=document_file.filename,
            ),
        )
        data["document_file"] = document_file_id
        ids.append(document_file_id)

        document_id = storage.documents.create(data=data)
        document = storage.documents.verify({"_id": document_id})
        return convert_to_document_out(document)
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.patch(
    "/documents/{document_id}/details_update", response_model=Document
)
async def update_document_details(
    document_id: str, data: DocumentUpdate
) -> Document:
    """
    updates an document's details
    """
    logger = getLogger(__name__ + ".update_document_details")
    try:
        update = data.model_dump(exclude_unset=True, exclude_none=True)
        storage.documents.update({"_id": document_id}, update=update)
        document = storage.documents.verify({"_id": document_id})
        return convert_to_document_out(document)
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.patch("/documents/{document_id}/files", response_model=Document)
async def update_document_files(
    document_id: str,
    document_file: Optional[UploadFile] = None,
) -> Document:
    """
    Update document's files
    """
    logger = getLogger(__name__ + ".update_document_files")
    try:
        document = storage.documents.verify({"_id": document_id})
        update = {}
        if document_file:
            storage.files.file_delete_record(
                {
                    "_id": document.document_file,
                }
            )

            document_file_id = storage.files.file_create_record(
                data=await document_file.read(),
                file_data=FileMetadata(
                    filename=document_file.filename,
                ),
            )
            update["document_file"] = document_file_id
            logger.info(f"Updated document_file for document({document_id})")

        updated_document = storage.documents.update(
            filter={"_id": document_id}, update=update
        )

        return convert_to_document_out(updated_document)
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@router.delete("/documents/{document_id}", response_model=Dict[str, str])
def delete_document(
    document_id: str,
) -> JSONResponse:
    """Deletes a user's document"""
    logger = getLogger(__name__ + ".delete_document")
    try:
        document = storage.documents.verify({"_id": document_id})
        ids = [document.document_file]

        for id in ids:
            try:
                storage.files.file_delete_record({"_id": id})
            except Exception as ex:
                logger.error(ex)

        storage.documents.delete({"_id": document_id})
        message = {"message": "Document deleted"}
        return JSONResponse(content=message)
    except HTTPException as ex:
        logger.error(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=500, detail=str(ex))
