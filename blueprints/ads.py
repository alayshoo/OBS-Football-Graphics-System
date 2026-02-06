import uuid
import os
from flask import Blueprint, jsonify, send_from_directory, request
from flask_socketio import emit


from config import ALLOWED_MEDIA_EXTENSIONS, MEDIA_UPLOAD_FOLDER
from services.helper import allowed_file
from services.database import db, Advertisement


ads_bp = Blueprint('ads', __name__)




@ads_bp.route('/ads', methods= ['GET'])
def get_ads():
    ads = Advertisement.query.all()
    return jsonify({'ads': [a.to_dict() for a in ads]})


@ads_bp.route('/static/media_assets/<path:filename>')
def serve_advertisement(filename):
    """Serve advertisement images from the static/media_assets folder"""
    return send_from_directory('static/media_assets', filename)


@ads_bp.route('/ads/upload-image', methods= ['POST'])
def upload_ad_image():
    try:
        if 'id' not in request.form:
            return jsonify({'success': False, 'error': 'Missing ad ID'}), 400
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400


        ad_id = int(request.form['id'])
        file = request.files['image']

        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_MEDIA_EXTENSIONS)}'
            }), 400

        ad = Advertisement.query.get(ad_id)
        if not ad:
            return jsonify({'success': False, 'error': 'Ad not found'}), 404

        old_image_path = ad.image_path

        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"ad_{ad_id}_{uuid.uuid4().hex[:8]}.{file_extension}"

        filepath = os.path.join(MEDIA_UPLOAD_FOLDER, unique_filename)
        file.save(filepath)

        if old_image_path and os.path.exists(old_image_path):
            try: 
                os.remove(old_image_path)
            except Exception as e:
                print(f"Error deleting old image: {str(e)}")

        relative_path = filepath.replace('\\', '/')

        ad.image_path = relative_path

        db.session.commit()

        return jsonify({'success': True, 'image_path': relative_path})

    except Exception as e:
        db.session.rollback()
        print(f"Error uploading image: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500






def register_ads_socketio(socketio):

    @socketio.on('create-ad')
    def handle_ad_creation(data):
        try:
            new_ad = Advertisement()
            db.session.add(new_ad)
            db.session.commit()

            emit('ad-created', {
                'success': True, 
                'ad': new_ad.to_dict()
            }, room=request.sid)
            emit('update-ads', broadcast=True)

        except Exception as e:
            db.session.rollback()
            print(f"Error creating ad: {e}")  # Add logging
            emit('ad-created', {
                'success': False, 
                'error': str(e)
            }, room=request.sid)


    @socketio.on('modify-ad')
    def handle_ad_modification(data):
        try:

            ad = Advertisement.query.get(data.get('id'))

            if not ad:
                emit('ad-modified', {'success': False, 'error': 'Ad not found'}, room= request.sid)
                return

            if 'name' in data:
                ad.name = data.get('name')
            if 'sponsor' in data:
                ad.sponsor = data.get('sponsor')
            if 'type' in data:
                ad.type = data.get('type')
            if 'duration' in data:
                ad.duration = data.get('duration')
            if 'image_path' in data:
                ad.image_path = data.get('image_path')


            db.session.commit()
            db.session.refresh(ad)

            emit('ad-modified', {'success': True}, room= request.sid)
            emit('update-ads', broadcast= True)

        except Exception as e:
            db.session.rollback()
            emit('ad-modified', {'success': False, 'error': str(e)}, room= request.sid)


    @socketio.on('delete-ad')
    def handle_ad_deletion(data):
        try:
            ad = Advertisement.query.get(data.get('id'))

            if ad:
                # Delete associated image file from disk
                if ad.image_path and os.path.exists(ad.image_path):
                    try:
                        os.remove(ad.image_path)
                    except Exception as e:
                        print(f"Error deleting image file: {e}")

                db.session.delete(ad)
                db.session.commit()

                emit('ad-deleted', {'success': True}, room=request.sid)
                emit('update-ads', broadcast=True)
            else:
                emit('ad-deleted', {
                    'success': False,
                    'error': 'Advertisement not found'
                }, room=request.sid)

        except Exception as e:
            db.session.rollback()
            emit('ad-deleted', {
                'success': False,
                'error': str(e)
            }, room=request.sid)


    @socketio.on('trigger-ad')
    def trigger_ad(data):
        try:
            emit('display-ad', {'id': data.get('id')}, broadcast= True)

        except Exception as e:
            print(f"Error triggering event: {e}")
            emit('ad-display-error', {'error': str(e)}, room=request.sid)