"""
Database seeding script for initial game data.

This script populates the database with:
- All 20 skills across 4 categories
- Starter zones and locations
- Basic items for new players
- NPC merchants
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import asyncio

from .database import AsyncSessionLocal
from ..models.skill import Skill, SKILL_DEFINITIONS
from ..models.inventory import Item, STARTER_ITEMS
from ..models.world import Zone, Location
from ..models.economy import NPCMerchant
from ..models.chat import ChatChannel


async def seed_skills(session: AsyncSession):
    """Seed all 20 skills across 4 categories."""
    print("Seeding skills...")

    # Check if skills already exist
    result = await session.execute(select(Skill))
    existing_skills = result.scalars().all()

    if existing_skills:
        print(f"Skills already exist ({len(existing_skills)} found), skipping...")
        return

    skill_count = 0
    for category, skills in SKILL_DEFINITIONS.items():
        for index, skill_data in enumerate(skills):
            skill = Skill(
                name=skill_data["name"],
                description=skill_data["description"],
                category=category,
                stat_bonuses=skill_data.get("stat_bonuses", {}),
                abilities=skill_data.get("abilities", {}),
                sort_order=index,
            )
            session.add(skill)
            skill_count += 1

    await session.commit()
    print(f"Seeded {skill_count} skills across {len(SKILL_DEFINITIONS)} categories")


async def seed_starter_zone(session: AsyncSession):
    """Seed the starter zone and key locations."""
    print("Seeding starter zone...")

    # Check if starter zone exists
    result = await session.execute(select(Zone).where(Zone.name == "Starter Town"))
    existing_zone = result.scalar_one_or_none()

    if existing_zone:
        print("Starter zone already exists, skipping...")
        return existing_zone

    # Create starter zone
    starter_zone = Zone(
        name="Starter Town",
        description="A peaceful town where new adventurers begin their journey.",
        min_x=0.0,
        max_x=1000.0,
        min_y=0.0,
        max_y=1000.0,
        level_requirement=1,
        is_safe_zone=True,
        respawn_x=500.0,
        respawn_y=500.0,
    )
    session.add(starter_zone)
    await session.flush()  # Get the ID

    # Create key locations in starter zone
    locations = [
        {
            "name": "Town Center",
            "description": "The heart of the starter town where adventurers gather.",
            "location_type": "landmark",
            "x_coordinate": 500.0,
            "y_coordinate": 500.0,
        },
        {
            "name": "General Store",
            "description": "A shop selling basic equipment and supplies.",
            "location_type": "shop",
            "x_coordinate": 450.0,
            "y_coordinate": 500.0,
        },
        {
            "name": "Training Grounds",
            "description": "Where new adventurers learn combat skills.",
            "location_type": "training",
            "x_coordinate": 600.0,
            "y_coordinate": 400.0,
        },
        {
            "name": "Mine Entrance",
            "description": "The entrance to the starter mining area.",
            "location_type": "dungeon",
            "x_coordinate": 200.0,
            "y_coordinate": 300.0,
        },
    ]

    for loc_data in locations:
        location = Location(zone_id=starter_zone.id, **loc_data)
        session.add(location)

    await session.commit()
    print(f"Seeded starter zone with {len(locations)} locations")
    return starter_zone


async def seed_starter_items(session: AsyncSession):
    """Seed basic items for new players."""
    print("Seeding starter items...")

    # Check if items already exist
    result = await session.execute(select(Item))
    existing_items = result.scalars().all()

    if existing_items:
        print(f"Items already exist ({len(existing_items)} found), skipping...")
        return

    for item_data in STARTER_ITEMS:
        item = Item(**item_data)
        session.add(item)

    await session.commit()
    print(f"Seeded {len(STARTER_ITEMS)} starter items")


async def seed_npc_merchant(session: AsyncSession, general_store_location: Location):
    """Seed a basic NPC merchant."""
    print("Seeding NPC merchant...")

    # Check if merchant already exists
    result = await session.execute(
        select(NPCMerchant).where(NPCMerchant.name == "Merchant Tom")
    )
    existing_merchant = result.scalar_one_or_none()

    if existing_merchant:
        print("NPC merchant already exists, skipping...")
        return

    merchant = NPCMerchant(
        name="Merchant Tom",
        location_id=general_store_location.id,
        merchant_type="general",
        inventory_data={
            "items": [
                {"item_name": "Health Potion", "stock": 50, "price_multiplier": 1.0},
                {"item_name": "Iron Sword", "stock": 10, "price_multiplier": 1.2},
                {"item_name": "Leather Tunic", "stock": 15, "price_multiplier": 1.1},
                {"item_name": "Iron Pickaxe", "stock": 5, "price_multiplier": 1.0},
            ]
        },
        pricing_data={
            "buy_multiplier": 0.6,  # Buy from players at 60% value
            "sell_multiplier": 1.2,  # Sell to players at 120% value
        },
    )
    session.add(merchant)
    await session.commit()
    print("Seeded NPC merchant: Merchant Tom")


async def seed_chat_channels(session: AsyncSession):
    """Seed basic chat channels."""
    print("Seeding chat channels...")

    # Check if channels already exist
    result = await session.execute(select(ChatChannel))
    existing_channels = result.scalars().all()

    if existing_channels:
        print(
            f"Chat channels already exist ({len(existing_channels)} found), skipping..."
        )
        return

    channels = [
        {"name": "Global", "channel_type": "global"},
        {"name": "Help", "channel_type": "help"},
        {"name": "Trade", "channel_type": "trade"},
    ]

    for channel_data in channels:
        channel = ChatChannel(**channel_data)
        session.add(channel)

    await session.commit()
    print(f"Seeded {len(channels)} chat channels")


async def seed_database():
    """Main seeding function that orchestrates all seeding operations."""
    print("Starting database seeding...")

    async with AsyncSessionLocal() as session:
        try:
            # Seed in order of dependencies
            await seed_skills(session)
            starter_zone = await seed_starter_zone(session)
            await seed_starter_items(session)
            await seed_chat_channels(session)

            # Get general store location for merchant
            result = await session.execute(
                select(Location).where(Location.name == "General Store")
            )
            general_store = result.scalar_one_or_none()

            if general_store:
                await seed_npc_merchant(session, general_store)

            print("Database seeding completed successfully!")

        except Exception as e:
            print(f"Error during seeding: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())
