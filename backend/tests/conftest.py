"""
Pytest configuration and fixtures for text-rpg backend tests.

Sets up test database, fixtures, and factories for comprehensive testing.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import create_engine, SQLModel
import factory
from faker import Faker

from app.core.config import settings
from app.core.database import get_session
from app.models import *
from app.models.user import UserRole, UserStatus
from app.models.skill import SkillCategory
from app.models.inventory import ItemType, ItemRarity, EquipmentSlot
from app.models.schemas import (
    ChatSettings, PrivacySettings, CharacterSettings,
    SkillBonuses, SkillAbilities,
    ItemStats, ItemEffects, ItemAttributes
)
import os

# Override settings for testing
# Use DATABASE_URL from environment if available (GitHub Actions), otherwise use SQLite
test_database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

fake = Faker()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create test database engine."""
    engine = create_async_engine(
        test_database_url,
        echo=False,
        future=True
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def create_tables(engine):
    """Create all database tables for testing."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
async def db_session(engine, create_tables) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async_session_maker = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_db(db_session):
    """Override the get_session dependency for testing."""
    async def _override_get_db():
        yield db_session
    return _override_get_db


# Factory classes for test data generation
class UserFactory(factory.Factory):
    """Factory for creating test users."""
    class Meta:
        model = dict
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    hashed_password = "$2b$12$example_hashed_password"
    role = UserRole.PLAYER
    status = UserStatus.ACTIVE
    is_verified = True
    max_characters = 5
    chat_settings = factory.LazyFunction(
        lambda: ChatSettings().model_dump()
    )
    privacy_settings = factory.LazyFunction(
        lambda: PrivacySettings().model_dump()
    )


class SkillFactory(factory.Factory):
    """Factory for creating test skills."""
    class Meta:
        model = dict
    
    name = factory.Sequence(lambda n: f"Skill {n}")
    description = factory.Faker('text', max_nb_chars=200)
    category = factory.Faker('random_element', elements=[e.value for e in SkillCategory])
    max_level = 100
    base_experience_required = 100
    experience_multiplier = 1.1
    prerequisite_skills = factory.LazyFunction(dict)
    min_character_level = 1
    stat_bonuses = factory.LazyFunction(
        lambda: SkillBonuses().model_dump()
    )
    abilities = factory.LazyFunction(
        lambda: SkillAbilities().model_dump()
    )
    sort_order = factory.Sequence(lambda n: n)
    is_active = True


class ZoneFactory(factory.Factory):
    """Factory for creating test zones."""
    class Meta:
        model = dict
    
    name = factory.Sequence(lambda n: f"Zone {n}")
    description = factory.Faker('text', max_nb_chars=500)
    min_x = 0.0
    max_x = 1000.0
    min_y = 0.0
    max_y = 1000.0
    level_requirement = factory.Faker('random_int', min=1, max=100)
    is_pvp_enabled = False
    is_safe_zone = True
    max_players = factory.Faker('random_int', min=10, max=100)
    respawn_x = 500.0
    respawn_y = 500.0


class ItemFactory(factory.Factory):
    """Factory for creating test items."""
    class Meta:
        model = dict
    
    name = factory.Sequence(lambda n: f"Item {n}")
    description = factory.Faker('text', max_nb_chars=200)
    item_type = factory.Faker('random_element', elements=[e.value for e in ItemType])
    rarity = factory.Faker('random_element', elements=[e.value for e in ItemRarity])
    base_value = factory.Faker('random_int', min=1, max=1000)
    max_stack_size = factory.Faker('random_int', min=1, max=100)
    weight = factory.Faker('pyfloat', min_value=0.1, max_value=10.0)
    required_level = factory.Faker('random_int', min=1, max=100)
    stats = factory.LazyFunction(
        lambda: ItemStats().model_dump()
    )
    effects = factory.LazyFunction(
        lambda: ItemEffects().model_dump()
    )
    attributes = factory.LazyFunction(
        lambda: ItemAttributes().model_dump()
    )
    is_tradeable = True
    is_droppable = True
    is_consumable = False
    is_unique = False


class CharacterFactory(factory.Factory):
    """Factory for creating test characters."""
    class Meta:
        model = dict
    
    name = factory.Sequence(lambda n: f"Character {n}")
    description = factory.Faker('text', max_nb_chars=500)
    level = factory.Faker('random_int', min=1, max=100)
    experience = factory.Faker('random_int', min=0, max=10000)
    experience_to_next_level = factory.Faker('random_int', min=100, max=1000)
    health = factory.Faker('random_int', min=50, max=500)
    max_health = factory.Faker('random_int', min=100, max=1000)
    mana = factory.Faker('random_int', min=25, max=250)
    max_mana = factory.Faker('random_int', min=50, max=500)
    gold = factory.Faker('random_int', min=0, max=10000)
    is_online = False
    is_in_combat = False
    is_dead = False
    x_coordinate = factory.Faker('pyfloat', min_value=0, max_value=1000)
    y_coordinate = factory.Faker('pyfloat', min_value=0, max_value=1000)
    total_skill_points = factory.Faker('random_int', min=0, max=1000)
    available_skill_points = factory.Faker('random_int', min=0, max=100)
    settings = factory.LazyFunction(
        lambda: CharacterSettings().model_dump()
    ) 