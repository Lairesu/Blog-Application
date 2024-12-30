from flask import Flask # type: ignore
from flask_sqlalchemy import SQLAlchemy # type: ignore

# Initialize the database
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialize database with app
    db.init_app(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Register blueprints
    from .routes import main
    app.register_blueprint(main)

    return app