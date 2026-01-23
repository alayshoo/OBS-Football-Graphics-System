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
│   ├── setup_adds.html             # Advertisement management
│   │
│   └── css/                        # Stylesheet directory
│       ├── shared.css              # Common styles used across pages
│       ├── scoreboard.css          # Scoreboard styling
│       ├── scoreboard_event.css    # Event card styling
│       ├── formation.css           # Formation overlay styling for scoreboard.html
│       └── formation_config.css    # Formation configuration styling for setup.html
│
├── static/                         # Static assets
│   ├── Logo.svg                    # Logo asset
│   └── advertisements/             # Advertisement images (generated at runtime)
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
  - Advertisement database management (JSON file: `advertisements_database.json`)
  - Game event queue system (stores last 50 events)
  - Advertisement event queue system (stores last 20 events)
  - QR code generation for easy mobile access
  - Image upload handling for advertisements

### Frontend Components

#### 1. **Scoreboard** (`scoreboard.html`)
- **Purpose**: OBS browser source display
- **Features**:
  - Real-time score and timer display
  - Game event card animations (goals, cards, substitutions)
  - Advertisement display triggered by launcher buttons or events
  - Formation overlay with team lineup visualization
  - Client-side timer calculation with server sync

#### 2. **Control Interface** (`control_interface.html`)
- **Purpose**: Operator control panel (desktop/tablet)
- **Features**:
  - Score management (+/- buttons)
  - Timer control (start/stop/reset, set time, add extra time)
  - Game event submission (goals, cards, substitutions, formations)
  - **Advertisement launcher buttons** (dynamically populated from database)
  - Real-time button refresh from advertisement database

#### 3. **Setup Interface** (`setup.html`)
- **Purpose**: Team and roster configuration
- **Features**:
  - Team name and manager input
  - Color customization (Predefined 9-color palette)
  - Player roster management
  - Formation configuration (goalkeeper + 4 lines)
  - Persistent storage between sessions

#### 4. **Advertisement Management** (`setup_adds.html`)
- **Purpose**: Advertisement database management
- **Features**:
  - Add, edit, and delete advertisements
  - Image upload for each advertisement
  - Sponsor field for each advertisement
  - Action trigger configuration (Launcher, Goal, Substitution, Red Card, Yellow Card)
  - Duration configuration for each ad
  - Real-time database synchronization

### Data Persistence
- **JSON** (`football_settings.json`): Team names, managers, colors, formations, rosters
- **JSON** (`advertisements_database.json`): Advertisement metadata, sponsor info, action triggers, and image paths
- **Images** (`static/advertisements/`): Advertisement image files

## Key Workflows

### Timer Synchronization
- **Server maintains**: `timer_anchor` (start time), `timer_offset` (elapsed seconds), `timer_running` (state)
- **Client receives**: `server_time` to calculate clock offset
- **Local calculation**: Client updates timer every 100ms without polling (reduces network load)
- Only re-syncs when server state changes

### Game Event Workflow
1. **Event submission**: Operator submits goal, card, substitution, or formation via control panel
2. **Event creation**: Backend generates event with ID, timestamp, team, and player info
3. **Event queuing**: Event added to `event_queue` (max 50 events)
4. **Scoreboard display**: Scoreboard polls `/events` and displays event cards sequentially
5. **Event deduplication**: Scoreboard tracks `lastEventIds` to prevent duplicate displays

### Advertisement Event Workflow
1. **Ad creation**: Advertisement created in setup with name, sponsor, action, duration, and image
2. **Launcher buttons**: Control interface fetches all "Launcher" action ads and renders buttons
3. **Button trigger**: Operator clicks launcher button to trigger advertisement
4. **Ad event creation**: Backend creates ad event with metadata (ID, name, sponsor, duration, image path)
5. **Ad event queuing**: Ad event added to `ad_event_queue` (max 20 events)
6. **Scoreboard display**: Scoreboard polls `/add-events` and displays ad according to duration and image
7. **Action-triggered ads**: Ads with "Goal", "Substitution", "Red Card", "Yellow Card" actions can be auto-triggered by corresponding game events (future implementation)

### Advertisement Management
- Images uploaded to `static/advertisements/` with unique filenames
- Old images automatically deleted when replaced
- File validation: PNG, JPG, JPEG, GIF, WebP (max 16MB)
- Database maintains reference to image paths, sponsor info, and action triggers
- Launcher buttons dynamically loaded from database on control interface

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Redirect to control |
| `/scoreboard` | GET | OBS overlay page |
| `/control` | GET | Operator control panel |
| `/setup` | GET | Team setup page |
| `/setup-adds` | GET | Advertisement management page |
| `/state` | GET | Fetch current game state |
| `/state` | POST | Update scores, timer, colors, names |
| `/events` | GET | Fetch last 10 game events |
| `/events` | POST | Submit new game event (goal/card/sub/formation) |
| `/add-events` | GET | Fetch last 10 advertisement events |
| `/add-events` | POST | Submit new advertisement event |
| `/setup/data` | GET | Fetch all settings |
| `/setup/data` | POST | Save all settings |
| `/setup-adds/data` | GET | Fetch all advertisements |
| `/setup-adds/data` | POST | Create new advertisement |
| `/setup-adds/data` | PATCH | Modify existing advertisement |
| `/setup-adds/data` | DELETE | Delete advertisement and image |
| `/setup-adds/upload-image` | POST | Upload image for advertisement |
| `/Logo.svg` | GET | Logo asset |

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
```json
{
  "team1_name": "Team 1",
  "team2_name": "Team 2",
  "team1_manager": "",
  "team2_manager": "",
  "team1_bg": "Blue",
  "team1_text": "White",
  "team2_bg": "Red",
  "team2_text": "White",
  "team1_formation": {
    "goalkeeper": "",
    "lines": [[], [], [], []]
  },
  "team2_formation": {
    "goalkeeper": "",
    "lines": [[], [], [], []]
  },
  "team1_roster": [
    {
      "number": 1,
      "name": "Player Name"
    }
  ],
  "team2_roster": [
    {
      "number": 1,
      "name": "Player Name"
    }
  ]
}
```

### `adverts_state` (Persistent)
```json
{
  "adverts": [
    {
      "id": 1,
      "name": "Sponsor Ad",
      "sponsor": "Company Name",
      "action": "Launcher",
      "duration": 10,
      "imagePath": "static/advertisements/ad_1_abc12345.jpg"
    }
  ],
  "next_id": 2
}
```

**Action Options**: `Launcher`, `Goal`, `Substitution`, `Red Card`, `Yellow Card`

### Game Event Objects
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
  formation, roster, team_bg, team_text, team_name, manager
}
```

### Advertisement Event Objects
```javascript
{
  id,                    // Unique event ID
  type: 'advert',        // Always 'advert'
  advert_id,             // ID from advertisements database
  name,                  // Advertisement name
  sponsor,               // Sponsor/company name
  duration,              // Display duration in seconds
  imagePath,             // Path to advertisement image
  timestamp              // When event was created
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
- **Formation**: Display team formation overlay on scoreboard

### Advertisement Launcher
- **Dynamic Buttons**: Auto-populated with all "Launcher" action advertisements
- **One-Click Launch**: Press button to immediately trigger advertisement event
- **Visual Feedback**: Sponsor name shown in button tooltip
- **Button Grid**: Responsive layout (2 columns mobile, 3 columns tablet, 4 columns desktop)
- **Real-time Updates**: Buttons refresh when new ads are created

### Additional Features
- **Settings Access**: Link to team/roster configuration
- **Advertisement Management**: Link to advertisement database editor
- **Mobile Access**: QR code and local IP address for remote operation via smartphone

## Advertisement Management Workflow

### Creating an Advertisement
1. Navigate to `/setup-adds`
2. Enter advertisement name, sponsor, and action
3. Configure duration (in seconds)
4. Click "Create Advertisement"
5. Auto-increment ID assigned
6. Ad appears in database with placeholder image

### Uploading an Image
1. Click "Add Image" button on advertisement row
2. Select image file (PNG, JPG, GIF, WebP, max 16MB)
3. File uploaded to `static/advertisements/` with unique filename
4. Image path stored in advertisement database
5. Old image automatically deleted if replaced

### Modifying an Advertisement
1. Edit name, sponsor, action, or duration fields
2. Click save/update button
3. Changes applied immediately
4. Image can be replaced without losing other metadata

### Deleting an Advertisement
1. Click delete button on advertisement row
2. Confirmation dialog appears
3. Advertisement removed from database
4. Associated image file deleted from disk

### Launcher Advertisement Usage
1. Create advertisement with action = "Launcher"
2. Upload advertisement image
3. Control interface automatically fetches and displays launcher button
4. Operator clicks button to trigger ad event
5. Scoreboard receives ad event and displays image for configured duration

### Advertisement Display Behaviour
- **Independent System**: Ads display independently from game event cards
- **Animation**: Slides up from bottom, stays for duration, slides back down
- **Dimensions**: Max 1825×150px with rounded top corners (12px radius)
- **Media Support**: Images (PNG, JPG, GIF, WebP) and videos (WebM)
- **Auto-Trigger**: Ads with action types (Goal, Substitution, Red Card, Yellow Card) automatically display when matching game events occur

## Advertisement Table Structure

The advertisement management interface displays a table with the following columns:

| Column | Type | Notes |
|--------|------|-------|
| Name | Text Input | Advertisement name |
| Sponsor | Text Input | Company or sponsor name |
| Action | Dropdown | Trigger action (Launcher, Goal, Substitution, Red Card, Yellow Card) |
| Duration | Number Input | Display duration in seconds |
| Image | Display Only | Shows thumbnail and filename |
| Upload | Button | Opens file upload for image |
| Edit | Button | Modify advertisement details |
| Delete | Button | Removes advertisement and image |

## Response Handling

### Game Event Queue Management
- Scoreboard tracks `lastEventIds` to prevent duplicates
- One event displays at a time (7-second duration)
- Next event automatically queued
- Formation events bypass event card, display overlay directly

### Advertisement Event Queue Management
- Scoreboard tracks `lastAdEventIds` to prevent duplicates
- Advertisements display for configured duration
- Multiple ads queue sequentially
- Auto-advance to next ad when duration expires

### File Upload Constraints
- Maximum file size: 16MB per image
- Allowed formats: PNG, JPG, JPEG, GIF, WebP, WebM
- Unique filenames prevent collisions (`ad_{id}_{random}.ext`)
- Automatic cleanup of replaced images
- Server-side validation on file extension and size

## Version & Attribution
- Current version: `0.8.4`
- Developed by: Diogo Aleixo
- Project: Brigantia Score System