from contextlib import asynccontextmanager

from fastapi import FastAPI

import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    yield
    await db.close_pool()


app = FastAPI(title="MySQL Web Console", lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Server is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)