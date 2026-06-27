import secrets
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import db
from config import cors_origins, require_login, token_expire_hours

_tokens: dict[str, float] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not require_login:
        await db.init_pool()
    yield
    await db.close_pool()
    _tokens.clear()


app = FastAPI(title="MySQL Web Console", lifespan=lifespan)

origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SqlRequest(BaseModel):
    sql: str


class FavoriteRequest(BaseModel):
    name: str
    sql: str
    force: bool = False


class LoginRequest(BaseModel):
    host: str
    port: int
    user: str
    password: str
    db: str


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if not require_login:
        return await call_next(request)

    path = request.url.path
    public_paths = {"/", "/api/auth-status", "/api/login"}
    if path in public_paths or path.startswith("/static"):
        return await call_next(request)

    if path.startswith("/api/"):
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if token in _tokens:
                elapsed_hours = (time.time() - _tokens[token]) / 3600
                if elapsed_hours > token_expire_hours:
                    _tokens.pop(token, None)
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Token 已过期，请重新登录"},
                    )
                if not db.is_pool_ready():
                    _tokens.pop(token, None)
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "连接已断开，请重新登录"},
                    )
                return await call_next(request)
        return JSONResponse(
            status_code=401,
            content={"detail": "未授权，请重新登录"},
        )

    return await call_next(request)


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/api/auth-status")
async def auth_status():
    return {
        "require_login": require_login,
        "authenticated": db.is_pool_ready(),
    }


@app.post("/api/login")
async def login(body: LoginRequest):
    config = {
        "host": body.host,
        "port": body.port,
        "user": body.user,
        "password": body.password,
        "db": body.db,
    }
    try:
        await db.init_pool_with_config(config)
    except Exception as e:
        return {"success": False, "message": f"连接失败: {str(e)}"}
    token = secrets.token_hex(32)
    _tokens[token] = time.time()
    return {"success": True, "token": token}


@app.post("/api/logout")
async def logout(request: Request):
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        _tokens.pop(token, None)
    await db.destroy_pool()
    return {"success": True}


@app.get("/api/info")
async def get_info():
    current_db = await db.get_current_db()
    return {"database": current_db}


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
                "out_params": [],
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
            "out_params": [],
        }


@app.post("/api/validate")
async def validate_sql(body: SqlRequest):
    result = await db.validate_sql(body.sql)
    return result


@app.get("/api/tables")
async def get_tables():
    tables = await db.get_tables()
    return {"tables": tables}


@app.get("/api/tables/{name}/desc")
async def describe_table(name: str):
    result = await db.describe_table(name)
    return result


@app.get("/api/procedures")
async def get_procedures():
    procedures = await db.get_procedures()
    return {"procedures": procedures}


@app.get("/api/procedures/{name}/params")
async def get_procedure_params(name: str):
    params = await db.get_procedure_params(name)
    return {"params": params}


@app.get("/api/favorites")
async def get_favorites():
    favorites = await db.get_favorites()
    return {"favorites": favorites}


@app.post("/api/favorites")
async def create_favorite(body: FavoriteRequest):
    if not body.name.strip():
        return {"success": False, "message": "收藏命名不能为空"}
    if not body.sql.strip():
        return {"success": False, "message": "SQL 语句不能为空"}
    if not body.force:
        validation = await db.validate_sql(body.sql)
        if not validation.get("valid"):
            return {"success": False, "message": validation.get("message", "SQL 校验未通过"), "validation_error": True}
    fav = await db.add_favorite(body.name.strip(), body.sql.strip())
    if fav is None:
        return {"success": False, "message": "收藏失败，请稍后重试"}
    return {"success": True, "favorite": fav}


@app.delete("/api/favorites/{fav_id}")
async def delete_favorite(fav_id: int):
    removed = await db.remove_favorite(fav_id)
    if removed:
        return {"success": True}
    return {"success": False, "message": "收藏不存在或已删除"}


@app.get("/api/favorites/search")
async def search_favorites(keyword: str = ""):
    if not keyword.strip():
        favorites = await db.get_favorites()
        return {"favorites": favorites}
    favorites = await db.search_favorites(keyword.strip())
    return {"favorites": favorites}


app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)