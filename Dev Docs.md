# Football Stream Overlay System - Project Overview

## Project Purpose
This is a browser-based graphics overlay system for football (soccer) video streams in OBS (Open Broadcaster Software). It allows real-time score, timer, and team information display on streams, with a web-based control interface for operators.

## Folder Structure

```
OBS-Football-Graphics-System/
│
├── app.py                          # Main Flask application entry point
├── config.py                       # Configuration settings (database URI, media settings, Flask config)
│
├── blueprints/                     # Modular Flask blueprints (route handlers)
│   ├── __init__.py                 # Blueprint package initialization
│   ├── pages.py                    # Page routes (control, setup, obs overlay)
│   ├── timer.py                    # Timer state management and SocketIO events
│   ├── game_events.py              # Score state and game event handling
│   ├── teams.py                    # Team, player, and formation CRUD operations
│   ├── ads.py                      # Advertisement management and image upload
│   └── obs_commands.py             # OBS command configuration management
│
├── services/                       # Core services and utilities
│   ├── database.py                 # SQLAlchemy models and database initialization
│   └── helper.py                   # Utility functions (IP detection, file validation)
│
├── templates/                      # HTML templates (Jinja2)
│   ├── scoreboard.html             # OBS overlay display page
│   ├── control_interface.html      # Operator control panel
│   ├── setup.html                  # Team & roster configuration
│   ├── setup_adds.html             # Advertisement management
│   └── setup_obs_commands.html     # OBS Commands management
│
├── static/                         # Static assets served by Flask
│   ├── css/                        # Stylesheet directory
│   │   ├── shared.css              # Common styles used across pages
│   │   ├── scoreboard.css          # Scoreboard styling
│   │   ├── scoreboard_event.css    # Event card styling
│   │   ├── scoreboard_ad.css       # Advertisement card styling
│   │   ├── formation.css           # Formation overlay styling for scoreboard.html
│   │   └── formation_config.css    # Formation configuration styling for setup.html
│   ├── Logo.svg                    # Logo asset
│   └── media_assets/               # Advertisement images (generated at runtime)
│
├── obs_interface_layer.py          # Standalone python file that receives obs-commands and executes them through key emulation
│
├── requirements.txt                # Python dependencies [ TO BE ADDED ]
├── .gitignore                      # Git ignore rules
└── Dev Docs.md                     # This documentation file

```

## Architecture

### Backend Architecture

#### Core Framework (`app.py`)
- **Framework**: Flask with Flask-SocketIO for real-time bidirectional communication
- **Database**: SQLAlchemy ORM with SQLite (`obs_football.db`)
- **Port**: Configurable via environment variable `PORT` (default: 5000)
- **CORS**: Enabled for cross-origin requests
- **Key Features**:
  - Modular blueprint-based architecture for route organization
  - Real-time state synchronization via Socket.IO
  - Persistent database storage for teams, players, formations, ads, and OBS commands
  - Runtime state management (timer and score) stored in memory
  - QR code generation for mobile access
  - Image upload handling for advertisements

#### Blueprint Modules

1. **`pages.py`** - Page Routes
   - Handles HTTP GET requests for HTML pages
   - Generates QR codes for mobile access
   - Serves static assets (Logo.svg)
   - Routes: `/`, `/obs`, `/control`, `/setup`, `/setup-adds`

2. **`timer.py`** - Timer Management
   - Manages match timer state (running, offset, anchor time, extra time)
   - HTTP endpoint: `/timer` (GET) - returns current timer state
   - Socket.IO events: `start-timer`, `stop-timer`, `reset-timer`, `set-timer`, `set-extra-time`
   - Broadcasts timer updates to all connected clients

3. **`game_events.py`** - Game State & Events
   - Manages score state (team1_score, team2_score)
   - HTTP endpoint: `/game_state` (GET) - returns current score
   - Socket.IO events: `trigger-goal`, `trigger-event`
   - Handles game event broadcasting (goals, cards, substitutions, formations)

4. **`teams.py`** - Team Management
   - CRUD operations for teams, players, and formations
   - HTTP endpoints: `/teams`, `/players`, `/formations` (GET)
   - Socket.IO events: `modify-team`, `create-player`, `modify-player`, `delete-player`, `modify-formation`
   - Database-backed persistent storage

5. **`ads.py`** - Advertisement Management
   - Advertisement CRUD operations and image upload handling
   - HTTP endpoints: `/ads` (GET), `/ads/upload-image` (POST), `/static/media_assets/<filename>` (GET)
   - Socket.IO events: `create-ad`, `modify-ad`, `delete-ad`, `trigger-ad`
   - File management: stores images in `static/media_assets/` with unique filenames

6. **`obs_commands.py`** - OBS Command Configuration
   - OBS command CRUD operations
   - HTTP endpoint: `/obs-commands` (GET)
   - Socket.IO events: `create-obs-command`, `modify-obs-command`, `delete-obs-command`, `trigger-obs-command`
   - Stores command configurations (name, color, shortcut)

#### Services Layer

1. **`services/database.py`** - Database Models
   - SQLAlchemy model definitions (Team, Player, Formation, Advertisement, OBSCommand)
   - Database initialization and session management
   - Model serialization methods (`to_dict()`)

2. **`services/helper.py`** - Utility Functions
   - Network utilities: `get_local_ip()` - detects local IP for QR code generation
   - File validation: `allowed_file()` - validates media file extensions

#### State Management

- **Persistent State** (SQLite Database):
  - Teams, Players, Formations, Advertisements, OBS Commands
  - Persists across server restarts

- **Runtime State** (In-Memory):
  - `timer_state`: `{timer_anchor, timer_offset, timer_running, extra_time}`
  - `score_state`: `{team1_score, team2_score}`
  - Resets on server restart

### Frontend Components

#### 1. **Scoreboard** (`scoreboard.html`)
- **Purpose**: OBS browser source display
- **Features**:
  - Real-time score and timer display via Socket.IO
  - Game event card animations (goals, cards, substitutions)
  - Advertisement display triggered by launcher buttons or events
  - Formation overlay with team lineup visualization
  - Client-side timer calculation with server sync
  - Listens for: `update-timer-start`, `update-timer-stop`, `update-timer`, `show-extra-time`, `add-to-score`, `display-event`, `display-ad`, `update-teams`, `update-formations`

#### 2. **Control Interface** (`control_interface.html`)
- **Purpose**: Operator control panel (desktop/tablet)
- **Features**:
  - Score management (+/- buttons)
  - Timer control (start/stop/reset, set time, add extra time)
  - Game event submission (goals, cards, substitutions, formations)
  - Advertisement launcher buttons (dynamically populated from database)
  - Real-time button refresh from advertisement database
  - QR code display for mobile access
  - Connection status indicator

#### 3. **Setup Interface** (`setup.html`)
- **Purpose**: Team and roster configuration
- **Features**:
  - Team name and manager input
  - Color customization (Predefined 9-color palette)
  - Player roster management (create, edit, delete)
  - Formation configuration (goalkeeper + up to 4 lines)
  - Real-time updates via Socket.IO

#### 4. **Advertisement Management** (`setup_ads.html`)
- **Purpose**: Advertisement database management
- **Features**:
  - Add, edit, and delete advertisements
  - Image upload for each advertisement
  - Action trigger configuration (Launcher, Goal, Substitution, Red Card, Yellow Card)
  - Duration configuration for each ad
  - Real-time database synchronization via Socket.IO

## Database

### Database System
- **Type**: SQLite
- **File**: `obs_football.db` (created automatically on first run)
- **ORM**: SQLAlchemy
- **Location**: Root directory of the project

### Database Schema

#### Table: `teams`
Stores team information and configuration.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | Primary Key | Team identifier (1 or 2) |
| `name` | String(255) | Nullable | Team name |
| `manager` | String(255) | Nullable | Manager/coach name |
| `bg_color` | String(255) | Nullable | Background color (hex code) |
| `text_color` | String(255) | Nullable | Text color (hex code) |

**Relationships**:
- One-to-Many: `Team.players` → `Player` (a team has many players)
- One-to-One: `Team.formation` → `Formation` (a team has one formation)

**Initialization**: Two teams (id=1, id=2) are automatically created if they don't exist.

---

#### Table: `players`
Stores player roster information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | Primary Key | Auto-incrementing player ID |
| `team_id` | Integer | Foreign Key → `teams.id` | Reference to parent team |
| `number` | Integer | Nullable | Player jersey number |
| `name` | String(255) | Nullable | Player name |

**Relationships**:
- Many-to-One: `Player.team` → `Team` (each player belongs to one team)
- Referenced by: `Formation.goalkeeper` (foreign key)

---

#### Table: `formations`
Stores team formation/lineup configuration.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | Primary Key | Auto-incrementing formation ID |
| `team_id` | Integer | Foreign Key → `teams.id` | Reference to parent team (unique per team) |
| `goalkeeper` | Integer | Foreign Key → `players.id`, Nullable | Player ID of goalkeeper |
| `lines` | JSON | Nullable | Array of formation lines, each containing player IDs |

**Structure Example**:
```json
{
  "goalkeeper": 5,
  "lines": [
    [1, 2, 3, 4],      // Line 1: 4 players
    [6, 7, 8],         // Line 2: 3 players
    [9, 10]            // Line 3: 2 players
  ]
}
```

**Relationships**:
- One-to-One: `Formation.team` → `Team` (each team has one formation)
- Many-to-One: `Formation.goalkeeper` → `Player` (references goalkeeper player)

**Initialization**: One formation per team (team_id=1, team_id=2) is automatically created if it doesn't exist.

---

#### Table: `advertisements`
Stores advertisement/sponsor information and media assets.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | Primary Key | Auto-incrementing advertisement ID |
| `name` | String(255) | Nullable | Advertisement name (displayed on launcher button) |
| `sponsor` | String(255) | Nullable | Sponsor/company name (for reference) |
| `type` | String(50) | Nullable | Trigger action type: `"Launcher"`, `"Goal"`, `"Substitution"`, `"Red Card"`, `"Yellow Card"` |
| `duration` | Integer | Nullable | Display duration in seconds |
| `image_path` | String(255) | Nullable | Relative path to image file (e.g., `"static/media_assets/ad_1_a1b2c3d4.png"`) |

**File Storage**: Images are stored in `static/media_assets/` with unique filenames: `ad_{id}_{uuid}.{ext}`

---

#### Table: `obs_commands`
Stores OBS command configurations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | Primary Key | Auto-incrementing command ID |
| `name` | String(255) | Nullable | Command name/label |
| `color` | String(7) | Default: `'#000000'` | Hex color code for UI display |
| `shortcut` | String(255) | Nullable | Keyboard shortcut or command identifier |

---

### Database Initialization

The database is initialized in `app.py`:

1. **Database Creation**: `db.create_all()` creates all tables if they don't exist
2. **Team Initialization**: Creates Team(id=1) and Team(id=2) if missing
3. **Formation Initialization**: Creates Formation for each team if missing

### Data Persistence

- **Persistent Data**: Teams, Players, Formations, Advertisements, OBS Commands
  - Stored in SQLite database
  - Persists across server restarts
  - Modified via Socket.IO events and HTTP endpoints

- **Runtime Data**: Timer state, Score state
  - Stored in Python dictionaries (`timer_state`, `score_state`)
  - Resets on server restart
  - Synchronized across clients via Socket.IO broadcasts

### Database Operations

All database operations use SQLAlchemy sessions:
- **Read**: `Model.query.all()`, `Model.query.get(id)`, `Model.query.filter_by(...)`
- **Create**: `db.session.add(model)`, `db.session.commit()`
- **Update**: Modify model attributes, then `db.session.commit()`
- **Delete**: `db.session.delete(model)`, `db.session.commit()`
- **Error Handling**: `db.session.rollback()` on exceptions


## API

### HTTP Endpoints

| Path | Method | Description | Response (JSON) |
|------|--------|-------------|------------------|
| `/` | GET | Redirects to control interface | 302 redirect to `/control` |
| `/obs` | GET | OBS/browser overlay page | HTML |
| `/control` | GET | Operator control interface with QR code | HTML |
| `/setup` | GET | Team, roster and formation management UI | HTML |
| `/setup-adds` | GET | Advertisement management UI | HTML |
| `/Logo.svg` | GET | Project logo asset | SVG |
| `/timer` | GET | Current timer state | `timer_state` object |
| `/game_state` | GET | Current score state | `score_state` object |
| `/teams` | GET | All teams | `{ "teams": Team[] }` |
| `/players` | GET | All players | `{ "players": Player[] }` |
| `/formations` | GET | All formations | `{ "formations": Formation[] }` |
| `/ads` | GET | All advertisements | `{ "ads": Advertisement[] }` |
| `/ads/upload-image` | POST | Upload/replace image for an advertisement | `{ success, image_path? , error? }` |
| `/static/media_assets/<filename>` | GET | Serve advertisement media assets | Binary file (image/video) |
| `/obs-commands` | GET | All OBS commands | `{ "obs_commands": OBSCommand[] }` |

### Socket.IO – events received by the server

| Event name | Payload (shape) | Description | Server-side effects / emitted events |
|-----------|-----------------|-------------|--------------------------------------|
| `start-timer` | none | Start match timer | Updates `timer_state`, emits `update-timer-start` (broadcast) |
| `stop-timer` | none | Stop match timer | Updates `timer_state`, emits `update-timer-stop` (broadcast) |
| `reset-timer` | none | Reset timer to 0:00 | Updates `timer_state`, emits `update-timer` (broadcast) |
| `set-timer` | `{ offset }` | Set timer offset (in seconds) | Updates `timer_state`, emits `update-timer` (broadcast) |
| `set-extra-time` | `{ extra-time }` | Set extra time value | Updates `timer_state`, emits `show-extra-time` (broadcast) |
| `trigger-goal` | `{ team: "team1" \| "team2" }` | Increment score for selected team | Updates `score_state`, emits `add-to-score` (broadcast) |
| `cancel-goal` | `{ team: "team1" \| "team2" }` | Decrease score for selected team | Updates `score_state`, emits `decrease-to-score` (broadcast) |
| `trigger-event` | `{ ... }` | Generic game event (goal/card/substitution/formation payload) | Emits `display-event` (broadcast) or `event-error` (to sender) |
| `modify-team` | `{ team, name?, manager?, bg_color?, text_color? }` | Update basic team info | Emits `team-modified` (to sender), `update-teams` (broadcast) |
| `create-player` | `{ team }` | Create a new player for a team | Emits `player-created`, `update-players` |
| `modify-player` | `{ id, name?, number? }` | Update existing player | Emits `player-modified`, `update-players` |
| `delete-player` | `{ id }` | Delete a player | Emits `player-deleted`, `update-players` |
| `modify-formation` | `{ id, goalkeeper?, lines? }` | Update team formation | Emits `formation-modified`, `update-formations` |
| `create-ad` | `{ }` | Create a new advertisement with default values | Emits `ad-created`, `update-ads` |
| `modify-ad` | `{ id, name?, sponsor?, type?, duration?, image_path? }` | Update advertisement fields | Emits `ad-modified`, `update-ads` |
| `delete-ad` | `{ id }` | Delete an advertisement | Emits `ad-deleted`, `update-ads` |
| `trigger-ad` | `{ id }` | Trigger display of an advertisement | Emits `display-ad` (broadcast) or `ad-display-error` (to sender) |
| `create-obs-command` | `{ }` | Create a new OBS command entry | Emits `obs-command-created`, `update-obs-commands` |
| `modify-obs-command` | `{ id, name?, color?, shortcut? }` | Update OBS command configuration | Emits `obs-command-modified`, `update-obs-commands` |
| `delete-obs-command` | `{ id }` | Delete an OBS command | Emits `obs-command-deleted`, `update-obs-commands` |
| `trigger-obs-command` | `{ ... }` | Trigger execution of an OBS command | Emits `obs-command-execution` (to sender) |

### Socket.IO – events emitted by the server

| Event name | Emitted from | Payload | Scope | Description |
|-----------|--------------|---------|-------|-------------|
| `update-timer-start` | `start-timer` handler | none | `broadcast=True` | Notify all clients that timer has started |
| `update-timer-stop` | `stop-timer` handler | none | `broadcast=True` | Notify all clients that timer has stopped |
| `update-timer` | `reset-timer`, `set-timer` handlers | none | `broadcast=True` | Notify all clients to refresh timer state |
| `show-extra-time` | `set-extra-time` handler | `{ extra-time }` | `broadcast=True` | Display extra time value on overlays |
| `add-to-score` | `trigger-goal` handler | `score_state` | `broadcast=True` | Notify all clients of updated score |
| `decrease-to-score` | `cancel-goal` handler | `score_state` | `broadcast=True` | Notify all clients of updated score |
| `display-event` | `trigger-event` handler | Generic event object | `broadcast=True` | Instruct overlays to display a game event card |
| `event-error` | `trigger-event` handler | `{ error }` | `room=request.sid` | Notify sender that event processing failed |
| `team-modified` | `modify-team` handler | `{ success, error? }` | `room=request.sid` | Acknowledge result of team update |
| `update-teams` | `modify-team` handler | none | `broadcast=True` | Tell clients to refresh team data |
| `player-created` | `create-player` handler | `{ success, player? , error? }` | default (to all) | Notify about newly created player |
| `player-modified` | `modify-player` handler | `{ success, error? }` | `room=request.sid` | Acknowledge player update |
| `player-deleted` | `delete-player` handler | `{ success, error? }` | `room=request.sid` | Acknowledge player deletion |
| `update-players` | create/modify/delete player handlers | none | `broadcast=True` | Tell clients to refresh player list |
| `formation-modified` | `modify-formation` handler | `{ success, error? }` | `room=request.sid` | Acknowledge formation update |
| `update-formations` | `modify-formation` handler | none | `broadcast=True` | Tell clients to refresh formations |
| `ad-created` | `create-ad` handler | `{ success, ad? , error? }` | default (to all) | Notify that an ad was created |
| `ad-modified` | `modify-ad` handler | `{ success, error? }` | `room=request.sid` | Acknowledge ad update |
| `ad-deleted` | `delete-ad` handler | `{ success, error? }` | `room=request.sid` | Acknowledge ad deletion |
| `update-ads` | create/modify/delete ad handlers | none | `broadcast=True` | Tell clients to refresh advertisement list |
| `display-ad` | `trigger-ad` handler | `{ id }` | `broadcast=True` | Instruct overlays to display an advertisement |
| `ad-display-error` | `trigger-ad` handler | `{ error }` | `room=request.sid` | Notify sender that ad display failed |
| `obs-command-created` | `create-obs-command` handler | `{ success, obs-command? , error? }` | default (to all) | Notify that an OBS command was created |
| `obs-command-modified` | `modify-obs-command` handler | `{ success, error? }` | `room=request.sid` | Acknowledge OBS command update |
| `obs-command-deleted` | `delete-obs-command` handler | `{ success, error? }` | `room=request.sid` | Acknowledge OBS command deletion |
| `update-obs-commands` | OBS command create/modify/delete handlers | none | `broadcast=True` | Tell clients to refresh OBS commands |
| `obs-command-execution` | `trigger-obs-command` handler | `{ success, error? }` | `room=request.sid` | Acknowledge OBS command execution result |

## State Structures

### `timer_state` (Runtime)
```javascript
{
  'timer_anchor': timer_anchor, 
  'timer_offset': timer_offset, 
  'timer_running': timer_running,
  'extra_time': extra_time
}
```

### `score_state` (Runtime)
```javascript
{
  team1_score, 
  team2_score
}
```


**Action Structures**

### Game Event Trigger
```javascript
{
  'type': type, 
  'team': team,
  // if type == 'goal'
  'player_id': id,
  // if type == 'card'
  'player_id': id,
  'card_type': card
  // if type == 'substitution'
  'player_id_out': id, 
  'player_id_in': id
  // if type == 'formation'
  // [none additional]
}
```

### Advertisement Event Trigger
```javascript
{
  'id': id
}
```

### OBS Command Event Trigger
```javascript
{
  'id': id                     // Unique command ID
}
```

## Control Interface Features

### Scoreboard Control
- **Score Management**: +1/-1 buttons for each team
- **Timer Control**: Start, stop, reset buttons with server sync
- **Timer Configuration**: Set time in minutes, add extra time
- **Connection Status**: Real-time indicator showing server connection state

### Event Management
- **Team Selection**: Toggle between Team 1 and Team 2 context
- **Goals**: Submit goal with player number
- **Penalty Cards**: Submit yellow or red card with player number
- **Substitutions**: Submit player swap (player out ↔ player in)
- **Lineup**: Display team formation overlay on scoreboard

### Advertisement Launcher
- **Dynamic Buttons**: Auto-populated with all "Launcher" action advertisements
- **One-Click Launch**: Press button to immediately trigger advertisement event
- **Visual Feedback**: Advertisement name shown in button tooltip
- **Button Grid**: Responsive layout (2 columns mobile, 3 columns tablet, 4 columns desktop)
- **Real-time Updates**: Buttons refresh when new ads are created

### Additional Features
- **Settings Access**: Link to team/roster configuration
- **Advertisement Management**: Link to advertisement database editor
- **Mobile Access**: QR code and local IP address for remote operation via smartphone displayed on the interface

## Advertisement Management Workflow

### Creating an Advertisement
1. Navigate to `/setup-ads`
2. Click "Create Advertisement"
3. Enter advertisement name (will display on the launcher button), sponsor (just for user's reference), and action
4. Configure duration (in seconds) 
5. Add Image
6. Ad appears in database with placeholder image

### Uploading an Image
1. Click "Add Image" button on advertisement row
2. Select image file (PNG, JPG, GIF, WebP, WebM, max 16MB)
3. File uploaded to `static/advertisements/` with unique filename
4. Image path stored in advertisement database
5. Old image automatically deleted if replaced

### Deleting an Advertisement
1. Click delete button on advertisement row
2. Confirmation dialog appears
3. Advertisement removed from database
4. Associated image file deleted from disk




## Version & Attribution
- Current version: `0.8.4`
- Developed by: Diogo Aleixo
- Project: OBS Football Graphics System