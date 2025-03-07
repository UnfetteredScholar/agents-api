import mimetypes
from io import BytesIO
from logging import getLogger

from bson.objectid import ObjectId
from core import storage
from core.authentication.auth_token import verify_access_token
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse

# from schemas.file import File, FileCategory, FileMetadata

router = APIRouter()


@router.get(path="/files/{file_token}/download")
def download_file(file_token: str, request: Request):
    """Downloads a file from the server"""
    logger = getLogger(__name__ + ".download_file")
    try:
        token_data = verify_access_token(file_token)
        file = storage.files.file_verify_record({"_id": token_data.id})

        file_obj = storage.files.fs.get(ObjectId(file.gridfs_id))
        file_size = file_obj.length
        mime_type, _ = mimetypes.guess_type(file.filename)
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Disposition": f"attachment; filename={file.filename}",
        }
        if mime_type is not None:
            headers["Content-Type"] = mime_type
        else:
            headers["Content-Type"] = "application/octet-stream"

        range_header = request.headers.get("range")
        if range_header:
            range_values = range_header.replace("bytes=", "").split("-")
            start = int(range_values[0]) if range_values[0] else 0
            end = (
                int(range_values[1])
                if len(range_values) > 1 and range_values[1]
                else file_size - 1
            )

            if start >= file_size or end >= file_size:
                raise HTTPException(
                    status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                    detail="Requested Range Not Satisfiable",
                )

            file_obj.seek(start)
            chunk_size = end - start + 1

            file_like = BytesIO(file_obj.read(chunk_size))

            headers.update(
                {
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Content-Length": str(chunk_size),
                }
            )
            return StreamingResponse(
                file_like,
                status_code=status.HTTP_206_PARTIAL_CONTENT,
                headers=headers,
            )
        else:
            headers["Content-Length"] = str(file_size)
            file_like = BytesIO(file_obj.read())

            return StreamingResponse(
                file_like, status_code=status.HTTP_200_OK, headers=headers
            )
    except Exception as ex:
        logger.exception(ex)
        if type(ex) is not HTTPException:
            raise HTTPException(status_code=500, detail=str(ex))
        raise ex


# @router.get(path="/files/{file_id}/unrestricted/download")
# def download_unrestricted_file(file_id: str, request: Request):
#     """Downloads a file from the server"""
#     logger = getLogger(__name__ + ".download_unrestricted_file")
#     try:
#         file = storage.file_verify_record({"_id": file_id})

#         file_obj = storage.fs.get(ObjectId(file.gridfs_id))
#         file_size = file_obj.length
#         mime_type, _ = mimetypes.guess_type(file.filename)
#         headers = {
#             "Accept-Ranges": "bytes",
#             "Content-Disposition": f"attachment; filename={file.filename}",
#         }
#         if mime_type is not None:
#             headers["Content-Type"] = mime_type
#         else:
#             headers["Content-Type"] = "application/octet-stream"

#         range_header = request.headers.get("range")
#         if range_header:
#             range_values = range_header.replace("bytes=", "").split("-")
#             start = int(range_values[0]) if range_values[0] else 0
#             end = (
#                 int(range_values[1])
#                 if len(range_values) > 1 and range_values[1]
#                 else file_size - 1
#             )

#             if start >= file_size or end >= file_size:
#                 raise HTTPException(
#                     status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
#                     detail="Requested Range Not Satisfiable",
#                 )

#             file_obj.seek(start)
#             chunk_size = end - start + 1

#             file_like = BytesIO(file_obj.read(chunk_size))

#             headers.update(
#                 {
#                     "Content-Range": f"bytes {start}-{end}/{file_size}",
#                     "Content-Length": str(chunk_size),
#                 }
#             )
#             return StreamingResponse(
#                 file_like,
#                 status_code=status.HTTP_206_PARTIAL_CONTENT,
#                 headers=headers,
#             )
#         else:
#             headers["Content-Length"] = str(file_size)
#             file_like = BytesIO(file_obj.read())
#             # print(headers)

#             return StreamingResponse(
#                 file_like, status_code=status.HTTP_200_OK, headers=headers
#             )

#             # data = file_obj.read()  # storage.file_get_data(file_id=file.id)
#             # file_like = BytesIO(data)

#             # response = StreamingResponse(
#             #     file_like, media_type="application/octet-stream"
#             # )
#             # response.headers["Content-Disposition"] = (
#             #     f"attachment; filename={file.filename}"
#             # )
#             # return response
#     except Exception as ex:
#         logger.error(ex)
#         if type(ex) is not HTTPException:
#             raise HTTPException(status_code=500, detail=str(ex))
#         raise ex
