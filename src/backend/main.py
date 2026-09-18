"""App-এর জীবনচক্র: startup → অনেক request → shutdown।"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.routes.documents import router as documents_router
from backend.api.routes.search import router as search_router
from backend.core.bootstrap import build_container
from backend.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # yield-এর আগে: দোকান খোলার মতো সব resource প্রস্তুত করো।
    # শুধু main.py import করলে এই model/client তৈরি হবে না।
    container = build_container(get_settings())
    app.state.container = container
    try:
        # এখানে setup থামে, FastAPI বহু request handle করে।
        # এটি প্রতি request-এর yield নয়; পুরো app lifetime-এর boundary।
        yield
    finally:
        # Server থামলে, এমনকি lifespan-এ exception এলেও, cleanup করো।
        # শুধু None করলে connection বন্ধ হয় না; close() দরকার।
        try:
            container.qdrant_client.close()
        finally:
            app.state.container = None


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="AI-powered document knowledge base using Vector Database",
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(documents_router)
app.include_router(search_router)
