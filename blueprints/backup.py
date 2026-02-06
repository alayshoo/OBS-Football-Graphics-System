from flask import Blueprint, jsonify, request, send_file
from services.database import db, Team, Player, Formation, Advertisement, OBSCommand
from datetime import datetime
import json
import io
import zipfile
import os
from pathlib import Path

backup_bp = Blueprint('backup', __name__)

def serialize_database():
    """Export all persistent data to JSON-serializable format"""
    return {
        'version': '0.8.4',
        'exported_at': datetime.now().isoformat(),
        'teams': [team.to_dict() for team in Team.query.all()],
        'players': [player.to_dict() for player in Player.query.all()],
        'formations': [
            {
                **formation.to_dict(),
                'lines': formation.lines or []
            } for formation in Formation.query.all()
        ],
        'advertisements': [ad.to_dict() for ad in Advertisement.query.all()],
        'obs_commands': [cmd.to_dict() for cmd in OBSCommand.query.all()]
    }

@backup_bp.route('/export', methods=['GET'])
def export_database():
    """Export database as ZIP file (JSON + images)"""
    try:
        data = serialize_database()
        filename = f"football_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        # Create in-memory ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add JSON export
            json_content = json.dumps(data, indent=2)
            zip_file.writestr('backup.json', json_content)
            
            # Add all advertisement images
            for ad in Advertisement.query.all():
                if ad.image_path:
                    image_file_path = Path(ad.image_path)
                    if image_file_path.exists():
                        # Store in ZIP as: images/ad_filename.ext
                        arcname = f"images/{image_file_path.name}"
                        zip_file.write(image_file_path, arcname=arcname)
        
        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/import', methods=['POST'])
def import_database():
    """Import database from ZIP file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        if not file.filename.endswith('.zip'):
            return jsonify({'error': 'File must be ZIP format'}), 400
        
        # Read ZIP file
        zip_buffer = io.BytesIO(file.read())
        
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            # Validate ZIP contents
            if 'backup.json' not in zip_file.namelist():
                return jsonify({'error': 'Invalid backup: missing backup.json'}), 400
            
            # Extract and parse JSON
            json_content = zip_file.read('backup.json').decode('utf-8')
            data = json.loads(json_content)
            
            # Validate structure
            required_keys = {'version', 'teams', 'players', 'formations', 'advertisements', 'obs_commands'}
            if not required_keys.issubset(data.keys()):
                return jsonify({'error': 'Invalid backup file structure'}), 400
            
            # Import data with images
            _import_data(data, zip_file)
        
        return jsonify({
            'success': True, 
            'message': 'Database and images imported successfully'
        }), 200
    
    except zipfile.BadZipFile:
        return jsonify({'error': 'Invalid ZIP file'}), 400
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON in backup'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def _import_data(data, zip_file):
    """Import database and restore images from ZIP"""
    
    # Create media directory if it doesn't exist
    media_dir = Path('static/media_assets')
    media_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear existing data
    Team.query.delete()
    Player.query.delete()
    Formation.query.delete()
    Advertisement.query.delete()
    OBSCommand.query.delete()
    
    # Delete old images
    for img_file in media_dir.glob('ad_*'):
        try:
            img_file.unlink()
        except Exception:
            pass
    
    # Extract images from ZIP
    image_mapping = {}  # Map old filename to new filename
    
    for image_file in zip_file.namelist():
        if image_file.startswith('images/') and image_file != 'images/':
            image_filename = Path(image_file).name
            image_data = zip_file.read(image_file)
            
            # Save image to static/media_assets
            new_path = media_dir / image_filename
            new_path.write_bytes(image_data)
            
            # Track mapping
            image_mapping[image_filename] = f"static/media_assets/{image_filename}"
    
    db.session.flush()
    
    # Import teams
    for team_data in data.get('teams', []):
        team = Team(**team_data)
        db.session.add(team)
    
    db.session.flush()
    
    # Import players
    for player_data in data.get('players', []):
        player = Player(**player_data)
        db.session.add(player)
    
    db.session.flush()
    
    # Import formations
    for formation_data in data.get('formations', []):
        formation = Formation(**formation_data)
        db.session.add(formation)
    
    # Import advertisements with image path restoration
    for ad_data in data.get('advertisements', []):
        # Update image path if it exists in the backup
        if ad_data.get('image_path'):
            old_filename = Path(ad_data['image_path']).name
            if old_filename in image_mapping:
                ad_data['image_path'] = image_mapping[old_filename]
        
        ad = Advertisement(**ad_data)
        db.session.add(ad)
    
    # Import OBS commands
    for cmd_data in data.get('obs_commands', []):
        cmd = OBSCommand(**cmd_data)
        db.session.add(cmd)
    
    db.session.commit()