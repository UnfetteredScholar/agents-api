from datetime import UTC, datetime
from typing import Dict, List, Literal, Optional

import gridfs
import schemas.file as s_file
from bson.objectid import ObjectId
from core.config import settings
from fastapi import HTTPException, status
from pymongo import MongoClient
from schemas import agent as s_agent
from schemas import consultant as s_consultant
from schemas.page import Page


class MongoStorage:
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
        self.agents_collection = self.db["agents"]

    # agents
    def agent_create_record(
        self,
        agent_data: s_agent.AgentBase,
    ) -> str:
        """Creates a agent record"""

        agents_table = self.db["agents"]

        date = datetime.now(UTC)
        agent = agent_data.model_dump()
        agent["date_created"] = date
        agent["date_modified"] = date

        id = str(agents_table.insert_one(agent).inserted_id)

        return id

    def agent_get_record(self, filter: Dict) -> Optional[s_agent.Agent]:
        """Gets a agent record from the db using the supplied filter"""
        agents = self.db["agents"]

        if "_id" in filter and type(filter["_id"]) is str:
            filter["_id"] = ObjectId(filter["_id"])

        agent = agents.find_one(filter)

        if agent:
            agent = s_agent.Agent(**agent)

        return agent

    def agent_get_all_records(
        self, filter: Dict, limit: int = 0
    ) -> List[s_agent.Agent]:
        """Gets all agent records from the db using the supplied filter"""
        agents = self.db["agents"]

        if "_id" in filter and type(filter["_id"]) is str:
            filter["_id"] = ObjectId(filter["_id"])

        agents_list = agents.find(filter).limit(limit=limit)
        agents_out = []

        for agent in agents_list:
            agent = s_agent.Agent(**agent)
            agents_out.append(agent)

        return agents_out

    def agent_get_page(
        self, filter: Dict, limit: int = 0, cursor: Optional[str] = None
    ) -> Page[s_agent.Agent]:
        """Gets a page of agents"""

        if cursor:
            filter["_id"] = {"$gt": ObjectId(cursor)}

        agents = self.agent_get_all_records(filter, limit=limit)

        item_count = len(agents)
        next_cursor = None

        if item_count > 0:
            count_query = filter.copy()
            count_query["_id"] = {"$gt": ObjectId(agents[-1].id)}
            last_item = storage.agent_get_record(count_query)
            if last_item and last_item.id != agents[-1].id:
                next_cursor = agents[-1].id

        agents_page = Page(
            items=agents,
            item_count=item_count,
            next_cursor=next_cursor,
        )

        return agents_page

    def agent_verify_record(self, filter: Dict) -> s_agent.Agent:
        """
        Gets a agent record using the filter
        and raises an error if a matching record is not found
        """

        agent = self.agent_get_record(filter)

        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        return agent

    def agent_update_record(self, filter: Dict, update: Dict):
        """Updates a agent record"""
        self.agent_verify_record(filter)

        for key in ["_id", "user_id"]:
            if key in update:
                raise KeyError(f"Invalid Key. KEY {key} cannot be changed")
        update["date_modified"] = datetime.now(UTC)

        self.db["agents"].update_one(filter, {"$set": update})

    def agent_advanced_update_record(self, filter: Dict, update: Dict):
        """Updates a agent record with more complex parameters"""
        self.agent_verify_record(filter)

        if "$set" in update:
            update["$set"]["date_modified"] = datetime.now(UTC)
        else:
            update["$set"] = {"date_modified": datetime.now(UTC)}

        return self.db["agents"].update_one(filter, update)

    def agent_delete_record(self, filter: Dict):
        """Deletes a agent record"""
        agent = self.agent_verify_record(filter)

        self.db["agents"].delete_one(filter)

        for file in storage.file_get_all_records({"agent_id": agent.id}):
            self.file_delete_record({"_id": file.id})

    # files
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
            if file.restrict_access:
                file.download_link = f"/api/v1/files/{file.id}/download"
            else:
                file.download_link = (
                    f"/api/v1/files/{file.id}/unrestricted/download"
                )

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
            if file.restrict_access:
                file.download_link = f"/api/v1/files/{file.id}/download"
            else:
                file.download_link = (
                    f"/api/v1/files/{file.id}/unrestricted/download"
                )
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

        file = storage.file_verify_record({"_id": file_id})

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

    # consultants
    def consultant_create_record(
        self,
        consultant_data: s_consultant.ConsultantBase,
    ) -> str:
        """Creates a consultant record"""

        consultants_table = self.db["consultants"]

        date = datetime.now(UTC)
        consultant = consultant_data.model_dump()
        consultant["date_created"] = date
        consultant["date_modified"] = date

        id = str(consultants_table.insert_one(consultant).inserted_id)

        return id

    def consultant_get_record(
        self, filter: Dict
    ) -> Optional[s_consultant.Consultant]:
        """Gets a consultant record from the db using the supplied filter"""
        consultants = self.db["consultants"]

        if "_id" in filter and type(filter["_id"]) is str:
            filter["_id"] = ObjectId(filter["_id"])

        consultant = consultants.find_one(filter)

        if consultant:
            consultant = s_consultant.Consultant(**consultant)

        return consultant

    def consultant_get_all_records(
        self, filter: Dict, limit: int = 0
    ) -> List[s_consultant.Consultant]:
        """Gets all consultant records from the db using the supplied filter"""
        consultants = self.db["consultants"]

        if "_id" in filter and type(filter["_id"]) is str:
            filter["_id"] = ObjectId(filter["_id"])

        consultants_list = consultants.find(filter).limit(limit=limit)
        consultants_out = []

        for consultant in consultants_list:
            consultant = s_consultant.Consultant(**consultant)
            consultants_out.append(consultant)

        return consultants_out

    def consultant_get_page(
        self, filter: Dict, limit: int = 0, cursor: Optional[str] = None
    ) -> Page[s_consultant.Consultant]:
        """Gets a page of consultants"""

        if cursor:
            filter["_id"] = {"$gt": ObjectId(cursor)}

        consultants = self.consultant_get_all_records(filter, limit=limit)

        item_count = len(consultants)
        next_cursor = None

        if item_count > 0:
            count_query = filter.copy()
            count_query["_id"] = {"$gt": ObjectId(consultants[-1].id)}
            last_item = storage.consultant_get_record(count_query)
            if last_item and last_item.id != consultants[-1].id:
                next_cursor = consultants[-1].id

        consultants_page = Page(
            items=consultants,
            item_count=item_count,
            next_cursor=next_cursor,
        )

        return consultants_page

    def consultant_verify_record(
        self, filter: Dict
    ) -> s_consultant.Consultant:
        """
        Gets a consultant record using the filter
        and raises an error if a matching record is not found
        """

        consultant = self.consultant_get_record(filter)

        if consultant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultant not found",
            )

        return consultant

    def consultant_update_record(self, filter: Dict, update: Dict):
        """Updates a consultant record"""
        self.consultant_verify_record(filter)

        for key in ["_id", "user_id"]:
            if key in update:
                raise KeyError(f"Invalid Key. KEY {key} cannot be changed")
        update["date_modified"] = datetime.now(UTC)

        self.db["consultants"].update_one(filter, {"$set": update})

    def consultant_advanced_update_record(self, filter: Dict, update: Dict):
        """Updates a consultant record with more complex parameters"""
        self.consultant_verify_record(filter)

        if "$set" in update:
            update["$set"]["date_modified"] = datetime.now(UTC)
        else:
            update["$set"] = {"date_modified": datetime.now(UTC)}

        return self.db["consultants"].update_one(filter, update)

    def consultant_delete_record(self, filter: Dict):
        """Deletes a consultant record"""
        consultant = self.consultant_verify_record(filter)

        self.db["consultants"].delete_one(filter)

        for id in [consultant.resume_file_id, consultant.profile_picture_id]:
            self.file_delete_record({"_id": id})


storage = MongoStorage()
