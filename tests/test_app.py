from app import create_app
from models import Note, User, db
from werkzeug.security import check_password_hash
from flask_jwt_extended import decode_token

def test_health():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-only-key-not-for-production"
    })

    with app.app_context():
        db.create_all()

    with app.test_client() as client:
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json == {"status": "healthy"}

def test_register():   
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-only-key-not-for-production"
    })

    with app.app_context():
        db.create_all()

        with app.test_client() as client:
            response = client.post("/register", json={
                "username": "alice",
                "password": "local-test-password"
            })

            assert response.status_code == 201
            assert "id" in response.json

            user = User.query.filter_by(
                username="alice"
            ).first()

            assert user is not None
            assert user.id == response.json["id"]

            # Verify that the password is not stored in plaintext
            assert user.password_hash != "local-test-password"

            # Verify that the password hash is valid
            assert check_password_hash( 
                user.password_hash, 
                "local-test-password"
                )

def test_create_note():   
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-only-key-not-for-production"
    })

    with app.app_context():
        db.create_all()

        with app.test_client() as client:
            response = client.post("/register", json={
                "username": "alice",
                "password": "local-test-password"
            })

            assert response.status_code == 201
            assert "id" in response.json

            user = User.query.filter_by(
                username="alice"
            ).first()

            assert user is not None
            assert user.id == response.json["id"]

            # Verify that the password is not stored in plaintext
            assert user.password_hash != "local-test-password"

            # Verify that the password hash is valid
            assert check_password_hash( 
                user.password_hash, 
                "local-test-password"
                )

def test_login():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-only-key-not-for-production"
    })

    with app.app_context():
        db.create_all()

        with app.test_client() as client:
            credentials = {
                "username": "alice",
                "password": "local-test-password"
            }

            registered = client.post(
                "/register", json=credentials
            )

            assert registered.status_code == 201

            response = client.post(
                "/login", json=credentials
            )

            assert response.status_code == 200
            assert "access_token" in response.json

            token = response.json["access_token"]
            decoded = decode_token(token)

            assert decoded["sub"] == str(registered.json["id"])
            assert decoded["type"] == "access"

def test_create_note2():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-only-key-not-for-production"
    })

    with app.app_context():
        db.create_all()

        with app.test_client() as client:
            credentials = {
                "username": "alice",
                "password": "local-test-password"
            }

            registered = client.post(
                "/register", json=credentials
            )

            assert registered.status_code == 201

            login = client.post(
                "/login", json=credentials
            )

            assert login.status_code == 200

            token = login.json["access_token"]

            headers = {
                "Authorization": f"Bearer {token}"
            }

            response = client.post(
                "/notes",
                headers=headers,
                json={"content": "My first test note"}
            )

            assert response.status_code == 201
            assert response.json["content"] == "My first test note"

            note = db.session.get(Note, response.json["id"])

            assert note is not None
            assert note.content == "My first test note"
            assert note.user_id == registered.json["id"]
            assert note.created_at is not None            