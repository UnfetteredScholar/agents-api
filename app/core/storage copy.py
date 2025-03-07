# from datetime import UTC, datetime
# from typing import Dict, List, Optional

# import gridfs
# import schemas.file as s_file
# from bson.objectid import ObjectId
# from core.config import settings
# from fastapi import HTTPException, status
# from pymongo import MongoClient
# from schemas import agent as s_agent
# from schemas import component as s_component
# from schemas import consultant as s_consultant
# from schemas import review as s_review
# from schemas.page import Page


# class MongoStorage:
#     """Storage class for interfacing with mongo db"""

#     def __init__(
#         self,
#         connection_string: str = settings.MONGODB_URI,
#         db_name: str = settings.DATABSE_NAME,
#     ):
#         """
#         Storage object with methods to Create, Read, Update,
#         Delete (CRUD) objects in the mongo database.
#         """
#         self.client = MongoClient(connection_string)
#         self.db = self.client[db_name]
#         self.fs = gridfs.GridFS(self.db)
#         self.agents_collection = self.db["agents"]

#     # agents
#     def agent_create_record(
#         self,
#         agent_data: s_agent.AgentBase,
#     ) -> str:
#         """Creates a agent record"""

#         agents_table = self.db["agents"]

#         date = datetime.now(UTC)
#         agent = agent_data.model_dump()
#         agent["date_created"] = date
#         agent["date_modified"] = date

#         id = str(agents_table.insert_one(agent).inserted_id)

#         return id

#     def agent_get_record(self, filter: Dict) -> Optional[s_agent.Agent]:
#         """Gets a agent record from the db using the supplied filter"""
#         agents = self.db["agents"]

#         if "_id" in filter and type(filter["_id"]) is str:
#             filter["_id"] = ObjectId(filter["_id"])

#         agent = agents.find_one(filter)

#         if agent:
#             agent = s_agent.Agent(**agent)

#         return agent

#     def agent_get_all_records(
#         self, filter: Dict, limit: int = 0
#     ) -> List[s_agent.Agent]:
#         """Gets all agent records from the db using the supplied filter"""
#         agents = self.db["agents"]

#         if "_id" in filter and type(filter["_id"]) is str:
#             filter["_id"] = ObjectId(filter["_id"])

#         agents_list = agents.find(filter).limit(limit=limit)
#         agents_out = []

#         for agent in agents_list:
#             agent = s_agent.Agent(**agent)
#             agents_out.append(agent)

#         return agents_out

#     def agent_get_page(
#         self, filter: Dict, limit: int = 0, cursor: Optional[str] = None
#     ) -> Page[s_agent.Agent]:
#         """Gets a page of agents"""

#         if cursor:
#             filter["_id"] = {"$gt": ObjectId(cursor)}

#         agents = self.agent_get_all_records(filter, limit=limit)

#         item_count = len(agents)
#         next_cursor = None

#         if item_count > 0:
#             count_query = filter.copy()
#             count_query["_id"] = {"$gt": ObjectId(agents[-1].id)}
#             last_item = storage.agent_get_record(count_query)
#             if last_item and last_item.id != agents[-1].id:
#                 next_cursor = agents[-1].id

#         agents_page = Page(
#             items=agents,
#             item_count=item_count,
#             next_cursor=next_cursor,
#         )

#         return agents_page

#     def agent_verify_record(self, filter: Dict) -> s_agent.Agent:
#         """
#         Gets a agent record using the filter
#         and raises an error if a matching record is not found
#         """

#         agent = self.agent_get_record(filter)

#         if agent is None:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Agent not found",
#             )

#         return agent

#     def agent_update_record(self, filter: Dict, update: Dict):
#         """Updates a agent record"""
#         self.agent_verify_record(filter)

#         for key in ["_id", "user_id"]:
#             if key in update:
#                 raise KeyError(f"Invalid Key. KEY {key} cannot be changed")
#         update["date_modified"] = datetime.now(UTC)

#         self.db["agents"].update_one(filter, {"$set": update})

#     def agent_advanced_update_record(self, filter: Dict, update: Dict):
#         """Updates a agent record with more complex parameters"""
#         self.agent_verify_record(filter)

#         if "$set" in update:
#             update["$set"]["date_modified"] = datetime.now(UTC)
#         else:
#             update["$set"] = {"date_modified": datetime.now(UTC)}

#         return self.db["agents"].update_one(filter, update)

#     def agent_delete_record(self, filter: Dict):
#         """Deletes a agent record"""
#         agent = self.agent_verify_record(filter)

#         self.db["agents"].delete_one(filter)

#         for file in storage.file_get_all_records({"agent_id": agent.id}):
#             self.file_delete_record({"_id": file.id})

#     # files
#     def file_create_record(
#         self,
#         data: bytes,
#         file_data: s_file.FileMetadata,
#     ) -> str:
#         """Creates a file record"""
#         files_table = self.db["files"]

#         gridfs_id = str(self.fs.put(data, **file_data.model_dump()))
#         date = datetime.now(UTC)
#         file = file_data.model_dump()
#         file["gridfs_id"] = gridfs_id
#         file["date_created"] = date
#         file["date_modified"] = date

#         id = str(files_table.insert_one(file).inserted_id)

#         return id

#     def file_get_record(self, filter: Dict) -> Optional[s_file.File]:
#         """Gets a file record from the db using the supplied filter"""
#         files = self.db["files"]

#         if "_id" in filter and type(filter["_id"]) is str:
#             filter["_id"] = ObjectId(filter["_id"])

#         file = files.find_one(filter)

#         if file:
#             file = s_file.File(**file)
#             if file.restrict_access:
#                 file.download_link = f"/api/v1/files/{file.id}/download"
#             else:
#                 file.download_link = (
#                     f"/api/v1/files/{file.id}/unrestricted/download"
#                 )

#         return file

#     def file_get_all_records(self, filter: Dict) -> List[s_file.File]:
#         """Gets all file records from the db using the supplied filter"""
#         files = self.db["files"]

#         if "_id" in filter and type(filter["_id"]) is str:
#             filter["_id"] = ObjectId(filter["_id"])

#         files_list = files.find(filter)
#         files_output = []

#         for file in files_list:
#             file = s_file.File(**file)
#             if file.restrict_access:
#                 file.download_link = f"/api/v1/files/{file.id}/download"
#             else:
#                 file.download_link = (
#                     f"/api/v1/files/{file.id}/unrestricted/download"
#                 )
#             files_output.append(file)

#         return files_output

#     def file_verify_record(self, filter: Dict) -> s_file.File:
#         """
#         Gets a file record using the filter
#         and raises an error if a matching record is not found
#         """

#         file = self.file_get_record(filter)

#         if file is None:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="File not found",
#             )

#         return file

#     def file_get_data(self, file_id: str) -> bytes:
#         """Gets the data of a file"""

#         file = storage.file_verify_record({"_id": file_id})

#         return self.fs.get(file_id=ObjectId(file.gridfs_id)).read()

#     def file_update_record(self, filter: Dict, update: Dict):
#         """Updates a file record"""
#         self.file_verify_record(filter)

#         for key in ["_id", "user_id", "project_id", "gridfs_id"]:
#             if key in update:
#                 raise KeyError(f"Invalid Key. KEY {key} cannot be changed")
#         update["date_modified"] = datetime.now(UTC)

#         self.db["files"].update_one(filter, {"$set": update})

#     def file_advanced_update_record(self, filter: Dict, update: Dict):
#         """Updates a file record with more complex parameters"""
#         self.file_verify_record(filter)

#         if "$set" in update:
#             update["$set"]["date_modified"] = datetime.now(UTC)
#         else:
#             update["$set"] = {"date_modified": datetime.now(UTC)}

#         return self.db["files"].update_one(filter, update)

#     def file_delete_record(self, filter: Dict):
#         """Deletes a file record"""
#         file = self.file_verify_record(filter)

#         self.db["files"].delete_one(filter)
#         self.fs.delete(file_id=ObjectId(file.gridfs_id))

#     # consultants
#     def consultant_create_record(
#         self,
#         consultant_data: s_consultant.ConsultantBase,
#     ) -> str:
#         """Creates a consultant record"""

#         consultants_table = self.db["consultants"]

#         date = datetime.now(UTC)
#         consultant = consultant_data.model_dump()
#         consultant["date_created"] = date
#         consultant["date_modified"] = date

#         id = str(consultants_table.insert_one(consultant).inserted_id)

#         return id

#     def consultant_get_record(
#         self, filter: Dict
#     ) -> Optional[s_consultant.Consultant]:
#         """Gets a consultant record from the db using the supplied filter"""
#         consultants = self.db["consultants"]

#         if "_id" in filter and type(filter["_id"]) is str:
#             filter["_id"] = ObjectId(filter["_id"])

#         consultant = consultants.find_one(filter)

#         if consultant:
#             consultant = s_consultant.Consultant(**consultant)

#         return consultant

#     def consultant_get_all_records(
#         self, filter: Dict, limit: int = 0
#     ) -> List[s_consultant.Consultant]:
#         """Gets all consultant records from the db using the supplied filter"""
#         consultants = self.db["consultants"]

#         if "_id" in filter and type(filter["_id"]) is str:
#             filter["_id"] = ObjectId(filter["_id"])

#         consultants_list = consultants.find(filter).limit(limit=limit)
#         consultants_out = []

#         for consultant in consultants_list:
#             consultant = s_consultant.Consultant(**consultant)
#             consultants_out.append(consultant)

#         return consultants_out

#     def consultant_get_page(
#         self, filter: Dict, limit: int = 0, cursor: Optional[str] = None
#     ) -> Page[s_consultant.Consultant]:
#         """Gets a page of consultants"""

#         if cursor:
#             filter["_id"] = {"$gt": ObjectId(cursor)}

#         consultants = self.consultant_get_all_records(filter, limit=limit)

#         item_count = len(consultants)
#         next_cursor = None

#         if item_count > 0:
#             count_query = filter.copy()
#             count_query["_id"] = {"$gt": ObjectId(consultants[-1].id)}
#             last_item = storage.consultant_get_record(count_query)
#             if last_item and last_item.id != consultants[-1].id:
#                 next_cursor = consultants[-1].id

#         consultants_page = Page(
#             items=consultants,
#             item_count=item_count,
#             next_cursor=next_cursor,
#         )

#         return consultants_page

#     def consultant_verify_record(
#         self, filter: Dict
#     ) -> s_consultant.Consultant:
#         """
#         Gets a consultant record using the filter
#         and raises an error if a matching record is not found
#         """

#         consultant = self.consultant_get_record(filter)

#         if consultant is None:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Consultant not found",
#             )

#         return consultant

#     def consultant_update_record(self, filter: Dict, update: Dict):
#         """Updates a consultant record"""
#         self.consultant_verify_record(filter)

#         for key in ["_id", "user_id"]:
#             if key in update:
#                 raise KeyError(f"Invalid Key. KEY {key} cannot be changed")
#         update["date_modified"] = datetime.now(UTC)

#         self.db["consultants"].update_one(filter, {"$set": update})

#     def consultant_advanced_update_record(self, filter: Dict, update: Dict):
#         """Updates a consultant record with more complex parameters"""
#         self.consultant_verify_record(filter)

#         if "$set" in update:
#             update["$set"]["date_modified"] = datetime.now(UTC)
#         else:
#             update["$set"] = {"date_modified": datetime.now(UTC)}

#         return self.db["consultants"].update_one(filter, update)

#     def consultant_delete_record(self, filter: Dict):
#         """Deletes a consultant record"""
#         consultant = self.consultant_verify_record(filter)

#         self.db["consultants"].delete_one(filter)

#         for id in [consultant.resume_file_id, consultant.profile_picture_id]:
#             self.file_delete_record({"_id": id})

#     # reviews
#     def review_create_record(
#         self,
#         review_data: s_review.ReviewBase,
#     ) -> str:
#         """Creates a review record"""

#         reviews_table = self.db["reviews"]

#         date = datetime.now(UTC)
#         review = review_data.model_dump()
#         review["date_created"] = date
#         review["date_modified"] = date

#         id = str(reviews_table.insert_one(review).inserted_id)

#         if review_data.target_type == s_review.TargetType.AGENT:
#             self.agent_advanced_update_record(
#                 filter={"_id": review_data.target_id},
#                 update={
#                     "$inc": {f"review_metrics.{review_data.reaction.value}": 1}
#                 },
#             )
#         elif review_data.target_type == s_review.TargetType.CONSULTANT:
#             self.consultant_advanced_update_record(
#                 filter={"_id": review_data.target_id},
#                 update={
#                     "$inc": {f"review_metrics.{review_data.reaction.value}": 1}
#                 },
#             )
#         else:
#             pass

#         return id

#     def review_get_record(self, filter: Dict) -> Optional[s_review.Review]:
#         """Gets a review record from the db using the supplied filter"""
#         reviews = self.db["reviews"]

#         if "_id" in filter and type(filter["_id"]) is str:
#             filter["_id"] = ObjectId(filter["_id"])

#         review = reviews.find_one(filter)

#         if review:
#             review = s_review.Review(**review)

#         return review

#     def review_get_all_records(
#         self, filter: Dict, limit: int = 0
#     ) -> List[s_review.Review]:
#         """Gets all review records from the db using the supplied filter"""
#         reviews = self.db["reviews"]

#         if "_id" in filter and type(filter["_id"]) is str:
#             filter["_id"] = ObjectId(filter["_id"])

#         reviews_list = reviews.find(filter).limit(limit=limit)
#         reviews_out = []

#         for review in reviews_list:
#             review = s_review.Review(**review)
#             reviews_out.append(review)

#         return reviews_out

#     def review_get_page(
#         self, filter: Dict, limit: int = 0, cursor: Optional[str] = None
#     ) -> Page[s_review.Review]:
#         """Gets a page of reviews"""

#         if cursor:
#             filter["_id"] = {"$gt": ObjectId(cursor)}

#         reviews = self.review_get_all_records(filter, limit=limit)

#         item_count = len(reviews)
#         next_cursor = None

#         if item_count > 0:
#             count_query = filter.copy()
#             count_query["_id"] = {"$gt": ObjectId(reviews[-1].id)}
#             last_item = storage.review_get_record(count_query)
#             if last_item and last_item.id != reviews[-1].id:
#                 next_cursor = reviews[-1].id

#         reviews_page = Page(
#             items=reviews,
#             item_count=item_count,
#             next_cursor=next_cursor,
#         )

#         return reviews_page

#     def review_verify_record(self, filter: Dict) -> s_review.Review:
#         """
#         Gets a review record using the filter
#         and raises an error if a matching record is not found
#         """

#         review = self.review_get_record(filter)

#         if review is None:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Review not found",
#             )

#         return review

#     def review_update_record(self, filter: Dict, update: Dict):
#         """Updates a review record"""
#         self.review_verify_record(filter)

#         for key in ["_id", "user_id"]:
#             if key in update:
#                 raise KeyError(f"Invalid Key. KEY {key} cannot be changed")
#         update["date_modified"] = datetime.now(UTC)

#         self.db["reviews"].update_one(filter, {"$set": update})

#     def review_advanced_update_record(self, filter: Dict, update: Dict):
#         """Updates a review record with more complex parameters"""
#         self.review_verify_record(filter)

#         if "$set" in update:
#             update["$set"]["date_modified"] = datetime.now(UTC)
#         else:
#             update["$set"] = {"date_modified": datetime.now(UTC)}

#         return self.db["reviews"].update_one(filter, update)

#     def review_delete_record(self, filter: Dict):
#         """Deletes a review record"""
#         review = self.review_verify_record(filter)

#         self.db["reviews"].delete_one(filter)

#         if review.target_type == s_review.TargetType.AGENT:
#             self.agent_advanced_update_record(
#                 filter={"_id": review.target_id},
#                 update={
#                     "$inc": {f"review_metrics.{review.reaction.value}": -1}
#                 },
#             )
#         elif review.target_type == s_review.TargetType.CONSULTANT:
#             self.consultant_advanced_update_record(
#                 filter={"_id": review.target_id},
#                 update={
#                     "$inc": {f"review_metrics.{review.reaction.value}": -1}
#                 },
#             )
#         else:
#             pass

#     def component_create_record(
#         self,
#         component_data: s_component.ComponentBase,
#     ) -> str:
#         """Creates a component record"""

#         components_table = self.db["components"]

#         date = datetime.now(UTC)
#         component = component_data.model_dump()
#         component["date_created"] = date
#         component["date_modified"] = date

#         id = str(components_table.insert_one(component).inserted_id)

#         return id

#     def component_get_record(
#         self, filter: Dict
#     ) -> Optional[s_component.Component]:
#         """Gets a component record from the db using the supplied filter"""
#         components = self.db["components"]

#         if "_id" in filter and type(filter["_id"]) is str:
#             filter["_id"] = ObjectId(filter["_id"])

#         component = components.find_one(filter)

#         if component:
#             component = s_component.Component(**component)

#         return component

#     def component_get_all_records(
#         self, filter: Dict, limit: int = 0
#     ) -> List[s_component.Component]:
#         """Gets all component records from the db using the supplied filter"""
#         components = self.db["components"]

#         if "_id" in filter and type(filter["_id"]) is str:
#             filter["_id"] = ObjectId(filter["_id"])

#         components_list = components.find(filter).limit(limit=limit)
#         components_out = []

#         for component in components_list:
#             component = s_component.Component(**component)
#             components_out.append(component)

#         return components_out

#     def component_get_page(
#         self, filter: Dict, limit: int = 0, cursor: Optional[str] = None
#     ) -> Page[s_component.Component]:
#         """Gets a page of components"""

#         if cursor:
#             filter["_id"] = {"$gt": ObjectId(cursor)}

#         components = self.component_get_all_records(filter, limit=limit)

#         item_count = len(components)
#         next_cursor = None

#         if item_count > 0:
#             count_query = filter.copy()
#             count_query["_id"] = {"$gt": ObjectId(components[-1].id)}
#             last_item = storage.component_get_record(count_query)
#             if last_item and last_item.id != components[-1].id:
#                 next_cursor = components[-1].id

#         components_page = Page(
#             items=components,
#             item_count=item_count,
#             next_cursor=next_cursor,
#         )

#         return components_page

#     def component_verify_record(self, filter: Dict) -> s_component.Component:
#         """
#         Gets a component record using the filter
#         and raises an error if a matching record is not found
#         """

#         component = self.component_get_record(filter)

#         if component is None:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Component not found",
#             )

#         return component

#     def component_update_record(self, filter: Dict, update: Dict):
#         """Updates a component record"""
#         self.component_verify_record(filter)

#         for key in ["_id", "user_id"]:
#             if key in update:
#                 raise KeyError(f"Invalid Key. KEY {key} cannot be changed")
#         update["date_modified"] = datetime.now(UTC)

#         self.db["components"].update_one(filter, {"$set": update})

#     def component_advanced_update_record(self, filter: Dict, update: Dict):
#         """Updates a component record with more complex parameters"""
#         self.component_verify_record(filter)

#         if "$set" in update:
#             update["$set"]["date_modified"] = datetime.now(UTC)
#         else:
#             update["$set"] = {"date_modified": datetime.now(UTC)}

#         return self.db["components"].update_one(filter, update)

#     def component_delete_record(self, filter: Dict):
#         """Deletes a component record"""
#         component = self.component_verify_record(filter)

#         self.db["components"].delete_one(filter)

#         for file in storage.file_get_all_records(
#             {"component_id": component.id}
#         ):
#             self.file_delete_record({"_id": file.id})


# storage = MongoStorage()
