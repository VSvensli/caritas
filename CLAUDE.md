# Caritas HARVEST

Agricultural data collection platform for Caritas field workers in East Nusa Tenggara, Indonesia. Field reporters submit harvest and input data via a mobile-friendly web app; staff view dashboards and manage villages through a web frontend.

## Architecture

- **Backend**: FastAPI (Python 3.14) with SQLAlchemy ORM, SQLite database, JWT auth
- **Frontend**: Web dashboard for staff (planned)
- **Mobile**: Mobile-friendly web app for field reporters (planned, replaces earlier native Android idea)
- **Package manager**: uv

## Project structure

```
backend/
  main.py          # FastAPI app, router registration
  database.py      # SQLAlchemy engine, session, Base
  auth.py          # JWT tokens, password/PIN hashing, role-based dependency guards
  models/          # SQLAlchemy ORM models (one file per entity)
  schemas/         # Pydantic request/response schemas (one file per entity)
  routers/         # API route handlers (one file per domain)
frontend/          # Web dashboard for staff (planned)
mobile/            # Mobile-friendly web app for field reporters (planned)
docs/              # Mock pages and design assets
```

## Dev setup

```sh
cd backend
uv sync
```

## Running the server

```sh
cd backend
uv run uvicorn backend.main:app --reload
```

The API is served at `http://localhost:8000`. Docs at `/docs`.

## Conventions

- **Models**: SQLAlchemy 2.0 `Mapped[]` style with `mapped_column()`. UUIDs as `String(36)` primary keys with `uuid.uuid7()` defaults. Timestamps use `DateTime(timezone=True)` with `server_default=func.now()`. All times are stored and returned in UTC.
- **Schemas**: Pydantic v2 `BaseModel`. Read schemas use `model_config = {"from_attributes": True}`. Separate `Create`, `Read`, and summary schemas per entity.
- **Routers**: One `APIRouter` per domain, mounted in `main.py`. Use `tags=[]` for OpenAPI grouping.
- **Auth**: Role-based access via typed dependency aliases (`AdminOnly`, `StaffWrite`, `StaffRead`, `AnyAuthenticated`). Inject these as route parameters — don't call `get_current_user` directly.
- **Roles**: `admin > editor > viewer > reporter`. Reporters are field workers; viewer+ are staff.
- **IDs**: All entity IDs are UUID7 strings. Mobile-generated records include a `client_id` for offline deduplication.
