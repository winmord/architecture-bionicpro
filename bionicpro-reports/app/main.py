from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import reports
import os

app = FastAPI(
    title="BionicPRO Reports API",
    description="API для получения отчётов о работе протезов",
    version="1.0.0"
)

# Настройка CORS с поддержкой кастомных заголовков
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Конкретный origin вместо "*"
    allow_credentials=True,  # Важно для cookies
    allow_methods=["*"],
    allow_headers=["*", "X-Session-Id"],  # Разрешаем кастомный заголовок
)

app.include_router(reports.router)


@app.get("/")
async def root():
    return {
        "service": "BionicPRO Reports API",
        "version": "1.0.0",
        "endpoints": {
            "reports": "/reports/{user_id}",
            "csv": "/reports/me/csv",
            "health": "/reports/health",
            "debug_session": "/reports/debug/session"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    )