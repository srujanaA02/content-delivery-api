from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.models.database import database, metadata, engine
from app.routes.assets import router
from app.services.storage import init_bucket


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    metadata.create_all(engine)
    print("✅ Tables created")
    await database.connect()
    print("✅ Database connected")
    init_bucket()
    yield
    # Shutdown
    await database.disconnect()


app = FastAPI(title="Content Delivery API", lifespan=lifespan)

app.include_router(router, prefix="/assets")


@app.get("/health")
async def health():
    return {"status": "OK"}