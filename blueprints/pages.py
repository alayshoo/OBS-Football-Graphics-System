from flask import Blueprint, render_template, render_template_string, send_file, redirect, url_for
import qrcode
import base64
import io

from config import APP_VERSION, PORT
from services.helper import get_local_ip



pages_bp = Blueprint('pages', __name__)




@pages_bp.route('/')
def index():
    return redirect('/control')


@pages_bp.route('/obs')
def scoreboard():
    return render_template('obs.html')


@pages_bp.route('/control')
def control():
    local_ip = get_local_ip()
    port = PORT
    url = f"http://{local_ip}:{port}/control"

    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    img_buffer = io.BytesIO()
    qr_img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    qr_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

    with open('templates/control_interface.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    return render_template_string(
        html_content, 
        app_version=APP_VERSION, 
        local_ip=local_ip, 
        port=port,
        qr_code=qr_base64
    )


@pages_bp.route('/setup')
def setup():
    return render_template('setup.html')


@pages_bp.route('/setup-ads')
def setup_adds():
    return render_template('setup_ads.html')


@pages_bp.route('/setup-obs-commands')
def setup_obs_commands():
    return render_template('setup_obs_commands.html')


@pages_bp.route('/Logo.svg')
def BrigantiaLogo():
    return send_file('static/Logo.svg', mimetype='image/svg+xml')