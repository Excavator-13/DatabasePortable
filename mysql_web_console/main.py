from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    yield
    await db.close_pool()


app = FastAPI(title="MySQL Web Console", lifespan=lifespan)


class SqlRequest(BaseModel):
    sql: str


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/api/execute")
async def execute_sql(body: SqlRequest):
    try:
        if not body.sql.strip():
            return {
                "success": False,
                "message": "SQL 语句不能为空",
                "duration_ms": 0.0,
                "columns": [],
                "rows": [],
                "affected_rows": 0,
            }
        result = await db.execute_sql(body.sql)
        return result
    except Exception as e:
        return {
            "success": False,
            "message": f"服务器内部错误: {str(e)}",
            "duration_ms": 0.0,
            "columns": [],
            "rows": [],
            "affected_rows": 0,
        }


app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)