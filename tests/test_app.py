from app import create_app
from models import User, db
from werkzeug.security import check_password_hash

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
