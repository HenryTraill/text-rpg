from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, timezone
from uuid import UUID, uuid4


class CombatSession(SQLModel, table=True):
    """Combat session model for active combat"""
    __tablename__ = "combat_sessions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    status: str = Field(default="active")  # active, completed, cancelled
    turn_number: int = Field(default=1)
    current_turn_character_id: Optional[UUID] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    participants: List["CombatParticipant"] = Relationship(back_populates="combat_session")
    actions: List["CombatAction"] = Relationship(back_populates="combat_session")


class CombatParticipant(SQLModel, table=True):
    """Combat participant model"""
    __tablename__ = "combat_participants"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    combat_session_id: UUID = Field(foreign_key="combat_sessions.id", index=True)
    character_id: UUID = Field(foreign_key="characters.id", index=True)
    is_alive: bool = Field(default=True)
    initiative: int = Field(default=0)
    
    # Relationships
    combat_session: CombatSession = Relationship(back_populates="participants")
    character: "Character" = Relationship(back_populates="combat_participants")


class CombatAction(SQLModel, table=True):
    """Combat action model for turn actions"""
    __tablename__ = "combat_actions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    combat_session_id: UUID = Field(foreign_key="combat_sessions.id", index=True)
    character_id: UUID = Field(foreign_key="characters.id", index=True)
    action_type: str = Field(default="attack")  # attack, defend, skill, item
    target_id: Optional[UUID] = Field(default=None)
    turn_number: int
    action_data: Optional[dict] = Field(default_factory=dict, sa_column_kwargs={"type_": "JSON"})
    result_data: Optional[dict] = Field(default_factory=dict, sa_column_kwargs={"type_": "JSON"})
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    combat_session: CombatSession = Relationship(back_populates="actions")


class CombatResult(SQLModel, table=True):
    """Combat result model for match outcomes"""
    __tablename__ = "combat_results"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    combat_session_id: UUID = Field(foreign_key="combat_sessions.id", index=True)
    winner_id: Optional[UUID] = Field(foreign_key="characters.id")
    experience_awarded: int = Field(default=0)
    gold_awarded: int = Field(default=0)
    items_awarded: Optional[dict] = Field(default_factory=dict, sa_column_kwargs={"type_": "JSON"})
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))