from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import reports

app = FastAPI(
    title="BionicPRO Reports API",
    description="API для получения отчётов о работе протезов",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports.router)


@app.get("/")
async def root():
    return {
        "service": "BionicPRO Reports API",
        "version": "1.0.0",
        "endpoints": {
            "reports": "/reports/{user_email}",
            "all_reports": "/reports/",
            "csv": "/reports/{user_email}/csv",
            "health": "/reports/health"
        }
    }