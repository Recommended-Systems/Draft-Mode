from flask import Flask, render_template
from flask_migrate import Migrate
from datetime import datetime
import os

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    if config_name == 'production':
        app.config.from_object('config.ProductionConfig')
    elif config_name == 'testing':
        app.config.from_object('config.TestingConfig')
    else:
        app.config.from_object('config.DevelopmentConfig')
    
    # Initialize extensions with app
    from models import db
    db.init_app(app)
    
    migrate = Migrate()
    migrate.init_app(app, db)
    
    # Import models (needed for migrations)
    from models import User, BlogDraft, DraftVersion
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.drafts import drafts_bp
    from routes.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(drafts_bp, url_prefix='/drafts')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    # Context processors
    @app.context_processor
    def inject_globals():
        return {
            'datetime': datetime
        }
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        from models import db
        db.create_all()
    app.run(debug=True)