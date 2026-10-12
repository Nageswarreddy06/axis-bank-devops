import os
from datetime import timedelta

from flask import Flask, jsonify

from .extensions import db, jwt


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///axis_bank.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "local-demo-secret-change-me"),
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=30),
        AUTO_CREATE_DB=True,
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    jwt.init_app(app)

    from .routes import api
    app.register_blueprint(api)

    @app.get("/")
    def index():
        return jsonify({
            "application": "axis-bank-demo",
            "message": "Educational banking API. Not an official bank application.",
            "health": "/health",
        })

    @app.get("/health")
    def health():
        return jsonify({"status": "healthy", "application": "axis-bank-demo"}), 200

    if app.config.get("AUTO_CREATE_DB", True):
        with app.app_context():
            db.create_all()

    return app
