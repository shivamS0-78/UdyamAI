from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import get_current_user
from app.api.routes import (
    agriculture,
    analysis,
    auth,
    businesses,
    chat,
    dashboard,
    economic,
    feasibility,
    finance,
    health,
    infrastructure,
    livestock,
    locations,
    markets,
    population,
    reports,
    schemes,
    users,
    weather,
)
from app.config import settings
from app.utils.errors import setup_exception_handlers
from app.utils.logging import setup_logging
from app.utils.rate_limiter import default_limiter

# Setup logging
setup_logging()

app = FastAPI(
    title="UdyamAI Backend API",
    description="API for UdyamAI business feasibility, financial analysis, geo services, and scheme recommendations.",
    version=settings.VERSION,
)

# Set CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup custom exception handlers
setup_exception_handlers(app)

# Include Routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Auth"],
    include_in_schema=False,
)
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(
    health.router,
    prefix="/api/v1/health",
    tags=["Health"],
    include_in_schema=False,
)

app.include_router(
    locations.router,
    prefix="/locations",
    tags=["Locations"],
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    locations.router,
    prefix="/api/v1/locations",
    tags=["Locations"],
    include_in_schema=False,
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    businesses.router,
    prefix="/business-categories",
    tags=["Business Categories"],
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    businesses.router,
    prefix="/api/v1/business-categories",
    tags=["Business Categories"],
    include_in_schema=False,
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    businesses.records_router,
    prefix="/businesses",
    tags=["Businesses"],
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    businesses.records_router,
    prefix="/api/v1/businesses",
    tags=["Businesses"],
    include_in_schema=False,
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    schemes.router, prefix="/schemes", tags=["Schemes"], dependencies=[Depends(default_limiter)]
)
app.include_router(
    schemes.router,
    prefix="/api/v1/schemes",
    tags=["Schemes"],
    include_in_schema=False,
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["Feasibility Analysis"],
    dependencies=[Depends(get_current_user), Depends(default_limiter)],
)
app.include_router(
    analysis.router,
    prefix="/api/v1/analysis",
    tags=["Feasibility Analysis"],
    include_in_schema=False,
    dependencies=[Depends(get_current_user), Depends(default_limiter)],
)
app.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"],
    dependencies=[Depends(get_current_user), Depends(default_limiter)],
)
app.include_router(
    chat.router,
    prefix="/api/v1/chat",
    tags=["Chat"],
    include_in_schema=False,
    dependencies=[Depends(get_current_user), Depends(default_limiter)],
)
app.include_router(
    finance.router, prefix="/finance", tags=["Finance"], dependencies=[Depends(default_limiter)]
)
app.include_router(
    finance.router,
    prefix="/api/v1/finance",
    tags=["Finance"],
    include_in_schema=False,
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_current_user), Depends(default_limiter)],
)
app.include_router(
    dashboard.router,
    prefix="/api/v1/dashboard",
    tags=["Dashboard"],
    include_in_schema=False,
    dependencies=[Depends(get_current_user), Depends(default_limiter)],
)
app.include_router(
    reports.router,
    prefix="/reports",
    tags=["Reports"],
    dependencies=[Depends(get_current_user), Depends(default_limiter)],
)
app.include_router(
    reports.router,
    prefix="/api/v1/reports",
    tags=["Reports"],
    include_in_schema=False,
    dependencies=[Depends(get_current_user), Depends(default_limiter)],
)
app.include_router(
    users.router, prefix="/users", tags=["Users"], dependencies=[Depends(default_limiter)]
)
app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["Users"],
    include_in_schema=False,
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    markets.router, prefix="/markets", tags=["Markets"], dependencies=[Depends(default_limiter)]
)
app.include_router(
    markets.router,
    prefix="/api/v1/markets",
    tags=["Markets"],
    include_in_schema=False,
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    feasibility.router,
    prefix="/feasibility",
    tags=["Feasibility Engine"],
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    feasibility.router,
    prefix="/api/v1/feasibility",
    tags=["Feasibility Engine"],
    include_in_schema=False,
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    infrastructure.router,
    prefix="/infrastructure",
    tags=["Infrastructure"],
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    infrastructure.router,
    prefix="/api/v1/infrastructure",
    tags=["Infrastructure"],
    include_in_schema=False,
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    agriculture.router,
    prefix="/agriculture",
    tags=["Agriculture"],
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    agriculture.router,
    prefix="/api/v1/agriculture",
    tags=["Agriculture"],
    include_in_schema=False,
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    livestock.router,
    prefix="/livestock",
    tags=["Livestock"],
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    livestock.router,
    prefix="/api/v1/livestock",
    tags=["Livestock"],
    include_in_schema=False,
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    population.router,
    prefix="/population",
    tags=["Population"],
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    population.router,
    prefix="/api/v1/population",
    tags=["Population"],
    include_in_schema=False,
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    weather.router,
    prefix="/weather",
    tags=["Weather"],
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    weather.router,
    prefix="/api/v1/weather",
    tags=["Weather"],
    include_in_schema=False,
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    economic.router,
    prefix="/economic",
    tags=["Economic"],
    dependencies=[Depends(default_limiter)],
)
app.include_router(
    economic.router,
    prefix="/api/v1/economic",
    tags=["Economic"],
    include_in_schema=False,
    dependencies=[Depends(default_limiter)],
)


@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} Core API Services"}
