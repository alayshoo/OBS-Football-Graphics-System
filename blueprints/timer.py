from flask import Blueprint, jsonify, request
from flask_socketio import emit
import time


timer_bp = Blueprint('timer', __name__)

# Will be set by app.py
timer_state = {}

def set_timer_timer_state(state):
    """Set the shared timer_state"""
    global timer_state
    timer_state = state





@timer_bp.route('/timer', methods=['GET'])
def get_game_state():
    return jsonify({**timer_state, 'server_time': time.time()})





def register_timer_events_socketio(socketio):
    """Register SocketIO events for timer events."""

    @socketio.on('start-timer')
    def handle_start_timer():

        now = time.time()

        timer_state['timer_running'] = True
        timer_state['timer_anchor'] = now

        emit('update-timer-start', broadcast= True)


    @socketio.on('stop-timer')
    def handle_stop_timer():
        
        now = time.time()

        elapsed = (now - timer_state['timer_anchor']) + timer_state['timer_offset']

        timer_state['timer_running'] = False
        timer_state['timer_anchor'] = now
        timer_state['timer_offset'] = int(elapsed)

        emit('update-timer-stop', broadcast= True)


    @socketio.on('reset-timer')
    def handle_reset_timer():
        now = time.time()
        
        timer_state['timer_running'] = False
        timer_state['timer_anchor'] = now
        timer_state['timer_offset'] = 0
        
        emit('update-timer', broadcast=True)


    @socketio.on('set-timer')
    def handle_set_timer(data):
        now = time.time()
        desired_seconds = int(data.get('set'))
        
        timer_state['timer_running'] = False
        timer_state['timer_anchor'] = now
        timer_state['timer_offset'] = desired_seconds
        
        emit('update-timer', broadcast=True)


    @socketio.on('set-extra-time')
    def handle_set_extra_time(data):

        timer_state['extra_time'] = data.get('extra-time')
        emit('show-extra-time', {'extra-time': data.get('extra-time')}, broadcast= True)



