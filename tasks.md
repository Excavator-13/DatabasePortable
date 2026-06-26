# 登录模式开发计划

## 概述

在现有 MySQL Web Console 基础上增加可选登录模式。通过 `.env` 中 `REQUIRE_LOGIN` 开关控制：关闭时保持原有直接连接行为；开启时前端展示登录页面，用户手动输入数据库凭据后建立连接。支持"记住登录"功能，凭据存储于浏览器 localStorage。

**核心原则：`REQUIRE_LOGIN=false` 时所有行为与现有完全一致，零影响。**

---

## Phase 1：后端 — 配置与认证基础设施

### Task 1.1：扩展 `.env` 与 `config.py` ✅

- 在 `.env` 和 `.env.example` 中新增 `REQUIRE_LOGIN=false`
- `config.py` 读取 `REQUIRE_LOGIN` 布尔值，暴露为 `require_login`
- 保留现有 `db_config` 不变（`REQUIRE_LOGIN=false` 时仍使用）

### Task 1.2：修改应用生命周期 `main.py` ✅

- `REQUIRE_LOGIN=false`：行为不变，启动时 `init_pool()`
- `REQUIRE_LOGIN=true`：启动时跳过 `init_pool()`，连接池延迟到登录后创建
- 新增 `db.init_pool_with_config(config_dict)` 函数，接受外部传入的连接参数

### Task 1.3：新增登录相关 API ✅

- `GET /api/auth-status`：返回 `{ require_login: bool, authenticated: bool }`
  - `require_login` 来自 `config.require_login`
  - `authenticated` 判断连接池是否已初始化（`_pool is not None`）
- `POST /api/login`：请求体 `{ host, port, user, password, db }`
  - 用传入参数尝试创建连接池（`aiomysql.create_pool`）
  - 成功则生成随机 session token（`secrets.token_hex(32)`），存入内存 dict
  - 返回 `{ success: true, token: "..." }`
  - 失败则返回 `{ success: false, message: "连接失败: ..." }`
- `POST /api/logout`：销毁当前连接池，清除 session token

### Task 1.4：API 鉴权中间件 ✅

- 当 `REQUIRE_LOGIN=true` 时，除 `/api/auth-status`、`/api/login`、`/`、静态资源外的所有 API 需携带 `Authorization: Bearer <token>` 头
- token 不匹配或缺失返回 `401 Unauthorized`，前端据此跳转登录页
- `REQUIRE_LOGIN=false` 时中间件不拦截
- 连接池失效时即使 token 有效也返回 401，提示"连接已断开，请重新登录"

### Task 1.5：`db.py` 适配 ✅

- 新增 `init_pool_with_config(config: dict)` 函数，与 `init_pool()` 逻辑相同但接受外部配置
- 新增 `is_pool_ready() -> bool` 函数，返回 `_pool is not None`
- 新增 `destroy_pool()` 函数，关闭并清空连接池
- `close_pool()` 改为调用 `destroy_pool()`，消除重复代码
- 确保所有现有函数在 `_pool is None` 时优雅返回（已有此逻辑，已确认覆盖）

---

## Phase 2：前端 — 登录页面

### Task 2.1：登录页 UI ✅

- 在 Vue app 中新增 `loginView` 状态，与主控台视图互斥
- 登录页包含：Host、Port、User、Password、Database 五个输入框
- "记住登录" 复选框（默认不勾选）
- "登录" 按钮，加载时显示 spinner
- 错误提示区域（红色，与现有错误样式一致）
- 整体风格延续暗色主题，居中卡片式布局，移动端友好

### Task 2.2：localStorage 凭据管理 ✅

- 存储键名：`mwc_credentials`
- 勾选"记住登录"时：登录成功后将 `{ host, port, user, password, db }` 写入 localStorage
- 不勾选"记住登录"时：登录成功后从 localStorage 删除 `mwc_credentials`
- 页面加载时：若 localStorage 中有凭据，自动填入表单并勾选复选框
- 密码字段：填入后仍以 `type="password"` 显示，需手动查看

### Task 2.3：登录流程逻辑 ✅

- 页面加载时调用 `GET /api/auth-status`
  - `require_login=false`：直接进入主控台，加载数据
  - `require_login=true && authenticated=true`：检查 localStorage token，有效则进入主控台
  - `require_login=true && authenticated=false`：显示登录页
- 登录提交：`POST /api/login`，成功后将 token 存入 localStorage（键 `mwc_token`）
- 所有 API 请求通过 `authedFetch` 统一携带 token
- 401 响应自动跳转登录页，读取后端返回的具体错误信息展示
- 登录页中，若 localStorage 有凭据则自动填入，用户只需点"登录"

### Task 2.4：登出功能 ✅

- 主控台 header 区域新增登出按钮（仅 `REQUIRE_LOGIN=true` 时显示）
- 点击后调用 `POST /api/logout`，清除 localStorage 中的 `mwc_token`
- 跳转回登录页，清空当前数据库状态

---

## Phase 3：集成与打磨

### Task 3.1：收藏夹兼容性 ✅

- 收藏夹表 `__sql_favorites` 保持现有结构，不增加帐号字段
- 所有登录用户共享同一收藏夹，符合"能登录就互通"的需求
- 无需修改收藏夹相关 API 和前端逻辑

### Task 3.2：连接断开处理 ✅

- 后端中间件增加连接池就绪检查：token 有效但连接池失效时返回 401
- 前端 `authedFetch` 拦截 401，读取后端具体错误信息（"连接已断开"或"未授权"）
- 自动清除 token 并跳转登录页
- `REQUIRE_LOGIN=false` 时显示错误信息即可（后端自行重连）

### Task 3.3：安全细节 ✅

- session token 使用 `secrets.token_hex(32)` 生成，足够随机
- 后端内存中存储 token，服务重启后失效（需重新登录）
- localStorage 中的密码为明文——与 `.env` 文件明文存储一致，风险等级相同
- 后续如需加密可引入 AES 加密存储，本期不做

### Task 3.4：移动端体验优化 ✅

- 登录表单在移动端全宽显示，输入框足够大（min-height 44px）
- Password 输入框增加显示/隐藏切换按钮（眼睛图标）
- Port 输入框使用 `inputmode="numeric"`
- 登录页底部显示简短说明文字

---

## 文件变更清单

| 文件                                  | 变更类型 | 说明                                                          |
| ------------------------------------- | -------- | ------------------------------------------------------------- |
| `mysql_web_console/.env`              | 修改     | 新增 `REQUIRE_LOGIN=false`                                    |
| `mysql_web_console/.env.example`      | 修改     | 新增 `REQUIRE_LOGIN=false`                                    |
| `mysql_web_console/config.py`         | 修改     | 读取 `REQUIRE_LOGIN`，暴露 `require_login`                    |
| `mysql_web_console/db.py`             | 修改     | 新增 `init_pool_with_config`、`is_pool_ready`、`destroy_pool` |
| `mysql_web_console/main.py`           | 修改     | 条件初始化池、新增登录/登出/状态 API、鉴权中间件              |
| `mysql_web_console/static/index.html` | 修改     | 新增登录页视图、localStorage 管理、API 拦截、登出按钮         |

---

## 开发顺序建议

1. **Task 1.1 → 1.2 → 1.5**：后端配置与数据库层适配（无破坏性变更）
2. **Task 1.3 → 1.4**：后端认证 API 与中间件
3. **Task 2.1 → 2.2 → 2.3**：前端登录页核心功能
4. **Task 3.1 → 3.2**：集成验证与错误处理
5. **Task 2.4 → 3.4**：登出与体验打磨
6. **Task 3.3**：安全审查（贯穿开发过程）
