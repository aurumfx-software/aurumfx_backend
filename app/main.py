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
from app.routers import binary_income
from app.routers import genealogy
from app.routers import level_commission
from app.routers import admin_level_commission
from app.routers import admin_dashboard
from app.routers import dashboard
import logging
from fastapi import Request

logger = logging.getLogger("api")






Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AurumFX API",
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
app.include_router(binary_income.router)
app.include_router(genealogy.router)
app.include_router(level_commission.router)
app.include_router(admin_level_commission.router)
app.include_router(admin_dashboard.router)
app.include_router(dashboard.router)

@app.middleware("http")
async def log_requests(request: Request, call_next):

    response = await call_next(request)

    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code}"
    )

    return response