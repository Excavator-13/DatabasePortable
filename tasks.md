# SQL 收藏功能改造计划：localStorage → MySQL + 命名

## 目标

将 SQL 收藏从浏览器 localStorage 迁移到 MySQL 持久化存储，并增加"命名"功能，
收藏下拉列表显示命名而非 SQL 本身。

## 原则

- 不影响现有功能（SQL 执行、表浏览、Procedure 调用、随机数等）
- 保持现有代码风格和架构模式
- 前后端改动最小化

---

## Task 1：db.py — 新增收藏表初始化与 CRUD 函数

### 1.1 新增 `init_favorites_table()` 函数

- 在 `init_pool()` 之后自动调用
- 建表语句：
  ```sql
  CREATE TABLE IF NOT EXISTS __sql_favorites (
      id         INT AUTO_INCREMENT PRIMARY KEY,
      name       VARCHAR(100) NOT NULL,
      sql        TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  )
  ```
- 使用 `IF NOT EXISTS` 确保幂等，不影响用户已有数据

### 1.2 新增收藏 CRUD 函数

- `get_favorites() -> list[dict]` — 查询所有收藏，按 created_at 倒序
- `add_favorite(name: str, sql: str) -> dict` — 新增收藏，返回新增记录
- `remove_favorite(fav_id: int) -> bool` — 按 id 删除收藏
- `search_favorites(keyword: str) -> list[dict]` — 按命名或 SQL 模糊搜索

### 1.3 在 `init_pool()` 末尾调用 `init_favorites_table()`

**涉及文件**：`mysql_web_console/db.py`

---

## Task 2：main.py — 新增收藏 API 路由

### 2.1 新增请求体模型

- `FavoriteRequest`：含 `name` 和 `sql` 两个字段

### 2.2 新增 API 端点

| 方法   | 路径                                | 功能               |
| ------ | ----------------------------------- | ------------------ |
| GET    | `/api/favorites`                    | 获取所有收藏       |
| POST   | `/api/favorites`                    | 新增收藏（含命名） |
| DELETE | `/api/favorites/{id}`               | 删除收藏           |
| GET    | `/api/favorites/search?keyword=xxx` | 搜索收藏           |

### 2.3 新增收藏时保留 SQL 校验

- 复用现有 `db.validate_sql()` 校验语法
- 校验通过后再存入

**涉及文件**：`mysql_web_console/main.py`

---

## Task 3：index.html — 前端改造

### 3.1 移除 localStorage 相关逻辑

- 删除 `loadFavorites()`、`saveFavorites()` 函数
- 删除 `localStorage.getItem/setItem` 调用

### 3.2 改造收藏交互流程

- 点击 ⭐ 收藏按钮 → 弹出输入框让用户输入命名 → 提交到后端
- 收藏下拉列表：显示命名（name），点击后将对应 SQL 填入输入框
- 搜索过滤：同时匹配 name 和 sql

### 3.3 改造 `handleFavorite()` 函数

- 弹出命名输入（内联输入框或小型弹窗，不用 alert/prompt）
- 调用 `POST /api/favorites` 提交 `{ name, sql }`

### 3.4 改造 `loadFavorites()` → 改为从 API 加载

- 页面初始化时调用 `GET /api/favorites`
- 赋值给 `favorites` ref

### 3.5 改造 `removeFavorite()`

- 调用 `DELETE /api/favorites/{id}`

### 3.6 改造 `filteredFavorites` 计算属性

- 搜索同时匹配 `name` 和 `sql`

### 3.7 收藏下拉列表 UI 调整

- 每条收藏显示：命名（主文字）+ SQL 预览（次要文字，截断显示）
- 保持现有暗色风格和交互模式

**涉及文件**：`mysql_web_console/static/index.html`

---

## Task 4：验证与清理

### 4.1 功能验证清单

- [x] 新增收藏（输入命名 + SQL）→ 成功存入 MySQL
- [x] 收藏列表正确显示命名
- [x] 点击收藏项 → SQL 正确填入输入框
- [x] 搜索收藏 → 按命名和 SQL 均可匹配
- [x] 删除收藏 → 从列表和数据库移除
- [x] 重复 SQL 收藏 → 允许（不同命名即可）
- [ ] SQL 执行功能不受影响
- [ ] 表浏览功能不受影响
- [ ] Procedure 调用功能不受影响
- [ ] 随机数功能不受影响

### 4.2 清理

- [x] 移除所有 localStorage 相关代码
- [x] 确认无残留的死代码

---

## 风险与注意事项

1. **建表位置**：`__sql_favorites` 表建在用户配置的数据库中，使用双下划线前缀避免与业务表冲突
2. **并发安全**：收藏操作频率极低，无需加锁
3. **向后兼容**：localStorage 中的旧收藏不会自动迁移（可后续加迁移逻辑，但非必须）
4. **命名唯一性**：不强制命名唯一，允许不同收藏使用相同命名
