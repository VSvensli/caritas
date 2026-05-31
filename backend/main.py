from fastapi import FastAPI

from backend.database import Base, engine
from backend.routers import auth, calendar, reports, sync, users, villages

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Caritas HARVEST", version="0.1.0")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(villages.router)
app.include_router(calendar.router)
app.include_router(reports.router)
app.include_router(sync.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
