
import os
from pathlib import Path
from sqlalchemy import inspect, text

from flask import Flask, send_from_directory

from config import Config
from app.extensions import db, login_manager
from app.models import *


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Create folders needed by the database and uploaded photos
    project_folder = Path(app.root_path).parent

    instance_folder = project_folder / "instance"
    upload_folder = instance_folder / "uploads"

    os.makedirs(instance_folder, exist_ok=True)
    os.makedirs(upload_folder, exist_ok=True)

    app.config["UPLOAD_FOLDER"] = str(upload_folder)

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "main.login"
    login_manager.login_message_category = "error"

    # Register website routes
    from app.routes import main
    app.register_blueprint(main)

    # Serve uploaded product photos
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            filename
        )

    # Create database tables
    with app.app_context():
        db.create_all()

        # Add profile fields to existing databases without deleting user accounts or listings.
        user_columns = {column["name"] for column in inspect(db.engine).get_columns("user")}
        profile_columns = {
            "bio": "TEXT",
            "facebook_url": "VARCHAR(500)",
            "profile_photo": "VARCHAR(255)",
        }
        for column_name, column_type in profile_columns.items():
            if column_name not in user_columns:
                db.session.execute(text(f"ALTER TABLE user ADD COLUMN {column_name} {column_type}"))
        db.session.commit()

        # Add the default selectable categories when the database is first created.
        from app.routes import seed_categories
        seed_categories()

    return app