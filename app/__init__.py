import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect

from .models import db, User
from .config import Config

login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Ensure upload directory exists
    upload_folder = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)

    from .auth import auth_bp
    from .tools import tools_bp
    from .lending import lending_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(lending_bp)

    @app.route('/')
    def root():
        return redirect(url_for('tools.index'))

    # ---------------------------------------------------------------
    # Security headers — applied to every response
    # ---------------------------------------------------------------
    @app.after_request
    def set_security_headers(response):
        # Prevent browsers from MIME-sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Deny framing (clickjacking protection)
        response.headers['X-Frame-Options'] = 'DENY'
        # Basic XSS protection for older browsers
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Force HTTPS when served in production
        response.headers['Strict-Transport-Security'] = (
            'max-age=31536000; includeSubDomains'
        )
        # Referrer policy — don't leak full URLs to third parties
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Content Security Policy
        # - Bootstrap and app JS/CSS served from same origin
        # - Images may come from same origin or data URIs (for uploaded images)
        # - No inline scripts (except what Bootstrap requires)
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        # Permissions policy — disable features we don't use
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), payment=()'
        )
        return response

    return app
