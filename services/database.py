from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key= True)

    name = db.Column(db.String(255))
    manager = db.Column(db.String(255))
    bg_color = db.Column(db.String(255))
    text_color = db.Column(db.String(255))

    players = db.relationship('Player', backref='team')
    formation = db.relationship('Formation', uselist= False, backref='team')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'manager': self.manager,
            'bg_color': self.bg_color,
            'text_color': self.text_color
        }


class Player(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key= True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))

    number = db.Column(db.Integer)
    name = db.Column(db.String(255))

    def to_dict(self):
        return {
            'id': self.id,
            'team_id': self.team_id,
            'number': self.number,
            'name': self.name
        }


class Formation(db.Model):
    __tablename__ = 'formations'

    id = db.Column(db.Integer, primary_key= True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))

    goalkeeper = db.Column(db.Integer, db.ForeignKey("players.id"))
    lines = db.Column(db.JSON)

    def to_dict(self):
        return {
            'id': self.id,
            'team_id': self.team_id,
            'goalkeeper': self.goalkeeper,
            'lines': self.lines
        }


class Advertisement(db.Model):
    __tablename__ = 'advertisements'

    id = db.Column(db.Integer, primary_key= True)
    name = db.Column(db.String(255))
    sponsor = db.Column(db.String(255))
    type = db.Column(db.String(50))
    duration = db.Column(db.Integer)
    image_path = db.Column(db.String(255))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sponsor': self.sponsor,
            'type': self.type,
            'duration': self.duration,
            'image_path': self.image_path
        }


class OBSCommand(db.Model):
    __tablename__ = 'obs_commands'

    id = db.Column(db.Integer, primary_key= True)
    name = db.Column(db.String(255))
    color = db.Column(db.String(7), default= '#000000')
    shortcut = db.Column(db.String(255))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'shortcut': self.shortcut
        }
