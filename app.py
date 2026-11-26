
import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from models import db, User, Note

load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__)

    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL", "sqlite:///notes.db"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY"),
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=30)
    )

    if test_config:
        app.config.update(test_config)

    if not app.config["JWT_SECRET_KEY"]:
        raise RuntimeError("JWT_SECRET_KEY is required")

    db.init_app(app)
    JWTManager(app)

    @app.get("/health")
    def health():
        return jsonify(status="healthy")

    @app.post("/register")
    def register():
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify(error="Invalid JSON"), 400

        username = data.get("username")
        password = data.get("password")

        if not isinstance(username, str):
            return jsonify(error="Invalid username"), 400

        if not isinstance(password, str):
            return jsonify(error="Invalid password"), 400

        username = username.strip()

        if not 3 <= len(username) <= 80:
            return jsonify(error="Invalid username length"), 400

        if not 12 <= len(password) <= 128:
            return jsonify(error="Invalid password length"), 400

        if User.query.filter_by(username=username).first():
            return jsonify(error="Username unavailable"), 409

        user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        return jsonify(id=user.id), 201

    @app.post("/login")
    def login():
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify(error="Invalid JSON"), 400

        username = data.get("username")
        password = data.get("password")

        if not isinstance(username, str) or \
                not isinstance(password, str):
            return jsonify(error="Invalid credentials"), 401

        user = User.query.filter_by(
            username=username
        ).first()

        if not user or not check_password_hash(
            user.password_hash, password
        ):
            return jsonify(error="Invalid credentials"), 401

        token = create_access_token(identity=str(user.id))

        return jsonify(access_token=token)

    @app.get("/notes")
    @jwt_required()
    def get_notes():
        user_id = int(get_jwt_identity())

        notes = Note.query.filter_by(
            user_id=user_id
        ).all()

        return jsonify([note.to_dict() for note in notes])

    @app.post("/notes")
    @jwt_required()
    def create_note():
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify(error="Invalid JSON"), 400

        content = data.get("content")

        if not isinstance(content, str) or \
                not 1 <= len(content.strip()) <= 5000:
            return jsonify(error="Invalid content"), 400

        note = Note(
            user_id=int(get_jwt_identity()),
            content=content.strip()
        )

        db.session.add(note)
        db.session.commit()

        return jsonify(note.to_dict()), 201

    @app.put("/notes/<int:note_id>")
    @jwt_required()
    def update_note(note_id):
        note = Note.query.filter_by(
            id=note_id,
            user_id=int(get_jwt_identity())
        ).first_or_404()

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify(error="Invalid JSON"), 400

        content = data.get("content")

        if not isinstance(content, str) or \
                not 1 <= len(content.strip()) <= 5000:
            return jsonify(error="Invalid content"), 400

        note.content = content.strip()
        db.session.commit()

        return jsonify(note.to_dict())

    @app.delete("/notes/<int:note_id>")
    @jwt_required()
    def delete_note(note_id):
        note = Note.query.filter_by(
            id=note_id,
            user_id=int(get_jwt_identity())
        ).first_or_404()

        db.session.delete(note)
        db.session.commit()

        return "", 204

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        print("Database initialized")

    return app
