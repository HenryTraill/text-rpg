from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from uuid import UUID, uuid4
from app.core.datetime_utils import utc_now

if TYPE_CHECKING:
    from .user import User
    from .world import Zone
    from .skill import CharacterSkill
    from .inventory import InventorySlot
    from .social import GuildMember, PartyMember
    from .combat import CombatParticipant


class Character(SQLModel, table=True):
    """
    Character model representing a player's character in the game.

    Each user can have multiple characters with individual stats and progression.
    """

    __tablename__ = "characters"

    # Primary Key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Foreign Keys
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # Character identity
    name: str = Field(index=True, unique=True, min_length=3, max_length=20)
    description: Optional[str] = Field(default=None, max_length=500)

    # Core stats
    level: int = Field(default=1, ge=1, le=100)
    experience: int = Field(default=0, ge=0)
    experience_to_next_level: int = Field(default=100)

    # Health and Mana
    health: int = Field(default=100, ge=0)
    max_health: int = Field(default=100, ge=1)
    mana: int = Field(default=50, ge=0)
    max_mana: int = Field(default=50, ge=1)

    # Currency
    gold: int = Field(default=100, ge=0)

    # Character state
    is_online: bool = Field(default=False)
    is_in_combat: bool = Field(default=False)
    is_dead: bool = Field(default=False)

    # Location (current zone and coordinates)
    current_zone_id: UUID = Field(foreign_key="zones.id", index=True)
    x_coordinate: float = Field(default=0.0)
    y_coordinate: float = Field(default=0.0)

    # Character progression
    total_skill_points: int = Field(default=0)
    available_skill_points: int = Field(default=0)

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    last_login: Optional[datetime] = Field(default=None)
    last_logout: Optional[datetime] = Field(default=None)

    # Character preferences and settings
    settings: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON))

    # Relationships
    user: "User" = Relationship(back_populates="characters")
    current_zone: "Zone" = Relationship()
    skills: List["CharacterSkill"] = Relationship(back_populates="character")
    inventory_slots: List["InventorySlot"] = Relationship(back_populates="character")
    guild_memberships: List["GuildMember"] = Relationship(back_populates="character")
    party_memberships: List["PartyMember"] = Relationship(back_populates="character")
    combat_participants: List["CombatParticipant"] = Relationship(
        back_populates="character"
    )

    # Location history
    location_history: List["CharacterLocation"] = Relationship(
        back_populates="character"
    )


class CharacterLocation(SQLModel, table=True):
    """
    Character location history model for tracking movement and position changes.

    Maintains a history of character locations for analytics and debugging.
    """

    __tablename__ = "character_locations"

    # Primary Key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Foreign Keys
    character_id: UUID = Field(foreign_key="characters.id", index=True)
    zone_id: UUID = Field(foreign_key="zones.id", index=True)

    # Location data
    x_coordinate: float
    y_coordinate: float

    # Movement context
    movement_type: str = Field(default="walk")  # walk, teleport, combat, respawn
    previous_x: Optional[float] = Field(default=None)
    previous_y: Optional[float] = Field(default=None)

    # Timestamps
    timestamp: datetime = Field(default_factory=utc_now)

    # Relationships
    character: Character = Relationship(back_populates="location_history")
    zone: "Zone" = Relationship()
