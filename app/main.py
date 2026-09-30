from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Create database tables automatically.
    Base.metadata.create_all(
        bind=engine
    )

    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "FitBuddy - AI Fitness Plan Generator "
        "using Gemini Models"
    ),
    version="1.0.0",
    lifespan=lifespan
)


app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)


app.include_router(router)