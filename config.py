import os
from dotenv import load_dotenv

load_dotenv()


APP_VERSION = "1.0.0"


PORT = int(os.getenv('PORT', 5000))


ALLOWED_MEDIA_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'webm'}
MEDIA_UPLOAD_FOLDER = 'static/media_assets'
MAX_MEDIA_SIZE = 16 * 1024 * 1024


DATABASE_URI = 'sqlite:///obs_football.db'


FLASK_CONFIG = {
    'SECRET_KEY': os.getenv(
        'SECRET_KEY', 'dev-key-temporary-make-sure-there-is-dotenv-file'
    ),
    'SQLALCHEMY_DATABASE_URI': DATABASE_URI,
    'SQLALCHEMY_TRACK_MODIFICATIONS': False
}