# API Contract - 局域网 MySQL Web 控制台

## 1. 概述

本文档定义了 MySQL Web Console 后端服务的 API 接口规范。后端基于 FastAPI 构建，前端（移动端网页）将通过这些 API 提交 SQL 并获取执行结果。

- **Base URL**: `http://<your_local_ip>:8000`
- **Content-Type**: `application/json`
- **字符编码**: `UTF-8`

---

## 2. 接口列表

### 2.1 获取前端页面

- **Method & Path**: `GET /`
- **描述**: 返回前端单页应用 HTML。
- **Response**: `text/html` (直接返回 `static/index.html` 内容)

---

### 2.2 执行 SQL 语句 (核心接口)

- **Method & Path**: `POST /api/execute`
- **描述**: 接收前端传来的单条 SQL 语句，在配置的 MySQL 数据库中执行，并返回结构化的执行结果。

#### 2.2.1 请求参数

| 参数名 | 类型   | 必填 | 说明                                              |
| :----- | :----- | :--- | :------------------------------------------------ |
| sql    | string | 是   | 要执行的 SQL 语句。**注意：仅支持单条语句执行。** |

**请求示例 (Request Body):**

```json
{
  "sql": "SELECT id, username, email FROM users LIMIT 5;"
}
```

#### 2.2.2 响应格式

所有响应均返回 HTTP 状态码 `200`，通过 JSON Body 中的 `success` 字段判断业务是否成功。这种设计便于前端统一拦截和处理。
**通用响应 Schema:**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| success | boolean | 是 | true 表示执行成功；false 表示执行失败（如语法错误、连接失败）。 |
| message | string | 是 | 执行结果的描述信息。 |
| duration_ms | float | 是 | SQL 执行耗时，单位毫秒 (保留1位小数)。失败时为 `0.0`。 |
| columns | string[] | 否 | 查询语句返回的列名数组。仅 `SELECT` 语句有此字段，失败或非查询语句为空数组 `[]`。 |
| rows | any[][] | 否 | 查询返回的数据二维数组（行数据 -> 列值）。仅 `SELECT` 语句有此字段，失败或非查询语句为空数组 `[]`。 |
| affected_rows | integer | 否 | 受影响的行数。仅 `INSERT/UPDATE/DELETE` 语句有此字段，查询语句或失败时为 `0`。 |

---

#### 2.2.3 响应示例

**场景 A：成功执行查询语句 (SELECT)**

```json
{
  "success": true,
  "message": "查询成功，共返回 2 行数据",
  "duration_ms": 15.2,
  "columns": ["id", "username", "email"],
  "rows": [
    [1, "alice", "alice@example.com"],
    [2, "bob", "bob@example.com"]
  ],
  "affected_rows": 0
}
```

**场景 B：成功执行非查询语句 (INSERT/UPDATE/DELETE)**

```json
{
  "success": true,
  "message": "执行成功",
  "duration_ms": 8.5,
  "columns": [],
  "rows": [],
  "affected_rows": 1
}
```

**场景 C：执行失败 (语法错误 / 数据库错误)**

```json
{
  "success": false,
  "message": "(1064, \"You have an error in your SQL syntax; check the manual...\")",
  "duration_ms": 0.0,
  "columns": [],
  "rows": [],
  "affected_rows": 0
}
```

**场景 D：请求参数错误 (前端未传 SQL 或为空字符串)**
HTTP Status 422 (FastAPI 默认行为) 或 返回:

```json
{
  "success": false,
  "message": "SQL 语句不能为空",
  "duration_ms": 0.0,
  "columns": [],
  "rows": [],
  "affected_rows": 0
}
```

---

## 3. 业务逻辑与安全约束

1. **单语句限制**: 前端传入的 SQL 必须作为单条语句执行。如果后端检测到包含多个分号结尾的语句（`SELECT 1; SELECT 2;`），应予以拒绝或在执行时只执行第一条，并在 `message` 中给出提示。**严禁使用允许执行多语句的驱动配置。**
2. **空值处理**: 如果前端传入空字符串或纯空格，后端应直接返回失败状态，不发起数据库连接。
3. **异常捕获**: 后端必须使用 `try-except` 捕获 `aiomysql` 抛出的所有异常，将异常信息格式化为字符串放入 `message` 字段，绝不能让后端服务抛出 500 错误导致崩溃。
4. **SQL 类型判定**: 后端通过解析 SQL 字符串的开头（去除空格并转大写）来判断是查询还是非查询操作：
   - 以 `SELECT`, `SHOW`, `DESC`, `EXPLAIN` 开头视为查询，使用 `fetchall()` 获取数据。
   - 其他视为非查询，使用 `cursor.rowcount` 获取受影响行数。
