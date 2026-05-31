"""Populate the database with mock data from seed_data.json."""

import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from backend.auth import hash_password, hash_pin
from backend.database import Base, SessionLocal, engine
from backend.models.calendar import SubTask, Task
from backend.models.report import Report
from backend.models.user import Gender, Role, User
from backend.models.village import Village
from backend.routers.villages import _slugify

SEED_FILE = Path(__file__).parent / "seed_data.json"


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        data = json.loads(SEED_FILE.read_text())

        # Admin user
        adm = data["admin"]
        admin_user = User(
            id=str(uuid.uuid7()),
            email=adm["email"],
            full_name=adm["full_name"],
            hashed_password=hash_password(adm["password"]),
            role=Role.admin,
        )
        db.add(admin_user)
        db.flush()

        # Villages
        village_map: dict[str, Village] = {}
        for v in data["villages"]:
            village = Village(
                id=str(uuid.uuid7()),
                name=v["name"],
                slug=_slugify(v["name"]),
                latitude=v["latitude"],
                longitude=v["longitude"],
                population=v["population"],
            )
            db.add(village)
            village_map[v["name"]] = village
        db.flush()

        # Reporters
        rep_data = data["reporters"]
        village = village_map[rep_data["village"]]
        reporter_ids: list[str] = []
        for u in rep_data["users"]:
            user = User(
                id=str(uuid.uuid7()),
                phone_number=u["phone_number"],
                full_name=u["full_name"],
                hashed_pin=hash_pin(u["pin"]),
                role=Role.reporter,
                village_id=village.id,
                gender=Gender(u["gender"]) if u.get("gender") else None,
            )
            db.add(user)
            reporter_ids.append(user.id)
        db.flush()

        # Reports
        rpt_data = data["reports"]
        village = village_map[rpt_data["village"]]
        for i, entry in enumerate(rpt_data["entries"]):
            report = Report(
                id=str(uuid.uuid7()),
                client_id=str(uuid.uuid7()),
                village_id=village.id,
                reporter_id=reporter_ids[i % len(reporter_ids)],
                reported_at=datetime.fromisoformat(entry["reported_at"]),
                yield_kg=entry.get("yield_kg"),
                self_consumption_kg=entry.get("self_consumption_kg"),
                sold_kg=entry.get("sold_kg"),
                revenue_idr=entry.get("revenue_idr"),
                fertilizer_used_kg=entry.get("fertilizer_used_kg"),
                fertilizer_produced_kg=entry.get("fertilizer_produced_kg"),
                pesticide_used_l=entry.get("pesticide_used_l"),
                pesticide_produced_l=entry.get("pesticide_produced_l"),
            )
            db.add(report)
        db.flush()

        # Tasks (calendar)
        task_data = data["tasks"]
        village = village_map[task_data["village"]]
        for t in task_data["entries"]:
            task = Task(
                id=str(uuid.uuid7()),
                village_id=village.id,
                title=t["title"],
                description=t.get("description"),
                task_type=t["task_type"],
                due_date=date.fromisoformat(t["due_date"]) if t.get("due_date") else None,
                season=t["season"],
                year=t["year"],
            )
            db.add(task)
            db.flush()

            for st in t.get("subtasks", []):
                subtask = SubTask(
                    id=str(uuid.uuid7()),
                    task_id=task.id,
                    title=st["title"],
                    due_date=date.fromisoformat(st["due_date"]) if st.get("due_date") else None,
                    is_done=st.get("is_done", False),
                )
                db.add(subtask)

        db.commit()
        print(f"Seeded: {len(village_map)} villages, {len(reporter_ids)} reporters, "
              f"{len(rpt_data['entries'])} reports, {len(task_data['entries'])} tasks")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
