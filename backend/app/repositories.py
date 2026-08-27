from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Conversation, Message


def create_conversation(
    database_session: Session,
    title: str = "Nouvelle conversation",
    user_email: str | None = None,
) -> Conversation:
    clean_title = title.strip() or "Nouvelle conversation"

    conversation = Conversation(
        title=clean_title,
        user_email=user_email,
    )

    database_session.add(conversation)
    database_session.commit()
    database_session.refresh(conversation)

    return conversation


def list_conversations(
    database_session: Session,
    user_email: str | None = None,
) -> list[Conversation]:
    statement = select(Conversation)

    if user_email:
        statement = statement.where(Conversation.user_email == user_email)
    else:
        # Sans auth: on renvoie uniquement les conversations anonymes
        statement = statement.where(Conversation.user_email.is_(None))

    statement = statement.order_by(Conversation.updated_at.desc())

    return list(
        database_session.scalars(statement).all()
    )


def get_conversation(
    database_session: Session,
    conversation_id: UUID,
) -> Conversation | None:
    statement = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )

    return database_session.scalar(statement)


def add_message(
    database_session: Session,
    conversation: Conversation,
    role: str,
    content: str,
    model: str | None = None,
) -> Message:
    if role not in {"user", "assistant"}:
        raise ValueError("Le rôle du message est invalide")

    clean_content = content.strip()

    if not clean_content:
        raise ValueError("Le contenu du message est vide")

    message = Message(
        conversation_id=conversation.id,
        role=role,
        content=clean_content,
        model=model,
    )

    conversation.updated_at = datetime.now(timezone.utc)

    try:
        database_session.add(message)
        database_session.add(conversation)
        database_session.commit()
        database_session.refresh(message)

    except Exception:
        database_session.rollback()
        raise

    return message


def add_exchange(
    database_session: Session,
    conversation: Conversation,
    user_content: str,
    assistant_content: str,
    model: str,
) -> tuple[Message, Message]:
    clean_user_content = user_content.strip()
    clean_assistant_content = assistant_content.strip()

    if not clean_user_content:
        raise ValueError("Le message utilisateur est vide")

    if not clean_assistant_content:
        raise ValueError("La réponse de l'assistant est vide")

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=clean_user_content,
        model=None,
    )

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=clean_assistant_content,
        model=model,
    )

    conversation.updated_at = datetime.now(timezone.utc)

    try:
        database_session.add_all(
            [
                user_message,
                assistant_message,
                conversation,
            ]
        )

        database_session.commit()
        database_session.refresh(user_message)
        database_session.refresh(assistant_message)

    except Exception:
        database_session.rollback()
        raise

    return user_message, assistant_message


def delete_conversation(
    database_session: Session,
    conversation: Conversation,
) -> None:
    try:
        database_session.delete(conversation)
        database_session.commit()

    except Exception:
        database_session.rollback()
        raise