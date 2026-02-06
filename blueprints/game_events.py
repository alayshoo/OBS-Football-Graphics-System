from flask import Blueprint, jsonify, request
from flask_socketio import emit

from services.database import db, Advertisement


game_events_bp = Blueprint('game_state', __name__)

# Will be set by app.py
score_state = {}

def set_game_events_score_state(states):
    """Set the shared score_state"""
    global score_state
    score_state = states


def _get_ad_type_for_event(data):
    """Map a game event to the corresponding advertisement type."""
    event_type = data.get('type')
    if event_type == 'card':
        card_type = data.get('card_type', '').lower()
        if card_type == 'red':
            return 'Red Card'
        elif card_type == 'yellow':
            return 'Yellow Card'
    mapping = {
        'goal': 'Goal',
        'substitution': 'Substitution',
    }
    return mapping.get(event_type)





@game_events_bp.route('/game_state', methods=['GET'])
def get_game_state():
    return jsonify(score_state)





def register_game_events_socketio(socketio):
    """Register SocketIO events for game events."""
    
    @socketio.on('trigger-goal')
    def handle_goal_trigger(data):
        
        team = data.get('team')

        if team == 'team1':
            score_state['team1_score'] += 1
        elif team == 'team2':
            score_state['team2_score'] += 1

        emit('add-to-score', score_state, broadcast= True)


    @socketio.on('cancel-goal')
    def handle_goal_trigger(data):
        
        team = data.get('team')

        if team == 'team1':
            score_state['team1_score'] -= 1
        elif team == 'team2':
            score_state['team2_score'] -= 1

        emit('decrease-to-score', score_state, broadcast= True)
        

    @socketio.on('trigger-event')
    def handle_event_trigger(data):
        try:
            # Broadcast the event to overlays as before
            emit('display-event', data, broadcast=True)

            # Check if there's an ad that should auto-trigger
            #ad_type = _get_ad_type_for_event(data)
            #if ad_type:
            #    ad = Advertisement.query.filter(
            #        db.func.lower(Advertisement.type) == ad_type.lower()
            #    ).first()
            #    if ad:
            #        emit('display-ad', {'id': ad.id}, broadcast=True)

        except Exception as e:
            print(f"Error triggering event: {e}")
            emit('event-error', {'error': str(e)}, room=request.sid)