"""pytest fixture — 真实 ORM 模型 + SQLite Integer PK 补丁 + Redis Mock。"""

import os
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Integer, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

# 先删旧库，避免字段类型残留
if os.path.exists("./test.db"):
    os.remove("./test.db")

# Mock Redis（测试环境不依赖 Redis 容器）
_mock_redis = MagicMock()
_mock_redis.get.return_value = None  # 永远缓存未命中，走真实 DB
_mock_redis.scan_iter.return_value = []
patch("app.core.redis.get_redis", return_value=_mock_redis).start()
patch("app.services.course_service.get_redis", return_value=_mock_redis).start()

from app.core.database import get_db  # noqa: E402
from app.core.security import create_access_token, generate_csrf_token  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.chapter import Chapter  # noqa: E402
from app.models.course import Course  # noqa: E402
from app.models.courseware import Courseware  # noqa: E402
from app.models.enrollment import Enrollment  # noqa: E402

TEST_DB = "sqlite:///./test.db"
test_engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

TEST_MODELS = [User, Category, Course, Chapter, Courseware, Enrollment]

# BigInteger → Integer（SQLite 才能自增）
for model in TEST_MODELS:
    for col in model.__table__.columns:
        if str(col.type).upper().startswith("BIGINT"):
            col.type = Integer()

for model in TEST_MODELS:
    model.__table__.create(bind=test_engine)


@event.listens_for(test_engine, "connect")
def _fk(dbapi_conn, _rec):
    dbapi_conn.execute("PRAGMA foreign_keys=ON")


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def clean_db():
    for model in reversed(TEST_MODELS):
        with test_engine.connect() as conn:
            conn.execute(model.__table__.delete())
            conn.commit()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db() -> Session:
    s = TestSessionLocal()
    try:
        yield s
    finally:
        s.close()


def create_user(db: Session, role=UserRole.admin, **kw) -> User:
    seq = kw.pop("_seq", 0)
    u = User(
        username=kw.pop("username", f"t{seq}"),
        email=kw.pop("email", f"t{seq}@t.com"),
        password_hash="x",
        role=role,
        **kw,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def auth_headers(user: User) -> dict:
    token = create_access_token(user.id)
    csrf = generate_csrf_token()
    return {"Cookie": f"access_token={token}; csrf_token={csrf}", "X-CSRF-Token": csrf}
