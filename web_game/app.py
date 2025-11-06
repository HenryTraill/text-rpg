#!/usr/bin/env python3
"""
Web-based Text RPG - The Lost Kingdom
Flask application for browser-based gameplay
"""

from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import secrets
import json
import random
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
from enum import Enum

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


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
    item_type: str
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
    char_class: str
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
    inventory: List[Dict] = field(default_factory=list)
    equipped_weapon: Optional[Dict] = None
    equipped_armor: Optional[Dict] = None
    location: str = "Village Square"
    quests: List[Dict] = field(default_factory=list)
    kills: Dict[str, int] = field(default_factory=dict)


# ==================== GAME DATA ====================

STARTING_STATS = {
    "Warrior": {
        "health": 120,
        "max_health": 120,
        "mana": 30,
        "max_mana": 30,
        "attack": 15,
        "defense": 8,
        "description": "Strong melee fighter with high health and defense"
    },
    "Mage": {
        "health": 80,
        "max_health": 80,
        "mana": 100,
        "max_mana": 100,
        "attack": 20,
        "defense": 3,
        "description": "Powerful spellcaster with high attack but low defense"
    },
    "Rogue": {
        "health": 90,
        "max_health": 90,
        "mana": 40,
        "max_mana": 40,
        "attack": 18,
        "defense": 5,
        "description": "Quick and agile with balanced stats and high critical chance"
    },
    "Cleric": {
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
    "Health Potion": {"name": "Health Potion", "item_type": "Potion", "value": 20, "description": "Restores 50 HP", "health_restore": 50, "attack_bonus": 0, "defense_bonus": 0},
    "Iron Sword": {"name": "Iron Sword", "item_type": "Weapon", "value": 50, "description": "A sturdy iron blade", "attack_bonus": 5, "defense_bonus": 0, "health_restore": 0},
    "Steel Sword": {"name": "Steel Sword", "item_type": "Weapon", "value": 150, "description": "A sharp steel blade", "attack_bonus": 12, "defense_bonus": 0, "health_restore": 0},
    "Legendary Blade": {"name": "Legendary Blade", "item_type": "Weapon", "value": 500, "description": "A legendary weapon", "attack_bonus": 25, "defense_bonus": 0, "health_restore": 0},
    "Leather Armor": {"name": "Leather Armor", "item_type": "Armor", "value": 40, "description": "Basic leather protection", "defense_bonus": 3, "attack_bonus": 0, "health_restore": 0},
    "Chainmail": {"name": "Chainmail", "item_type": "Armor", "value": 120, "description": "Strong metal armor", "defense_bonus": 8, "attack_bonus": 0, "health_restore": 0},
    "Plate Armor": {"name": "Plate Armor", "item_type": "Armor", "value": 300, "description": "Heavy plate protection", "defense_bonus": 15, "attack_bonus": 0, "health_restore": 0},
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
    "Goblin": {"health": 30, "attack": 8, "defense": 2, "gold": 10, "exp": 25, "level": 1},
    "Wolf": {"health": 35, "attack": 10, "defense": 3, "gold": 8, "exp": 20, "level": 1},
    "Bandit": {"health": 45, "attack": 12, "defense": 4, "gold": 25, "exp": 35, "level": 2},
    "Orc": {"health": 60, "attack": 15, "defense": 6, "gold": 30, "exp": 50, "level": 3},
    "Skeleton": {"health": 50, "attack": 13, "defense": 5, "gold": 20, "exp": 45, "level": 3},
    "Dark Knight": {"health": 100, "attack": 20, "defense": 10, "gold": 75, "exp": 100, "level": 5},
    "Dragon": {"health": 300, "attack": 35, "defense": 15, "gold": 500, "exp": 500, "level": 10},
}

NPC_DIALOGUES = {
    "Village Elder": "Greetings, brave adventurer! The kingdom needs heroes like you. Dark forces have awakened in the ancient ruins. Be careful!",
    "Bartender": "Welcome to my tavern! I've heard rumors of a fearsome dragon hoarding treasure in the mountains. Care for a drink?",
    "Mysterious Stranger": "I know secrets... for the right price. The ancient ruins hold great power, but also great danger.",
    "Shopkeeper": "Welcome! Check out my wares. I have the finest equipment in the land!",
    "Master Trainer": "Your skills are improving! Keep training and you'll become a legend!",
    "Ancient Guardian": "You have proven yourself worthy, adventurer. May the ancient spirits guide you in your quest."
}


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Main game page"""
    return render_template('index.html')


@app.route('/api/create_character', methods=['POST'])
def create_character():
    """Create a new character"""
    data = request.json
    name = data.get('name', 'Hero')
    char_class = data.get('char_class', 'Warrior')

    stats = STARTING_STATS[char_class]

    character = {
        'name': name,
        'char_class': char_class,
        'level': 1,
        'exp': 0,
        'exp_to_next': 100,
        'health': stats['health'],
        'max_health': stats['max_health'],
        'mana': stats['mana'],
        'max_mana': stats['max_mana'],
        'attack': stats['attack'],
        'defense': stats['defense'],
        'gold': 50,
        'inventory': [
            ITEMS_DATABASE["Health Potion"].copy(),
            ITEMS_DATABASE["Health Potion"].copy()
        ],
        'equipped_weapon': None,
        'equipped_armor': None,
        'location': 'Village Square',
        'quests': [{
            'name': 'The Lost Kingdom',
            'description': 'The kingdom has fallen into darkness. Investigate the ancient ruins.',
            'objective': 'Defeat the Dragon in the Dragon\'s Lair',
            'reward_gold': 1000,
            'reward_exp': 500,
            'completed': False,
            'progress': 0,
            'goal': 1
        }],
        'kills': {}
    }

    session['character'] = character
    session['in_combat'] = False
    session['current_enemy'] = None

    return jsonify({
        'success': True,
        'character': character,
        'message': f'Welcome, {name} the {char_class}! Your adventure begins...'
    })


@app.route('/api/get_game_state', methods=['GET'])
def get_game_state():
    """Get current game state"""
    character = session.get('character')
    if not character:
        return jsonify({'success': False, 'message': 'No active character'})

    location = LOCATIONS[character['location']]

    return jsonify({
        'success': True,
        'character': character,
        'location': location,
        'location_name': character['location'],
        'in_combat': session.get('in_combat', False),
        'current_enemy': session.get('current_enemy')
    })


@app.route('/api/travel', methods=['POST'])
def travel():
    """Travel to a new location"""
    character = session.get('character')
    if not character:
        return jsonify({'success': False, 'message': 'No active character'})

    destination = request.json.get('destination')
    current_location = LOCATIONS[character['location']]

    if destination in current_location['connections']:
        character['location'] = destination
        session['character'] = character
        return jsonify({
            'success': True,
            'message': f'Traveled to {destination}',
            'character': character
        })
    else:
        return jsonify({'success': False, 'message': 'Cannot travel there'})


@app.route('/api/talk_npc', methods=['POST'])
def talk_npc():
    """Talk to an NPC"""
    npc = request.json.get('npc')
    dialogue = NPC_DIALOGUES.get(npc, "Hello, adventurer!")

    return jsonify({
        'success': True,
        'npc': npc,
        'dialogue': dialogue
    })


@app.route('/api/encounter_enemy', methods=['POST'])
def encounter_enemy():
    """Start a random enemy encounter"""
    character = session.get('character')
    if not character:
        return jsonify({'success': False, 'message': 'No active character'})

    location = LOCATIONS[character['location']]
    if 'enemies' not in location:
        return jsonify({'success': False, 'message': 'No enemies here'})

    enemy_name = random.choice(location['enemies'])
    stats = ENEMY_STATS[enemy_name]

    enemy = {
        'name': enemy_name,
        'health': stats['health'],
        'max_health': stats['health'],
        'attack': stats['attack'],
        'defense': stats['defense'],
        'gold_drop': stats['gold'],
        'exp_drop': stats['exp'],
        'level': stats['level']
    }

    session['in_combat'] = True
    session['current_enemy'] = enemy

    return jsonify({
        'success': True,
        'message': f'A wild {enemy_name} appears!',
        'enemy': enemy
    })


@app.route('/api/combat_action', methods=['POST'])
def combat_action():
    """Perform a combat action"""
    character = session.get('character')
    enemy = session.get('current_enemy')

    if not character or not enemy:
        return jsonify({'success': False, 'message': 'Not in combat'})

    action = request.json.get('action')
    messages = []

    if action == 'attack':
        # Player attacks
        total_attack = character['attack']
        if character['equipped_weapon']:
            total_attack += character['equipped_weapon']['attack_bonus']

        damage = max(1, total_attack - enemy['defense'] + random.randint(-3, 3))

        # Critical hit
        crit_chance = 0.2 if character['char_class'] == 'Rogue' else 0.1
        if random.random() < crit_chance:
            damage *= 2
            messages.append(f"💥 CRITICAL HIT! You deal {damage} damage!")
        else:
            messages.append(f"⚔️ You attack for {damage} damage!")

        enemy['health'] -= damage

        if enemy['health'] <= 0:
            # Victory
            result = handle_victory(character, enemy)
            session['in_combat'] = False
            session['current_enemy'] = None
            session['character'] = character
            return jsonify({
                'success': True,
                'messages': messages + result['messages'],
                'victory': True,
                'character': character
            })

        # Enemy attacks
        total_defense = character['defense']
        if character['equipped_armor']:
            total_defense += character['equipped_armor']['defense_bonus']

        enemy_damage = max(1, enemy['attack'] - total_defense + random.randint(-2, 2))
        messages.append(f"🗡️ {enemy['name']} attacks for {enemy_damage} damage!")
        character['health'] -= enemy_damage

        if character['health'] <= 0:
            session['character'] = character
            return jsonify({
                'success': True,
                'messages': messages + ['💀 You have been defeated! Game Over.'],
                'defeat': True,
                'character': character
            })

        session['current_enemy'] = enemy
        session['character'] = character

        return jsonify({
            'success': True,
            'messages': messages,
            'character': character,
            'enemy': enemy
        })

    elif action == 'use_item':
        item_index = request.json.get('item_index')
        if item_index is not None and item_index < len(character['inventory']):
            item = character['inventory'][item_index]
            if item['item_type'] == 'Potion' and item['health_restore'] > 0:
                old_health = character['health']
                character['health'] = min(character['max_health'],
                                        character['health'] + item['health_restore'])
                healed = character['health'] - old_health
                messages.append(f"💚 Used {item['name']}! Restored {healed} HP.")
                character['inventory'].pop(item_index)

                # Enemy still attacks
                total_defense = character['defense']
                if character['equipped_armor']:
                    total_defense += character['equipped_armor']['defense_bonus']

                enemy_damage = max(1, enemy['attack'] - total_defense + random.randint(-2, 2))
                messages.append(f"🗡️ {enemy['name']} attacks for {enemy_damage} damage!")
                character['health'] -= enemy_damage

                session['character'] = character
                session['current_enemy'] = enemy

                return jsonify({
                    'success': True,
                    'messages': messages,
                    'character': character,
                    'enemy': enemy
                })

    elif action == 'run':
        if random.random() < 0.5:
            session['in_combat'] = False
            session['current_enemy'] = None
            return jsonify({
                'success': True,
                'messages': ['💨 You successfully ran away!'],
                'escaped': True
            })
        else:
            messages.append("❌ Couldn't escape!")

            # Enemy attacks
            total_defense = character['defense']
            if character['equipped_armor']:
                total_defense += character['equipped_armor']['defense_bonus']

            enemy_damage = max(1, enemy['attack'] - total_defense + random.randint(-2, 2))
            messages.append(f"🗡️ {enemy['name']} attacks for {enemy_damage} damage!")
            character['health'] -= enemy_damage

            session['character'] = character
            session['current_enemy'] = enemy

            return jsonify({
                'success': True,
                'messages': messages,
                'character': character,
                'enemy': enemy
            })

    return jsonify({'success': False, 'message': 'Invalid action'})


def handle_victory(character, enemy):
    """Handle victory rewards"""
    messages = [f"🎉 Victory! Defeated {enemy['name']}!"]

    # Track kills
    if enemy['name'] in character['kills']:
        character['kills'][enemy['name']] += 1
    else:
        character['kills'][enemy['name']] = 1

    # Rewards
    messages.append(f"💰 +{enemy['gold_drop']} gold")
    messages.append(f"⭐ +{enemy['exp_drop']} EXP")

    character['gold'] += enemy['gold_drop']
    character['exp'] += enemy['exp_drop']

    # Level up
    if character['exp'] >= character['exp_to_next']:
        level_messages = level_up(character)
        messages.extend(level_messages)

    # Quest progress
    for quest in character['quests']:
        if not quest['completed'] and 'Dragon' in quest['objective'] and enemy['name'] == 'Dragon':
            quest['progress'] += 1
            if quest['progress'] >= quest['goal']:
                quest['completed'] = True
                messages.append(f"🎊 QUEST COMPLETED: {quest['name']}!")
                messages.append(f"💰 +{quest['reward_gold']} gold")
                messages.append(f"⭐ +{quest['reward_exp']} EXP")
                character['gold'] += quest['reward_gold']
                character['exp'] += quest['reward_exp']

    # Random loot
    if random.random() < 0.3:
        loot_table = ["Health Potion", "Iron Sword", "Steel Sword", "Leather Armor", "Chainmail"]
        loot_name = random.choice(loot_table)
        loot = ITEMS_DATABASE[loot_name].copy()
        character['inventory'].append(loot)
        messages.append(f"🎁 Found: {loot['name']}!")

    return {'messages': messages}


def level_up(character):
    """Level up the character"""
    character['level'] += 1
    character['exp'] -= character['exp_to_next']
    character['exp_to_next'] = int(character['exp_to_next'] * 1.5)

    health_increase = 20
    mana_increase = 10
    attack_increase = 3
    defense_increase = 2

    character['max_health'] += health_increase
    character['health'] = character['max_health']
    character['max_mana'] += mana_increase
    character['mana'] = character['max_mana']
    character['attack'] += attack_increase
    character['defense'] += defense_increase

    return [
        f"🌟 LEVEL UP! Now level {character['level']}!",
        f"Max HP: +{health_increase}, Max Mana: +{mana_increase}",
        f"Attack: +{attack_increase}, Defense: +{defense_increase}"
    ]


@app.route('/api/use_item', methods=['POST'])
def use_item():
    """Use or equip an item"""
    character = session.get('character')
    if not character:
        return jsonify({'success': False, 'message': 'No active character'})

    item_index = request.json.get('item_index')
    if item_index is None or item_index >= len(character['inventory']):
        return jsonify({'success': False, 'message': 'Invalid item'})

    item = character['inventory'][item_index]

    if item['item_type'] == 'Potion':
        old_health = character['health']
        character['health'] = min(character['max_health'],
                                character['health'] + item['health_restore'])
        healed = character['health'] - old_health
        character['inventory'].pop(item_index)
        session['character'] = character

        return jsonify({
            'success': True,
            'message': f"Used {item['name']}! Restored {healed} HP.",
            'character': character
        })

    elif item['item_type'] == 'Weapon':
        if character['equipped_weapon']:
            character['inventory'].append(character['equipped_weapon'])
        character['equipped_weapon'] = character['inventory'].pop(item_index)
        session['character'] = character

        return jsonify({
            'success': True,
            'message': f"Equipped {item['name']}!",
            'character': character
        })

    elif item['item_type'] == 'Armor':
        if character['equipped_armor']:
            character['inventory'].append(character['equipped_armor'])
        character['equipped_armor'] = character['inventory'].pop(item_index)
        session['character'] = character

        return jsonify({
            'success': True,
            'message': f"Equipped {item['name']}!",
            'character': character
        })

    return jsonify({'success': False, 'message': 'Cannot use this item'})


@app.route('/api/shop', methods=['GET', 'POST'])
def shop():
    """Shop operations"""
    character = session.get('character')
    if not character:
        return jsonify({'success': False, 'message': 'No active character'})

    if request.method == 'GET':
        shop_items = [
            ITEMS_DATABASE["Health Potion"],
            ITEMS_DATABASE["Iron Sword"],
            ITEMS_DATABASE["Steel Sword"],
            ITEMS_DATABASE["Leather Armor"],
            ITEMS_DATABASE["Chainmail"],
        ]
        return jsonify({
            'success': True,
            'items': shop_items
        })

    else:  # POST - buy item
        item_name = request.json.get('item_name')
        if item_name in ITEMS_DATABASE:
            item = ITEMS_DATABASE[item_name]
            if character['gold'] >= item['value']:
                character['gold'] -= item['value']
                character['inventory'].append(item.copy())
                session['character'] = character

                return jsonify({
                    'success': True,
                    'message': f'Purchased {item_name}!',
                    'character': character
                })
            else:
                return jsonify({'success': False, 'message': 'Not enough gold!'})

        return jsonify({'success': False, 'message': 'Item not found'})


@app.route('/api/sell_item', methods=['POST'])
def sell_item():
    """Sell an item"""
    character = session.get('character')
    if not character:
        return jsonify({'success': False, 'message': 'No active character'})

    item_index = request.json.get('item_index')
    if item_index is None or item_index >= len(character['inventory']):
        return jsonify({'success': False, 'message': 'Invalid item'})

    item = character['inventory'].pop(item_index)
    sell_price = item['value'] // 2
    character['gold'] += sell_price
    session['character'] = character

    return jsonify({
        'success': True,
        'message': f'Sold {item["name"]} for {sell_price} gold!',
        'character': character
    })


@app.route('/api/reset', methods=['POST'])
def reset_game():
    """Reset the game"""
    session.clear()
    return jsonify({'success': True, 'message': 'Game reset'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
