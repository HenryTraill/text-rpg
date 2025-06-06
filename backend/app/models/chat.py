from sqlmodel import SQLModel, Field, Relationship
from typing import List
from datetime import datetime
from uuid import UUID, uuid4
from app.core.datetime_utils import utc_now


class ChatChannel(SQLModel, table=True):
    """Chat channel model"""

    __tablename__ = "chat_channels"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    channel_type: str = Field(default="general")  # general, guild, party, private
    created_at: datetime = Field(default_factory=utc_now)

    # Relationships
    messages: List["Message"] = Relationship(back_populates="channel")


class Message(SQLModel, table=True):
    """Message model for chat"""

    __tablename__ = "messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    channel_id: UUID = Field(foreign_key="chat_channels.id", index=True)
    sender_id: UUID = Field(foreign_key="characters.id", index=True)
    content: str
    created_at: datetime = Field(default_factory=utc_now)

    # Relationships
    channel: ChatChannel = Relationship(back_populates="messages")


class MessageHistory(SQLModel, table=True):
    """Message history for persistence"""

    __tablename__ = "message_history"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    message_id: UUID = Field(foreign_key="messages.id", index=True)
    archived_at: datetime = Field(default_factory=utc_now)


class ChannelMembership(SQLModel, table=True):
    """Channel membership for access control"""

    __tablename__ = "channel_memberships"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    channel_id: UUID = Field(foreign_key="chat_channels.id", index=True)
    character_id: UUID = Field(foreign_key="characters.id", index=True)
    joined_at: datetime = Field(default_factory=utc_now)
