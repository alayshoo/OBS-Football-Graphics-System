from flask import Blueprint, jsonify, request
from flask_socketio import emit


from services.database import db, OBSCommand


obs_commands_bp = Blueprint('obs_commands', __name__)




@obs_commands_bp.route('/obs-commands', methods= ['GET'])
def get_obs_commands():
    obs_commands = OBSCommand.query.all()
    return jsonify({'obs_commands': [o.to_dict() for o in obs_commands]})



def register_obs_commands_socketio(socketio):

    @socketio.on('create-obs-command')
    def handle_obs_command_creation(data):
        try:

            new_command = OBSCommand()

            db.session.add(new_command)
            db.session.commit()

            emit('obs-command-created', {'success': True, 'obs-command': new_command.to_dict()})
            emit('update-obs-commands', broadcast= True)

        except Exception as e:
            db.session.rollback()
            emit('obs-command-created', {'success': False, 'error': str(e)}, room= request.sid)


    @socketio.on('modify-obs-command')
    def handle_obs_command_modification(data):
        try:

            command = OBSCommand.query.get(data.get('id'))

            if not command:
                emit('obs-command-modified', {'success': False, 'error': 'OBS Command not found'}, room= request.sid)
                return


            if 'name' in data:
                command.name = data.get('name')
            if 'color' in data:
                command.color = data.get('color')
            if 'shortcut' in data:
                command.shortcut = data.get('shortcut')


            db.session.commit()
            db.session.refresh(command)

            emit('obs-command-modified', {'success': True}, room= request.sid)
            emit('update-obs-commands', broadcast= True)

        except Exception as e:
            db.session.rollback()
            emit('obs-command-modified', {'success': False, 'error': str(e)}, room= request.sid)


    @socketio.on('delete-obs-command')
    def handle_obs_command_deletion(data):
        try:

            command = OBSCommand.query.get(data.get('id'))

            if command:
                db.session.delete(command)
                db.session.commit()
                
                emit('obs-command-deleted', {'success': True}, room= request.sid)
                emit('update-obs-commands', broadcast= True)

            else:
                emit('obs-command-deleted', {'success': False, 'error': 'OBS Command not found'}, room= request.sid)

        except Exception as e:
            db.session.rollback()
            emit('obs-command-deleted', {'success': False, 'error': str(e)}, room= request.sid)

    @socketio.on('trigger-obs-command')
    def trigger_obs_command(data):
        try:
            command = OBSCommand.query.get(data.get('id'))
            if not command:
                emit('obs-command-execution',
                    {'success': False,
                    'error': 'OBS Command not found'},
                    room=request.sid)
                return

            if not command.shortcut:
                emit('obs-command-execution',
                    {'success': False,
                    'error': 'No shortcut configured'},
                    room=request.sid)
                return

            # Broadcast command execution to all connected shortcut clients
            emit('execute-obs-command',
                {'id': command.id,
                'name': command.name,
                'shortcut': command.shortcut},
                broadcast=True)

            emit('obs-command-execution',
                {'success': True},
                room=request.sid)

        except Exception as e:
            emit('obs-command-execution',
                {'success': False, 'error': str(e)},
                room=request.sid)