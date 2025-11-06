#!/usr/bin/env python3
"""
Text RPG - The Lost Kingdom
A command-line text-based RPG adventure game
"""

import json
import os
import random
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
from enum import Enum


# ==================== ENUMS AND DATA CLASSES ====================

class CharacterClass(Enum):
    WARRIOR = "Warrior"
    MAGE = "Mage"
    ROGUE = "Rogue"
    CLERIC = "Cleric"


class ItemType(Enum):
    WEAPON = "Weapon"
    ARMOR = "Armor"
    POTION = "Potion"
    QUEST = "Quest Item"


class EnemyType(Enum):
    GOBLIN = "Goblin"
    ORC = "Orc"
    SKELETON = "Skeleton"
    DARK_KNIGHT = "Dark Knight"
    DRAGON = "Dragon"
    BANDIT = "Bandit"
    WOLF = "Wolf"


@dataclass
class Item:
    name: str
    item_type: ItemType
    value: int
    description: str
    attack_bonus: int = 0
    defense_bonus: int = 0
    health_restore: int = 0


@dataclass
class Enemy:
    name: str
    health: int
    max_health: int
    attack: int
    defense: int
    gold_drop: int
    exp_drop: int
    level: int


@dataclass
class Quest:
    name: str
    description: str
    objective: str
    reward_gold: int
    reward_exp: int
    completed: bool = False
    progress: int = 0
    goal: int = 1


@dataclass
class Character:
    name: str
    char_class: CharacterClass
    level: int = 1
    exp: int = 0
    exp_to_next: int = 100
    health: int = 100
    max_health: int = 100
    mana: int = 50
    max_mana: int = 50
    attack: int = 10
    defense: int = 5
    gold: int = 50
    inventory: List[Item] = field(default_factory=list)
    equipped_weapon: Optional[Item] = None
    equipped_armor: Optional[Item] = None
    location: str = "Village Square"
    quests: List[Quest] = field(default_factory=list)
    kills: Dict[str, int] = field(default_factory=dict)


# ==================== GAME DATA ====================

STARTING_STATS = {
    CharacterClass.WARRIOR: {
        "health": 120,
        "max_health": 120,
        "mana": 30,
        "max_mana": 30,
        "attack": 15,
        "defense": 8,
        "description": "Strong melee fighter with high health and defense"
    },
    CharacterClass.MAGE: {
        "health": 80,
        "max_health": 80,
        "mana": 100,
        "max_mana": 100,
        "attack": 20,
        "defense": 3,
        "description": "Powerful spellcaster with high attack but low defense"
    },
    CharacterClass.ROGUE: {
        "health": 90,
        "max_health": 90,
        "mana": 40,
        "max_mana": 40,
        "attack": 18,
        "defense": 5,
        "description": "Quick and agile with balanced stats and high critical chance"
    },
    CharacterClass.CLERIC: {
        "health": 100,
        "max_health": 100,
        "mana": 80,
        "max_mana": 80,
        "attack": 12,
        "defense": 6,
        "description": "Healer with restorative abilities and balanced stats"
    }
}

ITEMS_DATABASE = {
    "Health Potion": Item("Health Potion", ItemType.POTION, 20, "Restores 50 HP", health_restore=50),
    "Iron Sword": Item("Iron Sword", ItemType.WEAPON, 50, "A sturdy iron blade", attack_bonus=5),
    "Steel Sword": Item("Steel Sword", ItemType.WEAPON, 150, "A sharp steel blade", attack_bonus=12),
    "Legendary Blade": Item("Legendary Blade", ItemType.WEAPON, 500, "A legendary weapon", attack_bonus=25),
    "Leather Armor": Item("Leather Armor", ItemType.ARMOR, 40, "Basic leather protection", defense_bonus=3),
    "Chainmail": Item("Chainmail", ItemType.ARMOR, 120, "Strong metal armor", defense_bonus=8),
    "Plate Armor": Item("Plate Armor", ItemType.ARMOR, 300, "Heavy plate protection", defense_bonus=15),
    "Ancient Key": Item("Ancient Key", ItemType.QUEST, 0, "An old rusty key with mysterious markings"),
    "Dragon Scale": Item("Dragon Scale", ItemType.QUEST, 0, "A shimmering scale from a dragon"),
}

LOCATIONS = {
    "Village Square": {
        "description": "The heart of the village. People bustle about their daily business.",
        "connections": ["Tavern", "General Store", "Forest Path", "Training Grounds"],
        "npcs": ["Village Elder"],
        "shop": False
    },
    "Tavern": {
        "description": "A cozy tavern filled with adventurers sharing stories.",
        "connections": ["Village Square"],
        "npcs": ["Bartender", "Mysterious Stranger"],
        "shop": False
    },
    "General Store": {
        "description": "A shop with various goods and equipment.",
        "connections": ["Village Square"],
        "npcs": ["Shopkeeper"],
        "shop": True
    },
    "Training Grounds": {
        "description": "An area where warriors train. Dummies and weapons are scattered about.",
        "connections": ["Village Square"],
        "npcs": ["Master Trainer"],
        "shop": False
    },
    "Forest Path": {
        "description": "A dirt path leading into the dark forest. You hear strange sounds.",
        "connections": ["Village Square", "Dark Forest", "Abandoned Mine"],
        "npcs": [],
        "enemies": ["Wolf", "Bandit"],
        "shop": False
    },
    "Dark Forest": {
        "description": "A dense, dark forest. Danger lurks behind every tree.",
        "connections": ["Forest Path", "Ancient Ruins"],
        "npcs": [],
        "enemies": ["Goblin", "Wolf", "Orc"],
        "shop": False
    },
    "Abandoned Mine": {
        "description": "An old mine shaft. The air is cold and damp.",
        "connections": ["Forest Path", "Deep Cavern"],
        "npcs": [],
        "enemies": ["Goblin", "Skeleton"],
        "shop": False
    },
    "Deep Cavern": {
        "description": "A deep, dark cavern. You can barely see ahead.",
        "connections": ["Abandoned Mine", "Dragon's Lair"],
        "npcs": [],
        "enemies": ["Skeleton", "Orc", "Dark Knight"],
        "shop": False
    },
    "Ancient Ruins": {
        "description": "Crumbling stone structures from a forgotten age.",
        "connections": ["Dark Forest"],
        "npcs": ["Ancient Guardian"],
        "enemies": ["Skeleton", "Dark Knight"],
        "shop": False
    },
    "Dragon's Lair": {
        "description": "A massive cave filled with treasures... and danger.",
        "connections": ["Deep Cavern"],
        "npcs": [],
        "enemies": ["Dragon"],
        "shop": False
    }
}

ENEMY_STATS = {
    EnemyType.GOBLIN: {"health": 30, "attack": 8, "defense": 2, "gold": 10, "exp": 25, "level": 1},
    EnemyType.WOLF: {"health": 35, "attack": 10, "defense": 3, "gold": 8, "exp": 20, "level": 1},
    EnemyType.BANDIT: {"health": 45, "attack": 12, "defense": 4, "gold": 25, "exp": 35, "level": 2},
    EnemyType.ORC: {"health": 60, "attack": 15, "defense": 6, "gold": 30, "exp": 50, "level": 3},
    EnemyType.SKELETON: {"health": 50, "attack": 13, "defense": 5, "gold": 20, "exp": 45, "level": 3},
    EnemyType.DARK_KNIGHT: {"health": 100, "attack": 20, "defense": 10, "gold": 75, "exp": 100, "level": 5},
    EnemyType.DRAGON: {"health": 300, "attack": 35, "defense": 15, "gold": 500, "exp": 500, "level": 10},
}


# ==================== GAME CLASS ====================

class Game:
    def __init__(self):
        self.character: Optional[Character] = None
        self.game_over = False
        self.save_file = "savegame.json"

    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_slow(self, text: str, delay: float = 0.03):
        """Print text with a typewriter effect"""
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()

    def print_separator(self):
        """Print a visual separator"""
        print("\n" + "=" * 70 + "\n")

    def print_title(self):
        """Print the game title"""
        self.clear_screen()
        title = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║              THE LOST KINGDOM - A Text RPG Adventure             ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
        """
        print(title)

    def press_enter(self):
        """Wait for user to press enter"""
        input("\nPress Enter to continue...")

    def create_character(self):
        """Character creation process"""
        self.print_title()
        self.print_slow("Welcome, brave adventurer!")
        self.print_separator()

        # Get character name
        name = input("Enter your character's name: ").strip()
        while not name:
            name = input("Please enter a valid name: ").strip()

        # Choose class
        print("\nChoose your class:\n")
        for i, char_class in enumerate(CharacterClass, 1):
            stats = STARTING_STATS[char_class]
            print(f"{i}. {char_class.value}")
            print(f"   {stats['description']}")
            print(f"   HP: {stats['health']} | Mana: {stats['mana']} | "
                  f"Attack: {stats['attack']} | Defense: {stats['defense']}\n")

        while True:
            try:
                choice = int(input("Enter your choice (1-4): "))
                if 1 <= choice <= 4:
                    chosen_class = list(CharacterClass)[choice - 1]
                    break
                else:
                    print("Invalid choice. Please enter a number between 1 and 4.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        # Create character with chosen stats
        stats = STARTING_STATS[chosen_class]
        self.character = Character(
            name=name,
            char_class=chosen_class,
            health=stats["health"],
            max_health=stats["max_health"],
            mana=stats["mana"],
            max_mana=stats["max_mana"],
            attack=stats["attack"],
            defense=stats["defense"]
        )

        # Add starting items
        self.character.inventory.append(ITEMS_DATABASE["Health Potion"])
        self.character.inventory.append(ITEMS_DATABASE["Health Potion"])

        # Add starting quest
        starter_quest = Quest(
            name="The Lost Kingdom",
            description="The kingdom has fallen into darkness. Investigate the ancient ruins.",
            objective="Defeat the Dragon in the Dragon's Lair",
            reward_gold=1000,
            reward_exp=500,
            goal=1
        )
        self.character.quests.append(starter_quest)

        self.print_separator()
        self.print_slow(f"\nWelcome, {name} the {chosen_class.value}!")
        self.print_slow("Your adventure begins in the Village Square...")
        self.press_enter()

    def show_stats(self):
        """Display character stats"""
        c = self.character
        print("\n" + "═" * 70)
        print(f"  {c.name} the {c.char_class.value} | Level {c.level}")
        print("═" * 70)
        print(f"  HP: {c.health}/{c.max_health} | Mana: {c.mana}/{c.max_mana} | Gold: {c.gold}")
        print(f"  Attack: {c.attack} | Defense: {c.defense}")
        print(f"  EXP: {c.exp}/{c.exp_to_next}")

        if c.equipped_weapon:
            print(f"  Weapon: {c.equipped_weapon.name} (+{c.equipped_weapon.attack_bonus} ATK)")
        if c.equipped_armor:
            print(f"  Armor: {c.equipped_armor.name} (+{c.equipped_armor.defense_bonus} DEF)")

        print(f"  Location: {c.location}")
        print("═" * 70 + "\n")

    def show_inventory(self):
        """Display and manage inventory"""
        while True:
            self.clear_screen()
            self.show_stats()
            print("INVENTORY")
            print("-" * 70)

            if not self.character.inventory:
                print("Your inventory is empty.")
            else:
                for i, item in enumerate(self.character.inventory, 1):
                    print(f"{i}. {item.name} ({item.item_type.value})")
                    print(f"   {item.description} | Value: {item.value} gold")
                    if item.attack_bonus > 0:
                        print(f"   Attack Bonus: +{item.attack_bonus}")
                    if item.defense_bonus > 0:
                        print(f"   Defense Bonus: +{item.defense_bonus}")
                    if item.health_restore > 0:
                        print(f"   Restores: {item.health_restore} HP")
                    print()

            print("\nOptions:")
            print("1. Use/Equip item")
            print("2. Drop item")
            print("3. Back to main menu")

            choice = input("\nChoose an option: ").strip()

            if choice == "1" and self.character.inventory:
                item_num = input("Enter item number to use/equip: ").strip()
                try:
                    item_idx = int(item_num) - 1
                    if 0 <= item_idx < len(self.character.inventory):
                        self.use_item(item_idx)
                except ValueError:
                    print("Invalid input.")
                    self.press_enter()
            elif choice == "2" and self.character.inventory:
                item_num = input("Enter item number to drop: ").strip()
                try:
                    item_idx = int(item_num) - 1
                    if 0 <= item_idx < len(self.character.inventory):
                        dropped = self.character.inventory.pop(item_idx)
                        print(f"\nDropped {dropped.name}.")
                        self.press_enter()
                except ValueError:
                    print("Invalid input.")
                    self.press_enter()
            elif choice == "3":
                break

    def use_item(self, item_idx: int):
        """Use or equip an item"""
        item = self.character.inventory[item_idx]

        if item.item_type == ItemType.POTION:
            if item.health_restore > 0:
                old_health = self.character.health
                self.character.health = min(self.character.max_health,
                                          self.character.health + item.health_restore)
                healed = self.character.health - old_health
                print(f"\nUsed {item.name}! Restored {healed} HP.")
                self.character.inventory.pop(item_idx)
                self.press_enter()

        elif item.item_type == ItemType.WEAPON:
            if self.character.equipped_weapon:
                self.character.inventory.append(self.character.equipped_weapon)
            self.character.equipped_weapon = self.character.inventory.pop(item_idx)
            print(f"\nEquipped {item.name}!")
            self.press_enter()

        elif item.item_type == ItemType.ARMOR:
            if self.character.equipped_armor:
                self.character.inventory.append(self.character.equipped_armor)
            self.character.equipped_armor = self.character.inventory.pop(item_idx)
            print(f"\nEquipped {item.name}!")
            self.press_enter()

        else:
            print(f"\nYou examine the {item.name}. {item.description}")
            self.press_enter()

    def show_quests(self):
        """Display active quests"""
        self.clear_screen()
        self.show_stats()
        print("ACTIVE QUESTS")
        print("-" * 70)

        if not self.character.quests:
            print("No active quests.")
        else:
            for quest in self.character.quests:
                status = "✓ COMPLETED" if quest.completed else f"Progress: {quest.progress}/{quest.goal}"
                print(f"\n{quest.name} [{status}]")
                print(f"  {quest.description}")
                print(f"  Objective: {quest.objective}")
                print(f"  Reward: {quest.reward_gold} gold, {quest.reward_exp} EXP")

        self.press_enter()

    def explore_location(self):
        """Explore current location"""
        location = LOCATIONS[self.character.location]

        self.clear_screen()
        self.show_stats()
        print(f"LOCATION: {self.character.location.upper()}")
        print("-" * 70)
        print(location["description"])
        print()

        # Show NPCs
        if location["npcs"]:
            print("NPCs here:")
            for npc in location["npcs"]:
                print(f"  - {npc}")
            print()

        # Show connections
        print("You can travel to:")
        for i, conn in enumerate(location["connections"], 1):
            print(f"  {i}. {conn}")
        print()

        print("Options:")
        print("T - Travel to another location")
        if location["npcs"]:
            print("N - Talk to NPC")
        if "enemies" in location:
            print("E - Look for enemies")
        if location["shop"]:
            print("S - Visit shop")
        print("B - Back to main menu")

        choice = input("\nWhat would you like to do? ").strip().upper()

        if choice == "T":
            self.travel(location["connections"])
        elif choice == "N" and location["npcs"]:
            self.talk_to_npc(location["npcs"])
        elif choice == "E" and "enemies" in location:
            self.encounter_enemy(location["enemies"])
        elif choice == "S" and location["shop"]:
            self.visit_shop()

    def travel(self, connections: List[str]):
        """Travel to a new location"""
        print("\nWhere would you like to go?")
        for i, conn in enumerate(connections, 1):
            print(f"{i}. {conn}")

        try:
            choice = int(input("\nEnter your choice: ")) - 1
            if 0 <= choice < len(connections):
                self.character.location = connections[choice]
                print(f"\nTraveling to {connections[choice]}...")
                time.sleep(1)
        except ValueError:
            print("Invalid input.")
            self.press_enter()

    def talk_to_npc(self, npcs: List[str]):
        """Talk to an NPC"""
        print("\nWho would you like to talk to?")
        for i, npc in enumerate(npcs, 1):
            print(f"{i}. {npc}")

        try:
            choice = int(input("\nEnter your choice: ")) - 1
            if 0 <= choice < len(npcs):
                npc = npcs[choice]
                self.npc_dialogue(npc)
        except ValueError:
            print("Invalid input.")
            self.press_enter()

    def npc_dialogue(self, npc_name: str):
        """Show NPC dialogue"""
        dialogues = {
            "Village Elder": "Greetings, brave adventurer! The kingdom needs heroes like you. "
                           "Dark forces have awakened in the ancient ruins. Be careful!",
            "Bartender": "Welcome to my tavern! I've heard rumors of a fearsome dragon "
                        "hoarding treasure in the mountains. Care for a drink?",
            "Mysterious Stranger": "I know secrets... for the right price. The ancient ruins "
                                  "hold great power, but also great danger.",
            "Shopkeeper": "Welcome! Check out my wares. I have the finest equipment in the land!",
            "Master Trainer": f"Your skills are improving, {self.character.name}. Keep training "
                            "and you'll become a legend!",
            "Ancient Guardian": "You have proven yourself worthy, adventurer. May the ancient "
                              "spirits guide you in your quest."
        }

        print(f"\n{npc_name} says:")
        self.print_slow(f'"{dialogues.get(npc_name, "Hello, adventurer!")}"')
        self.press_enter()

    def visit_shop(self):
        """Visit the shop to buy/sell items"""
        shop_items = [
            ITEMS_DATABASE["Health Potion"],
            ITEMS_DATABASE["Iron Sword"],
            ITEMS_DATABASE["Steel Sword"],
            ITEMS_DATABASE["Leather Armor"],
            ITEMS_DATABASE["Chainmail"],
        ]

        while True:
            self.clear_screen()
            self.show_stats()
            print("GENERAL STORE")
            print("-" * 70)
            print("Welcome to the shop!\n")
            print("Items for sale:")
            for i, item in enumerate(shop_items, 1):
                print(f"{i}. {item.name} - {item.value} gold")
                print(f"   {item.description}")
                if item.attack_bonus:
                    print(f"   +{item.attack_bonus} Attack")
                if item.defense_bonus:
                    print(f"   +{item.defense_bonus} Defense")
                print()

            print("\nOptions:")
            print("1. Buy item")
            print("2. Sell item")
            print("3. Leave shop")

            choice = input("\nWhat would you like to do? ").strip()

            if choice == "1":
                try:
                    item_num = int(input("Enter item number to buy: ")) - 1
                    if 0 <= item_num < len(shop_items):
                        item = shop_items[item_num]
                        if self.character.gold >= item.value:
                            self.character.gold -= item.value
                            # Create a new instance of the item
                            new_item = Item(item.name, item.item_type, item.value,
                                          item.description, item.attack_bonus,
                                          item.defense_bonus, item.health_restore)
                            self.character.inventory.append(new_item)
                            print(f"\nPurchased {item.name}!")
                        else:
                            print("\nNot enough gold!")
                    else:
                        print("\nInvalid item number.")
                except ValueError:
                    print("\nInvalid input.")
                self.press_enter()

            elif choice == "2":
                if self.character.inventory:
                    print("\nYour inventory:")
                    for i, item in enumerate(self.character.inventory, 1):
                        print(f"{i}. {item.name} - {item.value // 2} gold")
                    try:
                        item_num = int(input("\nEnter item number to sell: ")) - 1
                        if 0 <= item_num < len(self.character.inventory):
                            item = self.character.inventory.pop(item_num)
                            sell_price = item.value // 2
                            self.character.gold += sell_price
                            print(f"\nSold {item.name} for {sell_price} gold!")
                        else:
                            print("\nInvalid item number.")
                    except ValueError:
                        print("\nInvalid input.")
                else:
                    print("\nYour inventory is empty!")
                self.press_enter()

            elif choice == "3":
                break

    def encounter_enemy(self, enemy_list: List[str]):
        """Encounter a random enemy"""
        enemy_name = random.choice(enemy_list)
        enemy_type = EnemyType[enemy_name.upper().replace(" ", "_")]

        enemy = self.create_enemy(enemy_type)

        print(f"\nA wild {enemy.name} appears!")
        time.sleep(1)

        self.combat(enemy)

    def create_enemy(self, enemy_type: EnemyType) -> Enemy:
        """Create an enemy instance"""
        stats = ENEMY_STATS[enemy_type]
        return Enemy(
            name=enemy_type.value,
            health=stats["health"],
            max_health=stats["health"],
            attack=stats["attack"],
            defense=stats["defense"],
            gold_drop=stats["gold"],
            exp_drop=stats["exp"],
            level=stats["level"]
        )

    def combat(self, enemy: Enemy):
        """Combat system"""
        print("\n" + "=" * 70)
        print("COMBAT BEGINS!")
        print("=" * 70)

        while enemy.health > 0 and self.character.health > 0:
            # Show combat status
            print(f"\n{self.character.name}: {self.character.health}/{self.character.max_health} HP")
            print(f"{enemy.name}: {enemy.health}/{enemy.max_health} HP")
            print()

            # Player turn
            print("Your turn!")
            print("1. Attack")
            print("2. Use Item")
            print("3. Run Away")

            choice = input("\nWhat will you do? ").strip()

            if choice == "1":
                # Player attacks
                total_attack = self.character.attack
                if self.character.equipped_weapon:
                    total_attack += self.character.equipped_weapon.attack_bonus

                # Calculate damage with some randomness
                damage = max(1, total_attack - enemy.defense + random.randint(-3, 3))

                # Critical hit chance (20% for rogues, 10% for others)
                crit_chance = 0.2 if self.character.char_class == CharacterClass.ROGUE else 0.1
                if random.random() < crit_chance:
                    damage *= 2
                    print(f"\n💥 CRITICAL HIT! You deal {damage} damage to the {enemy.name}!")
                else:
                    print(f"\n⚔️  You attack the {enemy.name} for {damage} damage!")

                enemy.health -= damage
                time.sleep(1)

                if enemy.health <= 0:
                    self.victory(enemy)
                    return

                # Enemy turn
                total_defense = self.character.defense
                if self.character.equipped_armor:
                    total_defense += self.character.equipped_armor.defense_bonus

                enemy_damage = max(1, enemy.attack - total_defense + random.randint(-2, 2))
                print(f"\n🗡️  The {enemy.name} attacks you for {enemy_damage} damage!")
                self.character.health -= enemy_damage
                time.sleep(1)

                if self.character.health <= 0:
                    self.game_over = True
                    print("\n" + "=" * 70)
                    print("YOU HAVE BEEN DEFEATED!")
                    print("=" * 70)
                    print("\nGame Over...")
                    self.press_enter()
                    return

            elif choice == "2":
                # Use item
                potions = [(i, item) for i, item in enumerate(self.character.inventory)
                          if item.item_type == ItemType.POTION]

                if potions:
                    print("\nAvailable potions:")
                    for i, (idx, item) in enumerate(potions, 1):
                        print(f"{i}. {item.name}")

                    try:
                        potion_choice = int(input("Choose a potion: ")) - 1
                        if 0 <= potion_choice < len(potions):
                            idx, potion = potions[potion_choice]
                            old_health = self.character.health
                            self.character.health = min(self.character.max_health,
                                                       self.character.health + potion.health_restore)
                            healed = self.character.health - old_health
                            print(f"\n💚 Used {potion.name}! Restored {healed} HP.")
                            self.character.inventory.pop(idx)
                            time.sleep(1)

                            # Enemy still attacks
                            total_defense = self.character.defense
                            if self.character.equipped_armor:
                                total_defense += self.character.equipped_armor.defense_bonus

                            enemy_damage = max(1, enemy.attack - total_defense + random.randint(-2, 2))
                            print(f"\n🗡️  The {enemy.name} attacks you for {enemy_damage} damage!")
                            self.character.health -= enemy_damage
                            time.sleep(1)
                    except (ValueError, IndexError):
                        print("Invalid choice.")
                        time.sleep(1)
                else:
                    print("\nNo potions available!")
                    time.sleep(1)

            elif choice == "3":
                # Run away
                if random.random() < 0.5:
                    print("\nYou successfully ran away!")
                    self.press_enter()
                    return
                else:
                    print("\nCouldn't escape!")
                    # Enemy attacks
                    total_defense = self.character.defense
                    if self.character.equipped_armor:
                        total_defense += self.character.equipped_armor.defense_bonus

                    enemy_damage = max(1, enemy.attack - total_defense + random.randint(-2, 2))
                    print(f"\n🗡️  The {enemy.name} attacks you for {enemy_damage} damage!")
                    self.character.health -= enemy_damage
                    time.sleep(1)

    def victory(self, enemy: Enemy):
        """Handle victory after combat"""
        print("\n" + "=" * 70)
        print(f"🎉 VICTORY! You defeated the {enemy.name}!")
        print("=" * 70)

        # Track kills
        if enemy.name in self.character.kills:
            self.character.kills[enemy.name] += 1
        else:
            self.character.kills[enemy.name] = 1

        # Rewards
        print(f"\n💰 +{enemy.gold_drop} gold")
        print(f"⭐ +{enemy.exp_drop} EXP")

        self.character.gold += enemy.gold_drop
        self.character.exp += enemy.exp_drop

        # Check for level up
        if self.character.exp >= self.character.exp_to_next:
            self.level_up()

        # Update quests
        for quest in self.character.quests:
            if not quest.completed and "Dragon" in quest.objective and enemy.name == "Dragon":
                quest.progress += 1
                if quest.progress >= quest.goal:
                    quest.completed = True
                    print(f"\n🎊 QUEST COMPLETED: {quest.name}!")
                    print(f"💰 +{quest.reward_gold} gold")
                    print(f"⭐ +{quest.reward_exp} EXP")
                    self.character.gold += quest.reward_gold
                    self.character.exp += quest.reward_exp

        # Random loot
        if random.random() < 0.3:  # 30% chance
            loot_table = ["Health Potion", "Iron Sword", "Steel Sword", "Leather Armor", "Chainmail"]
            loot = ITEMS_DATABASE[random.choice(loot_table)]
            new_item = Item(loot.name, loot.item_type, loot.value,
                          loot.description, loot.attack_bonus,
                          loot.defense_bonus, loot.health_restore)
            self.character.inventory.append(new_item)
            print(f"🎁 Found: {loot.name}!")

        self.press_enter()

    def level_up(self):
        """Level up the character"""
        self.character.level += 1
        self.character.exp -= self.character.exp_to_next
        self.character.exp_to_next = int(self.character.exp_to_next * 1.5)

        # Stat increases
        health_increase = 20
        mana_increase = 10
        attack_increase = 3
        defense_increase = 2

        self.character.max_health += health_increase
        self.character.health = self.character.max_health
        self.character.max_mana += mana_increase
        self.character.mana = self.character.max_mana
        self.character.attack += attack_increase
        self.character.defense += defense_increase

        print("\n" + "=" * 70)
        print(f"🌟 LEVEL UP! You are now level {self.character.level}!")
        print("=" * 70)
        print(f"Max HP: +{health_increase}")
        print(f"Max Mana: +{mana_increase}")
        print(f"Attack: +{attack_increase}")
        print(f"Defense: +{defense_increase}")
        print("=" * 70)

    def save_game(self):
        """Save the game to a file"""
        if not self.character:
            print("No character to save!")
            return

        # Convert character to dict
        save_data = {
            "name": self.character.name,
            "char_class": self.character.char_class.value,
            "level": self.character.level,
            "exp": self.character.exp,
            "exp_to_next": self.character.exp_to_next,
            "health": self.character.health,
            "max_health": self.character.max_health,
            "mana": self.character.mana,
            "max_mana": self.character.max_mana,
            "attack": self.character.attack,
            "defense": self.character.defense,
            "gold": self.character.gold,
            "location": self.character.location,
            "kills": self.character.kills,
            "inventory": [asdict(item) for item in self.character.inventory],
            "equipped_weapon": asdict(self.character.equipped_weapon) if self.character.equipped_weapon else None,
            "equipped_armor": asdict(self.character.equipped_armor) if self.character.equipped_armor else None,
            "quests": [asdict(quest) for quest in self.character.quests]
        }

        with open(self.save_file, 'w') as f:
            json.dump(save_data, f, indent=2)

        print("\n💾 Game saved successfully!")
        self.press_enter()

    def load_game(self):
        """Load the game from a file"""
        if not os.path.exists(self.save_file):
            print("\nNo save file found!")
            self.press_enter()
            return False

        try:
            with open(self.save_file, 'r') as f:
                save_data = json.load(f)

            # Convert dict back to character
            char_class = CharacterClass(save_data["char_class"])

            # Reconstruct inventory
            inventory = []
            for item_data in save_data["inventory"]:
                item_data["item_type"] = ItemType(item_data["item_type"])
                inventory.append(Item(**item_data))

            # Reconstruct equipped items
            equipped_weapon = None
            if save_data["equipped_weapon"]:
                save_data["equipped_weapon"]["item_type"] = ItemType(save_data["equipped_weapon"]["item_type"])
                equipped_weapon = Item(**save_data["equipped_weapon"])

            equipped_armor = None
            if save_data["equipped_armor"]:
                save_data["equipped_armor"]["item_type"] = ItemType(save_data["equipped_armor"]["item_type"])
                equipped_armor = Item(**save_data["equipped_armor"])

            # Reconstruct quests
            quests = [Quest(**quest_data) for quest_data in save_data["quests"]]

            self.character = Character(
                name=save_data["name"],
                char_class=char_class,
                level=save_data["level"],
                exp=save_data["exp"],
                exp_to_next=save_data["exp_to_next"],
                health=save_data["health"],
                max_health=save_data["max_health"],
                mana=save_data["mana"],
                max_mana=save_data["max_mana"],
                attack=save_data["attack"],
                defense=save_data["defense"],
                gold=save_data["gold"],
                location=save_data["location"],
                kills=save_data["kills"],
                inventory=inventory,
                equipped_weapon=equipped_weapon,
                equipped_armor=equipped_armor,
                quests=quests
            )

            print("\n💾 Game loaded successfully!")
            self.press_enter()
            return True

        except Exception as e:
            print(f"\nError loading save file: {e}")
            self.press_enter()
            return False

    def main_menu(self):
        """Main game menu"""
        while not self.game_over:
            self.clear_screen()
            self.show_stats()

            print("MAIN MENU")
            print("-" * 70)
            print("1. Explore current location")
            print("2. View inventory")
            print("3. View quests")
            print("4. Character stats")
            print("5. Save game")
            print("6. Quit game")

            choice = input("\nWhat would you like to do? ").strip()

            if choice == "1":
                self.explore_location()
            elif choice == "2":
                self.show_inventory()
            elif choice == "3":
                self.show_quests()
            elif choice == "4":
                self.press_enter()
            elif choice == "5":
                self.save_game()
            elif choice == "6":
                confirm = input("\nAre you sure you want to quit? (y/n): ").strip().lower()
                if confirm == 'y':
                    print("\nThanks for playing The Lost Kingdom!")
                    break

    def start_game(self):
        """Start the game"""
        self.print_title()

        print("\n1. New Game")
        print("2. Load Game")
        print("3. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            self.create_character()
            self.main_menu()
        elif choice == "2":
            if self.load_game():
                self.main_menu()
            else:
                self.start_game()
        elif choice == "3":
            print("\nGoodbye!")
            return


# ==================== MAIN ====================

def main():
    """Main entry point"""
    game = Game()
    game.start_game()


if __name__ == "__main__":
    main()
