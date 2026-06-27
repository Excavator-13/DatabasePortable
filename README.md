# MySQL Web Console

局域网 MySQL 移动端 Web 控制台 —— 一个轻量级的本地 Web 应用，运行在电脑上，允许同一局域网内的手机通过浏览器直接执行 SQL 语句并操作 MySQL 数据库。

## 功能特性

- 📱 移动端优先的暗色模式 UI
- 🔐 可选登录认证模式（`REQUIRE_LOGIN=true`），支持 Web 端输入连接信息登录、Token 鉴权、记住登录、退出登录
- 🗄️ 数据库表列表面板，点击查看表结构（DESC），一键生成 SELECT / INSERT / UPDATE / DELETE 骨架语句
- 📞 浏览并快速生成 `CALL PROCEDURE` 语句（自动识别 IN/OUT/INOUT 参数，OUT 参数自动查询并独立展示，INOUT 参数自动 SET 赋值并回读）
- ⭐ SQL 收藏功能，支持命名收藏，收藏数据持久化到 MySQL，支持按命名和 SQL 搜索过滤，收藏前自动校验语法，校验未通过时可选择强制收藏
- ⇥ Tab 缩进按钮，方便手机端在 SQL 中插入缩进保持格式美观
- ' ' 引号按钮，在光标处插入单引号对并自动选中中间位置，方便输入字符串值
- ✕ 清空按钮，一键清空 SQL 输入框
- 📊 查询结果表格展示，支持横向滚动与斑马纹
- 📋 结果导出：复制 Markdown 表格 / 下载 CSV（支持 SELECT 结果集与 OUT 参数表）
- 🔒 单语句安全限制，防止批量执行
- ⏱️ 执行耗时实时反馈
- 🗄️ 当前数据库实时显示
- 🎲 内置随机数生成器（1 ~ N 范围）
- ⌨️ `Ctrl+Enter` / `Cmd+Enter` 快捷执行，`Tab` 键直接插入缩进

## 技术栈

- **后端**: Python 3.10+, FastAPI, Uvicorn, aiomysql, cryptography
- **前端**: Vue 3 (CDN), Tailwind CSS (CDN)
- **配置管理**: python-dotenv

## 项目结构

```
DatabasePortable/
├── start.sh                     # macOS/Linux 一键启动脚本（后台守护模式）
├── stop.sh                      # macOS/Linux 一键停止脚本
├── start.bat                    # Windows 一键启动脚本（后台运行）
├── stop.bat                     # Windows 一键停止脚本
├── mysql_web_console/
│   ├── main.py                  # FastAPI 应用入口及路由
│   ├── db.py                    # 数据库连接池与执行逻辑
│   ├── config.py                # 读取 .env 配置
│   ├── .env.example             # 环境变量示例
│   ├── requirements.txt         # Python 依赖
│   └── static/
│       └── index.html           # 移动端优先的单页前端
```

## 快速开始

### 1. 创建并激活虚拟环境

```bash
cd mysql_web_console
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 .env 文件

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 MySQL 连接信息：

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的密码
DB_NAME=你的数据库名
REQUIRE_LOGIN=false
```

> **登录认证模式**：将 `REQUIRE_LOGIN` 设为 `true` 时，应用启动后不会自动连接数据库，而是展示登录页面，用户在 Web 端输入 MySQL 连接信息后登录使用。设为 `false`（默认）时，应用启动时自动使用 `.env` 中的配置连接数据库，无需登录。

### 4. 启动与停止

#### 日常使用（推荐）

使用项目根目录的脚本，一键后台启动 / 停止：

**macOS / Linux：**

```bash
# 启动服务（后台运行，自动激活虚拟环境）
./start.sh

# 停止服务（优雅停止，超时后强制终止）
./stop.sh
```

**Windows：**

```cmd
# 启动服务（后台运行，自动激活虚拟环境）
start.bat

# 停止服务（优雅停止，超时后强制终止）
stop.bat
```

启动成功后终端会显示 PID 和访问地址，日志输出到 `mysql_web_console/app.log`。

#### 开发调试

如需前台运行（可实时查看日志输出，Ctrl+C 停止）：

```bash
cd mysql_web_console
source venv/bin/activate
python main.py
```

### 5. 在手机上访问

1. 确保手机和电脑连接**同一 Wi-Fi**
2. 启动服务后，终端会自动显示局域网访问地址（如 `http://192.168.1.x:8000`）
3. 在手机浏览器输入该地址即可访问

如需手动查看局域网 IP：

```bash
# macOS
ipconfig getifaddr en0
# Linux
hostname -I
# Windows
ipconfig
```

## API 接口

### 认证状态查询

`GET /api/auth-status`

无需认证即可访问。

**响应体**：

```json
{
  "require_login": true,
  "authenticated": false
}
```

### 登录

`POST /api/login`

无需认证即可访问。仅在 `REQUIRE_LOGIN=true` 模式下使用。

**请求体**：

```json
{
  "host": "127.0.0.1",
  "port": 3306,
  "user": "root",
  "password": "your_password",
  "db": "your_database"
}
```

**响应体（成功）**：

```json
{
  "success": true,
  "token": "a1b2c3d4..."
}
```

**响应体（失败）**：

```json
{
  "success": false,
  "message": "连接失败: ..."
}
```

### 退出登录

`POST /api/logout`

需要 Bearer Token 认证。退出后 Token 失效，连接池销毁。

**响应体**：

```json
{
  "success": true
}
```

### 获取当前数据库

`GET /api/info`

**响应体**：

```json
{
  "database": "mydb"
}
```

### 执行 SQL 语句

`POST /api/execute`

**请求体**：

```json
{
  "sql": "SELECT * FROM users LIMIT 10;"
}
```

**响应体**：

```json
{
  "success": true,
  "message": "查询成功，共返回 2 行数据",
  "duration_ms": 15.2,
  "columns": ["id", "name"],
  "rows": [
    [1, "Alice"],
    [2, "Bob"]
  ],
  "affected_rows": 0,
  "out_params": []
}
```

### 校验 SQL 语法

`POST /api/validate`

**请求体**：

```json
{
  "sql": "SELECT * FROM users WHERE id = 1;"
}
```

**响应体**：

```json
{
  "valid": true,
  "message": "SQL 格式正确"
}
```

### 获取表列表

`GET /api/tables`

**响应体**：

```json
{
  "tables": ["users", "orders", "products"]
}
```

### 获取表结构

`GET /api/tables/{name}/desc`

**响应体**：

```json
{
  "success": true,
  "message": "查询成功",
  "columns": ["Field", "Type", "Null", "Key", "Default", "Extra"],
  "rows": [
    ["id", "int", "NO", "PRI", null, "auto_increment"],
    ["name", "varchar(255)", "YES", "", null, ""]
  ]
}
```

### 获取所有 Stored Procedures

`GET /api/procedures`

**响应体**：

```json
{
  "procedures": ["proc_get_user", "proc_update_status"]
}
```

### 获取 Procedure 参数信息

`GET /api/procedures/{name}/params`

**响应体**：

```json
{
  "params": [
    { "name": "user_id", "type": "int", "direction": "IN" },
    { "name": "result", "type": "int", "direction": "OUT" },
    { "name": "counter", "type": "int", "direction": "INOUT" }
  ]
}
```

### 获取所有收藏

`GET /api/favorites`

**响应体**：

```json
{
  "favorites": [
    {
      "id": 1,
      "name": "查询用户",
      "sql": "SELECT * FROM users LIMIT 10;",
      "created_at": "2026-06-21 12:00:00"
    }
  ]
}
```

### 新增收藏

`POST /api/favorites`

**请求体**：

```json
{
  "name": "查询用户",
  "sql": "SELECT * FROM users LIMIT 10;",
  "force": false
}
```

- `force`（可选，默认 `false`）：设为 `true` 时跳过 SQL 语法校验，强制收藏。当 `force=false` 且校验未通过时，响应中会包含 `validation_error: true`，前端可据此提示用户选择是否强制收藏。

**响应体（成功）**：

```json
{
  "success": true,
  "favorite": {
    "id": 1,
    "name": "查询用户",
    "sql": "SELECT * FROM users LIMIT 10;",
    "created_at": "2026-06-21 12:00:00"
  }
}
```

**响应体（校验未通过）**：

```json
{
  "success": false,
  "message": "SQL 校验未通过: ...",
  "validation_error": true
}
```

### 删除收藏

`DELETE /api/favorites/{id}`

**响应体**：

```json
{
  "success": true
}
```

### 搜索收藏

`GET /api/favorites/search?keyword=用户`

按命名或 SQL 内容模糊搜索。

**响应体**：

```json
{
  "favorites": [
    {
      "id": 1,
      "name": "查询用户",
      "sql": "SELECT * FROM users LIMIT 10;",
      "created_at": "2026-06-21 12:00:00"
    }
  ]
}
```

### Procedure 参数处理机制

| 参数方向 | 生成格式         | 执行行为                                                                                            |
| -------- | ---------------- | --------------------------------------------------------------------------------------------------- |
| IN       | `<参数名>`       | 用户填入值，直接传入                                                                                |
| OUT      | `@参数名_auto`   | 自动生成会话变量，执行后 SELECT 回读                                                                |
| INOUT    | `<@参数名_auto>` | 用户填入值（如 `100`），后端自动 `SET @参数名_auto = 100` → `CALL proc(@参数名_auto)` → SELECT 回读 |

**INOUT 执行流程**：用户输入 `CALL proc(100)`，后端识别 INOUT 参数后，在同一连接内依次执行 `SET @counter_auto = 100`、`CALL proc(@counter_auto)`、`SELECT @counter_auto`，实现传入初值并回读返回值。

## 安全说明

- 仅支持单条 SQL 语句执行，自动拒绝含多条语句的请求
- 空值与纯空格输入会被拦截
- SQL 校验接口对非 SELECT 语句使用事务回滚，不产生数据库副作用
- 所有数据库异常均被捕获并格式化返回，不会导致服务崩溃
- 支持 `REQUIRE_LOGIN` 登录认证模式：启用后所有 API 请求需携带 Bearer Token，Token 由服务端随机生成，连接断开后自动失效
- 登录凭据仅用于直连 MySQL，不经过第三方服务
- 本项目设计为局域网内使用，请勿暴露到公网
