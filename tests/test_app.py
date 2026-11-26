from app import create_app
from models import db


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