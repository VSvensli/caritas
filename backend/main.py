from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import Base, engine
from backend.routers import auth, calendar, reports, sync, users, villages

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Caritas HARVEST", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

docs_dir = Path(__file__).resolve().parent.parent / "docs"
if docs_dir.is_dir():
    app.mount("/docs-static", StaticFiles(directory=docs_dir, html=True), name="docs")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(villages.router)
app.include_router(calendar.router)
app.include_router(reports.router)
app.include_router(sync.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
