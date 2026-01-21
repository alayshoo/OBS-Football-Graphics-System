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
from collections import deque

app_version = "0.1.0"

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
    'timer_anchor': None,  # Unix timestamp when timer started/resumed
    'timer_offset': 0,     # Seconds to add to elapsed time
    'timer_running': False,
    'extra_time': 0,
    'last_timer_update': time.time()  # For version tracking
}

# Event notifications (stores last 50 events)
event_queue = deque(maxlen=50)
event_counter = 0

app = Flask(__name__, template_folder='templates')
CORS(app)

def get_local_ip():
    try:
        # This creates a dummy connection to determine the local interface IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@app.route('/scoreboard')
def scoreboard():
    return render_template('scoreboard.html')

@app.route('/control')
def control():
    local_ip = get_local_ip()
    port = 5000
    url = f"http://{local_ip}:{port}/control"

    # Generate QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Convert QR to base64
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
        qr_code=qr_base64 # Pass the QR code to the template
    )

@app.route('/setup')
def setup():
    return

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
        'server_time': time.time()  # For clock sync
    })

@app.route('/events', methods=['GET'])
def get_events():
    """Get recent events (last 10)"""
    return jsonify(list(event_queue)[-10:])

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
    for field in fields:
        if field in data:
            game_state[field] = data[field]

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
                # Calculate elapsed time and store as offset
                elapsed = (now - game_state['timer_anchor']) + game_state[
                  'timer_offset'
                ]
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

    event_counter += 1
    event = {
        'id': event_counter,
        'type': event_type,
        'team': team,
        'timestamp': time.time(),
    }

    if event_type == 'goal':
        event['player'] = data.get('player', '?')
    elif event_type == 'card':
        event['player'] = data.get('player', '?')
        event['card_type'] = data.get('card_type', 'yellow')
    elif event_type == 'substitution':
        event['player_out'] = data.get('player_out', '?')
        event['player_in'] = data.get('player_in', '?')

    event_queue.append(event)
    return jsonify({'success': True, 'event_id': event_counter})

@app.route('/BrigantiaLogo.svg')
def BrigantiaLogo():
    return send_file('BrigantiaLogo.svg', mimetype='image/svg+xml')

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    threading.Thread(
        target=lambda: (
            time.sleep(2),
            webbrowser.open('http://localhost:5000/control'),
        ),
        daemon=True,
    ).start()
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)