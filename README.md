# MySQL Web Console

局域网 MySQL 移动端 Web 控制台 —— 一个轻量级的本地 Web 应用，运行在电脑上，允许同一局域网内的手机通过浏览器直接执行 SQL 语句并操作 MySQL 数据库。

## 功能特性

- 📱 移动端优先的暗色模式 UI
- ⇥ Tab 缩进按钮，方便手机端在 SQL 中插入缩进保持格式美观
- 📜 最近 5 条历史记录快速恢复
- 📊 查询结果表格展示，支持横向滚动与斑马纹
- 🔒 单语句安全限制，防止批量执行
- ⏱️ 执行耗时实时反馈
- 🗄️ 当前数据库实时显示
- 📞 支持浏览并快速生成 `CALL PROCEDURE` 语句（自动识别 IN/OUT 参数）
- 🎲 内置随机数生成器（1 ~ N 范围）
- ⌨️ `Ctrl+Enter` / `Cmd+Enter` 快捷执行，`Tab` 键直接插入缩进

## 技术栈

- **后端**: Python 3.10+, FastAPI, Uvicorn, aiomysql
- **前端**: Vue 3 (CDN), Tailwind CSS (CDN)
- **配置管理**: python-dotenv

## 项目结构

```
mysql_web_console/
├── main.py              # FastAPI 应用入口及路由
├── db.py                # 数据库连接池与执行逻辑
├── config.py            # 读取 .env 配置
├── .env.example         # 环境变量示例
├── requirements.txt     # Python 依赖
└── static/
    └── index.html       # 移动端优先的单页前端
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
```

### 4. 启动项目

```bash
python main.py
```

终端将显示：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 5. 在手机上访问

1. 确保手机和电脑连接**同一 Wi-Fi**
2. 在电脑终端查看局域网 IP：

```bash
# macOS
ipconfig getifaddr en0
# Linux
hostname -I
# Windows
ipconfig
```

3. 在手机浏览器输入：`http://<你的局域网IP>:8000`

## API 接口

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
  "affected_rows": 0
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
    { "name": "user_id", "direction": "IN" },
    { "name": "result", "direction": "OUT" }
  ]
}
```

## 安全说明

- 仅支持单条 SQL 语句执行，自动拒绝含多条语句的请求
- 空值与纯空格输入会被拦截
- 所有数据库异常均被捕获并格式化返回，不会导致服务崩溃
- 本项目设计为局域网内使用，请勿暴露到公网
