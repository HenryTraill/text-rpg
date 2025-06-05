"""Fix timestamp columns to support timezone

Revision ID: 781dd07d49aa
Revises: 193ad39ee128
Create Date: 2025-06-05 23:01:28.582962

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '781dd07d49aa'
down_revision: Union[str, None] = '193ad39ee128'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # List of all tables and their timestamp columns that need to be fixed
    timestamp_columns = [
        ('chat_channels', 'created_at'),
        ('combat_sessions', 'created_at'),
        ('combat_sessions', 'ended_at'),
        ('guilds', 'created_at'),
        ('items', 'created_at'),
        ('items', 'updated_at'),
        ('skills', 'created_at'),
        ('skills', 'updated_at'),
        ('users', 'created_at'),
        ('users', 'updated_at'),
        ('users', 'last_login'),
        ('users', 'locked_until'),
        ('world_events', 'start_time'),
        ('world_events', 'end_time'),
        ('world_events', 'created_at'),
        ('zones', 'created_at'),
        ('zones', 'updated_at'),
        ('characters', 'created_at'),
        ('characters', 'updated_at'),
        ('characters', 'last_login'),
        ('characters', 'last_logout'),
        ('crafting_recipes', 'created_at'),
        ('locations', 'created_at'),
        ('locations', 'updated_at'),
        ('user_sessions', 'created_at'),
        ('user_sessions', 'expires_at'),
        ('user_sessions', 'last_activity'),
        ('zone_instances', 'created_at'),
        ('auctions', 'expires_at'),
        ('auctions', 'created_at'),
        ('channel_memberships', 'joined_at'),
        ('character_locations', 'timestamp'),
        ('character_skills', 'last_used'),
        ('character_skills', 'last_trained'),
        ('character_skills', 'created_at'),
        ('character_skills', 'updated_at'),
        ('combat_actions', 'created_at'),
        ('combat_results', 'created_at'),
        ('friendships', 'created_at'),
        ('guild_members', 'joined_at'),
        ('inventory_slots', 'acquired_at'),
        ('inventory_slots', 'last_used'),
        ('messages', 'created_at'),
        ('npc_merchants', 'created_at'),
        ('parties', 'created_at'),
        ('trades', 'created_at'),
        ('trades', 'completed_at'),
        ('message_history', 'archived_at'),
        ('party_members', 'joined_at'),
    ]
    
    # Convert all timestamp columns to support timezone
    for table_name, column_name in timestamp_columns:
        op.execute(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE TIMESTAMP WITH TIME ZONE")


def downgrade() -> None:
    # List of all tables and their timestamp columns to revert
    timestamp_columns = [
        ('chat_channels', 'created_at'),
        ('combat_sessions', 'created_at'),
        ('combat_sessions', 'ended_at'),
        ('guilds', 'created_at'),
        ('items', 'created_at'),
        ('items', 'updated_at'),
        ('skills', 'created_at'),
        ('skills', 'updated_at'),
        ('users', 'created_at'),
        ('users', 'updated_at'),
        ('users', 'last_login'),
        ('users', 'locked_until'),
        ('world_events', 'start_time'),
        ('world_events', 'end_time'),
        ('world_events', 'created_at'),
        ('zones', 'created_at'),
        ('zones', 'updated_at'),
        ('characters', 'created_at'),
        ('characters', 'updated_at'),
        ('characters', 'last_login'),
        ('characters', 'last_logout'),
        ('crafting_recipes', 'created_at'),
        ('locations', 'created_at'),
        ('locations', 'updated_at'),
        ('user_sessions', 'created_at'),
        ('user_sessions', 'expires_at'),
        ('user_sessions', 'last_activity'),
        ('zone_instances', 'created_at'),
        ('auctions', 'expires_at'),
        ('auctions', 'created_at'),
        ('channel_memberships', 'joined_at'),
        ('character_locations', 'timestamp'),
        ('character_skills', 'last_used'),
        ('character_skills', 'last_trained'),
        ('character_skills', 'created_at'),
        ('character_skills', 'updated_at'),
        ('combat_actions', 'created_at'),
        ('combat_results', 'created_at'),
        ('friendships', 'created_at'),
        ('guild_members', 'joined_at'),
        ('inventory_slots', 'acquired_at'),
        ('inventory_slots', 'last_used'),
        ('messages', 'created_at'),
        ('npc_merchants', 'created_at'),
        ('parties', 'created_at'),
        ('trades', 'created_at'),
        ('trades', 'completed_at'),
        ('message_history', 'archived_at'),
        ('party_members', 'joined_at'),
    ]
    
    # Revert all timestamp columns back to without timezone
    for table_name, column_name in timestamp_columns:
        op.execute(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE TIMESTAMP WITHOUT TIME ZONE")
