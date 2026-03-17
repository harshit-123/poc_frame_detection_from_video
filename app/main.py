from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from fastapi.staticfiles import StaticFiles

def create_app() -> FastAPI:
    app = FastAPI(title="POC Video Frame API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()

app.mount("/snapshots", StaticFiles(directory="snapshots"), name="snapshots")
