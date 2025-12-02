"""FastAPI entrypoint for the DSSS simulator backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import routes


def create_app() -> FastAPI:
    app = FastAPI(title="DSSS Simulator API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(routes.router)
    return app


app = create_app()
