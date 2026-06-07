"""End-to-end verification of the chat feature against the real app.

Runs against its own isolated temp SQLite database (never caritas.db) and
overrides auth to switch the "current user" per request. The temp DB is
created on setup and removed on teardown — no manual cleanup needed.
Temporary — safe to delete once the feature is confirmed working.
"""

import os
import tempfile
import uuid
from datetime import datetime, timedelta, timezone

import pytest

# Point the app at an isolated temp database BEFORE importing backend modules,
# so the import-time create_all() in backend.main never touches caritas.db.
_db_fd, _db_path = tempfile.mkstemp(suffix=".db", prefix="caritas_test_")
os.close(_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"

from fastapi.testclient import TestClient  # noqa: E402

import backend.main as m  # noqa: E402
from backend.auth import get_current_user  # noqa: E402
from backend.database import Base, SessionLocal, engine, get_db  # noqa: E402
from backend.models.chat import (  # noqa: E402
    ChatMessage,
    ChatReadReceipt,
    ChatThread,
)
from backend.models.user import Role, User  # noqa: E402
from backend.models.village import Village  # noqa: E402


def teardown_module(module):
    """Drop the schema and delete the temp database file."""
    engine.dispose()
    if os.path.exists(_db_path):
        os.remove(_db_path)


@pytest.fixture
def env():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    v = Village(
        id=str(uuid.uuid7()),
        name="Ende",
        slug="ende",
        latitude=0,
        longitude=0,
        population=1,
    )
    db.add(v)
    db.flush()
    admin = User(
        id=str(uuid.uuid7()),
        email="ana@caritas.org",
        full_name="Ana",
        role=Role.admin,
    )
    budi = User(
        id=str(uuid.uuid7()),
        phone_number="+6281001",
        full_name="Budi",
        role=Role.reporter,
        village_id=v.id,
    )
    siti = User(
        id=str(uuid.uuid7()),
        phone_number="+6281002",
        full_name="Siti",
        role=Role.reporter,
        village_id=v.id,
    )
    db.add_all([admin, budi, siti])

    # Pre-seed Budi's thread with 3 messages; admin has read them all.
    t = ChatThread(id=str(uuid.uuid7()), reporter_id=budi.id)
    db.add(t)
    db.flush()
    base = datetime(2026, 5, 1, 8, 0, tzinfo=timezone.utc)
    for i, (s, c) in enumerate([(budi, "hi"), (admin, "hello"), (budi, "thx")]):
        db.add(
            ChatMessage(
                id=str(uuid.uuid7()),
                thread_id=t.id,
                sender_id=s.id,
                content=c,
                created_at=base + timedelta(minutes=i),
            )
        )
    t.updated_at = base + timedelta(minutes=2)
    db.add(
        ChatReadReceipt(
            id=str(uuid.uuid7()),
            thread_id=t.id,
            user_id=admin.id,
            last_read_at=base + timedelta(minutes=10),
        )
    )
    db.commit()

    current = {"id": admin.id}
    m.app.dependency_overrides[get_db] = lambda: SessionLocal()
    m.app.dependency_overrides[get_current_user] = lambda: db.get(
        User, current["id"]
    )
    client = TestClient(m.app)

    yield client, db, current, {"admin": admin, "budi": budi, "siti": siti}, t.id

    m.app.dependency_overrides.clear()
    db.close()
    # Reset schema so each test starts from a clean slate.
    Base.metadata.drop_all(bind=engine)


def _as(current, user):
    current["id"] = user.id


def test_chat_flow(env):
    client, db, current, users, budi_tid = env
    admin, budi, siti = users["admin"], users["budi"], users["siti"]

    # Admin lists threads: 1 thread, unread 0, last_message present.
    _as(current, admin)
    r = client.get("/chat/threads")
    assert r.status_code == 200, r.text
    th = r.json()
    assert len(th) == 1
    assert th[0]["unread_count"] == 0
    assert th[0]["reporter_name"] == "Budi"
    assert th[0]["last_message"]["content"] == "thx"
    assert th[0]["village_id"] is not None  # for dashboard grouping

    # Budi sees his own thread with 3 messages.
    _as(current, budi)
    r = client.get("/chat/threads/mine")
    assert r.status_code == 200, r.text
    mine = r.json()
    assert len(mine["messages"]) == 3
    assert mine["id"] == budi_tid

    # Budi sends a new message.
    r = client.post(f"/chat/threads/{budi_tid}/messages", json={"content": "new"})
    assert r.status_code == 201, r.text
    assert r.json()["sender_name"] == "Budi"

    # Admin now has 1 unread.
    _as(current, admin)
    assert client.get("/chat/threads").json()[0]["unread_count"] == 1

    # Opening the thread returns 4 messages and auto-marks read.
    r = client.get(f"/chat/threads/{budi_tid}")
    assert r.status_code == 200, r.text
    assert len(r.json()["messages"]) == 4
    assert client.get("/chat/threads").json()[0]["unread_count"] == 0

    # Siti has no thread yet -> lazily created, empty.
    _as(current, siti)
    r = client.get("/chat/threads/mine")
    assert r.status_code == 200, r.text
    assert r.json()["messages"] == []
    siti_tid = r.json()["id"]

    # Staff have no personal thread.
    _as(current, admin)
    assert client.get("/chat/threads/mine").status_code == 404

    # Reporter cannot access another reporter's thread.
    _as(current, budi)
    assert client.get(f"/chat/threads/{siti_tid}").status_code == 403
    assert (
        client.post(
            f"/chat/threads/{siti_tid}/messages", json={"content": "x"}
        ).status_code
        == 403
    )

    # Staff can open a chat with any reporter via get-or-create by reporter.
    _as(current, admin)
    r = client.get(f"/chat/threads/by-reporter/{budi.id}")
    assert r.status_code == 200, r.text
    assert r.json()["id"] == budi_tid  # existing thread reused
    # Siti's thread also resolvable; unknown reporter -> 404.
    assert client.get(f"/chat/threads/by-reporter/{siti.id}").status_code == 200
    assert client.get("/chat/threads/by-reporter/nope").status_code == 404
    # Reporters cannot use the staff endpoint.
    _as(current, budi)
    assert client.get(f"/chat/threads/by-reporter/{siti.id}").status_code == 403

    # Explicit mark-as-read.
    _as(current, admin)
    assert client.post(f"/chat/threads/{budi_tid}/read").status_code == 204

    # Unknown thread -> 404.
    assert client.get("/chat/threads/nope").status_code == 404
