from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
import enum


class GuildRole(str, enum.Enum):
    """Guild role enumeration"""

    MEMBER = "member"
    OFFICER = "officer"
    LEADER = "leader"


class Guild(SQLModel, table=True):
    """Guild model for player organizations"""

    __tablename__ = "guilds"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now())

    # Relationships
    members: List["GuildMember"] = Relationship(back_populates="guild")


class GuildMember(SQLModel, table=True):
    """Guild membership model"""

    __tablename__ = "guild_members"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    guild_id: UUID = Field(foreign_key="guilds.id", index=True)
    character_id: UUID = Field(foreign_key="characters.id", index=True)
    role: GuildRole = Field(default=GuildRole.MEMBER)
    joined_at: datetime = Field(default_factory=lambda: datetime.now())

    # Relationships
    guild: Guild = Relationship(back_populates="members")
    character: "Character" = Relationship(back_populates="guild_memberships")


class Party(SQLModel, table=True):
    """Party model for temporary groups"""

    __tablename__ = "parties"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: Optional[str] = Field(default=None)
    leader_id: UUID = Field(foreign_key="characters.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now())


class PartyMember(SQLModel, table=True):
    """Party membership model"""

    __tablename__ = "party_members"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    party_id: UUID = Field(foreign_key="parties.id", index=True)
    character_id: UUID = Field(foreign_key="characters.id", index=True)
    joined_at: datetime = Field(default_factory=lambda: datetime.now())

    # Relationships
    character: "Character" = Relationship(back_populates="party_memberships")


class Friendship(SQLModel, table=True):
    """Friendship model for player connections"""

    __tablename__ = "friendships"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    character_1_id: UUID = Field(foreign_key="characters.id", index=True)
    character_2_id: UUID = Field(foreign_key="characters.id", index=True)
    status: str = Field(default="pending")  # pending, accepted, blocked
    created_at: datetime = Field(default_factory=lambda: datetime.now())
