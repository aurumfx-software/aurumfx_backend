from fastapi import FastAPI
from app.database import Base, engine
from app.models import User, InvestmentPlan
from app.routers.auth import router as auth_router
from app.routers.investment_plan import router as investment_plan_router
from app.routers.investment import router as investment_router
from app.routers.return_type import router as return_type_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AurFX API",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(return_type_router)
app.include_router(investment_plan_router)
app.include_router(investment_router)