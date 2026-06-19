# Phase 2: 数据库执行逻辑层构建 - 开发计划

## 任务总览

Phase 2 的目标是实现核心数据库操作逻辑，共 3 个任务，按依赖顺序执行：

| 序号 | 任务                                                | 产出文件  | 依赖                         |
| :--: | :-------------------------------------------------- | :-------- | :--------------------------- |
|  1   | 编写 `db.py`：连接池管理 + `execute_sql()` 核心函数 | `db.py`   | `config.py` (Phase 1 已完成) |
|  2   | 更新 `main.py`：补充连接池生命周期管理              | `main.py` | 任务 1                       |
|  3   | 端到端逻辑验证                                      | 无新文件  | 任务 1, 任务 2               |

---

## 任务 1：编写 `db.py`

**目标**：实现 MySQL 异步连接池管理和 SQL 执行核心函数。

**设计要点**：

1. **全局连接池变量**：模块级变量 `_pool = None`，由外部（`main.py` 的 lifespan）调用初始化/关闭函数来管理。

2. **连接池初始化函数** `async def init_pool()`：
   - 从 `config.py` 导入 `db_config`
   - 调用 `aiomysql.create_pool()` 创建连接池，参数从 `db_config` 解包
   - 将返回值赋给模块级 `_pool`
   - 需设置 `autocommit=True`，避免手动事务管理

3. **连接池关闭函数** `async def close_pool()`：
   - 检查 `_pool` 是否存在，若存在则调用 `_pool.close()` + `await _pool.wait_closed()`
   - 关闭后将 `_pool` 置为 `None`

4. **核心执行函数** `async def execute_sql(sql: str) -> dict`：
   - **空值前置检查**：如果 `sql` 去除空格后为空，直接返回失败响应
   - **单语句安全检查**：检测 SQL 中是否包含多个分号（`;`），若存在则拒绝执行，在 `message` 中提示"仅支持单条语句执行"
   - **计时**：使用 `time.perf_counter()` 记录开始时间
   - **SQL 类型判定**：`sql.strip().upper()` 判断前缀，`SELECT`/`SHOW`/`DESC`/`EXPLAIN` 为查询
   - **查询分支**：`cursor.execute(sql)` → `cursor.description` 提取列名 → `cursor.fetchall()` 获取行数据
   - **非查询分支**：`cursor.execute(sql)` → `cursor.rowcount` 获取受影响行数
   - **耗时计算**：`(perf_counter() - start) * 1000`，保留 1 位小数 `round(x, 1)`
   - **异常捕获**：`try...except Exception as e`，捕获所有异常（含 `aiomysql` 异常），返回 `success: False`，`message` 为 `str(e)`
   - **返回值**：严格遵循 API 契约 Schema，6 个字段一个不少

**返回值 Schema 对照**（来自 `API_Contract.md` 第 2.2.2 节）：

| 字段            | 类型     | 查询成功                      | 非查询成功   | 失败           |
| :-------------- | :------- | :---------------------------- | :----------- | :------------- |
| `success`       | boolean  | `True`                        | `True`       | `False`        |
| `message`       | string   | `"查询成功，共返回 N 行数据"` | `"执行成功"` | 异常信息字符串 |
| `duration_ms`   | float    | 实际耗时                      | 实际耗时     | `0.0`          |
| `columns`       | string[] | 列名数组                      | `[]`         | `[]`           |
| `rows`          | any[][]  | 数据二维数组                  | `[]`         | `[]`           |
| `affected_rows` | integer  | `0`                           | 受影响行数   | `0`            |

**关键实现细节**：

- `cursor.description` 为 `None` 时（非查询语句），`columns` 应为 `[]`
- `cursor.fetchall()` 返回的每行是 `tuple`，需转为 `list` 以满足 JSON 序列化要求
- 连接池未初始化时的异常处理：若 `_pool` 为 `None`，返回 `success: False`，`message` 提示"数据库连接池未初始化"

---

## 任务 2：更新 `main.py` — 补充连接池生命周期管理

**目标**：在 FastAPI 应用启动时初始化连接池，关闭时释放连接池。

**设计要点**：

1. 使用 FastAPI 的 `lifespan` 上下文管理器（推荐方式，替代已废弃的 `startup`/`shutdown` 事件）：

   ```python
   from contextlib import asynccontextmanager

   @asynccontextmanager
   async def lifespan(app):
       # startup: 初始化连接池
       await db.init_pool()
       yield
       # shutdown: 关闭连接池
       await db.close_pool()
   ```

2. 将 `lifespan` 传入 `FastAPI(lifespan=lifespan)`

3. 添加 `import db`（即 `db.py` 模块）

**当前 `main.py` 状态**：仅有基础骨架（13 行），需修改为使用 lifespan 模式

---

## 任务 3：端到端逻辑验证

**目标**：确认 `db.py` + `main.py` 的连接池管理和 SQL 执行逻辑正确衔接。

**验证清单**：

1. ✅ `db.py` 中 `_pool` 在 `init_pool()` 后不为 `None`
2. ✅ `execute_sql()` 在连接池未初始化时返回 `success: False`
3. ✅ 查询类 SQL（`SELECT`, `SHOW`, `DESC`, `EXPLAIN`）返回 `columns` + `rows`
4. ✅ 非查询 SQL（`INSERT`, `UPDATE`, `DELETE`, `CREATE` 等）返回 `affected_rows`
5. ✅ SQL 语法错误时返回 `success: False`，`message` 包含错误信息，`duration_ms` 为 `0.0`
6. ✅ 空字符串 SQL 返回失败响应
7. ✅ 多语句 SQL 被拒绝
8. ✅ `duration_ms` 保留 1 位小数
9. ✅ `main.py` 的 lifespan 正确调用 `init_pool()` 和 `close_pool()`
10. ✅ 返回值字典的 6 个字段名与 `API_Contract.md` 完全一致

**注意**：此任务为逻辑审查，不产出新文件。实际数据库连接测试需要用户配置 `.env` 后手动验证。

---

## 文件变更汇总

| 文件                        | 操作                     | 说明                         |
| :-------------------------- | :----------------------- | :--------------------------- |
| `mysql_web_console/db.py`   | **新建**（当前为空文件） | 连接池管理 + `execute_sql()` |
| `mysql_web_console/main.py` | **修改**                 | 添加 lifespan、导入 db 模块  |
