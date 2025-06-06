from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4


class Trade(SQLModel, table=True):
    """Trade model for player-to-player trading"""

    __tablename__ = "trades"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    trader_1_id: UUID = Field(foreign_key="characters.id", index=True)
    trader_2_id: UUID = Field(foreign_key="characters.id", index=True)
    status: str = Field(default="pending")  # pending, completed, cancelled
    trade_data: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    completed_at: Optional[datetime] = Field(default=None)


class Auction(SQLModel, table=True):
    """Auction model for server-wide marketplace"""

    __tablename__ = "auctions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    seller_id: UUID = Field(foreign_key="characters.id", index=True)
    item_id: UUID = Field(foreign_key="items.id", index=True)
    starting_price: int = Field(ge=0)
    current_bid: int = Field(default=0, ge=0)
    buyout_price: Optional[int] = Field(default=None)
    highest_bidder_id: Optional[UUID] = Field(default=None)
    status: str = Field(default="active")  # active, sold, expired, cancelled
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now())


class NPCMerchant(SQLModel, table=True):
    """NPC merchant model with dynamic pricing"""

    __tablename__ = "npc_merchants"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    location_id: UUID = Field(foreign_key="locations.id", index=True)
    merchant_type: str = Field(default="general")  # general, weapons, armor, etc.
    inventory_data: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON))
    pricing_data: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON))
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now())


class CraftingRecipe(SQLModel, table=True):
    """Crafting recipe model with material requirements"""

    __tablename__ = "crafting_recipes"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    result_item_id: UUID = Field(foreign_key="items.id", index=True)
    required_skill: str
    required_skill_level: int = Field(default=1, ge=1)
    materials_required: dict = Field(sa_column=Column(JSON))
    crafting_time: int = Field(default=30)  # seconds
    success_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    experience_gained: int = Field(default=10, ge=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now())
