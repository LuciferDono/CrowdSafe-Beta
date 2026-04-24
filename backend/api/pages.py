from flask import Blueprint, render_template, current_app, redirect

pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/')
def dashboard():
    return render_template('dashboard.html')


@pages_bp.route('/login')
def login():
    # Demo mode: skip login, go straight to dashboard.
    if current_app.config.get('AUTH_DISABLED'):
        return redirect('/')
    return render_template('login.html')


@pages_bp.route('/camera/<camera_id>')
def camera_view(camera_id):
    return render_template('camera_view.html', camera_id=camera_id)


@pages_bp.route('/cameras')
def cameras():
    return render_template('cameras.html')


@pages_bp.route('/analytics')
def analytics():
    return render_template('analytics.html')


@pages_bp.route('/alerts')
def alerts_page():
    return render_template('alerts.html')


@pages_bp.route('/settings')
def settings():
    return render_template('settings.html')


@pages_bp.route('/users')
def user_management():
    return render_template('user_management.html')
