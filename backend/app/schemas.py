from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    title: str = Field(
        default="Nouvelle conversation",
        min_length=1,
        max_length=200,
    )


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    user_email: str | None = None
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=4000,
    )


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    model: str | None
    created_at: datetime


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse] = Field(
        default_factory=list,
    )