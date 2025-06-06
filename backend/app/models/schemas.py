"""
Pydantic schemas for JSON fields used in SQLModel entities.

These schemas provide type safety and validation for complex JSON data
stored in database columns.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


# User Settings Schemas
class ChatSettings(BaseModel):
    """User chat preferences and settings"""

    global_enabled: bool = True
    guild_enabled: bool = True
    party_enabled: bool = True
    trade_enabled: bool = True
    private_enabled: bool = True
    profanity_filter: bool = True
    message_sound: bool = True
    font_size: str = "medium"  # small, medium, large


class PrivacySettings(BaseModel):
    """User privacy settings"""

    show_online_status: bool = True
    allow_friend_requests: bool = True
    allow_party_invites: bool = True
    allow_guild_invites: bool = True
    show_location: bool = True
    show_level: bool = True


# Character Settings Schema
class CharacterSettings(BaseModel):
    """Character-specific game settings"""

    auto_loot: bool = True
    auto_sort_inventory: bool = False
    combat_auto_attack: bool = False
    movement_click_to_move: bool = True
    ui_theme: str = "default"
    hotkey_bindings: Dict[str, str] = Field(default_factory=dict)


# Skill System Schemas
class SkillPrerequisites(BaseModel):
    """Prerequisites for skill advancement"""

    required_skills: Dict[str, int] = Field(
        default_factory=dict
    )  # skill_name: required_level
    required_character_level: int = 1


class SkillBonuses(BaseModel):
    """Stat bonuses provided by a skill"""

    # Combat stats
    melee_damage: int = 0
    ranged_damage: int = 0
    spell_damage: int = 0
    accuracy: int = 0
    critical_chance: int = 0
    armor: int = 0
    block_chance: int = 0
    initiative: int = 0

    # Resource stats
    health: int = 0
    mana: int = 0

    # Gathering stats
    mining_speed: float = 0.0
    gathering_speed: float = 0.0
    catch_rate: int = 0

    # Crafting stats
    crafting_speed: float = 0.0
    item_durability: int = 0

    # Social stats
    party_bonus: int = 0
    npc_reputation: int = 0
    buy_discount: int = 0
    sell_bonus: int = 0


class SkillAbilities(BaseModel):
    """Special abilities unlocked by skills"""

    abilities: Dict[str, bool] = Field(default_factory=dict)
    special_actions: List[str] = Field(default_factory=list)


# Item System Schemas
class ItemStats(BaseModel):
    """Item statistics and bonuses"""

    # Weapon stats
    damage: int = 0
    accuracy: int = 0
    critical_chance: int = 0
    attack_speed: float = 1.0

    # Armor stats
    armor: int = 0
    magic_resistance: int = 0
    block_chance: int = 0

    # Resource bonuses
    health_bonus: int = 0
    mana_bonus: int = 0

    # Utility stats
    movement_speed: float = 0.0
    mining_speed: float = 0.0
    gathering_bonus: float = 0.0


class ItemEffects(BaseModel):
    """Item effects and special properties"""

    # Consumable effects
    heal: int = 0
    restore_mana: int = 0
    buff_duration: int = 0

    # Permanent effects
    permanent_bonuses: Dict[str, int] = Field(default_factory=dict)

    # Special effects
    on_hit_effects: List[str] = Field(default_factory=list)
    on_use_effects: List[str] = Field(default_factory=list)


class ItemAttributes(BaseModel):
    """Special item attributes and flags"""

    is_magical: bool = False
    is_cursed: bool = False
    is_quest_item: bool = False
    crafting_material: bool = False
    tool_type: Optional[str] = None
    set_bonus: Optional[str] = None


class Enchantments(BaseModel):
    """Item enchantments"""

    enchantments: Dict[str, int] = Field(
        default_factory=dict
    )  # enchantment_name: level
    durability_bonus: int = 0
    value_multiplier: float = 1.0


# World Events Schema
class WorldEventData(BaseModel):
    """World event configuration and data"""

    event_type: str
    affected_zones: List[str] = Field(default_factory=list)
    rewards: Dict[str, Any] = Field(default_factory=dict)
    conditions: Dict[str, Any] = Field(default_factory=dict)
    modifiers: Dict[str, float] = Field(default_factory=dict)


# Combat System Schemas
class CombatActionData(BaseModel):
    """Combat action input data"""

    action_type: str
    target_id: Optional[str] = None
    skill_used: Optional[str] = None
    item_used: Optional[str] = None
    modifiers: Dict[str, float] = Field(default_factory=dict)


class CombatResultData(BaseModel):
    """Combat action result data"""

    damage_dealt: int = 0
    damage_taken: int = 0
    hit_chance: float = 0.0
    critical_hit: bool = False
    status_effects: List[str] = Field(default_factory=list)
    skill_experience_gained: Dict[str, int] = Field(default_factory=dict)


class CombatRewards(BaseModel):
    """Combat completion rewards"""

    experience: int = 0
    gold: int = 0
    items: List[Dict[str, Any]] = Field(default_factory=list)
    skill_bonuses: Dict[str, int] = Field(default_factory=dict)


# Economy System Schemas
class TradeData(BaseModel):
    """Player-to-player trade data"""

    trader_1_items: List[Dict[str, Any]] = Field(default_factory=list)
    trader_2_items: List[Dict[str, Any]] = Field(default_factory=list)
    trader_1_gold: int = 0
    trader_2_gold: int = 0
    agreed_terms: Dict[str, Any] = Field(default_factory=dict)


class MerchantInventoryData(BaseModel):
    """NPC merchant inventory configuration"""

    items: List[Dict[str, Any]] = Field(default_factory=list)
    refresh_interval: int = 3600  # seconds
    stock_limits: Dict[str, int] = Field(default_factory=dict)
    special_offers: List[Dict[str, Any]] = Field(default_factory=list)


class MerchantPricingData(BaseModel):
    """NPC merchant pricing configuration"""

    buy_multiplier: float = 0.6  # Buy from players at 60% value
    sell_multiplier: float = 1.2  # Sell to players at 120% value
    reputation_modifiers: Dict[str, float] = Field(default_factory=dict)
    bulk_discounts: Dict[int, float] = Field(default_factory=dict)  # quantity: discount


class CraftingMaterials(BaseModel):
    """Crafting recipe material requirements"""

    required_items: Dict[str, int] = Field(default_factory=dict)  # item_name: quantity
    optional_items: Dict[str, int] = Field(default_factory=dict)
    tool_requirements: List[str] = Field(default_factory=list)
    consumables: Dict[str, int] = Field(default_factory=dict)
