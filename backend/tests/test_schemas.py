"""
Tests for Pydantic schemas used in JSON fields.

Validates that all Pydantic models work correctly and provide proper type safety.
"""

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    ChatSettings, PrivacySettings, CharacterSettings,
    SkillBonuses, SkillAbilities, SkillPrerequisites,
    ItemStats, ItemEffects, ItemAttributes, Enchantments,
    WorldEventData, CombatActionData, CombatResultData, CombatRewards,
    TradeData, MerchantInventoryData, MerchantPricingData, CraftingMaterials
)


class TestUserSchemas:
    """Test user-related Pydantic schemas."""
    
    def test_chat_settings_defaults(self):
        """Test ChatSettings with default values."""
        settings = ChatSettings()
        assert settings.global_enabled is True
        assert settings.guild_enabled is True
        assert settings.party_enabled is True
        assert settings.trade_enabled is True
        assert settings.private_enabled is True
        assert settings.profanity_filter is True
        assert settings.message_sound is True
        assert settings.font_size == "medium"
    
    def test_chat_settings_custom(self):
        """Test ChatSettings with custom values."""
        settings = ChatSettings(
            global_enabled=False,
            font_size="large",
            profanity_filter=False
        )
        assert settings.global_enabled is False
        assert settings.font_size == "large"
        assert settings.profanity_filter is False
        # Defaults should still be set
        assert settings.guild_enabled is True
    
    def test_privacy_settings_defaults(self):
        """Test PrivacySettings with default values."""
        settings = PrivacySettings()
        assert settings.show_online_status is True
        assert settings.allow_friend_requests is True
        assert settings.allow_party_invites is True
        assert settings.allow_guild_invites is True
        assert settings.show_location is True
        assert settings.show_level is True
    
    def test_privacy_settings_custom(self):
        """Test PrivacySettings with custom values."""
        settings = PrivacySettings(
            show_online_status=False,
            allow_friend_requests=False
        )
        assert settings.show_online_status is False
        assert settings.allow_friend_requests is False
        assert settings.allow_party_invites is True  # Default
    
    def test_character_settings_defaults(self):
        """Test CharacterSettings with default values."""
        settings = CharacterSettings()
        assert settings.auto_loot is True
        assert settings.auto_sort_inventory is False
        assert settings.combat_auto_attack is False
        assert settings.movement_click_to_move is True
        assert settings.ui_theme == "default"
        assert settings.hotkey_bindings == {}


class TestSkillSchemas:
    """Test skill-related Pydantic schemas."""
    
    def test_skill_bonuses_defaults(self):
        """Test SkillBonuses with default values."""
        bonuses = SkillBonuses()
        assert bonuses.melee_damage == 0
        assert bonuses.ranged_damage == 0
        assert bonuses.spell_damage == 0
        assert bonuses.accuracy == 0
        assert bonuses.critical_chance == 0
        assert bonuses.armor == 0
        assert bonuses.health == 0
        assert bonuses.mana == 0
        assert bonuses.mining_speed == 0.0
        assert bonuses.party_bonus == 0
    
    def test_skill_bonuses_custom(self):
        """Test SkillBonuses with custom values."""
        bonuses = SkillBonuses(
            melee_damage=5,
            accuracy=3,
            health=20,
            mining_speed=1.5
        )
        assert bonuses.melee_damage == 5
        assert bonuses.accuracy == 3
        assert bonuses.health == 20
        assert bonuses.mining_speed == 1.5
        # Defaults should still be set
        assert bonuses.ranged_damage == 0
    
    def test_skill_abilities_defaults(self):
        """Test SkillAbilities with default values."""
        abilities = SkillAbilities()
        assert abilities.abilities == {}
        assert abilities.special_actions == []
    
    def test_skill_abilities_custom(self):
        """Test SkillAbilities with custom values."""
        abilities = SkillAbilities(
            abilities={"parry": True, "riposte": False},
            special_actions=["charge", "dodge"]
        )
        assert abilities.abilities == {"parry": True, "riposte": False}
        assert abilities.special_actions == ["charge", "dodge"]
    
    def test_skill_prerequisites_defaults(self):
        """Test SkillPrerequisites with default values."""
        prereqs = SkillPrerequisites()
        assert prereqs.required_skills == {}
        assert prereqs.required_character_level == 1
    
    def test_skill_prerequisites_custom(self):
        """Test SkillPrerequisites with custom values."""
        prereqs = SkillPrerequisites(
            required_skills={"Swordsmanship": 10, "Defense": 5},
            required_character_level=15
        )
        assert prereqs.required_skills == {"Swordsmanship": 10, "Defense": 5}
        assert prereqs.required_character_level == 15


class TestItemSchemas:
    """Test item-related Pydantic schemas."""
    
    def test_item_stats_defaults(self):
        """Test ItemStats with default values."""
        stats = ItemStats()
        assert stats.damage == 0
        assert stats.accuracy == 0
        assert stats.critical_chance == 0
        assert stats.attack_speed == 1.0
        assert stats.armor == 0
        assert stats.health_bonus == 0
        assert stats.mana_bonus == 0
        assert stats.movement_speed == 0.0
        assert stats.mining_speed == 0.0
    
    def test_item_stats_custom(self):
        """Test ItemStats with custom values."""
        stats = ItemStats(
            damage=15,
            accuracy=8,
            critical_chance=5,
            armor=10,
            health_bonus=25
        )
        assert stats.damage == 15
        assert stats.accuracy == 8
        assert stats.critical_chance == 5
        assert stats.armor == 10
        assert stats.health_bonus == 25
        # Defaults should still be set
        assert stats.attack_speed == 1.0
    
    def test_item_effects_defaults(self):
        """Test ItemEffects with default values."""
        effects = ItemEffects()
        assert effects.heal == 0
        assert effects.restore_mana == 0
        assert effects.buff_duration == 0
        assert effects.permanent_bonuses == {}
        assert effects.on_hit_effects == []
        assert effects.on_use_effects == []
    
    def test_item_effects_custom(self):
        """Test ItemEffects with custom values."""
        effects = ItemEffects(
            heal=50,
            restore_mana=25,
            permanent_bonuses={"strength": 5},
            on_hit_effects=["poison", "slow"],
            on_use_effects=["heal_over_time"]
        )
        assert effects.heal == 50
        assert effects.restore_mana == 25
        assert effects.permanent_bonuses == {"strength": 5}
        assert effects.on_hit_effects == ["poison", "slow"]
        assert effects.on_use_effects == ["heal_over_time"]
    
    def test_item_attributes_defaults(self):
        """Test ItemAttributes with default values."""
        attrs = ItemAttributes()
        assert attrs.is_magical is False
        assert attrs.is_cursed is False
        assert attrs.is_quest_item is False
        assert attrs.crafting_material is False
        assert attrs.tool_type is None
        assert attrs.set_bonus is None
    
    def test_item_attributes_custom(self):
        """Test ItemAttributes with custom values."""
        attrs = ItemAttributes(
            is_magical=True,
            crafting_material=True,
            tool_type="pickaxe",
            set_bonus="warrior_set"
        )
        assert attrs.is_magical is True
        assert attrs.crafting_material is True
        assert attrs.tool_type == "pickaxe"
        assert attrs.set_bonus == "warrior_set"
        # Defaults should still be set
        assert attrs.is_cursed is False
    
    def test_enchantments_defaults(self):
        """Test Enchantments with default values."""
        enchants = Enchantments()
        assert enchants.enchantments == {}
        assert enchants.durability_bonus == 0
        assert enchants.value_multiplier == 1.0
    
    def test_enchantments_custom(self):
        """Test Enchantments with custom values."""
        enchants = Enchantments(
            enchantments={"sharpness": 3, "fire_damage": 2},
            durability_bonus=50,
            value_multiplier=2.5
        )
        assert enchants.enchantments == {"sharpness": 3, "fire_damage": 2}
        assert enchants.durability_bonus == 50
        assert enchants.value_multiplier == 2.5


class TestWorldSchemas:
    """Test world-related Pydantic schemas."""
    
    def test_world_event_data_required_field(self):
        """Test WorldEventData requires event_type."""
        with pytest.raises(ValidationError):
            WorldEventData()
    
    def test_world_event_data_valid(self):
        """Test WorldEventData with valid data."""
        event = WorldEventData(
            event_type="boss_spawn",
            affected_zones=["forest", "mountain"],
            rewards={"experience": 1000, "gold": 500},
            conditions={"min_players": 5},
            modifiers={"damage_multiplier": 1.5}
        )
        assert event.event_type == "boss_spawn"
        assert event.affected_zones == ["forest", "mountain"]
        assert event.rewards == {"experience": 1000, "gold": 500}
        assert event.conditions == {"min_players": 5}
        assert event.modifiers == {"damage_multiplier": 1.5}


class TestCombatSchemas:
    """Test combat-related Pydantic schemas."""
    
    def test_combat_action_data_required_field(self):
        """Test CombatActionData requires action_type."""
        with pytest.raises(ValidationError):
            CombatActionData()
    
    def test_combat_action_data_valid(self):
        """Test CombatActionData with valid data."""
        action = CombatActionData(
            action_type="attack",
            target_id="target_123",
            skill_used="swordsmanship",
            item_used=None,
            modifiers={"damage_boost": 1.2}
        )
        assert action.action_type == "attack"
        assert action.target_id == "target_123"
        assert action.skill_used == "swordsmanship"
        assert action.item_used is None
        assert action.modifiers == {"damage_boost": 1.2}
    
    def test_combat_result_data_defaults(self):
        """Test CombatResultData with default values."""
        result = CombatResultData()
        assert result.damage_dealt == 0
        assert result.damage_taken == 0
        assert result.hit_chance == 0.0
        assert result.critical_hit is False
        assert result.status_effects == []
        assert result.skill_experience_gained == {}
    
    def test_combat_rewards_defaults(self):
        """Test CombatRewards with default values."""
        rewards = CombatRewards()
        assert rewards.experience == 0
        assert rewards.gold == 0
        assert rewards.items == []
        assert rewards.skill_bonuses == {}


class TestEconomySchemas:
    """Test economy-related Pydantic schemas."""
    
    def test_trade_data_defaults(self):
        """Test TradeData with default values."""
        trade = TradeData()
        assert trade.trader_1_items == []
        assert trade.trader_2_items == []
        assert trade.trader_1_gold == 0
        assert trade.trader_2_gold == 0
        assert trade.agreed_terms == {}
    
    def test_trade_data_custom(self):
        """Test TradeData with custom values."""
        trade = TradeData(
            trader_1_items=[{"item_id": "sword", "quantity": 1}],
            trader_2_items=[{"item_id": "potion", "quantity": 5}],
            trader_1_gold=100,
            trader_2_gold=50,
            agreed_terms={"trade_tax": 5}
        )
        assert trade.trader_1_items == [{"item_id": "sword", "quantity": 1}]
        assert trade.trader_2_items == [{"item_id": "potion", "quantity": 5}]
        assert trade.trader_1_gold == 100
        assert trade.trader_2_gold == 50
        assert trade.agreed_terms == {"trade_tax": 5}
    
    def test_merchant_inventory_data_defaults(self):
        """Test MerchantInventoryData with default values."""
        inventory = MerchantInventoryData()
        assert inventory.items == []
        assert inventory.refresh_interval == 3600
        assert inventory.stock_limits == {}
        assert inventory.special_offers == []
    
    def test_merchant_pricing_data_defaults(self):
        """Test MerchantPricingData with default values."""
        pricing = MerchantPricingData()
        assert pricing.buy_multiplier == 0.6
        assert pricing.sell_multiplier == 1.2
        assert pricing.reputation_modifiers == {}
        assert pricing.bulk_discounts == {}
    
    def test_crafting_materials_defaults(self):
        """Test CraftingMaterials with default values."""
        materials = CraftingMaterials()
        assert materials.required_items == {}
        assert materials.optional_items == {}
        assert materials.tool_requirements == []
        assert materials.consumables == {}


class TestSchemaValidation:
    """Test schema validation and error handling."""
    
    def test_skill_bonuses_serialization(self):
        """Test that SkillBonuses can be serialized and deserialized."""
        bonuses = SkillBonuses(melee_damage=10, accuracy=5, health=25)
        serialized = bonuses.model_dump()
        deserialized = SkillBonuses(**serialized)
        
        assert deserialized.melee_damage == 10
        assert deserialized.accuracy == 5
        assert deserialized.health == 25
    
    def test_item_stats_serialization(self):
        """Test that ItemStats can be serialized and deserialized."""
        stats = ItemStats(damage=15, armor=8, health_bonus=30)
        serialized = stats.model_dump()
        deserialized = ItemStats(**serialized)
        
        assert deserialized.damage == 15
        assert deserialized.armor == 8
        assert deserialized.health_bonus == 30
    
    def test_complex_schema_nesting(self):
        """Test that complex nested data works correctly."""
        trade = TradeData(
            trader_1_items=[
                {"item_id": "sword", "quantity": 1, "enchantments": {"sharpness": 3}},
                {"item_id": "potion", "quantity": 5}
            ],
            agreed_terms={"trade_tax": 5, "completion_time": 300}
        )
        
        serialized = trade.model_dump()
        deserialized = TradeData(**serialized)
        
        assert len(deserialized.trader_1_items) == 2
        assert deserialized.trader_1_items[0]["enchantments"]["sharpness"] == 3
        assert deserialized.agreed_terms["trade_tax"] == 5 