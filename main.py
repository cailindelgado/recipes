from contextlib import asynccontextmanager

from fastapi import FastAPI

from recipes.database import Base, engine
from recipes.recipes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()

app = FastAPI(lifespan=lifespan)
app.include_router(router)

@app.get("/health")
async def health():
    return {"status": "ok"}
