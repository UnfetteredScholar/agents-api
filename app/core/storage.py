from datetime import UTC, datetime
from typing import Dict, Generic, List, Optional, Type, TypeVar

import gridfs
import schemas.file as s_file
from bson.objectid import ObjectId
from core.config import settings
from fastapi import HTTPException, status
from pydantic import BaseModel
from pymongo import MongoClient
from schemas import agent as s_agent
from schemas import component as s_component
from schemas import consultant as s_consultant
from schemas import document as s_document
from schemas import review as s_review
from schemas.page import Page

T = TypeVar("T", bound=BaseModel)


class MongoFileStorage:
    """Storage class for interfacing with mongo db"""

    def __init__(
        self,
        connection_string: str = settings.MONGODB_URI,
        db_name: str = settings.DATABSE_NAME,
    ):
        """
        Storage object with methods to Create, Read, Update,
        Delete (CRUD) objects in the mongo database.
        """
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.fs = gridfs.GridFS(self.db)

    def file_create_record(
        self,
        data: bytes,
        file_data: s_file.FileMetadata,
    ) -> str:
        """Creates a file record"""
        files_table = self.db["files"]

        gridfs_id = str(self.fs.put(data, **file_data.model_dump()))
        date = datetime.now(UTC)
        file = file_data.model_dump()
        file["gridfs_id"] = gridfs_id
        file["date_created"] = date
        file["date_modified"] = date

        id = str(files_table.insert_one(file).inserted_id)

        return id

    def file_get_record(self, filter: Dict) -> Optional[s_file.File]:
        """Gets a file record from the db using the supplied filter"""
        files = self.db["files"]

        if "_id" in filter and type(filter["_id"]) is str:
            filter["_id"] = ObjectId(filter["_id"])

        file = files.find_one(filter)

        if file:
            file = s_file.File(**file)
            # if file.restrict_access:
            #     file.download_link =
            # else:
            #     file.download_link = (
            #         f"/api/v1/files/{file.id}/unrestricted/download"
            #     )

        return file

    def file_get_all_records(self, filter: Dict) -> List[s_file.File]:
        """Gets all file records from the db using the supplied filter"""
        files = self.db["files"]

        if "_id" in filter and type(filter["_id"]) is str:
            filter["_id"] = ObjectId(filter["_id"])

        files_list = files.find(filter)
        files_output = []

        for file in files_list:
            file = s_file.File(**file)
            # if file.restrict_access:
            #     file.download_link = f"/api/v1/files/{file.id}/download"
            # else:
            #     file.download_link = (
            #         f"/api/v1/files/{file.id}/unrestricted/download"
            #     )
            files_output.append(file)

        return files_output

    def file_verify_record(self, filter: Dict) -> s_file.File:
        """
        Gets a file record using the filter
        and raises an error if a matching record is not found
        """

        file = self.file_get_record(filter)

        if file is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        return file

    def file_get_data(self, file_id: str) -> bytes:
        """Gets the data of a file"""

        file = self.file_verify_record({"_id": file_id})

        return self.fs.get(file_id=ObjectId(file.gridfs_id)).read()

    def file_update_record(self, filter: Dict, update: Dict):
        """Updates a file record"""
        self.file_verify_record(filter)

        for key in ["_id", "user_id", "project_id", "gridfs_id"]:
            if key in update:
                raise KeyError(f"Invalid Key. KEY {key} cannot be changed")
        update["date_modified"] = datetime.now(UTC)

        self.db["files"].update_one(filter, {"$set": update})

    def file_advanced_update_record(self, filter: Dict, update: Dict):
        """Updates a file record with more complex parameters"""
        self.file_verify_record(filter)

        if "$set" in update:
            update["$set"]["date_modified"] = datetime.now(UTC)
        else:
            update["$set"] = {"date_modified": datetime.now(UTC)}

        return self.db["files"].update_one(filter, update)

    def file_delete_record(self, filter: Dict):
        """Deletes a file record"""
        file = self.file_verify_record(filter)

        self.db["files"].delete_one(filter)
        self.fs.delete(file_id=ObjectId(file.gridfs_id))


class MongoStorage(Generic[T]):
    """Generic Storage class for interfacing with mongo db"""

    client = MongoClient(settings.MONGODB_URI)

    def __init__(
        self,
        collection_name: str,
        model: Type[T],
        db_name: str = settings.DATABSE_NAME,
        update_ban: List[str] = ["_id"],
    ):
        """
        Storage object with methods to Create, Read, Update,
        Delete (CRUD) objects in the mongo database.
        """

        self.db = self.client[db_name]
        self.fs = gridfs.GridFS(self.db)
        self.model = model
        self.collection_name = collection_name
        self.collection = self.db[collection_name]
        self.update_ban = update_ban

    def create(
        self,
        data: dict,
    ) -> str:
        """Creates a db record and returns the id"""

        date = datetime.now(UTC)
        data["date_created"] = date
        data["date_modified"] = date

        id = str(self.collection.insert_one(data).inserted_id)

        return id

    def get(self, filter: Dict) -> Optional[T]:
        """Gets a record from the db using the supplied filter"""

        if "_id" in filter and type(filter["_id"]) is str:
            filter["_id"] = ObjectId(filter["_id"])

        res = self.collection.find_one(filter)

        if res:
            res = self.model(**res)

        return res

    def get_all(
        self, filter: Dict, limit: int = 0, sort: dict = {"_id": 1}
    ) -> List[T]:
        """Gets all records from the db using the supplied filter"""

        if "_id" in filter and type(filter["_id"]) is str:
            filter["_id"] = ObjectId(filter["_id"])

        res_list = self.collection.find(filter).sort(sort).limit(limit=limit)
        res_out = [self.model(**item) for item in res_list]

        return res_out

    def get_page(
        self,
        filter: Dict,
        limit: int = 0,
        cursor: Optional[str] = None,
        sort: dict = {"_id": 1},
    ) -> Page[T]:
        """Gets a page of res"""

        if cursor:
            filter["_id"] = {"$gt": ObjectId(cursor)}

        res = self.get_all(filter, limit=limit, sort=sort)

        item_count = len(res)
        next_cursor = None

        if item_count > 0:
            count_query = filter.copy()
            count_query["_id"] = {"$gt": ObjectId(res[-1].id)}
            last_item = self.get(count_query)
            if last_item and last_item.id != res[-1].id:
                next_cursor = res[-1].id

        res_page = Page(
            items=res,
            item_count=item_count,
            next_cursor=next_cursor,
        )

        return res_page

    def verify(self, filter: Dict) -> T:
        """
        Gets a record using the filter
        and raises an error if a matching record is not found
        """

        res = self.get(filter)

        if res is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.collection_name} Item not found",
            )

        return res

    def update(self, filter: Dict, update: Dict):
        """Updates a record"""
        self.verify(filter)

        for key in self.update_ban:
            if key in update:
                raise KeyError(f"Invalid Key. KEY {key} cannot be changed")
        update["date_modified"] = datetime.now(UTC)

        return self.collection.update_one(filter, {"$set": update})

    def advanced_update(self, filter: Dict, update: Dict):
        """Updates a record with more complex parameters"""
        self.verify(filter)

        if "$set" in update:
            update["$set"]["date_modified"] = datetime.now(UTC)
        else:
            update["$set"] = {"date_modified": datetime.now(UTC)}

        return self.collection.update_one(filter, update)

    def delete(self, filter: Dict):
        """Deletes a component record"""
        self.verify(filter)

        self.collection.delete_one(filter)


agents = MongoStorage(
    collection_name="agents",
    model=s_agent.Agent,
    update_ban=["_id", "user_id"],
)

consultants = MongoStorage(
    collection_name="consultants",
    model=s_consultant.Consultant,
    update_ban=["_id", "user_id"],
)


reviews = MongoStorage(
    collection_name="reviews",
    model=s_review.Review,
    update_ban=["_id", "user_id"],
)

components = MongoStorage(
    collection_name="components",
    model=s_component.Component,
    update_ban=["_id", "user_id"],
)

documents = MongoStorage(
    collection_name="documents",
    model=s_document.Document,
    update_ban=["_id", "user_id"],
)

files = MongoFileStorage()
