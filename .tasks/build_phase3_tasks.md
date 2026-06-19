# Phase 3: 后端路由与接口层构建 - 开发计划

## 任务总览

Phase 3 的目标是在 `main.py` 中完成 API 路由层，将 `db.execute_sql()` 暴露给前端调用。共 3 个任务，按依赖顺序执行：

| 序号 | 任务                                        | 产出文件  | 依赖                             |
| :--: | :------------------------------------------ | :-------- | :------------------------------- |
|  1   | 配置静态文件挂载，`GET /` 返回 `index.html` | `main.py` | `static/` 目录已存在             |
|  2   | 实现 `POST /api/execute` 接口               | `main.py` | 任务 1, `db.py` (Phase 2 已完成) |
|  3   | API 层兜底异常捕获 + 逻辑审查               | 无新文件  | 任务 2                           |

---

## 任务 1：配置静态文件挂载

**目标**：让 `GET /` 返回 `static/index.html`，而非当前的 JSON 占位响应。

**设计要点**：

1. **方案选择**：使用 FastAPI 的 `StaticFiles` 中间件挂载 `static/` 目录，同时保留 `GET /` 路由返回 `FileResponse`。
   - `StaticFiles` 挂载到 `/static` 路径，用于服务静态资源（CSS/JS/图片等）
   - `GET /` 路由使用 `FileResponse` 返回 `static/index.html`

2. **具体实现**：
   - 导入 `from fastapi.responses import FileResponse`
   - 导入 `from fastapi.staticfiles import StaticFiles`
   - 修改现有 `@app.get("/")` 路由：返回 `FileResponse("static/index.html")`
   - 在路由定义之后挂载静态文件：`app.mount("/static", StaticFiles(directory="static"), name="static")`

3. **注意事项**：
   - `app.mount()` 必须放在所有路由定义之后，因为 mount 会匹配所有以 `/static` 开头的请求，若放在路由前会导致路由被拦截
   - `FileResponse` 的路径使用相对路径 `"static/index.html"`，因为工作目录为 `mysql_web_console/`

**当前代码需变更的部分**：

```python
# 当前（占位）
@app.get("/")
async def root():
    return {"message": "Server is running"}

# 目标
@app.get("/")
async def root():
    return FileResponse("static/index.html")

# 在路由定义之后添加
app.mount("/static", StaticFiles(directory="static"), name="static")
```

---

## 任务 2：实现 `POST /api/execute` 接口

**目标**：接收前端 JSON 请求，调用 `db.execute_sql()` 并返回结果。

**设计要点**：

1. **请求体模型**：使用 Pydantic `BaseModel` 定义请求体，确保类型安全和自动校验：

   ```python
   from pydantic import BaseModel

   class SqlRequest(BaseModel):
       sql: str
   ```

2. **空值前置校验**：
   - 虽然 `db.execute_sql()` 内部已有空值检查，但 API 层也应做前置校验
   - 原因：避免无意义的数据库连接池获取，提前快速失败
   - 校验逻辑：`if not body.sql.strip()` → 直接返回失败响应
   - 返回格式与 `API_Contract.md` 场景 D 一致

3. **调用 `db.execute_sql()`**：
   - 直接将 `body.sql` 传入，`db.execute_sql()` 内部会处理 strip、单语句检查、SQL 类型判定等
   - 将返回的 `dict` 直接作为 JSON Response 返回

4. **完整接口实现**：

   ```python
   @app.post("/api/execute")
   async def execute_sql(body: SqlRequest):
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
   ```

5. **关于 Pydantic 校验的说明**：
   - 如果前端未传 `sql` 字段或传了非字符串类型，Pydantic 会自动返回 422 错误
   - 这是 FastAPI 的默认行为，符合 `API_Contract.md` 场景 D 的预期
   - 无需额外处理

---

## 任务 3：API 层兜底异常捕获 + 逻辑审查

**目标**：确保 `POST /api/execute` 接口在任何异常下都不会导致服务崩溃，并审查整体逻辑正确性。

**设计要点**：

1. **兜底异常捕获**：在 `POST /api/execute` 路由函数外层包裹 `try-except`：

   ```python
   @app.post("/api/execute")
   async def execute_sql(body: SqlRequest):
       try:
           if not body.sql.strip():
               return { ... }
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
   ```

   - 虽然 `db.execute_sql()` 内部已有异常捕获，但 API 层的兜底可以防止 Pydantic 序列化异常、`db` 模块导入异常等意外情况
   - 这是双重保险，确保服务永不因单个请求而崩溃

2. **逻辑审查清单**：

   | #   | 检查项                                       | 预期结果                                           |
   | --- | :------------------------------------------- | :------------------------------------------------- |
   | 1   | `GET /` 返回 `static/index.html`             | HTTP 200, Content-Type: text/html                  |
   | 2   | `POST /api/execute` 正常查询 SQL             | 返回 `db.execute_sql()` 的结果字典                 |
   | 3   | `POST /api/execute` 空 SQL                   | 返回 `success: False, message: "SQL 语句不能为空"` |
   | 4   | `POST /api/execute` 缺少 `sql` 字段          | FastAPI 自动返回 422                               |
   | 5   | `POST /api/execute` 数据库异常               | `db.execute_sql()` 内部捕获，返回 `success: False` |
   | 6   | `POST /api/execute` 意外异常（如序列化失败） | API 层兜底捕获，返回 `success: False`              |
   | 7   | `app.mount("/static", ...)` 不影响已有路由   | `/api/execute` 等路由正常工作                      |
   | 8   | 返回值 JSON 结构 6 字段齐全                  | 与 `API_Contract.md` Schema 一致                   |
   | 9   | lifespan 正确管理连接池生命周期              | 启动时 `init_pool()`，关闭时 `close_pool()`        |

---

## 文件变更汇总

| 文件                        | 操作     | 说明                                                     |
| :-------------------------- | :------- | :------------------------------------------------------- |
| `mysql_web_console/main.py` | **修改** | 添加静态文件挂载、`POST /api/execute` 接口、兜底异常捕获 |

**变更前**（当前 26 行）：

- `lifespan` 管理连接池 ✅
- `GET /` 返回 JSON 占位 ❌（需改为 FileResponse）
- `POST /api/execute` 缺失 ❌（需新增）
- 兜底异常捕获 缺失 ❌（需新增）

**变更后**：

- `lifespan` 管理连接池 ✅
- `GET /` 返回 `FileResponse("static/index.html")` ✅
- `POST /api/execute` 接口 + 空值校验 + 兜底异常捕获 ✅
- `app.mount("/static", ...)` 静态文件服务 ✅
