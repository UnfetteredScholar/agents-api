from datetime import timedelta

from core import storage
from core.authentication.auth_token import create_access_token
from schemas.agent import Agent, AgentOut
from schemas.component import Component
from schemas.consultant import Consultant, ConsultantOut
from schemas.document import Document


def convert_to_component_out(input: Component) -> Component:
    data = input.model_dump()
    for k in ["dependency_file", "logo"]:
        id = data[k]
        payload = {"sub": id, "id": id, "type": "file_access", "role": "none"}
        token = create_access_token(
            data=payload, expires_delta=timedelta(days=2)
        )
        data[k] = f"/api/v1/files/{token}/download"

    return Component(**data)


def convert_to_document_out(input: Document) -> Document:
    data = input.model_dump()
    for k in ["document_file"]:
        id = data[k]
        payload = {"sub": id, "id": id, "type": "file_access", "role": "none"}
        token = create_access_token(
            data=payload, expires_delta=timedelta(days=2)
        )
        data[k] = f"/api/v1/files/{token}/download"

    return Document(**data)


def convert_to_agent_out(input: Agent) -> AgentOut:
    data = input.model_dump()
    supporting_documents = [
        convert_to_document_out(doc)
        for doc in storage.documents.get_all({"owner_id": input.id})
    ]
    dependencies = []
    for id in input.dependencies:
        dependencies.append(
            convert_to_component_out(storage.components.verify({"_id": id}))
        )
    for k in ["thumbnail_image", "platform_file"]:
        id = data[k]
        payload = {"sub": id, "id": id, "type": "file_access", "role": "none"}
        token = create_access_token(
            data=payload, expires_delta=timedelta(days=2)
        )
        data[k] = f"/api/v1/files/{token}/download"

    data["dependencies"] = dependencies
    data["supporting_documents"] = supporting_documents

    return AgentOut(**data)


def convert_to_consultant_out(input: Consultant) -> ConsultantOut:
    """Converts form Consultant to ConsultantOut"""
    data = input.model_dump()
    supporting_documents = [
        convert_to_document_out(doc)
        for doc in storage.documents.get_all({"owner_id": input.id})
    ]
    data["supporting_documents"] = supporting_documents
    for k in ["thumbnail_image", "resume_upload"]:
        id = data[k]
        payload = {"sub": id, "id": id, "type": "file_access", "role": "none"}
        token = create_access_token(
            data=payload, expires_delta=timedelta(days=2)
        )
        data[k] = f"/api/v1/files/{token}/download"

    return ConsultantOut(**data)
