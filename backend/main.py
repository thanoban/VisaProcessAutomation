from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router
from backend.database.session import init_db


def create_app() -> FastAPI:
    init_db()
    repo_root = Path(__file__).resolve().parents[1]
    frontend_dir = repo_root / "frontend"
    app = FastAPI(
        title="VisaFlow MAS",
        version="0.1.0",
        description="Government-grade Tourist Visa multi-agent decision support PoC.",
    )
    app.include_router(router)

    if frontend_dir.exists():
        app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")

        @app.get("/", include_in_schema=False)
        def root() -> RedirectResponse:
            return RedirectResponse(url="/frontend/")

    return app


app = create_app()
