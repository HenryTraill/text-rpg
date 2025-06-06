# Import all models to ensure they're registered with SQLModel.metadata
from .user import User, UserSession, UserRole, UserStatus
from .character import Character, CharacterLocation
from .skill import Skill, CharacterSkill, SkillCategory
from .inventory import Item, InventorySlot, ItemType, ItemRarity, EquipmentSlot
from .world import Zone, Location, WorldEvent, ZoneInstance
from .social import Guild, GuildMember, GuildRole, Party, Friendship
from .chat import ChatChannel, Message, MessageHistory, ChannelMembership
from .combat import CombatSession, CombatAction, CombatParticipant, CombatResult
from .economy import Trade, Auction, NPCMerchant, CraftingRecipe

__all__ = [
    # User models
    "User", "UserSession", "UserRole", "UserStatus",
    # Character models
    "Character", "CharacterLocation",
    # Skill models
    "Skill", "CharacterSkill", "SkillCategory",
    # Inventory models
    "Item", "InventorySlot", "ItemType", "ItemRarity", "EquipmentSlot",
    # World models
    "Zone", "Location", "WorldEvent", "ZoneInstance",
    # Social models
    "Guild", "GuildMember", "GuildRole", "Party", "Friendship",
    # Chat models
    "ChatChannel", "Message", "MessageHistory", "ChannelMembership",
    # Combat models
    "CombatSession", "CombatAction", "CombatParticipant", "CombatResult",
    # Economy models
    "Trade", "Auction", "NPCMerchant", "CraftingRecipe",
]