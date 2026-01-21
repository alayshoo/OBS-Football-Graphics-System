from flask import Flask, render_template, render_template_string, jsonify, send_file, request
from flask_cors import CORS
import threading
import webbrowser
import time
import os
import socket
import base64
import qrcode
import io
import json
import csv
from collections import deque

app_version = "0.4.0"

# Shared global state
game_state = {
    'team1_name': 'Team 1',
    'team2_name': 'Team 2',
    'team1_score': 0,
    'team2_score': 0,
    'team1_bg': 'Blue',
    'team1_text': 'White',
    'team2_bg': 'Red',
    'team2_text': 'White',
    'timer_anchor': None,
    'timer_offset': 0,
    'timer_running': False,
    'extra_time': 0,
    'last_timer_update': time.time()
}

settings_state = {
    'team1_name': 'Team 1',
    'team2_name': 'Team 2',
    'team1_bg': 'Blue',
    'team1_text': 'White',
    'team2_bg': 'Red',
    'team2_text': 'White',
}

# Event notifications (stores last 50 events)
event_queue = deque(maxlen=50)
event_counter = 0

app = Flask(__name__, template_folder='templates')
CORS(app)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def load_settings():
    """Load settings from file"""
    if os.path.exists('settings.json'):
        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
    return settings_state.copy()

def save_settings(settings):
    """Save settings to file"""
    try:
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

def load_team_roster(team_number):
    """Load team roster from CSV file"""
    filename = f'team{team_number}_players.csv'
    players = []
    
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    players.append({
                        'number': row['number'],
                        'name': row['name']
                    })
        except Exception as e:
            print(f"Error loading {filename}: {e}")
    
    return players

def save_team_roster(team_number, players):
    """Save team roster to CSV file"""
    filename = f'team{team_number}_players.csv'
    
    try:
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['number', 'name'])
            writer.writeheader()
            for player in players:
                writer.writerow({
                    'number': player['number'],
                    'name': player['name']
                })
        return True
    except Exception as e:
        print(f"Error saving {filename}: {e}")
        return False

@app.route('/scoreboard')
def scoreboard():
    return render_template('scoreboard.html')

@app.route('/control')
def control():
    local_ip = get_local_ip()
    port = 5000
    url = f"http://{local_ip}:{port}/control"

    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    img_buffer = io.BytesIO()
    qr_img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    qr_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

    with open('templates/control_interface.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    return render_template_string(
        html_content, 
        app_version=app_version, 
        local_ip=local_ip, 
        port=port,
        qr_code=qr_base64
    )

@app.route('/setup')
def setup():
    return render_template('setup.html')

@app.route('/teams/load', methods=['GET'])
def load_teams():
    """Load both team rosters"""
    current_settings = load_settings()
    return jsonify({
        'team1': load_team_roster(1),
        'team2': load_team_roster(2),
        'team1_name': current_settings.get('team1_name', 'Team 1'),
        'team2_name': current_settings.get('team2_name', 'Team 2'),
        'team1_bg': current_settings.get('team1_bg', 'Blue'),
        'team1_text': current_settings.get('team1_text', 'White'),
        'team2_bg': current_settings.get('team2_bg', 'Red'),
        'team2_text': current_settings.get('team2_text', 'White'),
    })

@app.route('/teams/save', methods=['POST'])
def save_teams():
    """Save both team rosters"""
    data = request.json
    
    team1_players = data.get('team1', [])
    team2_players = data.get('team2', [])
    
    success1 = save_team_roster(1, team1_players)
    success2 = save_team_roster(2, team2_players)
    
    if success1 and success2:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to save rosters'}), 500

@app.route('/settings/save', methods=['POST'])
def save_settings_route():
    """Save team settings"""
    data = request.json
    
    settings = {
        'team1_name': data.get('team1_name', 'Team 1'),
        'team2_name': data.get('team2_name', 'Team 2'),
        'team1_bg': data.get('team1_bg', 'Blue'),
        'team1_text': data.get('team1_text', 'White'),
        'team2_bg': data.get('team2_bg', 'Red'),
        'team2_text': data.get('team2_text', 'White'),
    }
    
    if save_settings(settings):
        # Also update game_state
        game_state.update(settings)
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to save settings'}), 500

@app.route('/state', methods=['GET'])
def get_state():
    """Returns state with anchor time for client-side calculation"""
    return jsonify({
        'team1_name': game_state['team1_name'],
        'team2_name': game_state['team2_name'],
        'team1_score': game_state['team1_score'],
        'team2_score': game_state['team2_score'],
        'team1_bg': game_state['team1_bg'],
        'team1_text': game_state['team1_text'],
        'team2_bg': game_state['team2_bg'],
        'team2_text': game_state['team2_text'],
        'timer_anchor': game_state['timer_anchor'],
        'timer_offset': game_state['timer_offset'],
        'timer_running': game_state['timer_running'],
        'extra_time': game_state['extra_time'],
        'last_timer_update': game_state['last_timer_update'],
        'server_time': time.time()
    })

@app.route('/events', methods=['GET'])
def get_events():
    """Get recent events (last 10)"""
    response = jsonify(list(event_queue)[-10:])
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/update', methods=['POST'])
def update_state():
    global game_state
    data = request.json

    fields = [
        'team1_name',
        'team2_name',
        'team1_score',
        'team2_score',
        'team1_bg',
        'team1_text',
        'team2_bg',
        'team2_text',
        'extra_time',
    ]
    
    settings_changed = False
    for field in fields:
        if field in data:
            game_state[field] = data[field]
            if field in ['team1_name', 'team2_name', 'team1_bg', 'team1_text', 'team2_bg', 'team2_text']:
                settings_changed = True

    # Save settings if any setting-related field changed
    if settings_changed:
        settings = {
            'team1_name': game_state['team1_name'],
            'team2_name': game_state['team2_name'],
            'team1_bg': game_state['team1_bg'],
            'team1_text': game_state['team1_text'],
            'team2_bg': game_state['team2_bg'],
            'team2_text': game_state['team2_text'],
        }
        save_settings(settings)

    if 'set_time' in data:
        try:
            minutes = int(data['set_time'])
            game_state['timer_offset'] = minutes * 60
            game_state['timer_anchor'] = time.time()
            game_state['timer_running'] = False
            game_state['last_timer_update'] = time.time()
        except:
            pass

    if 'timer_action' in data:
        action = data['timer_action']
        now = time.time()
        
        if action == 'start':
            if not game_state['timer_running']:
                game_state['timer_running'] = True
                game_state['timer_anchor'] = now
                game_state['last_timer_update'] = now
                
        elif action == 'stop':
            if game_state['timer_running']:
                elapsed = (now - game_state['timer_anchor']) + game_state['timer_offset']
                game_state['timer_offset'] = int(elapsed)
                game_state['timer_anchor'] = now
                game_state['timer_running'] = False
                game_state['last_timer_update'] = now
                
        elif action == 'reset':
            game_state['timer_running'] = False
            game_state['timer_anchor'] = now
            game_state['timer_offset'] = 0
            game_state['extra_time'] = 0
            game_state['last_timer_update'] = now

    return jsonify({'success': True})

@app.route('/event', methods=['POST'])
def add_event():
    global event_counter
    data = request.json

    event_type = data.get('type')
    team = data.get('team')

    if not event_type or not team:
        return jsonify({'success': False, 'error': 'Missing type or team'}), 400

    # Load the team roster and create lookup dict
    team_number = 1 if team == 'team1' else 2
    roster = load_team_roster(team_number)
    player_lookup = {str(p['number']): p['name'] for p in roster}

    event_counter += 1
    event = {
        'id': event_counter,
        'type': event_type,
        'team': team,
        'timestamp': time.time(),
    }

    if event_type == 'goal':
        player_num = data.get('player', '?')
        event['player'] = player_num
        event['player_name'] = player_lookup.get(str(player_num), '')
    elif event_type == 'card':
        player_num = data.get('player', '?')
        event['player'] = player_num
        event['player_name'] = player_lookup.get(str(player_num), '')
        event['card_type'] = data.get('card_type', 'yellow')
    elif event_type == 'substitution':
        player_out = data.get('player_out', '?')
        player_in = data.get('player_in', '?')
        event['player_out'] = player_out
        event['player_in'] = player_in
        event['player_out_name'] = player_lookup.get(str(player_out), '')
        event['player_in_name'] = player_lookup.get(str(player_in), '')

    event_queue.append(event)
    return jsonify({'success': True, 'event_id': event_counter})

@app.route('/BrigantiaLogo.svg')
def BrigantiaLogo():
    return send_file('BrigantiaLogo.svg', mimetype='image/svg+xml')

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    
    # Load saved settings
    saved_settings = load_settings()
    game_state.update(saved_settings)
    
    threading.Thread(
        target=lambda: (
            time.sleep(2),
            webbrowser.open('http://localhost:5000/control'),
        ),
        daemon=True,
    ).start()
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)