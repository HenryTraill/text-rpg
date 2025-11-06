// ==================== GLOBAL STATE ====================
let gameState = {
    character: null,
    location: null,
    inCombat: false,
    currentEnemy: null,
    selectedClass: 'Warrior'
};

// ==================== SCREEN MANAGEMENT ====================
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    document.getElementById(screenId).classList.add('active');
}

function showTitleScreen() {
    showScreen('title-screen');
}

function showCharacterCreation() {
    showScreen('character-creation');
}

function showInstructions() {
    showScreen('instructions-screen');
}

function showGameScreen() {
    showScreen('game-screen');
}

// ==================== TAB MANAGEMENT ====================
function showTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // Refresh content
    if (tabName === 'inventory') {
        updateInventory();
    } else if (tabName === 'quests') {
        updateQuests();
    }
}

// ==================== CHARACTER CREATION ====================
function selectClass(className) {
    gameState.selectedClass = className;

    // Update visual selection
    document.querySelectorAll('.class-card').forEach(card => {
        card.classList.remove('selected');
    });
    event.target.closest('.class-card').classList.add('selected');
}

async function createCharacter() {
    const name = document.getElementById('char-name').value.trim() || 'Hero';

    try {
        const response = await fetch('/api/create_character', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                char_class: gameState.selectedClass
            })
        });

        const data = await response.json();
        if (data.success) {
            gameState.character = data.character;
            showGameScreen();
            addLog(data.message, 'system');
            updateUI();
            loadGameState();
        }
    } catch (error) {
        console.error('Error creating character:', error);
        addLog('Error creating character. Please try again.', 'system');
    }
}

// ==================== GAME STATE ====================
async function loadGameState() {
    try {
        const response = await fetch('/api/get_game_state');
        const data = await response.json();

        if (data.success) {
            gameState.character = data.character;
            gameState.location = data.location;
            gameState.inCombat = data.in_combat;
            gameState.currentEnemy = data.current_enemy;

            updateUI();
            updateLocation();
        }
    } catch (error) {
        console.error('Error loading game state:', error);
    }
}

// ==================== UI UPDATES ====================
function updateUI() {
    if (!gameState.character) return;

    const char = gameState.character;

    // Update character name
    document.getElementById('char-name-display').textContent =
        `${char.name} the ${char.char_class}`;

    // Update health bar
    const healthPercent = (char.health / char.max_health) * 100;
    document.getElementById('health-fill').style.width = `${healthPercent}%`;
    document.getElementById('health-text').textContent =
        `${char.health}/${char.max_health}`;

    // Update XP bar
    const expPercent = (char.exp / char.exp_to_next) * 100;
    document.getElementById('exp-fill').style.width = `${expPercent}%`;
    document.getElementById('exp-text').textContent =
        `${char.exp}/${char.exp_to_next}`;

    // Update quick stats
    let totalAttack = char.attack;
    if (char.equipped_weapon) {
        totalAttack += char.equipped_weapon.attack_bonus;
    }
    let totalDefense = char.defense;
    if (char.equipped_armor) {
        totalDefense += char.equipped_armor.defense_bonus;
    }

    document.getElementById('attack-stat').textContent = totalAttack;
    document.getElementById('defense-stat').textContent = totalDefense;
    document.getElementById('gold-stat').textContent = char.gold;
    document.getElementById('level-stat').textContent = char.level;
}

function updateLocation() {
    if (!gameState.location) return;

    const loc = gameState.location;
    const locName = gameState.character.location;

    document.getElementById('location-name').textContent = locName;
    document.getElementById('location-desc').textContent = loc.description;

    // Update actions
    const actionsDiv = document.getElementById('location-actions');
    actionsDiv.innerHTML = '';

    // Travel actions
    if (loc.connections && loc.connections.length > 0) {
        loc.connections.forEach(conn => {
            const btn = document.createElement('button');
            btn.className = 'action-btn';
            btn.textContent = `🗺️ Travel to ${conn}`;
            btn.onclick = () => travelTo(conn);
            actionsDiv.appendChild(btn);
        });
    }

    // NPC actions
    if (loc.npcs && loc.npcs.length > 0) {
        loc.npcs.forEach(npc => {
            const btn = document.createElement('button');
            btn.className = 'action-btn';
            btn.textContent = `💬 Talk to ${npc}`;
            btn.onclick = () => talkToNpc(npc);
            actionsDiv.appendChild(btn);
        });
    }

    // Combat action
    if (loc.enemies && loc.enemies.length > 0) {
        const btn = document.createElement('button');
        btn.className = 'action-btn';
        btn.textContent = '⚔️ Look for enemies';
        btn.onclick = () => encounterEnemy();
        actionsDiv.appendChild(btn);
    }

    // Shop action
    if (loc.shop) {
        const btn = document.createElement('button');
        btn.className = 'action-btn';
        btn.textContent = '🏪 Visit General Store';
        btn.onclick = () => openShop();
        actionsDiv.appendChild(btn);
    }
}

function updateInventory() {
    if (!gameState.character) return;

    const inventoryDiv = document.getElementById('inventory-list');
    inventoryDiv.innerHTML = '';

    if (gameState.character.inventory.length === 0) {
        inventoryDiv.innerHTML = '<p style="color: #aaa;">Your inventory is empty.</p>';
        return;
    }

    gameState.character.inventory.forEach((item, index) => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'item-entry';

        let bonusText = '';
        if (item.attack_bonus > 0) bonusText += `+${item.attack_bonus} ATK `;
        if (item.defense_bonus > 0) bonusText += `+${item.defense_bonus} DEF `;
        if (item.health_restore > 0) bonusText += `Restores ${item.health_restore} HP `;

        itemDiv.innerHTML = `
            <h4>${item.name}</h4>
            <p>${item.description}</p>
            <p style="color: #ffd700;">Value: ${item.value} gold ${bonusText}</p>
            <div class="item-actions">
                <button class="item-btn" onclick="useItem(${index})">
                    ${item.item_type === 'Potion' ? 'Use' : 'Equip'}
                </button>
            </div>
        `;

        inventoryDiv.appendChild(itemDiv);
    });

    // Show equipped items
    if (gameState.character.equipped_weapon) {
        const weaponDiv = document.createElement('div');
        weaponDiv.className = 'item-entry';
        weaponDiv.style.borderColor = '#ffd700';
        weaponDiv.innerHTML = `
            <h4>⚔️ ${gameState.character.equipped_weapon.name} (Equipped)</h4>
            <p>${gameState.character.equipped_weapon.description}</p>
        `;
        inventoryDiv.prepend(weaponDiv);
    }

    if (gameState.character.equipped_armor) {
        const armorDiv = document.createElement('div');
        armorDiv.className = 'item-entry';
        armorDiv.style.borderColor = '#ffd700';
        armorDiv.innerHTML = `
            <h4>🛡️ ${gameState.character.equipped_armor.name} (Equipped)</h4>
            <p>${gameState.character.equipped_armor.description}</p>
        `;
        inventoryDiv.prepend(armorDiv);
    }
}

function updateQuests() {
    if (!gameState.character) return;

    const questsDiv = document.getElementById('quests-list');
    questsDiv.innerHTML = '';

    if (gameState.character.quests.length === 0) {
        questsDiv.innerHTML = '<p style="color: #aaa;">No active quests.</p>';
        return;
    }

    gameState.character.quests.forEach(quest => {
        const questDiv = document.createElement('div');
        questDiv.className = 'quest-entry';

        const status = quest.completed
            ? '✓ COMPLETED'
            : `Progress: ${quest.progress}/${quest.goal}`;

        questDiv.innerHTML = `
            <h4>${quest.name} [${status}]</h4>
            <p>${quest.description}</p>
            <p style="color: #ffd700;">Objective: ${quest.objective}</p>
            <p>Reward: ${quest.reward_gold} gold, ${quest.reward_exp} EXP</p>
        `;

        questsDiv.appendChild(questDiv);
    });
}

// ==================== GAME ACTIONS ====================
async function travelTo(destination) {
    try {
        const response = await fetch('/api/travel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ destination })
        });

        const data = await response.json();
        if (data.success) {
            addLog(data.message, 'system');
            loadGameState();
        } else {
            addLog(data.message, 'system');
        }
    } catch (error) {
        console.error('Error traveling:', error);
    }
}

async function talkToNpc(npc) {
    try {
        const response = await fetch('/api/talk_npc', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ npc })
        });

        const data = await response.json();
        if (data.success) {
            showNpcModal(data.npc, data.dialogue);
        }
    } catch (error) {
        console.error('Error talking to NPC:', error);
    }
}

async function encounterEnemy() {
    try {
        const response = await fetch('/api/encounter_enemy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();
        if (data.success) {
            gameState.inCombat = true;
            gameState.currentEnemy = data.enemy;
            addLog(data.message, 'combat');
            showCombatModal();
        } else {
            addLog(data.message, 'system');
        }
    } catch (error) {
        console.error('Error encountering enemy:', error);
    }
}

async function useItem(index) {
    try {
        const response = await fetch('/api/use_item', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_index: index })
        });

        const data = await response.json();
        if (data.success) {
            gameState.character = data.character;
            addLog(data.message, 'success');
            updateUI();
            updateInventory();
        } else {
            addLog(data.message, 'system');
        }
    } catch (error) {
        console.error('Error using item:', error);
    }
}

// ==================== COMBAT ====================
function showCombatModal() {
    updateCombatUI();
    document.getElementById('combat-modal').classList.add('active');
    document.getElementById('combat-items').classList.add('hidden');
    document.getElementById('combat-log').innerHTML = '';
}

function closeCombatModal() {
    document.getElementById('combat-modal').classList.remove('active');
    gameState.inCombat = false;
    gameState.currentEnemy = null;
}

function updateCombatUI() {
    if (!gameState.character || !gameState.currentEnemy) return;

    const char = gameState.character;
    const enemy = gameState.currentEnemy;

    // Player stats
    document.getElementById('combat-player-name').textContent = char.name;
    const playerHealthPercent = (char.health / char.max_health) * 100;
    document.getElementById('combat-player-health').style.width = `${playerHealthPercent}%`;
    document.getElementById('combat-player-hp').textContent = `${char.health}/${char.max_health} HP`;

    // Enemy stats
    document.getElementById('combat-enemy-name').textContent = enemy.name;
    const enemyHealthPercent = (enemy.health / enemy.max_health) * 100;
    document.getElementById('combat-enemy-health').style.width = `${enemyHealthPercent}%`;
    document.getElementById('combat-enemy-hp').textContent = `${enemy.health}/${enemy.max_health} HP`;
}

async function combatAction(action) {
    try {
        const response = await fetch('/api/combat_action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });

        const data = await response.json();
        if (data.success) {
            // Add messages to combat log
            data.messages.forEach(msg => {
                addCombatLog(msg);
                addLog(msg, 'combat');
            });

            if (data.victory) {
                gameState.character = data.character;
                updateUI();
                setTimeout(() => {
                    closeCombatModal();
                    loadGameState();
                }, 2000);
            } else if (data.defeat) {
                gameState.character = data.character;
                updateUI();
                setTimeout(() => {
                    closeCombatModal();
                    addLog('Game Over. Refresh the page to start a new game.', 'system');
                }, 2000);
            } else if (data.escaped) {
                closeCombatModal();
            } else {
                gameState.character = data.character;
                gameState.currentEnemy = data.enemy;
                updateUI();
                updateCombatUI();
            }
        }
    } catch (error) {
        console.error('Error in combat action:', error);
    }
}

function showCombatItems() {
    const itemsDiv = document.getElementById('combat-items');

    if (itemsDiv.classList.contains('hidden')) {
        // Show potions
        itemsDiv.innerHTML = '<h4 style="color: #ffd700; margin-bottom: 10px;">Potions:</h4>';

        const potions = gameState.character.inventory.filter(
            item => item.item_type === 'Potion'
        );

        if (potions.length === 0) {
            itemsDiv.innerHTML += '<p style="color: #aaa;">No potions available!</p>';
        } else {
            potions.forEach((potion, index) => {
                const actualIndex = gameState.character.inventory.indexOf(potion);
                const btn = document.createElement('button');
                btn.className = 'combat-item-btn';
                btn.textContent = `${potion.name} (Restores ${potion.health_restore} HP)`;
                btn.onclick = () => useCombatItem(actualIndex);
                itemsDiv.appendChild(btn);
            });
        }

        itemsDiv.classList.remove('hidden');
    } else {
        itemsDiv.classList.add('hidden');
    }
}

async function useCombatItem(index) {
    await combatAction('use_item');
    document.getElementById('combat-items').classList.add('hidden');
}

function addCombatLog(message) {
    const logDiv = document.getElementById('combat-log');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'combat-message';
    msgDiv.textContent = message;
    logDiv.appendChild(msgDiv);
    logDiv.scrollTop = logDiv.scrollHeight;
}

// ==================== SHOP ====================
async function openShop() {
    try {
        const response = await fetch('/api/shop');
        const data = await response.json();

        if (data.success) {
            const shopItemsDiv = document.getElementById('shop-items');
            shopItemsDiv.innerHTML = '';

            data.items.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'shop-item';

                let bonusText = '';
                if (item.attack_bonus > 0) bonusText += `+${item.attack_bonus} ATK `;
                if (item.defense_bonus > 0) bonusText += `+${item.defense_bonus} DEF `;

                itemDiv.innerHTML = `
                    <div class="shop-item-info">
                        <h4>${item.name}</h4>
                        <p>${item.description} ${bonusText}</p>
                    </div>
                    <span class="shop-item-price">${item.value} 💰</span>
                    <button onclick="buyItem('${item.name}')">Buy</button>
                `;

                shopItemsDiv.appendChild(itemDiv);
            });

            // Update sell tab
            updateSellTab();

            document.getElementById('shop-modal').classList.add('active');
        }
    } catch (error) {
        console.error('Error opening shop:', error);
    }
}

function closeShop() {
    document.getElementById('shop-modal').classList.remove('active');
}

function showShopTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.shop-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update tab content
    document.querySelectorAll('.shop-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');

    if (tabName === 'sell') {
        updateSellTab();
    }
}

function updateSellTab() {
    const sellItemsDiv = document.getElementById('sell-items');
    sellItemsDiv.innerHTML = '';

    if (!gameState.character || gameState.character.inventory.length === 0) {
        sellItemsDiv.innerHTML = '<p style="color: #aaa;">Nothing to sell.</p>';
        return;
    }

    gameState.character.inventory.forEach((item, index) => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'shop-item';

        const sellPrice = Math.floor(item.value / 2);

        itemDiv.innerHTML = `
            <div class="shop-item-info">
                <h4>${item.name}</h4>
                <p>${item.description}</p>
            </div>
            <span class="shop-item-price">${sellPrice} 💰</span>
            <button onclick="sellItem(${index})">Sell</button>
        `;

        sellItemsDiv.appendChild(itemDiv);
    });
}

async function buyItem(itemName) {
    try {
        const response = await fetch('/api/shop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_name: itemName })
        });

        const data = await response.json();
        if (data.success) {
            gameState.character = data.character;
            addLog(data.message, 'success');
            updateUI();
            updateSellTab();
        } else {
            addLog(data.message, 'system');
        }
    } catch (error) {
        console.error('Error buying item:', error);
    }
}

async function sellItem(index) {
    try {
        const response = await fetch('/api/sell_item', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_index: index })
        });

        const data = await response.json();
        if (data.success) {
            gameState.character = data.character;
            addLog(data.message, 'success');
            updateUI();
            updateSellTab();
        } else {
            addLog(data.message, 'system');
        }
    } catch (error) {
        console.error('Error selling item:', error);
    }
}

// ==================== NPC MODAL ====================
function showNpcModal(npc, dialogue) {
    document.getElementById('npc-name').textContent = npc;
    document.getElementById('npc-dialogue').textContent = `"${dialogue}"`;
    document.getElementById('npc-modal').classList.add('active');
}

function closeNpcModal() {
    document.getElementById('npc-modal').classList.remove('active');
}

// ==================== GAME LOG ====================
function addLog(message, type = 'normal') {
    const logDiv = document.getElementById('game-log');
    const msgDiv = document.createElement('div');
    msgDiv.className = `log-message ${type}`;
    msgDiv.textContent = message;
    logDiv.appendChild(msgDiv);
    logDiv.scrollTop = logDiv.scrollHeight;
}

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    console.log('The Lost Kingdom - Web RPG Loaded');
});
