# 收藏 SQL 功能开发任务清单

## 现有界面设计规范（必须遵循）

| 要素     | 规范                                                                                                |
| -------- | --------------------------------------------------------------------------------------------------- |
| 主题     | 深色模式，三层灰度：`bg-gray-900`(页面) → `bg-gray-800`(容器/输入) → `bg-gray-700`(按钮)            |
| 强调色   | 标题 `text-blue-400`，数据库名 `text-emerald-400`，主按钮 `bg-blue-600`，收藏星标 `text-yellow-400` |
| 布局     | `max-w-3xl mx-auto` 单栏，移动端优先（项目定位：局域网移动端 SQL 控制台）                           |
| 字体     | `font-mono`，正文 `text-sm`                                                                         |
| 交互模式 | 快速标签 = 小圆角按钮组，下拉菜单 = 自定义浮层（参考 CALL PROC 下拉）                               |
| 触控目标 | 移动端友好，按钮最小 `py-1` + `px-3`，主操作按钮 `py-3`                                             |
| 过渡动画 | 统一使用 `transition-colors`，下拉箭头用 `transition-transform`                                     |

---

## 功能概述

将现有的"历史记录"下拉列表替换为"收藏 SQL"下拉列表，支持搜索过滤。在 SQL 输入框旁添加收藏（⭐）按钮，点击后校验 SQL 格式，通过后完成收藏。收藏数据持久化到 `localStorage`，跨会话保留。

---

## 任务分解

### 任务 1：后端 — 新增 SQL 格式校验接口

- **文件**: `mysql_web_console/main.py`
- **内容**:
  - 新增 `POST /api/validate` 路由
  - 接收 `{ "sql": "..." }` 请求体
  - 调用 `db.validate_sql(sql)` 进行校验
  - 返回 `{ "valid": true/false, "message": "..." }`
- **注意**: 路由定义须放在 `app.mount("/static", ...)` 之前

### 任务 2：后端 — 新增 SQL 校验函数

- **文件**: `mysql_web_console/db.py`
- **内容**:
  - 新增 `validate_sql(sql: str) -> dict` 函数
  - 校验逻辑：
    1. 空值检查：SQL 为空 → `{"valid": False, "message": "SQL 语句不能为空"}`
    2. 单语句检查：复用现有 `_check_single_statement()` → 多语句时拒绝
    3. 语法检查：使用 `EXPLAIN` + SQL 执行预检
       - 对 SELECT 语句：执行 `EXPLAIN <原始SQL>`
       - 对非 SELECT 语句：使用 `conn.cursor().execute(sql)` 配合 `conn.rollback()` 回滚，不实际提交
       - 捕获异常，若抛出 ProgrammingError / OperationalError 则返回语法错误信息
    4. 全部通过 → `{"valid": True, "message": "SQL 格式正确"}`
  - 异常兜底：任何未预期异常返回 `{"valid": False, "message": str(e)}`
- **关键**: 校验过程不能对数据库产生副作用，非 SELECT 语句必须回滚

### 任务 3：前端 — 移除历史记录相关代码

- **文件**: `mysql_web_console/static/index.html`
- **内容**:
  - 移除 `history` 响应式变量
  - 移除 `historyOpen` 响应式变量
  - 移除 `addToHistory()` 函数
  - 移除历史记录下拉按钮及浮层的 HTML 模板
  - 移除 `executeSql()` 中调用 `addToHistory()` 的逻辑
  - 移除 `document.addEventListener("click", ...)` 中 `historyOpen` 的关闭逻辑
  - 移除 `return` 对象中的 `history`、`historyOpen` 导出

### 任务 4：前端 — 新增收藏数据管理层

- **文件**: `mysql_web_console/static/index.html`
- **内容**:
  - 新增响应式变量：
    - `favorites` (ref\<Array\>) — 收藏列表，每项结构 `{ id: string, sql: string, createdAt: number }`
    - `favOpen` (ref\<boolean\>) — 收藏下拉开关
    - `favSearch` (ref\<string\>) — 收藏搜索关键词
    - `favLoading` (ref\<boolean\>) — 校验中状态
    - `favToast` (ref\<Object|null\>) — 收藏操作提示，结构 `{ text: string, type: 'success' | 'error' | 'warn' }`
  - 新增计算属性：
    - `filteredFavorites` — 根据 `favSearch` 过滤 `favorites`，支持 SQL 文本模糊匹配
  - 新增 localStorage 持久化函数：
    - `loadFavorites()` — 从 `localStorage.getItem("sql_favorites")` 读取，JSON 解析后赋值给 `favorites`，异常时返回空数组
    - `saveFavorites()` — 将 `favorites` 序列化为 JSON 写入 `localStorage.setItem("sql_favorites", ...)`
  - 新增收藏管理函数：
    - `addFavorite(sqlStr)` — 生成唯一 id（`Date.now().toString(36)`），构造对象插入 `favorites` 头部，调用 `saveFavorites()`
    - `removeFavorite(id)` — 按 id 过滤移除，调用 `saveFavorites()`
  - 初始化：在 `setup()` 中调用 `loadFavorites()`

### 任务 5：前端 — 收藏（⭐）按钮 UI 与交互

- **文件**: `mysql_web_console/static/index.html`
- **位置**: SQL 输入框右上角，覆盖在 textarea 上方
- **UI 设计**:
  - 使用绝对定位放置在 textarea 容器的右上角
  - 外层容器改为 `relative`，textarea 保持不变
  - 按钮样式：`absolute top-2 right-2 w-8 h-8 flex items-center justify-center rounded transition-colors z-10`
  - 默认状态：`text-gray-500 hover:text-yellow-400 hover:bg-gray-700`
  - 收藏中（favLoading）：`text-yellow-400 animate-pulse`
  - 图标：使用 SVG 星形图标（空心星 ☆）
- **交互逻辑**:
  - 点击 ⭐ 按钮触发 `handleFavorite()` 函数：
    1. 前置检查：SQL 输入框为空 → 显示 toast "请先输入 SQL 语句"，return
    2. 去重检查：SQL 已存在于 `favorites` 中 → 显示 toast "该 SQL 已收藏"，return
    3. 设置 `favLoading = true`
    4. 调用 `POST /api/validate`，发送 `{ sql: sql.value.trim() }`
    5. 校验成功（`valid: true`）→ 调用 `addFavorite(sql.value.trim())`，显示 toast "⭐ 收藏成功"
    6. 校验失败（`valid: false`）→ 显示 toast "收藏失败：{message}"
    7. 网络异常 → 显示 toast "校验请求失败"
    8. 最终 `favLoading = false`

### 任务 6：前端 — 收藏 SQL 下拉列表 UI

- **文件**: `mysql_web_console/static/index.html`
- **位置**: 原"历史记录"按钮位置（快速标签栏第二行）
- **UI 设计**:
  - 替换原历史记录按钮为"⭐ 收藏"按钮
  - 按钮样式：`bg-gray-700 hover:bg-gray-600 text-sm px-3 py-1 rounded transition-colors inline-flex items-center gap-1`
  - 按钮文本："⭐ 收藏"，右侧带下拉箭头 SVG（复用 CALL PROC 的箭头）
  - 点击切换 `favOpen` 状态
  - 浮层样式与 CALL PROC 下拉完全一致：`absolute top-full left-0 mt-1 w-72 bg-gray-800 border border-gray-700 rounded shadow-lg z-10 max-h-60 overflow-y-auto`
  - 浮层内容（从上到下）：
    1. **搜索框**：`bg-gray-700 border-b border-gray-600 px-3 py-2 text-sm w-full outline-none`，placeholder "搜索收藏的 SQL..."，绑定 `favSearch`
    2. **收藏列表**：每项为可点击行
       - 左侧显示 SQL 文本（`truncate` 截断），点击后填入 SQL 输入框并关闭下拉
       - 右侧显示删除按钮（✕），点击后调用 `removeFavorite(id)` 移除该项
       - 样式：`flex items-center justify-between px-3 py-2 text-sm hover:bg-gray-700 transition-colors border-b border-gray-700/50 last:border-b-0`
    3. **空状态**：
       - 有收藏但搜索无匹配 → `text-gray-500 text-sm px-3 py-2` "无匹配结果"
       - 无任何收藏 → `text-gray-500 text-sm px-3 py-2` "暂无收藏，点击 ⭐ 收藏 SQL"

### 任务 7：前端 — Toast 提示组件

- **文件**: `mysql_web_console/static/index.html`
- **内容**:
  - 复用现有 `copyToast` 的模式，新增 `favToast` 变量
  - 在 `handleFavorite()` 中设置 `favToast`，2 秒后自动清除
  - Toast 样式与 `copyToast` 一致：`fixed bottom-4 left-1/2 -translate-x-1/2 text-white text-sm px-4 py-2 rounded-lg shadow-lg z-50`
  - 根据 toast 类型区分颜色：
    - 成功（success）：`bg-emerald-600`
    - 失败（error）：`bg-red-600`
    - 提示（warn）：`bg-yellow-600`
  - 实现方式：`favToast` 结构为 `{ text: string, type: 'success' | 'error' | 'warn' } | null`

### 任务 8：前端 — 全局点击关闭与事件整合

- **文件**: `mysql_web_console/static/index.html`
- **内容**:
  - 修改现有 `document.addEventListener("click", ...)` 回调
  - 移除 `historyOpen.value = false`
  - 新增 `favOpen.value = false`
  - 搜索框需添加 `@click.stop` 阻止冒泡（与 CALL PROC 搜索框一致）
  - 删除按钮需添加 `@click.stop` 阻止冒泡，避免触发行点击事件

---

## 执行顺序

| 步骤 | 任务编号 | 说明                                                 |
| ---- | -------- | ---------------------------------------------------- |
| 1    | #2       | 后端新增 SQL 校验函数                                |
| 2    | #1       | 后端注册校验 API 路由                                |
| 3    | #3       | 前端移除历史记录相关代码                             |
| 4    | #4       | 前端新增收藏数据管理层（变量 + localStorage + CRUD） |
| 5    | #5       | 前端收藏按钮 UI 与交互逻辑                           |
| 6    | #6       | 前端收藏下拉列表 UI                                  |
| 7    | #7       | 前端 Toast 提示组件                                  |
| 8    | #8       | 前端全局事件整合                                     |

---

## 涉及文件

| 文件                                  | 修改类型                        |
| ------------------------------------- | ------------------------------- |
| `mysql_web_console/db.py`             | 新增 `validate_sql()` 函数      |
| `mysql_web_console/main.py`           | 新增 `POST /api/validate` 路由  |
| `mysql_web_console/static/index.html` | 移除历史记录 + 新增收藏功能全套 |

---

## 数据结构定义

### 收藏项 (Favorite Item)

```json
{
  "id": "m1a2b3c",
  "sql": "SELECT * FROM users WHERE id = 1;",
  "createdAt": 1718800000000
}
```

### localStorage Key

- 键名：`sql_favorites`
- 值：JSON 序列化的 `Favorite Item[]`

### API 接口

| 方法 | 路径            | 请求体             | 响应体                                |
| ---- | --------------- | ------------------ | ------------------------------------- |
| POST | `/api/validate` | `{ "sql": "..." }` | `{ "valid": true, "message": "..." }` |

---

## 设计一致性检查清单

- [ ] 所有新增颜色使用 `gray-700/800/900` 三层灰度 + `blue/emerald/yellow` 强调色
- [ ] 收藏下拉浮层复用 CALL PROC 下拉的样式和交互模式
- [ ] ⭐ 按钮使用 `text-yellow-400` 作为收藏强调色，与现有色彩体系协调
- [ ] 按钮触控区域足够大，适配移动端
- [ ] 新增组件在 `max-w-3xl` 单栏布局下不溢出
- [ ] 点击外部关闭下拉的行为与 CALL PROC 下拉一致
- [ ] localStorage 读写有异常兜底，不因存储问题导致页面崩溃
- [ ] SQL 校验不产生数据库副作用（非 SELECT 语句需回滚）
