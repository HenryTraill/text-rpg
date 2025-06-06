from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4


class Zone(SQLModel, table=True):
    """
    Zone model representing different areas in the game world.

    Zones contain characters and define boundaries for gameplay areas.
    """

    __tablename__ = "zones"

    # Primary Key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Zone identity
    name: str = Field(index=True, unique=True)
    description: str

    # Zone boundaries
    min_x: float = Field(default=0.0)
    max_x: float = Field(default=1000.0)
    min_y: float = Field(default=0.0)
    max_y: float = Field(default=1000.0)

    # Zone properties
    level_requirement: int = Field(default=1, ge=1)
    is_pvp_enabled: bool = Field(default=False)
    is_safe_zone: bool = Field(default=False)
    max_players: Optional[int] = Field(default=None)

    # Zone settings
    respawn_x: float = Field(default=500.0)
    respawn_y: float = Field(default=500.0)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())

    # Relationships
    characters: List["Character"] = Relationship(back_populates="current_zone")
    location_history: List["CharacterLocation"] = Relationship(back_populates="zone")


class Location(SQLModel, table=True):
    """
    Location model for specific points of interest within zones.

    Represents named locations, NPCs, and interactive objects.
    """

    __tablename__ = "locations"

    # Primary Key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Foreign Keys
    zone_id: UUID = Field(foreign_key="zones.id", index=True)

    # Location identity
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    location_type: str = Field(default="landmark")  # landmark, npc, shop, etc.

    # Coordinates
    x_coordinate: float
    y_coordinate: float

    # Location properties
    interaction_radius: float = Field(default=5.0)
    is_active: bool = Field(default=True)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())

    # Relationships
    zone: Zone = Relationship()


class WorldEvent(SQLModel, table=True):
    """
    World event model for server-wide events and activities.
    """

    __tablename__ = "world_events"

    # Primary Key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Event identity
    name: str = Field(index=True)
    description: str
    event_type: str = Field(default="general")

    # Event timing
    start_time: datetime
    end_time: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=False)

    # Event data
    event_data: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON))

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now())


class ZoneInstance(SQLModel, table=True):
    """
    Zone instance model for handling multiple instances of the same zone.
    """

    __tablename__ = "zone_instances"

    # Primary Key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Foreign Keys
    zone_id: UUID = Field(foreign_key="zones.id", index=True)

    # Instance properties
    instance_name: str
    current_players: int = Field(default=0)
    max_players: int = Field(default=100)
    is_active: bool = Field(default=True)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now())

    # Relationships
    zone: Zone = Relationship()
