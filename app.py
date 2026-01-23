from flask import Flask, render_template, render_template_string, jsonify, send_file, send_from_directory, request, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
import uuid
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

app_version = "0.9.0"

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
    'team1_manager': '',
    'team2_manager': '',
    'team1_bg': 'Blue',
    'team1_text': 'White',
    'team2_bg': 'Red',
    'team2_text': 'White',
    'team1_formation': {'goalkeeper': '', 'lines': [[], [], [], []]},
    'team2_formation': {'goalkeeper': '', 'lines': [[], [], [], []]},
}

# Event notifications (stores last 50 events)
event_queue = deque(maxlen=50)
event_counter = 0
ad_event_queue = deque(maxlen=20)
ad_event_counter = 0

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='templates',
    static_url_path=''
)
CORS(app)

# Image upload system for addverts
UPLOAD_FOLDER = 'static/advertisements'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'webm'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    """Load all settings from file (teams, rosters, formations)"""
    default = {
        'team1_name': 'Team 1',
        'team2_name': 'Team 2',
        'team1_manager': '',
        'team2_manager': '',
        'team1_bg': 'Blue',
        'team1_text': 'White',
        'team2_bg': 'Red',
        'team2_text': 'White',
        'team1_formation': {'goalkeeper': '', 'lines': [[], [], [], []]},
        'team2_formation': {'goalkeeper': '', 'lines': [[], [], [], []]},
        'team1_roster': [],
        'team2_roster': [],
    }
    
    if os.path.exists('football_settings.json'):
        try:
            with open('football_settings.json', 'r', encoding='utf-8') as f:
                saved = json.load(f)
                default.update(saved)
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    return default

def save_settings(settings):
    """Save all settings to file"""
    try:
        with open('football_settings.json', 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

def load_adverts():
    """Load advertisements database from file"""
    default = {
        'adverts': [],
        'next_id': 1
    }
    
    if os.path.exists('advertisements_database.json'):
        try:
            with open('advertisements_database.json', 'r', encoding='utf-8') as f:
                saved = json.load(f)
                default.update(saved)
        except Exception as e:
            print(f"Error loading adverts: {e}")
    
    return default

def save_adverts(adverts_data):
    """Save advertisements database to file"""
    try:
        with open('advertisements_database.json', 'w', encoding='utf-8') as f:
            json.dump(adverts_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving adverts: {e}")
        return False

def trigger_associated_ads(event_type, card_type=None):
    """Trigger any ads associated with the given event type"""
    global ad_event_counter

    # Map event types to ad action names
    action_map = {
        'goal': 'Goal',
        'substitution': 'Substitution',
    }

    # Handle card types separately
    if event_type == 'card':
        if card_type == 'red':
            target_action = 'Red Card'
        else:
            target_action = 'Yellow Card'
    else:
        target_action = action_map.get(event_type)

    if not target_action:
        return

    # Load advertisements and find matching ones
    adverts_data = load_adverts()
    matching_ads = [
        ad for ad in adverts_data.get('adverts', [])
        if ad.get('action') == target_action and ad.get('imagePath')
    ]

    # Create ad events for each matching advertisement
    for ad in matching_ads:
        ad_event_counter += 1
        ad_event = {
            'id': ad_event_counter,
            'type': 'advert',
            'advert_id': ad.get('id'),
            'name': ad.get('name', ''),
            'sponsor': ad.get('sponsor', ''),
            'duration': ad.get('duration', 10),
            'imagePath': ad.get('imagePath', ''),
            'timestamp': time.time()
        }
        ad_event_queue.append(ad_event)

# Routes

@app.route('/')
def index():
    return redirect(url_for('control'))

@app.route('/scoreboard')
def scoreboard():
    return render_template('scoreboard.html')

@app.route('/control')
def control():
    local_ip = get_local_ip()
    port = 8246
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

@app.route('/setup/data', methods=['GET'])
def get_setup_data():
    """Load all setup data"""
    settings = load_settings()
    return jsonify(settings)

@app.route('/setup-adds')
def setup_adds():
    return render_template('setup_adds.html')

@app.route('/setup-adds/data', methods=['GET'])
def get_setup_adds_data():
    """ Gets all add database """
    adverts_data = load_adverts()
    return jsonify(adverts_data['adverts'])

@app.route('/setup-adds/data', methods=['POST'])
def post_new_add():
    """ Creates a new add """
    data = request.json
    
    # Load current database
    adverts_data = load_adverts()
    
    # Create new advert with auto-incremented ID
    new_advert = {
        'id': adverts_data['next_id'],
        'name': data.get('name', ''),
        'sponsor': data.get('sponsor', ''),
        'action': data.get('action', 'Launcher'),
        'duration': data.get('duration', 10),
        'imagePath': data.get('imagePath', '')
    }
    
    # Add to database
    adverts_data['adverts'].append(new_advert)
    adverts_data['next_id'] += 1
    
    # Save and return
    if save_adverts(adverts_data):
        return jsonify({'success': True, 'advert': new_advert})
    else:
        return jsonify({'success': False, 'error': 'Failed to save advert'}), 500

@app.route('/setup-adds/data', methods=['PATCH'])
def modify_add():
    """ Modifies an existing add """
    data = request.json
    
    advert_id = data.get('id')
    if not advert_id:
        return jsonify({'success': False, 'error': 'Missing advert ID'}), 400
    
    # Load current database
    adverts_data = load_adverts()
    
    # Find and update the advert
    found = False
    for advert in adverts_data['adverts']:
        if advert['id'] == advert_id:
            # Update only provided fields
            if 'name' in data:
                advert['name'] = data['name']
            if 'sponsor' in data:
                advert['sponsor'] = data['sponsor']
            if 'action' in data:
                advert['action'] = data['action']
            if 'duration' in data:
                advert['duration'] = data['duration']
            if 'imagePath' in data:
                advert['imagePath'] = data['imagePath']
            found = True
            break
    
    if not found:
        return jsonify({'success': False, 'error': 'Advert not found'}), 404
    
    # Save and return
    if save_adverts(adverts_data):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to save changes'}), 500

@app.route('/setup-adds/data', methods=['DELETE'])
def delete_advert():
    """Deletes an existing add and its image"""
    data = request.json
    
    advert_id = data.get('id')
    if not advert_id:
        return jsonify({'success': False, 'error': 'Missing advert ID'}), 400
    
    # Load current database
    adverts_data = load_adverts()
    
    # Find the advert and get its image path
    advert_to_delete = None
    for advert in adverts_data['adverts']:
        if advert['id'] == advert_id:
            advert_to_delete = advert
            break
    
    if not advert_to_delete:
        return jsonify({'success': False, 'error': 'Advert not found'}), 404
    
    # Delete the image file if it exists
    if advert_to_delete['imagePath']:
        image_path = advert_to_delete['imagePath']
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
                print(f"Deleted image: {image_path}")
            except Exception as e:
                print(f"Error deleting image file: {e}")
    
    # Remove from database
    adverts_data['adverts'] = [
        advert for advert in adverts_data['adverts'] 
        if advert['id'] != advert_id
    ]
    
    # Save and return
    if save_adverts(adverts_data):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to save changes'}), 500

@app.route('/setup-adds/upload-image', methods=['POST'])
def upload_add_image():
    """Upload image for an advertisement"""
    # Check if advert_id is provided
    if 'advert_id' not in request.form:
        return jsonify({'success': False, 'error': 'Missing advert ID'}), 400
    
    advert_id = int(request.form['advert_id'])
    
    # Check if file is in request
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['image']
    
    # Check if file was selected
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Validate file type
    if not allowed_file(file.filename):
        return jsonify({
            'success': False, 
            'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    try:
        # Load adverts database
        adverts_data = load_adverts()
        
        # Find the advert
        advert = None
        for ad in adverts_data['adverts']:
            if ad['id'] == advert_id:
                advert = ad
                break
        
        if not advert:
            return jsonify({'success': False, 'error': 'Advert not found'}), 404
        
        # Create upload directory if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Delete old image if it exists
        if advert['imagePath']:
            old_image_path = advert['imagePath']
            if os.path.exists(old_image_path):
                try:
                    os.remove(old_image_path)
                except Exception as e:
                    print(f"Error deleting old image: {e}")
        
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"ad_{advert_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
        
        # Save file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # Update advert with new image path
        advert['imagePath'] = filepath
        
        # Save database
        if save_adverts(adverts_data):
            return jsonify({
                'success': True, 
                'imagePath': filepath,
                'imageUrl': f'/{filepath}'  # URL for browser access
            })
        else:
            # If save fails, delete the uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'success': False, 'error': 'Failed to save changes'}), 500
            
    except Exception as e:
        print(f"Error uploading image: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/setup/data', methods=['POST'])
def post_setup_data():
    """Save all setup data"""
    data = request.json

    settings = {
        'team1_name': data.get('team1_name', 'Team 1'),
        'team2_name': data.get('team2_name', 'Team 2'),
        'team1_manager': data.get('team1_manager', ''),
        'team2_manager': data.get('team2_manager', ''),
        'team1_bg': data.get('team1_bg', 'Blue'),
        'team1_text': data.get('team1_text', 'White'),
        'team2_bg': data.get('team2_bg', 'Red'),
        'team2_text': data.get('team2_text', 'White'),
        'team1_formation': data.get(
            'team1_formation',
            {'goalkeeper': '', 'lines': [[], [], [], []]},
        ),
        'team2_formation': data.get(
            'team2_formation',
            {'goalkeeper': '', 'lines': [[], [], [], []]},
        ),
        'team1_roster': data.get('team1_roster', []),
        'team2_roster': data.get('team2_roster', []),
    }

    if save_settings(settings):
        # Update game_state with display-relevant fields
        game_state.update({
            'team1_name': settings['team1_name'],
            'team2_name': settings['team2_name'],
            'team1_bg': settings['team1_bg'],
            'team1_text': settings['team1_text'],
            'team2_bg': settings['team2_bg'],
            'team2_text': settings['team2_text'],
        })
        return jsonify({'success': True})
    else:
        return jsonify(
            {'success': False, 'error': 'Failed to save settings'}
        ), 500

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

@app.route('/state', methods=['POST'])
def post_to_state():
    global game_state
    data = request.json

    fields = [
        'team1_name',
        'team2_name',
        'team1_manager',
        'team2_manager',
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
        # Load existing settings to preserve formations
        existing_settings = load_settings()
        existing_settings.update({
            'team1_name': game_state['team1_name'],
            'team2_name': game_state['team2_name'],
            'team1_bg': game_state['team1_bg'],
            'team1_text': game_state['team1_text'],
            'team2_bg': game_state['team2_bg'],
            'team2_text': game_state['team2_text'],
        })
        save_settings(existing_settings)

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

@app.route('/events', methods=['GET'])
def get_events():
    """Returns the last 10 events"""
    response = jsonify(list(event_queue)[-10:])
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/events', methods=['POST'])
def post_event():
    global event_counter
    data = request.json

    event_type = data.get('type')
    team = data.get('team')

    if not event_type or not team:
        return jsonify(
            {'success': False, 'error': 'Missing type or team'}
        ), 400

    # Load the team roster and create lookup dict
    settings = load_settings()
    roster_key = (
        'team1_roster' if team == 'team1' else 'team2_roster'
    )
    roster = settings.get(roster_key, [])
    player_lookup = {
        str(p['number']): p['name'] for p in roster
    }

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
        event['player_name'] = player_lookup.get(
            str(player_num), ''
        )
    elif event_type == 'card':
        player_num = data.get('player', '?')
        event['player'] = player_num
        event['player_name'] = player_lookup.get(
            str(player_num), ''
        )
        event['card_type'] = data.get('card_type', 'yellow')
    elif event_type == 'substitution':
        player_out = data.get('player_out', '?')
        player_in = data.get('player_in', '?')
        event['player_out'] = player_out
        event['player_in'] = player_in
        event['player_out_name'] = player_lookup.get(
            str(player_out), ''
        )
        event['player_in_name'] = player_lookup.get(
            str(player_in), ''
        )
    elif event_type == 'formation':
        formation_key = (
            'team1_formation'
            if team == 'team1'
            else 'team2_formation'
        )
        bg_key = 'team1_bg' if team == 'team1' else 'team2_bg'
        text_key = (
            'team1_text' if team == 'team1' else 'team2_text'
        )
        name_key = (
            'team1_name' if team == 'team1' else 'team2_name'
        )
        manager_key = (
            'team1_manager'
            if team == 'team1'
            else 'team2_manager'
        )

        event['formation'] = settings.get(
            formation_key,
            {'goalkeeper': '', 'lines': [[], [], [], []]},
        )
        event['roster'] = roster
        event['team_bg'] = settings.get(bg_key, 'Blue')
        event['team_text'] = settings.get(text_key, 'White')
        event['team_name'] = settings.get(name_key, 'Team')
        event['manager'] = settings.get(manager_key, '')

    event_queue.append(event)

    # Auto-trigger associated advertisements
    if event_type in ['goal', 'card', 'substitution']:
        trigger_associated_ads(event_type, data.get('card_type'))

    return jsonify({'success': True, 'event_id': event_counter})

@app.route('/add-events', methods=['GET'])
def get_add_events():
    """Returns the last 10 ad events"""
    response = jsonify(list(ad_event_queue)[-10:])
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/add-events', methods=['POST'])
def post_add_event():
    global ad_event_counter
    data = request.json

    if data.get('type') != 'advert':
        return jsonify({'success': False, 'error': 'Invalid event type'}), 400

    ad_event_counter += 1
    event = {
        'id': ad_event_counter,
        'type': 'advert',
        'advert_id': data.get('advert_id'),
        'name': data.get('name', ''),
        'sponsor': data.get('sponsor', ''),
        'duration': data.get('duration', 10),
        'imagePath': data.get('imagePath', ''),
        'timestamp': time.time()
    }

    ad_event_queue.append(event)
    return jsonify({'success': True, 'event_id': ad_event_counter})

@app.route('/static/advertisements/<path:filename>')
def serve_advertisement(filename):
    """Serve advertisement images from the static/advertisements folder"""
    return send_from_directory('static/advertisements', filename)

@app.route('/Logo.svg')
def BrigantiaLogo():
    return send_file('static/Logo.svg', mimetype='image/svg+xml')

@app.route('/debug/files')
def debug_files():
    import os
    files = {}
    for root, dirs, filenames in os.walk('templates'):
        for f in filenames:
            filepath = os.path.join(root, f)
            mtime = os.path.getmtime(filepath)
            files[filepath] = mtime
    return jsonify(files)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    
    # Load saved settings
    saved_settings = load_settings()
    game_state.update(saved_settings)
    
    threading.Thread(
        target=lambda: (
            time.sleep(2),
            webbrowser.open('http://localhost:8246/control'),
        ),
        daemon=True,
    ).start()
    app.run(host='0.0.0.0', port=8246, debug=True, threaded=True)