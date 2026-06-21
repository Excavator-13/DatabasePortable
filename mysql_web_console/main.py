# FastAPI 应用入口：定义路由、生命周期管理与静态文件服务
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import db


# 应用生命周期：启动时初始化数据库连接池，关闭时释放连接池
@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    yield
    await db.close_pool()


app = FastAPI(title="MySQL Web Console", lifespan=lifespan)


# SQL 执行请求体模型，仅包含一个 sql 字段
class SqlRequest(BaseModel):
    sql: str


class FavoriteRequest(BaseModel):
    name: str
    sql: str


# 根路由：返回前端单页应用页面
@app.get("/")
async def root():
    return FileResponse("static/index.html")


# 数据库信息接口：返回当前使用的数据库名
@app.get("/api/info")
async def get_info():
    current_db = await db.get_current_db()
    return {"database": current_db}


# 核心 SQL 执行接口：接收 SQL 语句，执行并返回结构化结果
# 包含空值前置检查和全局异常兜底，确保不会抛出 500 错误
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
    validation = await db.validate_sql(body.sql)
    if not validation.get("valid"):
        return {"success": False, "message": "收藏失败：" + validation.get("message", "SQL 校验未通过")}
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


# 挂载静态文件目录，需放在路由定义之后，避免拦截 /api 等路由
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn

    # host 绑定 0.0.0.0 以允许局域网内其他设备访问
    uvicorn.run(app, host="0.0.0.0", port=8000)