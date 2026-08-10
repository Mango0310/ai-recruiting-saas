import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import engine, Base, SessionLocal
from routers import jobs, upload, candidates, talent_pool, dashboard, employees, company as company_router, auth as auth_router


async def check_alerts_loop():
    """Background task: check probation/contract alerts daily and notify via webhook."""
    while True:
        try:
            from services.notify_service import notify_probation_alert, is_enabled
            if is_enabled():
                db = SessionLocal()
                try:
                    from models.employee import Employee
                    employees = db.query(Employee).filter(Employee.status == "probation").all()
                    alerted = [e for e in employees if e.probation_alert in ("urgent", "overdue")]
                    if alerted:
                        notify_probation_alert(alerted)
                finally:
                    db.close()
        except Exception:
            pass
        await asyncio.sleep(86400)  # 24 hours


@asynccontextmanager
async def lifespan(app: FastAPI):
    from auth import check_jwt_secret_on_startup
    check_jwt_secret_on_startup()
    task = asyncio.create_task(check_alerts_loop())
    yield
    task.cancel()


app = FastAPI(title="AI Recruiting Assistant", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# create_all handles new tables. For new *columns* on existing tables, the
# schema doctor adds them automatically — no need to drop and rebuild the DB.
Base.metadata.create_all(bind=engine)

from services.schema_doctor import apply_migrations
apply_migrations(engine, Base.metadata)

app.include_router(jobs.router)
app.include_router(upload.router)
app.include_router(candidates.router)
app.include_router(talent_pool.router)
app.include_router(dashboard.router)
app.include_router(employees.router)
app.include_router(company_router.router)
app.include_router(auth_router.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/notify/test")
def test_notification():
    """Send a test webhook notification to verify configuration."""
    from services.notify_service import send, is_enabled
    if not is_enabled():
        return {"ok": False, "message": "Webhook not configured. Set WEBHOOK_URL in .env"}
    ok = send("测试通知", "如果你收到这条消息，说明 Webhook 配置正确。", "info")
    return {"ok": ok, "message": "Sent" if ok else "Failed — check backend logs"}
