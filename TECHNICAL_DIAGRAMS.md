# Technical Architecture Diagrams

## System Architecture Overview

### High-Level System Architecture
```mermaid
graph TB
    subgraph "Client Layer"
        RC[React Client]
        WS_CLIENT[WebSocket Client]
    end
    
    subgraph "Load Balancer"
        LB[Nginx Load Balancer]
    end
    
    subgraph "API Gateway"
        API[FastAPI Gateway]
        AUTH[Authentication Service]
        RATE[Rate Limiter]
    end
    
    subgraph "Core Game Services"
        GAME[Game Engine Service]
        COMBAT[Combat Service]
        WORLD[World Service]
        SOCIAL[Social Service]
        ECONOMY[Economy Service]
        QUEST[Quest Service]
    end
    
    subgraph "Real-time Layer"
        WS[WebSocket Manager]
        REDIS[Redis Cache/PubSub]
        CELERY[Celery Workers]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL)]
        BACKUP[(Daily Backup)]
    end
    
    subgraph "External Services"
        EMAIL[Email Service]
        MOD[Moderation AI]
    end
    
    RC --> LB
    WS_CLIENT --> LB
    LB --> API
    API --> AUTH
    API --> RATE
    API --> GAME
    API --> COMBAT
    API --> WORLD
    API --> SOCIAL
    API --> ECONOMY
    API --> QUEST
    
    GAME --> WS
    COMBAT --> WS
    WORLD --> WS
    SOCIAL --> WS
    
    WS --> REDIS
    CELERY --> REDIS
    
    GAME --> PG
    COMBAT --> PG
    WORLD --> PG
    SOCIAL --> PG
    ECONOMY --> PG
    QUEST --> PG
    
    PG --> BACKUP
    AUTH --> EMAIL
    SOCIAL --> MOD
```

## Database Entity Relationship Diagram

```mermaid
erDiagram
    USERS {
        uuid id PK
        string username UK
        string email UK
        string password_hash
        datetime created_at
        datetime last_login
        boolean is_active
        string role
    }
    
    CHARACTERS {
        uuid id PK
        uuid user_id FK
        string name UK
        int level
        int experience
        float x_coordinate
        float y_coordinate
        string current_zone
        int health
        int max_health
        int mana
        int max_mana
        datetime created_at
        datetime last_active
    }
    
    SKILLS {
        uuid id PK
        uuid character_id FK
        string skill_name
        int skill_level
        int experience
        string skill_type
    }
    
    ITEMS {
        uuid id PK
        string name
        string description
        string item_type
        int value
        jsonb stats
        string rarity
        boolean craftable
    }
    
    INVENTORY {
        uuid id PK
        uuid character_id FK
        uuid item_id FK
        int quantity
        int slot_position
        boolean equipped
    }
    
    GUILDS {
        uuid id PK
        string name UK
        string description
        uuid leader_id FK
        datetime created_at
        int member_limit
        string guild_type
    }
    
    GUILD_MEMBERS {
        uuid guild_id FK
        uuid character_id FK
        string rank
        datetime joined_at
        int contribution_points
    }
    
    TERRITORIES {
        uuid id PK
        string name
        float x1_boundary
        float y1_boundary
        float x2_boundary
        float y2_boundary
        uuid controlling_guild_id FK
        datetime captured_at
        jsonb resources
    }
    
    COMBAT_INSTANCES {
        uuid id PK
        string combat_type
        jsonb participants
        string status
        datetime started_at
        datetime ended_at
        jsonb combat_log
    }
    
    QUESTS {
        uuid id PK
        string title
        string description
        string quest_type
        jsonb requirements
        jsonb rewards
        boolean is_active
        string generation_type
    }
    
    CHARACTER_QUESTS {
        uuid character_id FK
        uuid quest_id FK
        string status
        jsonb progress
        datetime started_at
        datetime completed_at
    }
    
    AUCTION_HOUSE {
        uuid id PK
        uuid seller_id FK
        uuid item_id FK
        int quantity
        int starting_price
        int current_bid
        uuid highest_bidder_id FK
        datetime expires_at
        string status
    }
    
    TRADE_TRANSACTIONS {
        uuid id PK
        uuid buyer_id FK
        uuid seller_id FK
        jsonb items_traded
        int gold_amount
        datetime completed_at
        string transaction_type
    }
    
    WORLD_EVENTS {
        uuid id PK
        string event_type
        string title
        string description
        float x_coordinate
        float y_coordinate
        datetime start_time
        datetime end_time
        jsonb participants
        string status
    }
    
    MESSAGES {
        uuid id PK
        uuid sender_id FK
        string channel_type
        string channel_id
        string content
        datetime sent_at
        boolean moderated
    }
    
    USERS ||--o{ CHARACTERS : owns
    CHARACTERS ||--o{ SKILLS : develops
    CHARACTERS ||--o{ INVENTORY : has
    CHARACTERS ||--o{ CHARACTER_QUESTS : undertakes
    CHARACTERS ||--o{ GUILD_MEMBERS : joins
    CHARACTERS ||--o{ MESSAGES : sends
    
    ITEMS ||--o{ INVENTORY : stored_in
    ITEMS ||--o{ AUCTION_HOUSE : listed_in
    
    GUILDS ||--o{ GUILD_MEMBERS : contains
    GUILDS ||--o{ TERRITORIES : controls
    
    QUESTS ||--o{ CHARACTER_QUESTS : assigned_to
    
    CHARACTERS ||--o{ AUCTION_HOUSE : sells
    CHARACTERS ||--o{ TRADE_TRANSACTIONS : trades
```

## Combat System Flow

```mermaid
flowchart TD
    START[Combat Initiated] --> TYPE{Combat Type?}
    
    TYPE -->|1v1 PvP| PVP[Create PvP Instance]
    TYPE -->|1v1 PvE| PVE[Create PvE Instance]
    TYPE -->|Boss Raid| RAID[Create Raid Instance]
    
    PVP --> INIT[Initialize Combat State]
    PVE --> INIT
    RAID --> INIT
    
    INIT --> TURN[Start Turn Cycle]
    
    TURN --> PLAYER_ACTION{Player Action Type?}
    
    PLAYER_ACTION -->|Manual Action| MANUAL[Wait for Player Input]
    PLAYER_ACTION -->|Auto Combat| AUTO[Execute AI Action]
    
    MANUAL --> INPUT[Process Player Input]
    AUTO --> AI_LOGIC[AI Decision Logic]
    
    INPUT --> VALIDATE[Validate Action]
    AI_LOGIC --> VALIDATE
    
    VALIDATE -->|Invalid| PLAYER_ACTION
    VALIDATE -->|Valid| EXECUTE[Execute Action]
    
    EXECUTE --> DAMAGE[Calculate Damage/Effects]
    DAMAGE --> UPDATE[Update Character States]
    UPDATE --> BROADCAST[Broadcast to All Participants]
    
    BROADCAST --> CHECK{Combat End Condition?}
    
    CHECK -->|Health <= 0| DEATH[Handle Death/Defeat]
    CHECK -->|Surrender| SURRENDER[Process Surrender]
    CHECK -->|Continue| NEXT_TURN[Next Player Turn]
    
    NEXT_TURN --> TURN
    
    DEATH --> REWARDS[Calculate Rewards/XP]
    SURRENDER --> REWARDS
    
    REWARDS --> LOOT[Distribute Loot]
    LOOT --> SKILL_XP[Award Skill Experience]
    SKILL_XP --> CLEANUP[Cleanup Combat Instance]
    CLEANUP --> END[Combat Complete]
    
    subgraph "Auto Combat Logic"
        AI_LOGIC --> SKILL_CHECK[Check Available Skills]
        SKILL_CHECK --> TARGET_SELECT[Select Best Target]
        TARGET_SELECT --> ACTION_SELECT[Select Optimal Action]
        ACTION_SELECT --> VALIDATE
    end
    
    subgraph "Raid Specific"
        RAID --> BOSS_MECHANICS[Initialize Boss Mechanics]
        BOSS_MECHANICS --> PHASE_CHECK[Check Boss Phase]
        PHASE_CHECK --> SPECIAL_ABILITIES[Handle Special Abilities]
        SPECIAL_ABILITIES --> INIT
    end
```

## Real-Time Communication Sequence

```mermaid
sequenceDiagram
    participant Client as React Client
    participant WS as WebSocket Manager
    participant Redis as Redis PubSub
    participant Game as Game Service
    participant DB as PostgreSQL
    
    Note over Client, DB: Player Connection & Authentication
    Client->>WS: Connect with JWT Token
    WS->>Game: Validate Token
    Game->>DB: Check User/Character
    DB-->>Game: User Data
    Game-->>WS: Authentication Success
    WS-->>Client: Connection Established
    
    Note over Client, DB: Join Game Channels
    WS->>Redis: Subscribe to Player Channels
    WS->>Redis: Subscribe to Zone Channels
    WS->>Redis: Subscribe to Guild Channels
    
    Note over Client, DB: Real-time Chat
    Client->>WS: Send Chat Message
    WS->>Game: Process Message
    Game->>DB: Store Message
    Game->>Redis: Publish to Channel
    Redis-->>WS: Broadcast Message
    WS-->>Client: Deliver to Recipients
    
    Note over Client, DB: Combat Notifications
    Game->>Redis: Publish Combat Start
    Redis-->>WS: Combat Event
    WS-->>Client: Combat Notification
    
    Client->>WS: Combat Action
    WS->>Game: Process Action
    Game->>DB: Update Combat State
    Game->>Redis: Publish Action Result
    Redis-->>WS: Action Broadcast
    WS-->>Client: Update Combat UI
    
    Note over Client, DB: World Events
    Game->>Redis: Publish World Event
    Redis-->>WS: Event Notification
    WS-->>Client: World Event Alert
    
    Note over Client, DB: Player Movement
    Client->>WS: Move Character
    WS->>Game: Update Position
    Game->>DB: Store New Position
    Game->>Redis: Publish Movement
    Redis-->>WS: Movement Update
    WS-->>Client: Update Nearby Players
    
    Note over Client, DB: Guild Activities
    Client->>WS: Guild Action
    WS->>Game: Process Guild Event
    Game->>DB: Update Guild Data
    Game->>Redis: Publish to Guild Channel
    Redis-->>WS: Guild Notification
    WS-->>Client: Update Guild Members
    
    Note over Client, DB: Auction House Updates
    Game->>Redis: Publish Auction Update
    Redis-->>WS: Auction Event
    WS-->>Client: Real-time Price Update
```

## API Structure Overview

```mermaid
graph LR
    subgraph "Authentication API"
        AUTH_API["/api/auth"]
        AUTH_API --> REGISTER["/register"]
        AUTH_API --> LOGIN["/login"]
        AUTH_API --> REFRESH["/refresh"]
        AUTH_API --> LOGOUT["/logout"]
        AUTH_API --> RESET["/password-reset"]
    end
    
    subgraph "Character API"
        CHAR_API["/api/characters"]
        CHAR_API --> CREATE_CHAR["/create"]
        CHAR_API --> GET_CHAR["/me"]
        CHAR_API --> UPDATE_CHAR["/update"]
        CHAR_API --> SKILLS_API["/skills"]
        CHAR_API --> INVENTORY_API["/inventory"]
        CHAR_API --> STATS["/stats"]
    end
    
    subgraph "World API"
        WORLD_API["/api/world"]
        WORLD_API --> MOVE["/move"]
        WORLD_API --> LOCATION["/location"]
        WORLD_API --> NEARBY["/nearby-players"]
        WORLD_API --> ZONES["/zones"]
        WORLD_API --> EVENTS["/events"]
        WORLD_API --> TERRITORIES_API["/territories"]
    end
    
    subgraph "Combat API"
        COMBAT_API["/api/combat"]
        COMBAT_API --> CHALLENGE["/challenge"]
        COMBAT_API --> ACTION["/action"]
        COMBAT_API --> STATUS["/status"]
        COMBAT_API --> AUTO_TOGGLE["/auto-combat"]
        COMBAT_API --> SURRENDER["/surrender"]
        COMBAT_API --> RAIDS["/raids"]
    end
    
    subgraph "Social API"
        SOCIAL_API["/api/social"]
        SOCIAL_API --> GUILDS["/guilds"]
        SOCIAL_API --> PARTIES["/parties"]
        SOCIAL_API --> FRIENDS["/friends"]
        SOCIAL_API --> MESSAGES["/messages"]
        SOCIAL_API --> MENTORSHIP["/mentorship"]
    end
    
    subgraph "Economy API"
        ECON_API["/api/economy"]
        ECON_API --> TRADE["/trade"]
        ECON_API --> AUCTION["/auction-house"]
        ECON_API --> CRAFT["/crafting"]
        ECON_API --> SHOPS["/npc-shops"]
        ECON_API --> MARKET["/market-data"]
    end
    
    subgraph "Quest API"
        QUEST_API["/api/quests"]
        QUEST_API --> AVAILABLE["/available"]
        QUEST_API --> ACTIVE["/active"]
        QUEST_API --> COMPLETE["/complete"]
        QUEST_API --> ABANDON["/abandon"]
        QUEST_API --> PROGRESS["/progress"]
    end
    
    subgraph "Admin API"
        ADMIN_API["/api/admin"]
        ADMIN_API --> MODERATE["/moderation"]
        ADMIN_API --> ANALYTICS["/analytics"]
        ADMIN_API --> WORLD_MGMT["/world-management"]
        ADMIN_API --> USER_MGMT["/user-management"]
        ADMIN_API --> SYSTEM["/system"]
    end
    
    subgraph "WebSocket Endpoints"
        WS_GAME["/ws/game"]
        WS_CHAT["/ws/chat"]
        WS_COMBAT["/ws/combat"]
        WS_WORLD["/ws/world"]
    end
```

## Character Progression System

```mermaid
graph TD
    subgraph "Character Progression System"
        CHAR[Character Creation] --> SKILLS[Skill Selection]
        
        subgraph "Combat Skills"
            MELEE[Melee Combat]
            RANGED[Ranged Combat]
            MAGIC[Magic Arts]
            DEFENSE[Defense & Armor]
            TACTICS[Combat Tactics]
        end
        
        subgraph "Gathering Skills"
            MINING[Mining]
            LOGGING[Logging]
            HERBALISM[Herbalism]
            HUNTING[Hunting]
            FISHING[Fishing]
        end
        
        subgraph "Crafting Skills"
            SMITHING[Smithing]
            ALCHEMY[Alchemy]
            COOKING[Cooking]
            TAILORING[Tailoring]
            ENCHANTING[Enchanting]
        end
        
        subgraph "Social Skills"
            LEADERSHIP[Leadership]
            DIPLOMACY[Diplomacy]
            TRADE[Trading]
            LORE[Lore & Knowledge]
        end
        
        SKILLS --> MELEE
        SKILLS --> RANGED
        SKILLS --> MAGIC
        SKILLS --> DEFENSE
        SKILLS --> TACTICS
        SKILLS --> MINING
        SKILLS --> LOGGING
        SKILLS --> HERBALISM
        SKILLS --> HUNTING
        SKILLS --> FISHING
        SKILLS --> SMITHING
        SKILLS --> ALCHEMY
        SKILLS --> COOKING
        SKILLS --> TAILORING
        SKILLS --> ENCHANTING
        SKILLS --> LEADERSHIP
        SKILLS --> DIPLOMACY
        SKILLS --> TRADE
        SKILLS --> LORE
        
        MELEE --> COMBAT_EFFECTIVENESS[Combat Effectiveness]
        RANGED --> COMBAT_EFFECTIVENESS
        MAGIC --> COMBAT_EFFECTIVENESS
        DEFENSE --> SURVIVAL[Survival Rate]
        TACTICS --> COMBAT_EFFECTIVENESS
        
        MINING --> RESOURCES[Resource Access]
        LOGGING --> RESOURCES
        HERBALISM --> RESOURCES
        HUNTING --> RESOURCES
        FISHING --> RESOURCES
        
        SMITHING --> EQUIPMENT[Equipment Quality]
        ALCHEMY --> CONSUMABLES[Consumable Quality]
        COOKING --> CONSUMABLES
        TAILORING --> EQUIPMENT
        ENCHANTING --> EQUIPMENT
        
        LEADERSHIP --> GUILD_BENEFITS[Guild Benefits]
        DIPLOMACY --> SOCIAL_BENEFITS[Social Benefits]
        TRADE --> ECONOMIC_BENEFITS[Economic Benefits]
        LORE --> QUEST_ACCESS[Quest Access]
        
        COMBAT_EFFECTIVENESS --> PVP_SUCCESS[PvP Success]
        COMBAT_EFFECTIVENESS --> RAID_ACCESS[Raid Access]
        SURVIVAL --> PVP_SUCCESS
        SURVIVAL --> RAID_ACCESS
        
        RESOURCES --> CRAFTING_MATERIALS[Crafting Materials]
        EQUIPMENT --> COMBAT_POWER[Combat Power]
        CONSUMABLES --> COMBAT_POWER
        
        GUILD_BENEFITS --> TERRITORY_CONTROL[Territory Control]
        SOCIAL_BENEFITS --> MENTORSHIP[Mentorship Access]
        ECONOMIC_BENEFITS --> WEALTH[Wealth Accumulation]
        QUEST_ACCESS --> STORYLINE[Storyline Progression]
    end
```

## Guild and Territory Control State Diagram

```mermaid
stateDiagram-v2
    [*] --> Unclaimed_Territory
    
    state Guild_System {
        [*] --> Guild_Creation
        Guild_Creation --> Recruiting_Members
        Recruiting_Members --> Active_Guild
        Active_Guild --> Territory_Claims
        Territory_Claims --> Territory_Wars
        Territory_Wars --> Territory_Control
        Territory_Control --> Resource_Management
        Resource_Management --> Guild_Expansion
        Guild_Expansion --> Territory_Claims
        
        state Active_Guild {
            [*] --> Member_Management
            Member_Management --> Rank_Assignment
            Rank_Assignment --> Guild_Activities
            Guild_Activities --> Member_Management
            
            state Guild_Activities {
                [*] --> Raids
                Raids --> PvP_Events
                PvP_Events --> Crafting_Projects
                Crafting_Projects --> Territory_Defense
                Territory_Defense --> Raids
            }
        }
        
        state Territory_Control {
            [*] --> Resource_Generation
            Resource_Generation --> Defense_Setup
            Defense_Setup --> Tax_Collection
            Tax_Collection --> Territory_Upgrades
            Territory_Upgrades --> Resource_Generation
        }
    }
    
    state Territory_States {
        Unclaimed_Territory --> Claimed_Territory: Guild_Claims
        Claimed_Territory --> Contested_Territory: Challenge_Issued
        Contested_Territory --> Under_Siege: War_Declared
        Under_Siege --> Claimed_Territory: Successful_Defense
        Under_Siege --> Changing_Hands: Successful_Attack
        Changing_Hands --> Claimed_Territory: New_Owner
        Claimed_Territory --> Unclaimed_Territory: Guild_Abandons
    }
    
    state Combat_Events {
        [*] --> Scheduled_Raid
        Scheduled_Raid --> Raid_Preparation
        Raid_Preparation --> Raid_Execution
        Raid_Execution --> Victory_Defeat
        Victory_Defeat --> Loot_Distribution
        Loot_Distribution --> [*]
        
        [*] --> Territory_War
        Territory_War --> Siege_Preparation
        Siege_Preparation --> Battle_Phase
        Battle_Phase --> Territory_Change
        Territory_Change --> [*]
        
        [*] --> Guild_PvP
        Guild_PvP --> Team_Formation
        Team_Formation --> Arena_Combat
        Arena_Combat --> Ranking_Update
        Ranking_Update --> [*]
    }
    
    Guild_System --> Territory_States: Interaction
    Territory_States --> Combat_Events: Triggers
    Combat_Events --> Guild_System: Results
```

## Technical Implementation Notes

### Database Indexing Strategy
- **Spatial Indexes**: x_coordinate, y_coordinate for world queries
- **Temporal Indexes**: created_at, last_active for time-based queries
- **Composite Indexes**: (character_id, skill_name) for skill lookups
- **Full-text Indexes**: message content for search functionality

### Performance Optimization
- **Connection Pooling**: 20 connections per service instance
- **Query Optimization**: Use EXPLAIN for all complex queries
- **Caching Strategy**: 5-minute TTL for character data, 1-minute for world state
- **Background Processing**: Use Celery for non-critical operations

### Security Considerations
- **Input Validation**: All user inputs validated with Pydantic models
- **SQL Injection Prevention**: Parameterized queries only
- **Rate Limiting**: 100 requests per minute per authenticated user
- **WebSocket Security**: JWT validation on connection and periodic re-validation

### Monitoring Requirements
- **Response Time Tracking**: 95th percentile under 100ms
- **Error Rate Monitoring**: Alert on >1% error rate
- **Concurrent User Tracking**: Real-time player count dashboard
- **Database Performance**: Query execution time monitoring
- **Memory Usage**: Alert on >80% memory utilization 