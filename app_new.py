#!/usr/bin/env python3
"""
Ransomware Detection System - Professional Implementation
Main Flask application with modular architecture
"""

import os
from flask import Flask, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Import configuration and modules
from config import get_config
from config.logging import setup_logging
from models.database import init_db, get_db_stats
from routes.auth import auth_bp
from routes.predict import predict_bp
from utils.ml_model import validate_model

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)

    # Load configuration
    config = get_config()
    app.config.from_object(config)

    # Initialize logging
    logger = setup_logging()

    # Initialize extensions
    init_db(app)

    # Rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )

    # CSRF protection
    csrf = CSRFProtect(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(predict_bp)

    # Context processors
    @app.context_processor
    def inject_auth_status():
        from flask import session
        return dict(
            logged_in=session.get("logged_in", False),
            username=session.get("username")
        )

    @app.context_processor
    def inject_stats():
        return dict(db_stats=get_db_stats())

    # Health check endpoint
    @app.route("/health")
    def health_check():
        """Health check endpoint for monitoring"""
        model_status = validate_model()
        db_status = True  # Assume DB is working if we reach here

        status = "healthy" if model_status and db_status else "unhealthy"

        return {
            "status": status,
            "model_loaded": model_status,
            "database_connected": db_status,
            "version": "2.0.0"
        }, 200 if status == "healthy" else 503

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return render_template('500.html'), 500

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return render_template('429.html'), 429

    logger.info("✅ Flask application created successfully")
    return app

# Create application instance
app = create_app()

if __name__ == "__main__":
    # Check if running in Electron mode
    electron_mode = os.environ.get("ELECTRON_MODE", "false").lower() == "true"

    if electron_mode:
        # Run on all interfaces for Electron
        app.run(host="0.0.0.0", port=int(os.environ.get("ELECTRON_PORT", 5000)), debug=False)
    else:
        app.run(debug=app.config.get("DEBUG", True))
