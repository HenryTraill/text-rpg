"""
Tests for SQLModel entities and database operations.

Tests all models for proper CRUD operations, relationships, and field validation.
"""

import pytest
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid

from app.models import *
from .conftest import UserFactory, SkillFactory, ZoneFactory, ItemFactory, CharacterFactory


class TestUserModel:
    """Test User model and related operations."""
    
    async def test_create_user(self, db_session):
        """Test creating a new user."""
        user_data = UserFactory()
        user = User(**user_data)
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.username == user_data["username"]
        assert user.email == user_data["email"]
        assert user.role == UserRole.PLAYER
        assert user.status == UserStatus.ACTIVE
        assert user.is_verified is True
        assert user.created_at is not None
        assert user.updated_at is not None
    
    async def test_user_unique_constraints(self, db_session):
        """Test that username and email are unique."""
        user_data = UserFactory()
        user1 = User(**user_data)
        
        db_session.add(user1)
        await db_session.commit()
        
        # Try to create another user with same username
        user2_data = UserFactory()
        user2_data["username"] = user_data["username"]
        user2 = User(**user2_data)
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    async def test_user_role_enum(self, db_session):
        """Test that user role enum works correctly."""
        user_data = UserFactory()
        user_data["role"] = UserRole.ADMIN
        user = User(**user_data)
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.role == UserRole.ADMIN
    
    async def test_user_json_fields(self, db_session):
        """Test that JSON fields work correctly."""
        user_data = UserFactory()
        user = User(**user_data)
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert isinstance(user.chat_settings, dict)
        assert isinstance(user.privacy_settings, dict)
        assert "global_enabled" in user.chat_settings
        assert "show_online_status" in user.privacy_settings


class TestSkillModel:
    """Test Skill model and related operations."""
    
    async def test_create_skill(self, db_session):
        """Test creating a new skill."""
        skill_data = SkillFactory()
        skill = Skill(**skill_data)
        
        db_session.add(skill)
        await db_session.commit()
        await db_session.refresh(skill)
        
        assert skill.id is not None
        assert skill.name == skill_data["name"]
        assert skill.category == SkillCategory(skill_data["category"])
        assert skill.max_level == 100
        assert skill.is_active is True
        assert skill.created_at is not None
    
    async def test_skill_unique_name(self, db_session):
        """Test that skill names are unique."""
        skill_data = SkillFactory()
        skill1 = Skill(**skill_data)
        
        db_session.add(skill1)
        await db_session.commit()
        
        # Try to create another skill with same name
        skill2_data = SkillFactory()
        skill2_data["name"] = skill_data["name"]
        skill2 = Skill(**skill2_data)
        
        db_session.add(skill2)
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    async def test_skill_categories(self, db_session):
        """Test all skill categories."""
        categories = [SkillCategory.COMBAT, SkillCategory.GATHERING, 
                     SkillCategory.CRAFTING, SkillCategory.SOCIAL]
        
        for category in categories:
            skill_data = SkillFactory()
            skill_data["category"] = category.value
            skill = Skill(**skill_data)
            
            db_session.add(skill)
        
        await db_session.commit()
        
        # Verify all categories were saved
        result = await db_session.execute(select(Skill))
        skills = result.scalars().all()
        saved_categories = [skill.category for skill in skills]
        
        for category in categories:
            assert category in saved_categories
    
    async def test_skill_json_fields(self, db_session):
        """Test skill JSON fields."""
        skill_data = SkillFactory()
        skill = Skill(**skill_data)
        
        db_session.add(skill)
        await db_session.commit()
        await db_session.refresh(skill)
        
        assert isinstance(skill.stat_bonuses, dict)
        assert isinstance(skill.abilities, dict)
        assert isinstance(skill.prerequisite_skills, dict)


class TestCharacterModel:
    """Test Character model and related operations."""
    
    async def test_create_character(self, db_session):
        """Test creating a character with user and zone relationships."""
        # Create user first
        user_data = UserFactory()
        user = User(**user_data)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create zone
        zone_data = ZoneFactory()
        zone = Zone(**zone_data)
        db_session.add(zone)
        await db_session.commit()
        await db_session.refresh(zone)
        
        # Create character
        char_data = CharacterFactory()
        char_data["user_id"] = user.id
        char_data["current_zone_id"] = zone.id
        character = Character(**char_data)
        
        db_session.add(character)
        await db_session.commit()
        await db_session.refresh(character)
        
        assert character.id is not None
        assert character.user_id == user.id
        assert character.current_zone_id == zone.id
        assert character.level >= 1
        assert character.health > 0
        assert character.max_health > 0
        assert character.created_at is not None
    
    async def test_character_unique_name(self, db_session):
        """Test that character names are unique."""
        # Create user and zone
        user_data = UserFactory()
        user = User(**user_data)
        zone_data = ZoneFactory()
        zone = Zone(**zone_data)
        db_session.add_all([user, zone])
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(zone)
        
        # Create first character
        char_data = CharacterFactory()
        char_data["user_id"] = user.id
        char_data["current_zone_id"] = zone.id
        character1 = Character(**char_data)
        
        db_session.add(character1)
        await db_session.commit()
        
        # Try to create another character with same name
        char2_data = CharacterFactory()
        char2_data["name"] = char_data["name"]
        char2_data["user_id"] = user.id
        char2_data["current_zone_id"] = zone.id
        character2 = Character(**char2_data)
        
        db_session.add(character2)
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    async def test_character_relationships(self, db_session):
        """Test character relationships with user and zone."""
        # Create user and zone
        user_data = UserFactory()
        user = User(**user_data)
        zone_data = ZoneFactory()
        zone = Zone(**zone_data)
        db_session.add_all([user, zone])
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(zone)
        
        # Create character
        char_data = CharacterFactory()
        char_data["user_id"] = user.id
        char_data["current_zone_id"] = zone.id
        character = Character(**char_data)
        
        db_session.add(character)
        await db_session.commit()
        await db_session.refresh(character)
        
        # Test relationships (would need to fetch with joins in real app)
        assert character.user_id == user.id
        assert character.current_zone_id == zone.id


class TestItemModel:
    """Test Item model and related operations."""
    
    async def test_create_item(self, db_session):
        """Test creating a new item."""
        item_data = ItemFactory()
        item = Item(**item_data)
        
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)
        
        assert item.id is not None
        assert item.name == item_data["name"]
        assert item.item_type == ItemType(item_data["item_type"])
        assert item.rarity == ItemRarity(item_data["rarity"])
        assert item.base_value >= 0
        assert item.weight >= 0
        assert item.created_at is not None
    
    async def test_item_types_and_rarities(self, db_session):
        """Test all item types and rarities."""
        # Create items of different types and rarities with unique names
        test_uuid = str(uuid.uuid4())[:8]
        item_types = [ItemType.WEAPON, ItemType.ARMOR, ItemType.CONSUMABLE, 
                     ItemType.MATERIAL, ItemType.TOOL]
        rarities = [ItemRarity.COMMON, ItemRarity.UNCOMMON, ItemRarity.RARE, 
                   ItemRarity.EPIC, ItemRarity.LEGENDARY]
        
        for item_type in item_types:
            for rarity in rarities:
                item_data = ItemFactory()
                item_data["item_type"] = item_type.value
                item_data["rarity"] = rarity.value
                item_data["name"] = f"{item_type.value}_{rarity.value}_{test_uuid}"
                item = Item(**item_data)
                
                db_session.add(item)
        
        await db_session.commit()
        
        # Verify items were saved with correct types (only count items created in this test)
        result = await db_session.execute(
            select(Item).where(Item.name.like(f"%{test_uuid}%"))
        )
        items = result.scalars().all()
        
        assert len(items) == len(item_types) * len(rarities)
    
    async def test_item_json_fields(self, db_session):
        """Test item JSON fields."""
        item_data = ItemFactory()
        item = Item(**item_data)
        
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)
        
        assert isinstance(item.stats, dict)
        assert isinstance(item.effects, dict)
        assert isinstance(item.attributes, dict)


class TestZoneModel:
    """Test Zone model and related operations."""
    
    async def test_create_zone(self, db_session):
        """Test creating a new zone."""
        zone_data = ZoneFactory()
        zone = Zone(**zone_data)
        
        db_session.add(zone)
        await db_session.commit()
        await db_session.refresh(zone)
        
        assert zone.id is not None
        assert zone.name == zone_data["name"]
        assert zone.min_x <= zone.max_x
        assert zone.min_y <= zone.max_y
        assert zone.level_requirement >= 1
        assert zone.created_at is not None
    
    async def test_zone_unique_name(self, db_session):
        """Test that zone names are unique."""
        zone_data = ZoneFactory()
        zone1 = Zone(**zone_data)
        
        db_session.add(zone1)
        await db_session.commit()
        
        # Try to create another zone with same name
        zone2_data = ZoneFactory()
        zone2_data["name"] = zone_data["name"]
        zone2 = Zone(**zone2_data)
        
        db_session.add(zone2)
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestLocationModel:
    """Test Location model and related operations."""
    
    async def test_create_location(self, db_session):
        """Test creating a location within a zone."""
        # Create zone first
        zone_data = ZoneFactory()
        zone = Zone(**zone_data)
        db_session.add(zone)
        await db_session.commit()
        await db_session.refresh(zone)
        
        # Create location
        location = Location(
            zone_id=zone.id,
            name="Test Location",
            description="A test location",
            location_type="landmark",
            x_coordinate=500.0,
            y_coordinate=500.0,
            interaction_radius=10.0,
            is_active=True
        )
        
        db_session.add(location)
        await db_session.commit()
        await db_session.refresh(location)
        
        assert location.id is not None
        assert location.zone_id == zone.id
        assert location.name == "Test Location"
        assert location.is_active is True


class TestInventoryModel:
    """Test InventorySlot model and related operations."""
    
    async def test_create_inventory_slot(self, db_session):
        """Test creating an inventory slot."""
        # Create dependencies
        user_data = UserFactory()
        user = User(**user_data)
        zone_data = ZoneFactory()
        zone = Zone(**zone_data)
        item_data = ItemFactory()
        item = Item(**item_data)
        
        db_session.add_all([user, zone, item])
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(zone)
        await db_session.refresh(item)
        
        # Create character
        char_data = CharacterFactory()
        char_data["user_id"] = user.id
        char_data["current_zone_id"] = zone.id
        character = Character(**char_data)
        
        db_session.add(character)
        await db_session.commit()
        await db_session.refresh(character)
        
        # Create inventory slot
        inventory_slot = InventorySlot(
            character_id=character.id,
            item_id=item.id,
            slot_number=0,
            quantity=1,
            condition=1.0,
            is_equipped=False
        )
        
        db_session.add(inventory_slot)
        await db_session.commit()
        await db_session.refresh(inventory_slot)
        
        assert inventory_slot.id is not None
        assert inventory_slot.character_id == character.id
        assert inventory_slot.item_id == item.id
        assert inventory_slot.quantity == 1
        assert inventory_slot.condition == 1.0


class TestUserSessionModel:
    """Test UserSession model."""
    
    async def test_create_user_session(self, db_session):
        """Test creating a user session."""
        # Create user first
        user_data = UserFactory()
        user = User(**user_data)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create session
        session = UserSession(
            user_id=user.id,
            token_jti="test_jti_123",
            device_info="test device",
            ip_address="127.0.0.1",
            user_agent="test agent",
            is_active=True,
            expires_at=datetime.now()
        )
        
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        
        assert session.id is not None
        assert session.user_id == user.id
        assert session.token_jti == "test_jti_123"
        assert session.is_active is True


class TestChatModel:
    """Test ChatChannel and Message models."""
    
    async def test_create_chat_channel(self, db_session):
        """Test creating a chat channel."""
        channel = ChatChannel(
            name="Global",
            channel_type="global"
        )
        
        db_session.add(channel)
        await db_session.commit()
        await db_session.refresh(channel)
        
        assert channel.id is not None
        assert channel.name == "Global"
        assert channel.channel_type == "global"
        assert channel.created_at is not None


class TestCombatModel:
    """Test combat-related models."""
    
    async def test_create_combat_session(self, db_session):
        """Test creating a combat session."""
        combat_session = CombatSession(
            status="active",
            turn_number=1,
            current_turn_character_id=None
        )
        
        db_session.add(combat_session)
        await db_session.commit()
        await db_session.refresh(combat_session)
        
        assert combat_session.id is not None
        assert combat_session.status == "active"
        assert combat_session.turn_number == 1
        assert combat_session.created_at is not None


class TestEconomyModel:
    """Test economy-related models."""
    
    async def test_create_trade(self, db_session):
        """Test creating a trade."""
        # Create dependencies
        user_data1 = UserFactory()
        user_data2 = UserFactory()
        user1 = User(**user_data1)
        user2 = User(**user_data2)
        zone_data = ZoneFactory()
        zone = Zone(**zone_data)
        
        db_session.add_all([user1, user2, zone])
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)
        await db_session.refresh(zone)
        
        # Create characters
        char1_data = CharacterFactory()
        char1_data["user_id"] = user1.id
        char1_data["current_zone_id"] = zone.id
        character1 = Character(**char1_data)
        
        char2_data = CharacterFactory()
        char2_data["user_id"] = user2.id
        char2_data["current_zone_id"] = zone.id
        character2 = Character(**char2_data)
        
        db_session.add_all([character1, character2])
        await db_session.commit()
        await db_session.refresh(character1)
        await db_session.refresh(character2)
        
        # Create trade
        trade = Trade(
            trader_1_id=character1.id,
            trader_2_id=character2.id,
            status="pending",
            trade_data={}
        )
        
        db_session.add(trade)
        await db_session.commit()
        await db_session.refresh(trade)
        
        assert trade.id is not None
        assert trade.trader_1_id == character1.id
        assert trade.trader_2_id == character2.id
        assert trade.status == "pending"


class TestSocialModel:
    """Test social-related models."""
    
    async def test_create_guild(self, db_session):
        """Test creating a guild."""
        guild = Guild(
            name="Test Guild",
            description="A test guild"
        )
        
        db_session.add(guild)
        await db_session.commit()
        await db_session.refresh(guild)
        
        assert guild.id is not None
        assert guild.name == "Test Guild"
        assert guild.description == "A test guild"
        assert guild.created_at is not None


class TestModelQueries:
    """Test complex queries and relationships."""
    
    async def test_user_character_relationship(self, db_session):
        """Test querying users with their characters."""
        # Create user and zone
        user_data = UserFactory()
        user = User(**user_data)
        zone_data = ZoneFactory()
        zone = Zone(**zone_data)
        db_session.add_all([user, zone])
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(zone)
        
        # Create multiple characters for the user with unique names
        test_uuid = str(uuid.uuid4())[:8]
        for i in range(3):
            char_data = CharacterFactory()
            char_data["user_id"] = user.id
            char_data["current_zone_id"] = zone.id
            char_data["name"] = f"TestChar_{test_uuid}_{i}"
            character = Character(**char_data)
            db_session.add(character)
        
        await db_session.commit()
        
        # Query characters for the user
        result = await db_session.execute(
            select(Character).where(Character.user_id == user.id)
        )
        characters = result.scalars().all()
        
        assert len(characters) == 3
        for character in characters:
            assert character.user_id == user.id
    
    async def test_skill_by_category(self, db_session):
        """Test querying skills by category."""
        # Create skills in different categories with unique names
        test_uuid = str(uuid.uuid4())[:8]
        categories = [SkillCategory.COMBAT, SkillCategory.GATHERING, SkillCategory.CRAFTING]
        
        for category in categories:
            for i in range(2):
                skill_data = SkillFactory()
                skill_data["category"] = category.value
                skill_data["name"] = f"{category.value}_Skill_{test_uuid}_{i}"
                skill = Skill(**skill_data)
                db_session.add(skill)
        
        await db_session.commit()
        
        # Query combat skills created in this test
        result = await db_session.execute(
            select(Skill).where(
                Skill.category == SkillCategory.COMBAT,
                Skill.name.like(f"%{test_uuid}%")
            )
        )
        combat_skills = result.scalars().all()
        
        assert len(combat_skills) == 2
        for skill in combat_skills:
            assert skill.category == SkillCategory.COMBAT
    
    async def test_items_by_type(self, db_session):
        """Test querying items by type."""
        # Create items of different types with unique names
        test_uuid = str(uuid.uuid4())[:8]
        item_types = [ItemType.WEAPON, ItemType.ARMOR, ItemType.CONSUMABLE]
        
        for item_type in item_types:
            for i in range(2):
                item_data = ItemFactory()
                item_data["item_type"] = item_type.value
                item_data["name"] = f"{item_type.value}_{test_uuid}_{i}"
                item = Item(**item_data)
                db_session.add(item)
        
        await db_session.commit()
        
        # Query weapons created in this test
        result = await db_session.execute(
            select(Item).where(
                Item.item_type == ItemType.WEAPON,
                Item.name.like(f"%{test_uuid}%")
            )
        )
        weapons = result.scalars().all()
        
        assert len(weapons) == 2
        for weapon in weapons:
            assert weapon.item_type == ItemType.WEAPON 