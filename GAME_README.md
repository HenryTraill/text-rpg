# The Lost Kingdom - Text RPG Game

Welcome to **The Lost Kingdom**, a command-line text-based RPG adventure game!

## 🎮 How to Play

### Starting the Game

Run the game with Python 3:

```bash
python3 game.py
```

### Game Features

#### 🎭 Character Creation
- **Choose your name**: Create your unique hero
- **Select your class**: Pick from 4 unique character classes
  - **Warrior**: High HP and defense, excellent for beginners
  - **Mage**: Powerful attacks with high mana but low defense
  - **Rogue**: Balanced stats with high critical hit chance
  - **Cleric**: Balanced stats with healing capabilities

#### 🗺️ World Exploration
Explore multiple locations:
- **Village Square**: Safe starting area with shops and NPCs
- **Dark Forest**: Dangerous woods filled with enemies
- **Abandoned Mine**: Dark tunnels with undead creatures
- **Deep Cavern**: Treacherous caves leading to the dragon
- **Ancient Ruins**: Mysterious structures from a forgotten age
- **Dragon's Lair**: Face the ultimate challenge

#### ⚔️ Combat System
- **Turn-based combat**: Strategic battles against enemies
- **Attack**: Deal damage based on your attack stat and equipped weapon
- **Use Items**: Consume potions during battle to heal
- **Run Away**: 50% chance to escape from combat
- **Critical Hits**: Deal 2x damage (20% chance for Rogues, 10% for others)

#### 📦 Inventory & Equipment
- **Weapons**: Increase your attack power
  - Iron Sword (+5 ATK)
  - Steel Sword (+12 ATK)
  - Legendary Blade (+25 ATK)
- **Armor**: Boost your defense
  - Leather Armor (+3 DEF)
  - Chainmail (+8 DEF)
  - Plate Armor (+15 DEF)
- **Potions**: Restore health during or outside combat
  - Health Potion (restores 50 HP)

#### 🏪 Shopping
Visit the General Store to:
- Buy weapons, armor, and potions
- Sell unwanted items for gold (50% of value)
- Stock up before dangerous quests

#### 🎯 Quests
- Complete the main quest: "The Lost Kingdom"
- Defeat the Dragon to save the kingdom
- Earn rewards: gold and experience points

#### 👾 Enemies
Battle various enemies with increasing difficulty:
- **Wolf** (Level 1): Starting enemy in the forest
- **Goblin** (Level 1): Weak but numerous
- **Bandit** (Level 2): Human outlaws
- **Skeleton** (Level 3): Undead warriors
- **Orc** (Level 3): Strong melee fighters
- **Dark Knight** (Level 5): Elite warriors
- **Dragon** (Level 10): Final boss with massive HP and damage

#### 📊 Character Progression
- **Gain Experience**: Defeat enemies to earn EXP
- **Level Up**: Increase stats automatically
  - +20 Max HP
  - +10 Max Mana
  - +3 Attack
  - +2 Defense
- **Track Progress**: View your stats, inventory, and quests anytime

#### 💾 Save System
- **Save Game**: Save your progress anytime from the main menu
- **Load Game**: Continue your adventure from where you left off
- Save file: `savegame.json` in the game directory

## 🎯 Game Tips

1. **Start Safe**: Begin by exploring the Village Square and talking to NPCs
2. **Buy Supplies**: Purchase health potions before venturing into dangerous areas
3. **Upgrade Equipment**: Better weapons and armor make combat easier
4. **Level Up**: Fight weaker enemies first to gain levels
5. **Save Often**: Use the save feature regularly to preserve progress
6. **Explore Carefully**: Some areas have tougher enemies than others
7. **Manage Resources**: Don't waste health potions on small injuries

## 🗺️ Recommended Path

1. **Start**: Village Square - talk to NPCs, buy supplies
2. **Early Combat**: Forest Path - fight Wolves and Bandits
3. **Level 2-3**: Dark Forest - battle Goblins and Orcs
4. **Level 3-4**: Abandoned Mine - face Goblins and Skeletons
5. **Level 4-5**: Deep Cavern - fight Skeletons and Dark Knights
6. **Level 5+**: Ancient Ruins - prepare for the dragon
7. **Final Challenge**: Dragon's Lair - defeat the dragon!

## 📋 Controls

### Main Menu
- `1` - Explore current location
- `2` - View/manage inventory
- `3` - View active quests
- `4` - View character stats
- `5` - Save game
- `6` - Quit game

### Exploration
- `T` - Travel to another location
- `N` - Talk to NPCs
- `E` - Look for enemies to fight
- `S` - Visit shop (when available)
- `B` - Back to main menu

### Combat
- `1` - Attack the enemy
- `2` - Use a potion
- `3` - Attempt to run away

### Inventory
- `1` - Use or equip an item
- `2` - Drop an item
- `3` - Return to main menu

## 🎨 Game Stats Explained

- **HP (Health Points)**: Your life. When it reaches 0, game over!
- **Mana**: Reserved for future magical abilities
- **Attack**: Damage dealt to enemies (modified by weapons)
- **Defense**: Reduces damage taken (modified by armor)
- **Gold**: Currency for buying items
- **EXP**: Experience points needed to level up
- **Level**: Your character's power level

## 🎪 NPCs

- **Village Elder**: Provides quest information and lore
- **Bartender**: Shares rumors and stories
- **Mysterious Stranger**: Hints about secrets
- **Shopkeeper**: Manages the General Store
- **Master Trainer**: Encourages your progress
- **Ancient Guardian**: Blesses worthy adventurers

## 🏆 Victory Conditions

Complete the main quest "The Lost Kingdom" by:
1. Exploring the world
2. Gaining levels and equipment
3. Finding the Dragon's Lair
4. Defeating the Dragon

## ⚠️ Game Over

You'll face game over if:
- Your HP reaches 0 in combat
- Don't worry! You can start a new game or load a previous save

## 🔧 Technical Requirements

- Python 3.6 or higher
- Terminal/Command Prompt
- No additional dependencies required (uses only Python standard library)

## 🎮 System Features

- **Clear Screen**: Terminal clears for a clean interface (works on Windows, Mac, Linux)
- **Typewriter Effect**: Story text prints character-by-character
- **Auto-Save**: Manual save system with JSON format
- **Random Events**: Enemy encounters and loot drops have randomization
- **Stat Calculations**: Damage formula includes attack, defense, and randomness

## 📝 Character Classes Comparison

| Class   | HP  | Mana | Attack | Defense | Special                |
|---------|-----|------|--------|---------|------------------------|
| Warrior | 120 | 30   | 15     | 8       | High survivability     |
| Mage    | 80  | 100  | 20     | 3       | Highest damage         |
| Rogue   | 90  | 40   | 18     | 5       | 20% critical hit rate  |
| Cleric  | 100 | 80   | 12     | 6       | Balanced healer        |

## 🎯 Combat Mechanics

### Damage Formula
```
Player Damage = (Attack + Weapon Bonus - Enemy Defense) + Random(-3 to +3)
Enemy Damage = (Enemy Attack - (Defense + Armor Bonus)) + Random(-2 to +2)
Minimum Damage = 1 (always)
```

### Critical Hits
- **Rogue**: 20% chance for 2x damage
- **Other Classes**: 10% chance for 2x damage

### Running Away
- 50% success rate
- Enemy attacks if you fail to escape

## 💎 Loot System

After defeating enemies:
- **Guaranteed**: Gold and EXP based on enemy level
- **Random Loot**: 30% chance to find equipment or potions
- **Quest Items**: Special drops for completing objectives

## 🎊 Future Features (Not Yet Implemented)

The backend system includes models for:
- Multiplayer functionality
- Guild systems
- Advanced crafting
- World events
- PvP combat

These are planned features in the full web-based version!

## 🐛 Known Issues

- None currently! Report any bugs you find.

## 📜 Credits

Created for the Text RPG project using Python 3.
Part of the Lost Kingdom MMO development initiative.

## 🎮 Enjoy Your Adventure!

May your blade be sharp and your potions plenty!
Good luck, adventurer! 🗡️🛡️✨
