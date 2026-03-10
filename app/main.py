from fastapi import FastAPI

from app.api.routes import router
from fastapi.staticfiles import StaticFiles

def create_app() -> FastAPI:
    app = FastAPI(title="POC Video Frame API")
    app.include_router(router)
    return app


app = create_app()

app.mount("/snapshots", StaticFiles(directory="snapshots"), name="snapshots")
