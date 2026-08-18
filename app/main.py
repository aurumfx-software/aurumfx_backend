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
# from app.routers import admin_commission
from app.routers import lot_setting
# from app.routers import admin_binary_tree
# from app.routers import binary_income
from app.routers import genealogy
from app.routers import level_commission
from app.routers import admin_level_commission
from app.routers import admin_dashboard
from app.routers import dashboard
from app.routers import  admin_rank
from app.routers import admin_fee
from app.routers import admin_referral_commission_settings
from app.routers.admin_payout import router as admin_payout_router
from app.routers.enroller import router as enroller_router
from app.routers.user_genealogy import (router as user_genealogy_router)
from app.routers import user_rank
from app.routers import user_kyc
from app.routers import user_payout_history
from app.routers.help_center import router as help_center_router
from app.routers.admin_help_center import router as admin_help_center_router




import logging
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware


logger = logging.getLogger("api")






Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AurumFX API",
    version="1.0.0"
)



origins = [
    "http://localhost:3000",      # React
    "http://localhost:5173",      # Vite
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5000",
    "https://aurumfx-app-ec739.ondigitalocean.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(return_type_router)
app.include_router(investment_plan_router)
app.include_router(investment_router)
app.include_router(admin_investment.router)
app.include_router(wallet.router)
app.include_router(admin_wallet.router)
# app.include_router(admin_commission.router)
app.include_router(lot_setting.router)
# app.include_router(admin_binary_tree.router)
# app.include_router(binary_income.router)
app.include_router(genealogy.router)
app.include_router(level_commission.router)
app.include_router(admin_level_commission.router)
app.include_router(admin_rank.router)
app.include_router(admin_dashboard.router)
app.include_router(dashboard.router)
app.include_router(admin_fee.router)
app.include_router(admin_referral_commission_settings.router)
app.include_router(admin_payout_router)
app.include_router(enroller_router)
app.include_router(user_genealogy_router)
app.include_router(user_rank.router)
app.include_router(user_kyc.router)
app.include_router(user_payout_history.router)
app.include_router(help_center_router)
app.include_router(admin_help_center_router)







@app.middleware("http")
async def log_requests(request: Request, call_next):

    response = await call_next(request)

    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code}"
    )

    return response