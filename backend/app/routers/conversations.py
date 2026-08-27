from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.auth_routes import get_current_user
from app.database import get_database_session
from app.models import Conversation, User
from app.repositories import (
    create_conversation,
    get_conversation,
    list_conversations,
)
from app.schemas import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationResponse,
)


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


def get_owned_conversation(
    conversation_id: UUID,
    current_user: User,
    database_session: Session,
) -> Conversation:
    conversation = get_conversation(
        database_session=database_session,
        conversation_id=conversation_id,
    )

    if (
        conversation is None
        or conversation.user_email
        != current_user.email
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation introuvable.",
        )

    return conversation


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(
        get_current_user
    ),
    database_session: Session = Depends(
        get_database_session
    ),
):
    return create_conversation(
        database_session=database_session,
        title=payload.title,
        user_email=current_user.email,
    )


@router.get(
    "",
    response_model=list[ConversationResponse],
)
def get_all_conversations(
    current_user: User = Depends(
        get_current_user
    ),
    database_session: Session = Depends(
        get_database_session
    ),
):
    return list_conversations(
        database_session=database_session,
        user_email=current_user.email,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
)
def get_conversation_by_id(
    conversation_id: UUID,
    current_user: User = Depends(
        get_current_user
    ),
    database_session: Session = Depends(
        get_database_session
    ),
):
    return get_owned_conversation(
        conversation_id=conversation_id,
        current_user=current_user,
        database_session=database_session,
    )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_conversation(
    conversation_id: UUID,
    current_user: User = Depends(
        get_current_user
    ),
    database_session: Session = Depends(
        get_database_session
    ),
) -> Response:
    conversation = get_owned_conversation(
        conversation_id=conversation_id,
        current_user=current_user,
        database_session=database_session,
    )

    database_session.delete(
        conversation
    )

    database_session.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
