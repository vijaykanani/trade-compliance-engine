from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.db.database import init_db
from app.routers import compliance, rules
from app.config import get_settings
from app.security import valid_demo_api_secret

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Pre & Post Trade Compliance Rule Engine",
    description=(
        "Automated trade compliance checks covering Corporate Restrictions, "
        "USA (SEC/FINRA/CFTC/Volcker) and EMEA (MiFID II/MAR/EMIR/UCITS/SFDR) regulations. "
        "Powered by DecisionRules.io with local fallback rule sets."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def require_demo_access(request, call_next):
    if request.url.path in {"/", "/health"}:
        return await call_next(request)

    expected_secret = os.environ.get("DEMO_ACCESS_SECRET", "")
    supplied_secret = request.headers.get("X-Demo-Access-Secret", "")
    if not valid_demo_api_secret(expected_secret, supplied_secret):
        return JSONResponse(status_code=403, content={"detail": "Approved demo access required"})
    return await call_next(request)


app.include_router(compliance.router)
app.include_router(rules.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "Trade Compliance Rule Engine",
        "version": "1.0.0",
        "rule_engine": "DecisionRules.io" if settings.decision_rules_configured else "Local (fallback)",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "decision_rules_configured": settings.decision_rules_configured,
    }
