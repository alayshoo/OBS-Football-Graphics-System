from flask import Blueprint, jsonify, request
from flask_socketio import emit


from services.database import db, Team, Player, Formation


teams_bp = Blueprint('teams', __name__)




@teams_bp.route('/teams', methods=['GET'])
def get_teams_data():
    teams = Team.query.all()
    return jsonify({"teams": [t.to_dict() for t in teams]})


@teams_bp.route('/players', methods= ['GET'])
def get_players_data():
    players = Player.query.all()
    return jsonify({"players": [p.to_dict() for p in players]})


@teams_bp.route('/formations', methods= ['GET'])
def get_formations_data():
    formations = Formation.query.all()
    return jsonify({"formations": [f.to_dict() for f in formations]})




def register_teams_socketio(socketio):
    """Register Teams SocketIO events."""

    @socketio.on('modify-team')
    def handle_team_modification(data):
        try:

            team = Team.query.get(int(data.get('team')))

            if not team:
                emit('team-modified', {'success': False, 'error': 'Team not found'}, room= request.sid)
                return

            if 'name' in data:
                team.name = data.get('name')
            if 'manager' in data:
                team.manager = data.get('manager')
            if 'bg_color' in data:
                team.bg_color = data.get('bg_color')
            if 'text_color' in data:
                team.text_color = data.get('text_color')

            db.session.commit()
            db.session.refresh(team)

            emit('team-modified', {'success': True}, room= request.sid)
            emit('update-teams', broadcast= True)

        except Exception as e:
            db.session.rollback()
            emit('team-modified', {'success': False, 'error': str(e)}, room= request.sid)


    @socketio.on('create-player')
    def handle_player_creation(data):
        try:

            new_player = Player(
                team_id= int(data.get('team'))
            )

            db.session.add(new_player)
            db.session.commit()

            emit('player-created', {'success': True, 'player': new_player.to_dict()})
            emit('update-players', broadcast= True)

        except Exception as e:
            db.session.rollback()
            emit('player-created', {'success': False, 'error': str(e)}, room= request.sid)


    @socketio.on('modify-player')
    def handle_player_modification(data):
        try:

            player = Player.query.get(data.get('id'))

            if not player:
                emit('player-modified', {'success': False, 'error': 'Player not found in database'}, room= request.sid)
                return

            if 'name' in data:
                player.name = data.get('name')
            if 'number' in data:
                player.number = data.get('number')

            db.session.commit()
            db.session.refresh(player)

            emit('player-modified', {'success': True}, room= request.sid)
            emit('update-players', broadcast= True)

        except Exception as e:
            db.session.rollback()
            emit('player-modified', {'success': False, 'error': str(e)}, room= request.sid)


    @socketio.on('delete-player')
    def handle_player_deletion(data):
        try:

            player = Player.query.get(data.get('id'))

            if player:
                db.session.delete(player)
                db.session.commit()
                
                emit('player-deleted', {'success': True}, room= request.sid)
                emit('update-players', broadcast= True)

            else:
                emit('player-deleted', {'success': False, 'error': 'Player not found'}, room= request.sid)

        except Exception as e:
            db.session.rollback()
            emit('player-deleted', {'success': False, 'error': str(e)}, room= request.sid)


    @socketio.on('modify-formation')
    def handle_formation_modification(data):
        try:

            formation = Formation.query.get(data.get('id'))

            if not formation:
                emit('formation-modified', {'success': False, 'error': 'Formation not found in database'}, room= request.sid)
                return

            if 'goalkeeper' in data:
                formation.goalkeeper = data.get('goalkeeper')
            if 'lines' in data:
                formation.lines = data.get('lines')

            db.session.commit()
            db.session.refresh(formation)

            emit('formation-modified', {'success': True}, room= request.sid)
            emit('update-formations', broadcast= True)

        except Exception as e:
            db.session.rollback()
            emit('formation-modified', {'success': False, 'error': str(e)}, room= request.sid)