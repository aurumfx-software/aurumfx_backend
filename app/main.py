from fastapi import FastAPI
from app.database import Base, engine
from app.models import User
from app.routers.auth import router as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AurFX API",
    version="1.0.0"
)

app.include_router(auth_router)