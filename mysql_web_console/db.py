import time

import aiomysql

from config import db_config

_pool: aiomysql.Pool | None = None

_QUERY_PREFIXES = ("SELECT", "SHOW", "DESC", "EXPLAIN")


async def init_pool():
    global _pool
    _pool = await aiomysql.create_pool(
        **db_config,
        autocommit=True,
        minsize=1,
        maxsize=5,
    )


async def close_pool():
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


def _is_query(sql_stripped_upper: str) -> bool:
    return sql_stripped_upper.startswith(_QUERY_PREFIXES)


def _check_single_statement(sql: str) -> str | None:
    trimmed = sql.strip()
    if trimmed.endswith(";"):
        trimmed = trimmed[:-1].strip()
    if ";" in trimmed:
        return "仅支持单条语句执行"
    return None


async def execute_sql(sql: str) -> dict:
    empty_result = {
        "success": False,
        "message": "",
        "duration_ms": 0.0,
        "columns": [],
        "rows": [],
        "affected_rows": 0,
    }

    if not sql or not sql.strip():
        empty_result["message"] = "SQL 语句不能为空"
        return empty_result

    multi_stmt_error = _check_single_statement(sql)
    if multi_stmt_error:
        empty_result["message"] = multi_stmt_error
        return empty_result

    if _pool is None:
        empty_result["message"] = "数据库连接池未初始化"
        return empty_result

    start = time.perf_counter()

    try:
        async with _pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql)

                sql_upper = sql.strip().upper()

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
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "duration_ms": 0.0,
            "columns": [],
            "rows": [],
            "affected_rows": 0,
        }