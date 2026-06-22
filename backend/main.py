from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.database import Base, engine
from backend.routers import auth, calendar, chat, reports, sync, users, villages

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Caritas HARVEST", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(villages.router)
app.include_router(calendar.router)
app.include_router(reports.router)
app.include_router(sync.router)
app.include_router(chat.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── Static frontends ──────────────────────────────────────────────────
# Both web apps and their shared assets are served from this same origin,
# so the pages' `http://localhost:8000` API calls need no CORS handling.
# Each directory is mounted at a path matching its name so the relative
# links between them (../assets, ../frontend-mobile/home.html) resolve.
REPO_ROOT = Path(__file__).resolve().parent.parent

for name in ("assets", "frontend-dashboard", "frontend-mobile"):
    directory = REPO_ROOT / name
    if directory.is_dir():
        app.mount(
            f"/{name}",
            StaticFiles(directory=directory, html=True),
            name=name,
        )

# `/docs` is FastAPI's Swagger UI, so design docs are served from /docs-static.
docs_dir = REPO_ROOT / "docs"
if docs_dir.is_dir():
    app.mount("/docs-static", StaticFiles(directory=docs_dir, html=True), name="docs")


@app.get("/", include_in_schema=False)
def index():
    # Developer hub linking to both frontends (see repo-root index.html).
    return FileResponse(REPO_ROOT / "index.html")
