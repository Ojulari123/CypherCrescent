import os
import pytest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import tables
from tables import Base, get_db
from Routes.user import user_router
from Routes.holding import holding_router
from Routes.market import market_router
from Routes.dashboard import dashboard_router
from Utils.rate_limit import limiter

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
tables.engine = test_engine
tables.Local_Session = TestSession

os.environ.setdefault("NPGUSER", "test")
os.environ.setdefault("NPGPASSWORD", "test")
os.environ.setdefault("NPGDB", "test")
os.environ.setdefault("NPGHOST", "localhost")
os.environ.setdefault("NPGPORT", "5432")
os.environ.setdefault("JWT_SECRET", "test-secret-please-change")
os.environ.setdefault("SMTP_HOST", "smtp.test")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_USER", "test@example.com")
os.environ.setdefault("SMTP_PASSWORD", "x")
os.environ.setdefault("EMAIL_FROM", "test@example.com")
os.environ.setdefault("CLOUDINARY_CLOUD_NAME", "x")
os.environ.setdefault("CLOUDINARY_API_KEY", "x")
os.environ.setdefault("CLOUDINARY_API_SECRET", "x")

limiter.enabled = False  # Disable rate limits during tests

SAMPLE_USER = {
    "email": "alice@example.com",
    "password": "Secret123!",
    "first_name": "Alice",
    "last_name": "Smith",
    "display_name": "alice",
}

def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

def register(client: TestClient, payload: dict | None = None) -> dict:
    body = payload or SAMPLE_USER
    r = client.post("/api/users/register", json=body)
    assert r.status_code == 201, r.text
    return r.json()

@pytest.fixture()
def client():
    Base.metadata.create_all(bind=test_engine)

    app = FastAPI()
    app.state.limiter = limiter

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(user_router, prefix="/api/users")
    app.include_router(holding_router, prefix="/api/holdings")
    app.include_router(market_router, prefix="/api/market")
    app.include_router(dashboard_router, prefix="/api/dashboard")

    with TestClient(app) as c:
        yield c

    Base.metadata.drop_all(bind=test_engine)

# Stub out SMTP and Cloudinary so tests don't touch the network.
@pytest.fixture(autouse=True)
def patch_external_io():
    with patch("Routes.user.send_verification") as mock_send_v, \
         patch("Routes.user.send_password_reset_email") as mock_send_pr, \
         patch("Routes.user.upload_image_to_cloudinary") as mock_upload, \
         patch("Routes.user.delete_image_from_cloudinary") as mock_delete, \
         patch("Utils.user.delete_image_from_cloudinary") as mock_cascade_delete:
        mock_upload.return_value = (
            "https://res.cloudinary.com/test/image/upload/v123/userDP/1/avatar.jpg"
        )
        yield {
            "send_verification": mock_send_v,
            "send_password_reset_email": mock_send_pr,
            "upload": mock_upload,
            "delete": mock_delete,
            "cascade_delete": mock_cascade_delete,
        }
