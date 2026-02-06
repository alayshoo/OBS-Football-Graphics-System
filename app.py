from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from pathlib import Path


from config import FLASK_CONFIG, MEDIA_UPLOAD_FOLDER, PORT


from services.database import db, Team, Formation


from blueprints.pages import pages_bp
from blueprints.timer import timer_bp, set_timer_timer_state, register_timer_events_socketio
from blueprints.game_events import game_events_bp, set_game_events_score_state, register_game_events_socketio
from blueprints.teams import teams_bp, register_teams_socketio
from blueprints.ads import ads_bp, register_ads_socketio
from blueprints.obs_commands import obs_commands_bp, register_obs_commands_socketio
from blueprints.backup import backup_bp


Path(MEDIA_UPLOAD_FOLDER).mkdir(parents= True, exist_ok= True)


app = Flask(__name__)
app.config.update(FLASK_CONFIG)

db.init_app(app)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", engineio_logger= True)

with app.app_context():

    db.create_all()

    # Create 2 Teams if they don't exist already
    for team_id in (1, 2):
        team = Team.query.get(team_id)
        if not team:
            new_team = Team(id = team_id)
            db.session.add(new_team)
            db.session.commit()

    # Create Formation for each team if not yet created
    for team_id in (1, 2):
        formation = Formation.query.filter_by(team_id=team_id).first()
        if not formation:
            new_formation = Formation(team_id=team_id, goalkeeper=None, lines=[])
            db.session.add(new_formation)
            db.session.commit()





timer_state = {
    'timer_anchor': None,
    'timer_offset': 0, 
    'timer_running': False,
    'extra_time': 0
}

score_state = {
    'team1_score': 0,
    'team2_score': 0
}




set_timer_timer_state(timer_state)
set_game_events_score_state(score_state)


app.register_blueprint(pages_bp)
app.register_blueprint(timer_bp)
app.register_blueprint(game_events_bp)
app.register_blueprint(teams_bp)
app.register_blueprint(ads_bp)
app.register_blueprint(obs_commands_bp)
app.register_blueprint(backup_bp)


register_timer_events_socketio(socketio)
register_game_events_socketio(socketio)
register_teams_socketio(socketio)
register_ads_socketio(socketio)
register_obs_commands_socketio(socketio)




if __name__ == '__main__':

    try:
        socketio.run(app, debug=True, use_reloader=False, host='0.0.0.0', port=PORT)
    except KeyboardInterrupt:
        print("\nServer stopped by user.")