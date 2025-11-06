# The Lost Kingdom - Web Version

Welcome to the **browser-based version** of The Lost Kingdom text RPG!

## 🌐 Play in Your Browser

This is a Flask-powered web application that brings the text RPG experience to your browser with a beautiful, interactive UI.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd web_game
pip3 install -r requirements.txt
```

### 2. Run the Game Server

```bash
python3 app.py
```

### 3. Open in Browser

Navigate to: **http://localhost:5000**

That's it! The game will load in your browser.

## 🎮 How to Play

### Character Creation
1. Click "New Game" on the title screen
2. Enter your character name
3. Select your class (Warrior, Mage, Rogue, or Cleric)
4. Click "Start Adventure"

### Game Interface

The web interface is divided into several sections:

#### Header (Top)
- **Character Name & Class**
- **Health Bar** (HP): Your current health
- **Experience Bar** (XP): Progress to next level
- **Quick Stats**: Attack, Defense, Gold, and Level

#### Main Game Log (Left)
- Displays all game events, messages, and story text
- Color-coded messages:
  - **Gold**: General messages
  - **Blue**: System messages
  - **Red**: Combat messages
  - **Green**: Success messages

#### Sidebar (Right)
Three tabs for managing your character:

**📍 Location Tab**
- Current location name and description
- Available actions (travel, talk to NPCs, fight enemies, visit shops)

**🎒 Inventory Tab**
- View all items in your inventory
- Equipped weapons and armor shown at top
- Click "Use" or "Equip" to use items
- Items show bonuses and descriptions

**🎯 Quests Tab**
- View active quests
- Track quest progress
- See quest rewards

### Game Actions

#### Exploration
- Click location buttons to travel between areas
- Talk to NPCs to learn about the world
- Look for enemies to start combat
- Visit the General Store to buy/sell items

#### Combat
When you encounter an enemy, a combat modal appears:
- **⚔️ Attack**: Deal damage to the enemy
- **🧪 Use Item**: Consume a potion to heal
- **💨 Run**: Attempt to flee (50% chance)

Combat is turn-based - after each action, the enemy attacks back!

#### Shopping
At the General Store:
- **Buy Tab**: Purchase weapons, armor, and potions
- **Sell Tab**: Sell items from your inventory for gold

## 🎨 Features

### Visual Design
- **Dark Fantasy Theme**: Immersive gold and dark blue color scheme
- **Animated Health Bars**: Real-time health tracking
- **Modal Dialogs**: Clean combat and shop interfaces
- **Responsive Design**: Works on desktop and mobile devices

### Game Mechanics
- **4 Unique Classes**: Each with different stats and playstyles
- **Turn-Based Combat**: Strategic battles with critical hits
- **10 Locations**: Explore villages, forests, mines, and dragon lairs
- **Quest System**: Complete the main storyline
- **Economy**: Buy and sell equipment and items
- **Character Progression**: Level up and grow stronger
- **Multiple Enemy Types**: From Goblins to Dragons

### Session Management
- Your game state is saved in the browser session
- No need to manually save - progress is automatic
- Refresh the page to start a new game

## 📁 Project Structure

```
web_game/
├── app.py                  # Flask application and game logic
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── templates/
│   └── index.html         # Main game HTML template
└── static/
    ├── css/
    │   └── style.css      # Game styling
    └── js/
        └── game.js        # Client-side game logic
```

## 🎯 Game Tips

1. **Start in the Village**: Talk to NPCs and buy supplies before adventuring
2. **Equip Better Gear**: Buy weapons and armor to boost your stats
3. **Heal Before Tough Fights**: Stock up on Health Potions
4. **Level Up**: Fight weaker enemies first to gain levels
5. **Explore Carefully**: Some areas have stronger enemies
6. **Complete the Quest**: Defeat the Dragon to win!

## 🗺️ Location Guide

- **Village Square**: Safe starting zone with NPCs
- **Tavern**: Learn rumors from the bartender
- **General Store**: Buy and sell items
- **Training Grounds**: Talk to the Master Trainer
- **Forest Path**: Fight Wolves and Bandits (Level 1-2)
- **Dark Forest**: Battle Goblins and Orcs (Level 2-3)
- **Abandoned Mine**: Face Goblins and Skeletons (Level 2-3)
- **Deep Cavern**: Fight Skeletons and Dark Knights (Level 4-5)
- **Ancient Ruins**: Prepare for the final challenge (Level 4-5)
- **Dragon's Lair**: Face the mighty Dragon (Level 10)

## ⚔️ Combat Mechanics

### Damage Calculation
```
Your Damage = (Attack + Weapon Bonus - Enemy Defense) + Random Variance
Enemy Damage = (Enemy Attack - Your Defense - Armor Bonus) + Random Variance
```

### Critical Hits
- **Rogue**: 20% chance to deal 2x damage
- **Other Classes**: 10% chance to deal 2x damage

### Fleeing
- 50% success rate
- Enemy attacks if you fail to escape

## 🏆 Character Classes

| Class   | HP  | Mana | Attack | Defense | Specialty           |
|---------|-----|------|--------|---------|---------------------|
| Warrior | 120 | 30   | 15     | 8       | High survivability  |
| Mage    | 80  | 100  | 20     | 3       | Highest damage      |
| Rogue   | 90  | 40   | 18     | 5       | Critical hits       |
| Cleric  | 100 | 80   | 12     | 6       | Balanced stats      |

## 🔧 Technical Details

### Requirements
- Python 3.7+
- Flask 3.0.0
- Flask-Session 0.5.0

### Running on Different Hosts/Ports

To run on a different host or port:

```bash
# Run on all interfaces (accessible from other devices on network)
python3 app.py

# Or modify app.py, last line:
# app.run(debug=True, host='0.0.0.0', port=5000)
```

### Deployment

For production deployment, use a production WSGI server like Gunicorn:

```bash
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 🐛 Troubleshooting

### Port Already in Use
If port 5000 is already in use, modify the last line in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8080)  # Use port 8080 instead
```

### Session Errors
If you encounter session errors, ensure the Flask-Session directory is writable:
```bash
chmod -R 755 flask_session/
```

### Module Not Found
Ensure you've installed all dependencies:
```bash
pip3 install -r requirements.txt
```

## 📝 Differences from CLI Version

The web version includes:
- ✅ Beautiful graphical interface
- ✅ Real-time health bars and stats
- ✅ Modal dialogs for combat and shopping
- ✅ Tabbed interface for inventory and quests
- ✅ Color-coded game log
- ✅ No need for terminal/command line
- ✅ Responsive design for mobile devices

## 🎊 Enjoy Your Adventure!

Have fun exploring The Lost Kingdom in your browser! May your blade be sharp and your health bar full! ⚔️🛡️✨

---

**Note**: This is a single-player browser game. Each browser session maintains its own game state. Opening multiple tabs will create separate game sessions.
