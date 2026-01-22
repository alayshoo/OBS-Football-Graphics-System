# Football Stream Overlay System - Project Overview

## Project Purpose
This is a browser-based graphics overlay system for football (soccer) video streams in OBS (Open Broadcaster Software). It allows real-time score, timer, and team information display on streams, with a web-based control interface for operators.

## Folder Structure

```
football-stream-overlay/
│
├── app.py                          # Main Flask backend server
│
├── football_settings.json          # Persistent settings (generated at runtime)
│
├── advertisements_database.json    # Persistent advertisements database (generated at runtime)
│
├── templates/                      # Frontend HTML & CSS
│   ├── scoreboard.html             # OBS overlay display page
│   ├── control_interface.html      # Operator control panel
│   ├── setup.html                  # Team & roster configuration
│   ├── setup_adds.html             # [WORK IN PROGRESS - Advertisement management]
│   │
│   └── css/                        # Stylesheet directory
│       ├── shared.css              # Common styles used across pages
│       ├── scoreboard.css          # Scoreboard styling
│       ├── scoreboard_event.css    # Event card styling
│       ├── formation.css           # Formation overlay styling for scoreboard.html
│       └── formation_config.css    # Formation configuration styling for setup.html
│
├── static/                         # Static assets
│   └── BrigantiaLogo.svg           # Logo asset
│
├── requirements.txt                # Python dependencies [ TO BE ADDED ]
│
└── .gitignore                      # Git ignore rules

```

## Architecture

### Backend (`app.py`)
- **Framework**: Flask with CORS support
- **Port**: 8246 (configurable)
- **Key Features**:
  - Shared game state management (scores, timer, team info)
  - Settings persistence (JSON file: `football_settings.json`)
  - Event queue system (stores last 50 events)
  - QR code generation for easy mobile access

### Frontend Components

#### 1. **Scoreboard** (`scoreboard.html`)
- **Purpose**: OBS browser source display
- **Features**:
  - Real-time score and timer display
  - Event card animations (goals, cards, substitutions)
  - Formation overlay with team lineup visualization
  - Client-side timer calculation with server sync

#### 2. **Control Interface** (`control_interface.html`)
- **Purpose**: Operator control panel (desktop/tablet)
- **Features**:
  - Score management (+/- buttons)
  - Timer control (start/stop/reset, set time, add extra time)
  - Event submission (goals, cards, substitutions)
  - Formation display trigger

#### 3. **Setup Interface** (`setup.html`)
- **Purpose**: Team and roster configuration
- **Features**:
  - Team name and manager input
  - Color customization (Predefined 9-color palette)
  - Player roster management
  - Formation configuration (goalkeeper + 4 lines)
  - Persistent storage between sessions

### Data Persistence
- **JSON** (`football_settings.json`): Team names, managers, colors, formations, rosters

## Key Workflows

### Timer Synchronization
- **Server maintains**: `timer_anchor` (start time), `timer_offset` (elapsed seconds), `timer_running` (state)
- **Client receives**: `server_time` to calculate clock offset
- **Local calculation**: Client updates timer every 100ms without polling (reduces network load)
- Only re-syncs when server state changes

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Redirect to control |
| `/scoreboard` | GET | OBS overlay page |
| `/control` | GET | Operator control panel |
| `/setup` | GET | Team setup page |
| `/state` | GET | Fetch current game state |
| `/state` | POST | Update scores, timer, colors, names |
| `/events` | GET | Fetch last 10 events |
| `/events` | POST | Submit new event (goal/card/sub/formation) |
| `/setup/data` | GET | Fetch all settings |
| `/setup/data` | POST | Save all settings |
| `/BrigantiaLogo.svg` | GET | Logo asset |

## State Structure

### `game_state` (Runtime)
```javascript
{
  team1_name, team2_name,
  team1_score, team2_score,
  team1_bg, team1_text, team2_bg, team2_text,
  timer_anchor, timer_offset, timer_running,
  extra_time, last_timer_update
}
```

### `settings_state` (Persistent)
```javascript
{
  team1_name, team2_name, team1_manager, team2_manager,
  team1_bg, team1_text, team2_bg, team2_text,
  team1_formation: { goalkeeper: number, lines: [[], [], [], []] },
  team2_formation: { goalkeeper: number, lines: [[], [], [], []] },
  team1_roster: [{ number, name }, ...],
  team2_roster: [{ number, name }, ...]
}
```

### Event Objects
```javascript
{
  id, type, team, timestamp,
  // type: 'goal'
  player, player_name,
  // type: 'card'
  player, player_name, card_type,
  // type: 'substitution'
  player_out, player_in, player_out_name, player_in_name,
  // type: 'formation'
  formation, roster, team_bg_color, team_text_color, team_name, manager
}
```

## Response Handling

### Event Queue Management
- Scoreboard tracks `lastEventIds` to prevent duplicates
- One event displays at a time (7-second duration)
- Next event queued automatically
- Formation events bypass event card, display overlay directly

## Version & Attribution
- Current version: `0.8.3`
- Developed by: Diogo Aleixo
- Project: Brigantia Score System