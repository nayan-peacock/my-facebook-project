import os
from flask import Flask
from datetime import timedelta
from .config import Config
from .extensions import db, jwt, socketio, limiter, cors
from .models import * # Import models to be registered

def create_app(config_class=Config):
    """
    Application factory function
    """
    
    # We specify the frontend folders as static/template paths
    app = Flask(__name__,
                template_folder='../frontend/templates',
                static_folder='../frontend/static')
    
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)
    limiter.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}}) # Apply CORS only to API routes

    # Create upload folders
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'posts'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'stories'), exist_ok=True)

    # Register Blueprints (routes)
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.profile import profile_bp
    from .routes.posts import posts_bp
    from .routes.friends import friends_bp
    from .routes.messaging import messaging_bp
    from .routes.notifications import notifications_bp
    from .routes.stories import stories_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(profile_bp, url_prefix='/api')
    app.register_blueprint(posts_bp, url_prefix='/api')
    app.register_blueprint(friends_bp, url_prefix='/api')
    app.register_blueprint(messaging_bp, url_prefix='/api')
    app.register_blueprint(notifications_bp, url_prefix='/api')
    app.register_blueprint(stories_bp, url_prefix='/api')

    # Import socket handlers to register them
    from .sockets import handlers

    return app