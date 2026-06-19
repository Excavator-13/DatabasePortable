# Tables 面板功能开发任务

## 概述

在 Tab/清空按钮上方添加一个可滑动的数据库表名列表面板，支持点击查看 DESC 结果和 CRUD 骨架填充。

---

## Phase 1: 后端 API

### Task 1.1: 新增 `/api/tables` 接口

- **文件**: `db.py`, `main.py`
- **内容**:
  - `db.py` 新增 `get_tables()` 函数，执行 `SHOW TABLES` 并返回表名列表
  - `main.py` 新增 `GET /api/tables` 路由，调用 `db.get_tables()` 返回 `{"tables": [...]}`
- **验收**: 访问 `/api/tables` 返回当前数据库所有表名数组

### Task 1.2: 新增 `/api/tables/{name}/desc` 接口

- **文件**: `db.py`, `main.py`
- **内容**:
  - `db.py` 新增 `describe_table(table_name)` 函数，执行 `DESC {table_name}` 并返回列信息
  - `main.py` 新增 `GET /api/tables/{name}/desc` 路由
  - 返回格式: `{"columns": [...], "rows": [...]}`，复用现有 execute_sql 的结果结构
- **验收**: 访问 `/api/tables/users/desc` 返回该表的列描述信息

---

## Phase 2: 前端 - 表列表面板 UI

### Task 2.1: 添加表列表面板容器

- **文件**: `static/index.html`
- **位置**: Tab/清空按钮的 `<section>` 上方，新增一个 `<section>`
- **内容**:
  - 固定高度容器（约 180px，可容纳 4-5 行），`overflow-y: auto` 实现内部滚动
  - 使用 Vue 响应式数据 `tableList`、`tableListView`（枚举: `'list'` | `'detail'`）
  - 加载状态显示 skeleton / spinner
  - 空状态提示（无表 / 未连接数据库）
- **关键**: 容器使用固定高度，无论内容多少都不影响下方布局，避免"挤下去"问题

### Task 2.2: 表列表视图

- **文件**: `static/index.html`
- **内容**:
  - 每行一个 table 名，行高 40px+ 适合手指点击
  - 行样式: 左侧表名 + 右侧小箭头指示可点击
  - 点击行 → 调用 `/api/tables/{name}/desc` 获取结构，切换到 detail 视图
  - 样式与现有暗色主题一致（bg-gray-800, hover:bg-gray-700）

### Task 2.3: 表详情视图（DESC 结果 + 返回 + CRUD）

- **文件**: `static/index.html`
- **内容**:
  - 顶部操作栏: 返回按钮（← 返回）+ 4个 CRUD 按钮（SELECT / INSERT / UPDATE / DELETE）
  - 操作栏固定在面板顶部，不随内容滚动
  - 下方为 DESC 结果表格（紧凑样式），在面板剩余空间内滚动
  - 返回按钮点击 → 切回 list 视图
  - CRUD 按钮点击 → 自动填充 SQL 骨架到输入框

### Task 2.4: CRUD 骨架模板逻辑

- **文件**: `static/index.html`
- **内容**:
  - 点击 SELECT 按钮: 填充 `SELECT * FROM {table_name} WHERE <条件>;`
  - 点击 INSERT 按钮: 填充 `INSERT INTO {table_name} (<列名列表>) VALUES (<值占位符>);`
    - 列名从 DESC 结果中提取，VALUES 部分用 `<值>` 标记待填写
  - 点击 UPDATE 按钮: 填充 `UPDATE {table_name} SET <列名>=<值> WHERE <条件>;`
    - SET 部分列出所有列，值用 `<值>` 标记
  - 点击 DELETE 按钮: 填充 `DELETE FROM {table_name} WHERE <条件>;`
  - 自动填入后聚焦 textarea，光标定位到第一个 `<` 占位符处

---

## Phase 3: 数据刷新与联动

### Task 3.1: 初始加载表列表

- **文件**: `static/index.html`
- **内容**:
  - 页面加载时（`fetchDbInfo` 之后）自动调用 `loadTables()`
  - `loadTables()` 调用 `/api/tables` 接口，填充 `tableList`

### Task 3.2: 执行 SQL 后刷新表列表

- **文件**: `static/index.html`
- **内容**:
  - 在 `executeSql()` 成功后，调用 `loadTables()` 刷新列表
  - 如果当前处于 detail 视图，刷新后切回 list 视图（因为表结构可能已变）

### Task 3.3: 切换数据库后刷新

- **文件**: `static/index.html`
- **内容**:
  - 在 `executeSql()` 中检测到 `USE ` 语句成功后，重新加载表列表
  - 重置 `tableListView` 为 `'list'`

---

## Phase 4: 交互细节与优化

### Task 4.1: 防止布局跳动

- **文件**: `static/index.html`
- **内容**:
  - 面板容器使用 `min-h-[180px] max-h-[180px]` 固定高度
  - list 视图和 detail 视图共享同一容器，切换时高度不变
  - detail 视图内部使用 flex 布局：操作栏固定 + 表格区域 flex-1 overflow-y-auto

### Task 4.2: 移动端触摸优化

- **文件**: `static/index.html`
- **内容**:
  - 表名行使用 `-webkit-overflow-scrolling: touch` 优化滑动
  - 行点击区域足够大（min-h-[44px]），符合移动端触摸目标建议
  - CRUD 按钮大小适合手指点击

---

## 执行顺序

Phase 1 → Phase 2 → Phase 3 → Phase 4（严格顺序，后端先行）
