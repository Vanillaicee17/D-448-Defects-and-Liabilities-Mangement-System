# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from db.session import engine
from app.db.base import Base
from app.db.seed import init_admin, init_roles
from app.db.session import SessionLocal

from api import auth, vessel, defect, defect_assignment, user, vendor, equipment


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ Create tables
    Base.metadata.create_all(bind=engine)

    # ✅ Create DB session for seeding
    db = SessionLocal()
    try:
        init_roles(db)
        init_admin(db)
    finally:
        db.close()

    yield

app = FastAPI(title="Defect Management System", lifespan=lifespan)

# 🔌 Routers
app.include_router(auth.router)
app.include_router(vessel.router)
app.include_router(defect.router)
app.include_router(user.router)
app.include_router(defect_assignment.router)
app.include_router(vendor.router)
app.include_router(equipment.router)


@app.get("/")
def root():
    return {"message": "API is running"}
