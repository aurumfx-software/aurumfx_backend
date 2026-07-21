from fastapi import FastAPI
from app.database import Base, engine
from app.models import User, InvestmentPlan
from app.routers.auth import router as auth_router
from app.routers.investment_plan import router as investment_plan_router
from app.routers.investment import router as investment_router
from app.routers.return_type import router as return_type_router
from app.routers import admin_investment
from app.routers import wallet
from app.routers import admin_wallet
from app.routers import admin_commission
from app.routers import lot_setting
from app.routers import admin_binary_tree




Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AurFX API",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(return_type_router)
app.include_router(investment_plan_router)
app.include_router(investment_router)
app.include_router(admin_investment.router)
app.include_router(wallet.router)
app.include_router(admin_wallet.router)
app.include_router(admin_commission.router)
app.include_router(lot_setting.router)
app.include_router(admin_binary_tree.router)


