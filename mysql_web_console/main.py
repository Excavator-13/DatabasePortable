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


@app.get("/api/procedures")
async def get_procedures():
    procedures = await db.get_procedures()
    return {"procedures": procedures}


@app.get("/api/procedures/{name}/params")
async def get_procedure_params(name: str):
    params = await db.get_procedure_params(name)
    return {"params": params}


# 挂载静态文件目录，需放在路由定义之后，避免拦截 /api 等路由
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn

    # host 绑定 0.0.0.0 以允许局域网内其他设备访问
    uvicorn.run(app, host="0.0.0.0", port=8000)