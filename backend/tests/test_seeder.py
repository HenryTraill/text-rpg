"""
Tests for database seeder functionality.

Validates that the seeder properly populates the database with initial game data.
"""

import pytest
from sqlmodel import select

from app.core.seeder import (
    seed_skills, seed_starter_zone, seed_starter_items,
    seed_chat_channels, seed_npc_merchant, seed_database
)
from app.models import *


class TestSkillSeeding:
    """Test skill seeding functionality."""
    
    async def test_seed_skills(self, db_session):
        """Test that all 20 skills are seeded correctly."""
        await seed_skills(db_session)
        
        # Check total count (at least 20, may have more from other tests)
        result = await db_session.execute(select(Skill))
        skills = result.scalars().all()
        assert len(skills) >= 20
        
        # Check categories (at least 5 of each, may have more from other tests)
        combat_result = await db_session.execute(
            select(Skill).where(Skill.category == SkillCategory.COMBAT)
        )
        combat_skills = combat_result.scalars().all()
        assert len(combat_skills) >= 5
        
        gathering_result = await db_session.execute(
            select(Skill).where(Skill.category == SkillCategory.GATHERING)
        )
        gathering_skills = gathering_result.scalars().all()
        assert len(gathering_skills) >= 5
        
        crafting_result = await db_session.execute(
            select(Skill).where(Skill.category == SkillCategory.CRAFTING)
        )
        crafting_skills = crafting_result.scalars().all()
        assert len(crafting_skills) >= 5
        
        social_result = await db_session.execute(
            select(Skill).where(Skill.category == SkillCategory.SOCIAL)
        )
        social_skills = social_result.scalars().all()
        assert len(social_skills) >= 5
    
    async def test_seed_skills_idempotent(self, db_session):
        """Test that seeding skills multiple times doesn't create duplicates."""
        await seed_skills(db_session)
        first_count = len((await db_session.execute(select(Skill))).scalars().all())
        
        await seed_skills(db_session)  # Run again
        
        result = await db_session.execute(select(Skill))
        skills = result.scalars().all()
        assert len(skills) == first_count  # Should still be the same count
    
    async def test_seeded_skills_have_valid_data(self, db_session):
        """Test that seeded skills have valid data structures."""
        await seed_skills(db_session)
        
        result = await db_session.execute(select(Skill))
        skills = result.scalars().all()
        
        for skill in skills:
            assert skill.name is not None
            assert len(skill.name) > 0
            assert skill.description is not None
            assert len(skill.description) > 0
            assert skill.category in [e for e in SkillCategory]
            assert skill.max_level == 100
            assert skill.base_experience_required == 100
            assert skill.experience_multiplier == 1.1
            assert skill.is_active is True
            assert isinstance(skill.stat_bonuses, dict)
            assert isinstance(skill.abilities, dict)
    
    async def test_swordsmanship_skill_seeded(self, db_session):
        """Test that the Swordsmanship skill is seeded with correct data."""
        await seed_skills(db_session)
        
        result = await db_session.execute(
            select(Skill).where(Skill.name == "Swordsmanship")
        )
        swordsmanship = result.scalar_one_or_none()
        
        assert swordsmanship is not None
        assert swordsmanship.category == SkillCategory.COMBAT
        assert swordsmanship.description == "Expertise in sword combat, increasing damage and accuracy with bladed weapons."
        assert "melee_damage" in swordsmanship.stat_bonuses
        assert "accuracy" in swordsmanship.stat_bonuses
        assert "parry" in swordsmanship.abilities["abilities"]
        assert "riposte" in swordsmanship.abilities["abilities"]


class TestZoneSeeding:
    """Test zone and location seeding functionality."""
    
    async def test_seed_starter_zone(self, db_session):
        """Test that starter zone and locations are seeded correctly."""
        zone = await seed_starter_zone(db_session)
        
        assert zone is not None
        assert zone.name == "Starter Town"
        assert zone.description == "A peaceful town where new adventurers begin their journey."
        assert zone.is_safe_zone is True
        assert zone.level_requirement == 1
        
        # Check locations
        result = await db_session.execute(
            select(Location).where(Location.zone_id == zone.id)
        )
        locations = result.scalars().all()
        assert len(locations) == 4
        
        location_names = [loc.name for loc in locations]
        assert "Town Center" in location_names
        assert "General Store" in location_names
        assert "Training Grounds" in location_names
        assert "Mine Entrance" in location_names
    
    async def test_seed_starter_zone_idempotent(self, db_session):
        """Test that seeding starter zone multiple times doesn't create duplicates."""
        zone1 = await seed_starter_zone(db_session)
        initial_zone_count = len((await db_session.execute(select(Zone))).scalars().all())
        initial_location_count = len((await db_session.execute(select(Location))).scalars().all())
        
        zone2 = await seed_starter_zone(db_session)  # Run again
        
        assert zone1.id == zone2.id  # Should return the same zone
        
        # Check that zone count didn't increase
        result = await db_session.execute(select(Zone))
        zones = result.scalars().all()
        assert len(zones) == initial_zone_count
        
        # Check that location count didn't increase
        result = await db_session.execute(select(Location))
        locations = result.scalars().all()
        assert len(locations) == initial_location_count


class TestItemSeeding:
    """Test item seeding functionality."""
    
    async def test_seed_starter_items(self, db_session):
        """Test that starter items are seeded correctly."""
        await seed_starter_items(db_session)
        
        result = await db_session.execute(select(Item))
        items = result.scalars().all()
        assert len(items) >= 5  # At least 5, may have more from other tests
        
        item_names = [item.name for item in items]
        assert "Iron Sword" in item_names
        assert "Leather Tunic" in item_names
        assert "Health Potion" in item_names
        assert "Iron Ore" in item_names
        assert "Iron Pickaxe" in item_names
    
    async def test_seed_starter_items_idempotent(self, db_session):
        """Test that seeding items multiple times doesn't create duplicates."""
        await seed_starter_items(db_session)
        first_count = len((await db_session.execute(select(Item))).scalars().all())
        
        await seed_starter_items(db_session)  # Run again
        
        result = await db_session.execute(select(Item))
        items = result.scalars().all()
        assert len(items) == first_count  # Should still be the same count
    
    async def test_seeded_items_have_valid_data(self, db_session):
        """Test that seeded items have valid data structures."""
        await seed_starter_items(db_session)
        
        result = await db_session.execute(select(Item))
        items = result.scalars().all()
        
        for item in items:
            assert item.name is not None
            assert len(item.name) > 0
            assert item.description is not None
            assert len(item.description) > 0
            assert item.item_type in [e for e in ItemType]
            assert item.rarity in [e for e in ItemRarity]
            assert item.base_value >= 0
            assert item.weight >= 0
            assert item.required_level >= 1
    
    async def test_iron_sword_item_seeded(self, db_session):
        """Test that Iron Sword is seeded with correct data."""
        await seed_starter_items(db_session)
        
        result = await db_session.execute(
            select(Item).where(Item.name == "Iron Sword")
        )
        iron_sword = result.scalar_one_or_none()
        
        assert iron_sword is not None
        assert iron_sword.item_type == ItemType.WEAPON
        assert iron_sword.rarity == ItemRarity.COMMON
        assert iron_sword.equipment_slot == EquipmentSlot.MAIN_HAND
        assert iron_sword.base_value == 50
        assert iron_sword.max_durability == 100
        assert iron_sword.stats["damage"] == 10
        assert iron_sword.stats["accuracy"] == 5


class TestChatChannelSeeding:
    """Test chat channel seeding functionality."""
    
    async def test_seed_chat_channels(self, db_session):
        """Test that chat channels are seeded correctly."""
        await seed_chat_channels(db_session)
        
        result = await db_session.execute(select(ChatChannel))
        channels = result.scalars().all()
        assert len(channels) >= 3  # At least 3, may have more from other tests
        
        channel_names = [channel.name for channel in channels]
        assert "Global" in channel_names
        assert "Help" in channel_names
        assert "Trade" in channel_names
    
    async def test_seed_chat_channels_idempotent(self, db_session):
        """Test that seeding channels multiple times doesn't create duplicates."""
        await seed_chat_channels(db_session)
        first_count = len((await db_session.execute(select(ChatChannel))).scalars().all())
        
        await seed_chat_channels(db_session)  # Run again
        
        result = await db_session.execute(select(ChatChannel))
        channels = result.scalars().all()
        assert len(channels) == first_count  # Should still be the same count


class TestNPCMerchantSeeding:
    """Test NPC merchant seeding functionality."""
    
    async def test_seed_npc_merchant(self, db_session):
        """Test that NPC merchant is seeded correctly."""
        # First seed the starter zone to get the general store location
        zone = await seed_starter_zone(db_session)
        
        result = await db_session.execute(
            select(Location).where(Location.name == "General Store")
        )
        general_store = result.scalar_one()
        
        await seed_npc_merchant(db_session, general_store)
        
        result = await db_session.execute(select(NPCMerchant))
        merchants = result.scalars().all()
        assert len(merchants) == 1
        
        merchant = merchants[0]
        assert merchant.name == "Merchant Tom"
        assert merchant.location_id == general_store.id
        assert merchant.merchant_type == "general"
        assert merchant.is_active is True
        assert isinstance(merchant.inventory_data, dict)
        assert isinstance(merchant.pricing_data, dict)
        assert "items" in merchant.inventory_data
        assert "buy_multiplier" in merchant.pricing_data
        assert "sell_multiplier" in merchant.pricing_data
    
    async def test_seed_npc_merchant_idempotent(self, db_session):
        """Test that seeding merchant multiple times doesn't create duplicates."""
        zone = await seed_starter_zone(db_session)
        
        result = await db_session.execute(
            select(Location).where(Location.name == "General Store")
        )
        general_store = result.scalar_one()
        
        await seed_npc_merchant(db_session, general_store)
        await seed_npc_merchant(db_session, general_store)  # Run again
        
        result = await db_session.execute(select(NPCMerchant))
        merchants = result.scalars().all()
        assert len(merchants) == 1  # Should still be 1, not 2


class TestFullDatabaseSeeding:
    """Test complete database seeding process."""
    
    async def test_seed_database_complete(self, db_session):
        """Test that the complete seeding process works correctly."""
        # Note: We can't easily test the full seed_database() function here
        # because it creates its own session, but we can test the components
        
        # Seed all components in order
        await seed_skills(db_session)
        starter_zone = await seed_starter_zone(db_session)
        await seed_starter_items(db_session)
        await seed_chat_channels(db_session)
        
        # Get general store for merchant
        result = await db_session.execute(
            select(Location).where(Location.name == "General Store")
        )
        general_store = result.scalar_one()
        
        await seed_npc_merchant(db_session, general_store)
        
        # Verify everything was seeded
        skills_result = await db_session.execute(select(Skill))
        skills = skills_result.scalars().all()
        assert len(skills) >= 20  # At least 20
        
        zones_result = await db_session.execute(select(Zone))
        zones = zones_result.scalars().all()
        assert len(zones) >= 1  # At least 1
        
        locations_result = await db_session.execute(select(Location))
        locations = locations_result.scalars().all()
        assert len(locations) >= 4  # At least 4
        
        items_result = await db_session.execute(select(Item))
        items = items_result.scalars().all()
        assert len(items) >= 5  # At least 5
        
        channels_result = await db_session.execute(select(ChatChannel))
        channels = channels_result.scalars().all()
        assert len(channels) >= 3  # At least 3
        
        merchants_result = await db_session.execute(select(NPCMerchant))
        merchants = merchants_result.scalars().all()
        assert len(merchants) == 1
    
    async def test_seeding_creates_functional_game_world(self, db_session):
        """Test that seeded data creates a functional game world."""
        # Seed everything
        await seed_skills(db_session)
        starter_zone = await seed_starter_zone(db_session)
        await seed_starter_items(db_session)
        await seed_chat_channels(db_session)
        
        result = await db_session.execute(
            select(Location).where(Location.name == "General Store")
        )
        general_store = result.scalar_one()
        
        await seed_npc_merchant(db_session, general_store)
        
        # Verify we can create a functional character
        from .conftest import UserFactory, CharacterFactory
        
        user_data = UserFactory()
        user = User(**user_data)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        char_data = CharacterFactory()
        char_data["user_id"] = user.id
        char_data["current_zone_id"] = starter_zone.id
        character = Character(**char_data)
        
        db_session.add(character)
        await db_session.commit()
        await db_session.refresh(character)
        
        # Verify character can be placed in the world
        assert character.current_zone_id == starter_zone.id
        assert starter_zone.min_x <= character.x_coordinate <= starter_zone.max_x
        assert starter_zone.min_y <= character.y_coordinate <= starter_zone.max_y
        
        # Verify character can learn skills
        result = await db_session.execute(
            select(Skill).where(Skill.name == "Swordsmanship")
        )
        swordsmanship = result.scalar_one()
        
        char_skill = CharacterSkill(
            character_id=character.id,
            skill_id=swordsmanship.id,
            level=1,
            experience=0,
            experience_to_next_level=100
        )
        
        db_session.add(char_skill)
        await db_session.commit()
        await db_session.refresh(char_skill)
        
        assert char_skill.level == 1
        assert char_skill.character_id == character.id
        assert char_skill.skill_id == swordsmanship.id
        
        # Verify character can acquire items
        result = await db_session.execute(
            select(Item).where(Item.name == "Iron Sword")
        )
        iron_sword = result.scalar_one()
        
        inventory_slot = InventorySlot(
            character_id=character.id,
            item_id=iron_sword.id,
            slot_number=0,
            quantity=1,
            condition=1.0
        )
        
        db_session.add(inventory_slot)
        await db_session.commit()
        await db_session.refresh(inventory_slot)
        
        assert inventory_slot.character_id == character.id
        assert inventory_slot.item_id == iron_sword.id 