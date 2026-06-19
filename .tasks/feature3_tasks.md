# 存储过程结果集与 OUT 参数修复 — 开发任务

## 目标

1. 存储过程内部 SELECT 产生的结果集能正确返回并展示，行为与直接 SELECT 一致
2. OUT 参数自动填写为 `@{参数名}_auto`，执行后自动查询并以独立表格外显参数名与值
3. SELECT 结果集与 OUT 参数表同时存在时互不冲突，分区展示

---

## 任务一：后端 — 识别 CALL 语句并获取结果集

**文件**: `mysql_web_console/db.py`

- 在 `execute_sql` 中新增对 `CALL` 语句的识别分支
- `CALL` 语句执行后，检查 `cursor.description` 是否存在：
  - 存在 → 说明有 SELECT 结果集，用 `fetchall` 获取，行为与普通 SELECT 一致
  - 不存在 → 无结果集
- 从 CALL 语句中解析出所有 `@xxx_auto` 形式的 OUT 参数变量名
- 执行 `SELECT @xxx_auto, @yyy_auto, ...` 获取 OUT 参数值
- 将结果集与 OUT 参数值统一封装返回

### 返回结构变更

原结构：

```json
{
  "success": true,
  "columns": [...],
  "rows": [...],
  "affected_rows": 0
}
```

新增 `out_params` 字段：

```json
{
  "success": true,
  "columns": [...],
  "rows": [...],
  "affected_rows": 0,
  "out_params": [
    {"name": "xxx", "value": "123"},
    {"name": "yyy", "value": null}
  ]
}
```

非 CALL 语句时 `out_params` 为空列表 `[]`，不影响现有逻辑。

---

## 任务二：后端 — 解析 CALL 语句中的 OUT 参数变量

**文件**: `mysql_web_console/db.py`

- 新增辅助函数 `_parse_out_params(sql: str) -> list[str]`
- 从 CALL 语句中提取所有 `@xxx_auto` 模式的变量名
- 使用正则 `r@(\w+_auto)\b` 匹配
- 返回变量名列表（不含 `@` 前缀），如 `["xxx_auto", "yyy_auto"]`
- 参数原名通过去掉 `_auto` 后缀还原，如 `xxx_auto` → `xxx`

---

## 任务三：后端 — CALL 语句执行后自动查询 OUT 参数值

**文件**: `mysql_web_console/db.py`

- 在 CALL 执行完毕、结果集获取之后，若解析到 OUT 参数变量：
  - 构造 `SELECT @xxx_auto AS xxx, @yyy_auto AS yyy`
  - 使用同一连接执行该 SELECT（确保会话变量可访问）
  - 获取单行结果，组装为 `out_params` 列表
- 此 SELECT 为内部生成，不受 `_check_single_statement` 限制

---

## 任务四：前端 — OUT 参数自动填写为 `{参数名}_auto`

**文件**: `mysql_web_console/static/index.html`

- 修改 `selectProcedure` 函数中 OUT 参数的拼接逻辑
- 原逻辑：`p.direction === "OUT" ? "@" + p.name : ...`
- 新逻辑：`p.direction === "OUT" ? "@" + p.name + "_auto" : ...`
- 生成示例：`CALL my_proc(<input_val>, @xxx_auto);`

---

## 任务五：前端 — OUT 参数表格展示

**文件**: `mysql_web_console/static/index.html`

- 在结果区域中，当 `result.out_params` 非空时，渲染独立的 OUT 参数表格
- 表格结构：两列（参数名 | 值），与 SELECT 结果集表格视觉分离
- 展示顺序：先展示 SELECT 结果集表格，再展示 OUT 参数表格
- OUT 参数表格标题标注"OUT 参数"，避免与 SELECT 结果混淆
- NULL 值显示为灰色斜体 `NULL`，与 SELECT 结果集行为一致

---

## 任务六：前端 — 状态提示文案适配

**文件**: `mysql_web_console/static/index.html`

- 顶部成功提示栏需同时体现结果集行数与 OUT 参数数量
- 示例：
  - 仅有结果集：`查询成功，耗时 xx ms，共 N 行`
  - 仅有 OUT 参数：`执行成功，返回 N 个 OUT 参数，耗时 xx ms`
  - 两者均有：`查询成功，共 N 行，返回 M 个 OUT 参数，耗时 xx ms`

---

## 执行顺序

1 → 2 → 3 → 4 → 5 → 6（按序执行，后端先行，前端跟进）
