# INOUT 参数支持开发计划

## 目标

为存储过程的 INOUT 参数提供完整支持：用户传入字面值，后端自动 SET → CALL → SELECT 回读。

## 方案

用户在 CALL 中为 INOUT 参数传入字面值（如 `100`），后端在**同一连接内**依次执行：

1. `SET @param_auto = 100`（将字面值赋给会话变量）
2. `CALL proc(@param_auto, ...)`（用变量替代字面值执行）
3. `SELECT @param_auto AS param`（回读过程修改后的值）

这不是多语句提交，而是同一连接上的多次 `cursor.execute()`，与现有 OUT 参数的 SELECT 回读机制一致。

## 影响范围

仅涉及 INOUT 参数的处理逻辑，不改动任何 IN、OUT、内部 SELECT 外显的现有行为。

---

## Task 1: 前端 — selectProcedure 中 INOUT 参数生成逻辑 ✅

**文件**: `mysql_web_console/static/index.html`
**位置**: `selectProcedure` 函数内的 `params.map(...)` 回调

**改动**: 新增 INOUT 分支，生成 `<@name_auto>` 格式：

```javascript
const args = params.map((p) => {
  if (p.direction === "OUT") return "@" + p.name + "_auto";
  if (p.direction === "INOUT") return "<@" + p.name + "_auto>";
  return "<" + p.name + ">";
});
```

**三种参数的生成结果**:
| direction | 生成内容 | 示例 |
|-----------|---------|------|
| IN | `<参数名>` | `<p_name>` （不变） |
| OUT | `@参数名_auto` | `@p_name_auto` （不变） |
| INOUT | `<@参数名_auto>` | `<@p_count_auto>` （新增） |

---

## Task 2: 后端 — 新增 \_parse_call_args 辅助函数 ✅

**文件**: `mysql_web_console/db.py`

**功能**: 解析 CALL 语句，提取存储过程名和参数列表。

**实现**: 状态机逐字符扫描，正确处理引号字符串、嵌套括号、逗号分隔。

---

## Task 3: 后端 — 新增 \_get_proc_params_on_conn 辅助函数 ✅

**文件**: `mysql_web_console/db.py`

**功能**: 在当前连接上查询指定存储过程的参数元数据（名称 + 方向），复用 `information_schema.PARAMETERS` 查询。

---

## Task 4: 后端 — execute_sql CALL 分支 INOUT 处理 ✅

**文件**: `mysql_web_console/db.py`
**位置**: `execute_sql` 函数的 CALL 分支

**改动流程**:

1. 解析 CALL 语句获取过程名和参数列表
2. 查询参数元数据，找出 INOUT 参数
3. 对 INOUT 位置的字面值参数：生成 `SET @name_auto = 值`，将 CALL 中的字面值替换为 `@name_auto`
4. 先执行 SET，再执行（可能修改过的）CALL
5. 用 `actual_sql`（而非原始 sql）调用 `_parse_out_params`，确保 INOUT 变量也被回读

**无 INOUT 参数或 INOUT 已是 @var 时**：不修改 SQL，行为与原来完全一致。

---

## 风险控制

| 检查项                  | 说明                                                         |
| ----------------------- | ------------------------------------------------------------ |
| IN 参数行为             | 前端仍生成 `<name>` 占位符，后端不处理 IN 方向参数           |
| OUT 参数行为            | 前端仍生成 `@name_auto`，后端 OUT 不走 SET 逻辑              |
| 内部 SELECT 外显        | `cursor.description` + `nextset()` 逻辑不变                  |
| 后端 \_parse_out_params | 正则和 SELECT 回读逻辑不变，仅输入从 `sql` 改为 `actual_sql` |
| 无 INOUT 的 CALL        | `inout_set_vars` 为空，`actual_sql == sql`，行为完全不变     |
| 单语句检查              | 不涉及，后端内部多次 execute 不是多语句提交                  |
| 元数据查询失败          | try/except 兜底，回退到原始 SQL 执行                         |
