# 数据库连接池管理与 SQL 执行逻辑
# 负责连接池的创建/销毁、SQL 类型判定、单语句安全检查以及执行结果的统一封装
from __future__ import annotations

import time

import aiomysql

from config import db_config

# 全局连接池实例，在 lifespan 启动时初始化
_pool: aiomysql.Pool | None = None

# 查询类 SQL 的前缀，这些语句需要使用 fetchall 获取结果集
_QUERY_PREFIXES = ("SELECT", "SHOW", "DESC", "EXPLAIN")


# 初始化连接池，应用启动时调用
async def init_pool():
    global _pool
    _pool = await aiomysql.create_pool(
        **db_config,
        autocommit=True,
        minsize=1,
        maxsize=5,
    )


# 关闭连接池，应用关闭时调用
async def close_pool():
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


# 判断 SQL 是否为查询语句（SELECT/SHOW/DESC/EXPLAIN）
# 查询语句使用 fetchall 获取数据，非查询语句使用 rowcount 获取影响行数
def _is_query(sql_stripped_upper: str) -> bool:
    return sql_stripped_upper.startswith(_QUERY_PREFIXES)


# 单语句安全检查：防止批量执行多条 SQL
# 去除末尾分号后，若仍包含分号则视为多条语句，予以拒绝
def _check_single_statement(sql: str) -> str | None:
    trimmed = sql.strip()
    if trimmed.endswith(";"):
        trimmed = trimmed[:-1].strip()
    if ";" in trimmed:
        return "仅支持单条语句执行"
    return None


# 查询当前连接使用的数据库名，通过 SELECT DATABASE() 获取
async def get_current_db() -> str | None:
    if _pool is None:
        return None
    try:
        async with _pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT DATABASE()")
                row = await cursor.fetchone()
                return row[0] if row else None
    except Exception:
        return None


async def get_procedures() -> list[str]:
    if _pool is None:
        return []
    try:
        current_db = await get_current_db()
        if not current_db:
            return []
        async with _pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SHOW PROCEDURE STATUS WHERE Db = %s", (current_db,)
                )
                rows = await cursor.fetchall()
                return sorted(row[1] for row in rows)
    except Exception:
        return []


async def get_procedure_params(proc_name: str) -> list[dict]:
    if _pool is None:
        return []
    try:
        current_db = await get_current_db()
        if not current_db:
            return []
        async with _pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT PARAMETER_NAME, DATA_TYPE, PARAMETER_MODE "
                    "FROM information_schema.PARAMETERS "
                    "WHERE SPECIFIC_SCHEMA = %s AND SPECIFIC_NAME = %s "
                    "AND PARAMETER_MODE IS NOT NULL "
                    "ORDER BY ORDINAL_POSITION",
                    (current_db, proc_name),
                )
                rows = await cursor.fetchall()
                return [
                    {"name": row[0], "type": row[1], "direction": row[2]}
                    for row in rows
                ]
    except Exception:
        return []


# 核心 SQL 执行函数
# 执行流程：空值检查 → 单语句检查 → 连接池获取 → 执行 SQL → 结果封装
async def execute_sql(sql: str) -> dict:
    empty_result = {
        "success": False,
        "message": "",
        "duration_ms": 0.0,
        "columns": [],
        "rows": [],
        "affected_rows": 0,
    }

    # 空值检查
    if not sql or not sql.strip():
        empty_result["message"] = "SQL 语句不能为空"
        return empty_result

    # 单语句安全检查
    multi_stmt_error = _check_single_statement(sql)
    if multi_stmt_error:
        empty_result["message"] = multi_stmt_error
        return empty_result

    # 连接池状态检查
    if _pool is None:
        empty_result["message"] = "数据库连接池未初始化"
        return empty_result

    start = time.perf_counter()

    try:
        async with _pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql)

                sql_upper = sql.strip().upper()

                # 查询语句：返回列名和数据行
                if _is_query(sql_upper):
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    rows = [list(row) for row in await cursor.fetchall()]
                    duration_ms = round((time.perf_counter() - start) * 1000, 1)
                    return {
                        "success": True,
                        "message": f"查询成功，共返回 {len(rows)} 行数据",
                        "duration_ms": duration_ms,
                        "columns": columns,
                        "rows": rows,
                        "affected_rows": 0,
                    }
                # 非查询语句：返回受影响行数
                else:
                    affected_rows = cursor.rowcount
                    duration_ms = round((time.perf_counter() - start) * 1000, 1)
                    return {
                        "success": True,
                        "message": "执行成功",
                        "duration_ms": duration_ms,
                        "columns": [],
                        "rows": [],
                        "affected_rows": affected_rows,
                    }
    # 捕获所有数据库异常，将错误信息格式化返回，避免服务崩溃
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "duration_ms": 0.0,
            "columns": [],
            "rows": [],
            "affected_rows": 0,
        }