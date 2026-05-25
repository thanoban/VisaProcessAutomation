from fastapi import FastAPI

from backend.api.routes import router
from backend.database.session import init_db


def create_app() -> FastAPI:
    init_db()
    app = FastAPI(
        title="VisaFlow MAS",
        version="0.1.0",
        description="Government-grade Tourist Visa multi-agent decision support PoC.",
    )
    app.include_router(router)
    return app


app = create_app()
