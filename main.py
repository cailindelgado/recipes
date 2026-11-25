from contextlib import asynccontextmanager

from fastapi import FastAPI

from recipes.database import Base, engine, ensure_postgis


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok"}
