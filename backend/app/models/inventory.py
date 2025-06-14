from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from uuid import UUID, uuid4
import enum
from app.core.datetime_utils import utc_now

if TYPE_CHECKING:
    from .character import Character
from .schemas import ItemStats, ItemEffects, ItemAttributes


class ItemType(str, enum.Enum):
    """Item type enumeration for categorizing items"""

    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    MATERIAL = "material"
    TOOL = "tool"
    QUEST = "quest"
    CURRENCY = "currency"


class ItemRarity(str, enum.Enum):
    """Item rarity enumeration for item quality"""

    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class EquipmentSlot(str, enum.Enum):
    """Equipment slot enumeration for character equipment"""

    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    HEAD = "head"
    CHEST = "chest"
    LEGS = "legs"
    FEET = "feet"
    GLOVES = "gloves"
    RING_1 = "ring_1"
    RING_2 = "ring_2"
    NECK = "neck"
    BACK = "back"


class Item(SQLModel, table=True):
    """
    Item definition model containing all item templates in the game.

    Uses JSON fields for flexible stat storage and properties.
    """

    __tablename__ = "items"

    # Primary Key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Item identity
    name: str = Field(index=True)
    description: str
    item_type: ItemType = Field(index=True)
    rarity: ItemRarity = Field(default=ItemRarity.COMMON, index=True)

    # Item properties
    base_value: int = Field(default=0, ge=0)  # Base gold value
    max_stack_size: int = Field(default=1, ge=1)  # How many can stack
    weight: float = Field(default=1.0, ge=0.0)  # Weight for inventory limits

    # Equipment properties (if applicable)
    equipment_slot: Optional[EquipmentSlot] = Field(default=None)
    required_level: int = Field(default=1, ge=1)
    required_skills: Optional[dict] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )

    # Item stats and effects (flexible JSON storage)
    stats: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON))
    effects: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON))
    attributes: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON))

    # Durability system
    max_durability: Optional[int] = Field(default=None)
    repair_cost_multiplier: float = Field(default=0.1)

    # Item flags
    is_tradeable: bool = Field(default=True)
    is_droppable: bool = Field(default=True)
    is_consumable: bool = Field(default=False)
    is_unique: bool = Field(default=False)  # Only one can be owned

    # Crafting
    crafting_recipe_id: Optional[UUID] = Field(default=None)
    crafting_skill_required: Optional[str] = Field(default=None)

    # Item metadata
    icon_path: Optional[str] = Field(default=None)
    lore_text: Optional[str] = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Relationships
    inventory_slots: List["InventorySlot"] = Relationship(back_populates="item")


class InventorySlot(SQLModel, table=True):
    """
    Character inventory slot model linking characters to items.

    Represents individual items in a character's inventory with quantity and condition.
    """

    __tablename__ = "inventory_slots"

    # Primary Key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Foreign Keys
    character_id: UUID = Field(foreign_key="characters.id", index=True)
    item_id: UUID = Field(foreign_key="items.id", index=True)

    # Slot properties
    slot_number: int = Field(ge=0)  # Position in inventory grid
    quantity: int = Field(default=1, ge=1)

    # Item condition
    durability: Optional[int] = Field(default=None)  # Current durability
    condition: float = Field(default=1.0, ge=0.0, le=1.0)  # 0.0 to 1.0

    # Equipment status
    is_equipped: bool = Field(default=False)
    equipped_slot: Optional[EquipmentSlot] = Field(default=None)

    # Item customization
    custom_name: Optional[str] = Field(default=None)
    enchantments: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON))

    # Item binding
    is_bound: bool = Field(default=False)
    bound_to_character: bool = Field(default=False)

    # Timestamps
    acquired_at: datetime = Field(default_factory=utc_now)
    last_used: Optional[datetime] = Field(default=None)

    # Relationships
    character: "Character" = Relationship(back_populates="inventory_slots")
    item: Item = Relationship(back_populates="inventory_slots")


# Starter item definitions for seeding
STARTER_ITEMS = [
    # Basic Weapons
    {
        "name": "Iron Sword",
        "description": "A basic iron sword suitable for new adventurers.",
        "item_type": ItemType.WEAPON,
        "rarity": ItemRarity.COMMON,
        "base_value": 50,
        "weight": 3.0,
        "equipment_slot": EquipmentSlot.MAIN_HAND,
        "required_level": 1,
        "stats": ItemStats(damage=10, accuracy=5).model_dump(),
        "max_durability": 100,
    },
    # Basic Armor
    {
        "name": "Leather Tunic",
        "description": "Simple leather armor providing basic protection.",
        "item_type": ItemType.ARMOR,
        "rarity": ItemRarity.COMMON,
        "base_value": 30,
        "weight": 2.0,
        "equipment_slot": EquipmentSlot.CHEST,
        "required_level": 1,
        "stats": ItemStats(armor=5, health_bonus=10).model_dump(),
        "max_durability": 80,
    },
    # Consumables
    {
        "name": "Health Potion",
        "description": "Restores 50 health points when consumed.",
        "item_type": ItemType.CONSUMABLE,
        "rarity": ItemRarity.COMMON,
        "base_value": 10,
        "weight": 0.5,
        "max_stack_size": 10,
        "is_consumable": True,
        "effects": ItemEffects(heal=50).model_dump(),
    },
    # Materials
    {
        "name": "Iron Ore",
        "description": "Raw iron ore used in smithing.",
        "item_type": ItemType.MATERIAL,
        "rarity": ItemRarity.COMMON,
        "base_value": 5,
        "weight": 1.0,
        "max_stack_size": 50,
        "attributes": ItemAttributes(crafting_material=True).model_dump(),
    },
    # Tools
    {
        "name": "Iron Pickaxe",
        "description": "A sturdy pickaxe for mining operations.",
        "item_type": ItemType.TOOL,
        "rarity": ItemRarity.COMMON,
        "base_value": 25,
        "weight": 4.0,
        "required_skills": {"Mining": 1},
        "stats": ItemStats(mining_speed=1.2).model_dump(),
        "max_durability": 200,
    },
]
