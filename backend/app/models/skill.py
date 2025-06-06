from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from uuid import UUID, uuid4
import enum
from app.core.datetime_utils import utc_now

if TYPE_CHECKING:
    from .character import Character
from .schemas import SkillBonuses, SkillAbilities


class SkillCategory(str, enum.Enum):
    """Skill category enumeration - 4 main categories"""

    COMBAT = "combat"
    GATHERING = "gathering"
    CRAFTING = "crafting"
    SOCIAL = "social"


class Skill(SQLModel, table=True):
    """
    Skill definition model containing all available skills in the game.

    Defines the 20 skills across 4 categories with their properties and prerequisites.
    """

    __tablename__ = "skills"

    # Primary Key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Skill identity
    name: str = Field(index=True, unique=True)
    description: str
    category: SkillCategory = Field(index=True)

    # Skill mechanics
    max_level: int = Field(default=100)
    base_experience_required: int = Field(default=100)
    experience_multiplier: float = Field(default=1.1)  # Experience scaling per level

    # Prerequisites
    prerequisite_skills: Optional[dict] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )
    min_character_level: int = Field(default=1)

    # Skill effects and bonuses
    stat_bonuses: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON))
    abilities: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON))

    # Display order and grouping
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Relationships
    character_skills: List["CharacterSkill"] = Relationship(back_populates="skill")


class CharacterSkill(SQLModel, table=True):
    """
    Character skill progression model linking characters to their skill levels.

    Tracks individual character progress in each skill with experience and level.
    """

    __tablename__ = "character_skills"

    # Composite Primary Key
    character_id: UUID = Field(foreign_key="characters.id", primary_key=True)
    skill_id: UUID = Field(foreign_key="skills.id", primary_key=True)

    # Skill progression
    level: int = Field(default=1, ge=1, le=100)
    experience: int = Field(default=0, ge=0)
    experience_to_next_level: int = Field(default=100)

    # Training and practice
    times_used: int = Field(default=0)
    last_used: Optional[datetime] = Field(default=None)
    last_trained: Optional[datetime] = Field(default=None)

    # Skill mastery and bonuses
    mastery_bonus: float = Field(default=0.0)  # Additional bonus for skill mastery
    is_favorite: bool = Field(default=False)  # Player marked as favorite skill

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Relationships
    character: "Character" = Relationship(back_populates="skills")
    skill: Skill = Relationship(back_populates="character_skills")


# Skill definitions data - these will be seeded into the database
SKILL_DEFINITIONS = {
    # Combat Skills (5 skills)
    SkillCategory.COMBAT: [
        {
            "name": "Swordsmanship",
            "description": "Expertise in sword combat, increasing damage and accuracy with bladed weapons.",
            "stat_bonuses": SkillBonuses(melee_damage=2, accuracy=1).model_dump(),
            "abilities": SkillAbilities(
                abilities={"parry": True, "riposte": True}
            ).model_dump(),
        },
        {
            "name": "Archery",
            "description": "Proficiency with bows and crossbows, improving range and precision.",
            "stat_bonuses": {"ranged_damage": 2, "critical_chance": 1},
            "abilities": {"aimed_shot": True, "piercing_shot": True},
        },
        {
            "name": "Magic",
            "description": "Knowledge of arcane arts, enabling spellcasting and mana manipulation.",
            "stat_bonuses": {"spell_damage": 3, "mana": 5},
            "abilities": {"fireball": True, "heal": True, "shield": True},
        },
        {
            "name": "Defense",
            "description": "Mastery of defensive techniques, reducing damage taken and improving armor.",
            "stat_bonuses": {"armor": 2, "block_chance": 2},
            "abilities": {"shield_wall": True, "damage_reduction": True},
        },
        {
            "name": "Tactics",
            "description": "Strategic combat knowledge, providing initiative and team bonuses.",
            "stat_bonuses": {"initiative": 3, "team_bonus": 1},
            "abilities": {"battle_cry": True, "strategic_strike": True},
        },
    ],
    # Gathering Skills (5 skills)
    SkillCategory.GATHERING: [
        {
            "name": "Mining",
            "description": "Extraction of ores and precious metals from the earth.",
            "stat_bonuses": {"mining_speed": 2, "ore_quality": 1},
            "abilities": {"vein_detection": True, "efficient_extraction": True},
        },
        {
            "name": "Herbalism",
            "description": "Collection and identification of plants and herbs for crafting.",
            "stat_bonuses": {"gathering_speed": 2, "herb_quality": 1},
            "abilities": {"rare_herb_detection": True, "preservation": True},
        },
        {
            "name": "Fishing",
            "description": "Catching fish and aquatic resources from various water sources.",
            "stat_bonuses": {"catch_rate": 2, "fish_quality": 1},
            "abilities": {"fish_tracking": True, "net_fishing": True},
        },
        {
            "name": "Hunting",
            "description": "Tracking and hunting wild animals for meat, hides, and trophies.",
            "stat_bonuses": {"tracking": 2, "stealth": 1},
            "abilities": {"animal_tracking": True, "silent_movement": True},
        },
        {
            "name": "Exploration",
            "description": "Discovery of new locations, hidden treasures, and secret passages.",
            "stat_bonuses": {"movement_speed": 1, "detection": 2},
            "abilities": {"treasure_sense": True, "path_finding": True},
        },
    ],
    # Crafting Skills (5 skills)
    SkillCategory.CRAFTING: [
        {
            "name": "Smithing",
            "description": "Forging weapons and armor from metals and other materials.",
            "stat_bonuses": {"crafting_speed": 2, "item_durability": 2},
            "abilities": {"masterwork": True, "repair": True},
        },
        {
            "name": "Alchemy",
            "description": "Brewing potions and creating magical substances for various effects.",
            "stat_bonuses": {"potion_potency": 2, "brewing_speed": 1},
            "abilities": {"transmutation": True, "explosive_potions": True},
        },
        {
            "name": "Cooking",
            "description": "Preparation of food items that provide temporary stat bonuses.",
            "stat_bonuses": {"food_effects": 2, "cooking_speed": 1},
            "abilities": {"feast_preparation": True, "preservation": True},
        },
        {
            "name": "Tailoring",
            "description": "Creating clothing, robes, and cloth armor with magical properties.",
            "stat_bonuses": {"cloth_quality": 2, "enchantment_slots": 1},
            "abilities": {"magical_threading": True, "reinforcement": True},
        },
        {
            "name": "Enchanting",
            "description": "Imbuing items with magical properties and enhancing equipment.",
            "stat_bonuses": {"enchantment_power": 3, "enchantment_duration": 1},
            "abilities": {"soul_binding": True, "disenchantment": True},
        },
    ],
    # Social Skills (5 skills)
    SkillCategory.SOCIAL: [
        {
            "name": "Leadership",
            "description": "Inspiring and commanding others, improving party and guild effectiveness.",
            "stat_bonuses": {"party_bonus": 2, "command_range": 1},
            "abilities": {"rally": True, "inspire": True},
        },
        {
            "name": "Trading",
            "description": "Negotiation and commerce skills for better prices and deals.",
            "stat_bonuses": {"buy_discount": 2, "sell_bonus": 2},
            "abilities": {"appraisal": True, "bulk_discount": True},
        },
        {
            "name": "Diplomacy",
            "description": "Peaceful resolution of conflicts and improved NPC relations.",
            "stat_bonuses": {"npc_reputation": 2, "quest_rewards": 1},
            "abilities": {"negotiation": True, "peace_treaty": True},
        },
        {
            "name": "Intimidation",
            "description": "Using fear and presence to influence others and enemies.",
            "stat_bonuses": {"fear_resistance": 2, "intimidation_power": 2},
            "abilities": {"menacing_presence": True, "demoralize": True},
        },
        {
            "name": "Charisma",
            "description": "Personal magnetism and charm, improving social interactions.",
            "stat_bonuses": {"social_bonus": 2, "friend_limit": 10},
            "abilities": {"charm": True, "persuasion": True},
        },
    ],
}
