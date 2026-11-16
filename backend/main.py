from fastapi import FastAPI
from database import get_connection
from routers import auth
from routers import auth, checks
app = FastAPI(title="Scam Shield API")
app.include_router(auth.router)
app.include_router(checks.router)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    with get_connection() as conn:
        row = conn.execute("SELECT 1 AS ok").fetchone()
    return {"db": row["ok"] == 1}