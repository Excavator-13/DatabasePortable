# 局域网 MySQL 移动端 Web 控制台 (MySQL Web Console)

## 1. 项目概述

这是一个轻量级的本地 Web 应用，运行在电脑上，允许同一局域网内的手机通过浏览器访问网页，直接执行 SQL 语句并操作 MySQL 数据库。项目需提供良好的移动端适配、便捷的输入方式、清晰的数据展示和及时的操作反馈。

## 2. 技术栈

- **后端**: Python 3.10+, FastAPI, Uvicorn, aiomysql (异步MySQL驱动)
- **前端**: 单页 HTML (Vue 3 via CDN, Tailwind CSS via CDN)
- **配置管理**: python-dotenv
- **部署环境**: 本地局域网 (需绑定到 `0.0.0.0`)

## 3. 项目结构

请按照以下结构生成文件：

```text
mysql_web_console/
├── main.py              # FastAPI 应用入口及路由
├── db.py                # 数据库连接池与执行逻辑
├── config.py            # 读取 .env 配置
├── .env.example         # 环境变量示例
├── requirements.txt     # Python 依赖
└── static/
    └── index.html       # 移动端优先的单页前端
```

## 4. 核心功能需求

### 4.1 后端 API (`main.py` & `db.py`)

1. **静态文件服务**: FastAPI 需挂载 `static` 目录，根路径 `/` 返回 `static/index.html`。
2. **SQL 执行接口**: `POST /api/execute`
   - **请求体**: `{ "sql": "SELECT * FROM users;" }`
   - **响应体**:
     ```json
     {
       "success": true,
       "message": "查询成功",
       "duration_ms": 15.2,
       "columns": ["id", "name"],
       "rows": [
         [1, "Alice"],
         [2, "Bob"]
       ],
       "affected_rows": 0
     }
     ```
   - **逻辑要求**:
     - 接收 SQL 字符串，去除前后空格。
     - 使用 `aiomysql` 创建连接池执行。
     - 如果是 `SELECT` 语句：返回 `columns` 和 `rows`。
     - 如果是 `INSERT/UPDATE/DELETE` 语句：返回 `affected_rows`。
     - 捕获数据库异常，返回 `success: false` 及具体的 `message` (如语法错误)。
     - 记录执行耗时 (`duration_ms`)。
     - **安全限制**: 只允许执行单条语句（通过基本检查或截断分号后内容，防止简单的注入或批量执行）。

### 4.2 前端 UI/UX (`static/index.html`)

前端必须是一个移动端优先的单页应用，界面美观，采用暗色模式为主。

1. **输入区域**:
   - 一个多行文本域 (`<textarea>`) 用于输入 SQL。
   - “执行”按钮 (大号，固定在底部或输入区下方，便于手机点击)。
   - **快捷标签**: 提供几个常用快捷按钮，点击后自动将模板 SQL 填入输入框：
     - `SHOW TABLES;`
     - `SELECT * FROM <table> LIMIT 10;`
     - `DESC <table>;`
   - **历史记录**: 下拉框或折叠面板，保存最近 5 次执行过的 SQL，点击可快速恢复到输入框。
2. **输出区域**:
   - **状态提示框**: 显示执行结果。成功显示绿色（如“查询成功，耗时 15ms，共 10 行”），失败显示红色并展示具体错误信息。
   - **数据表格**:
     - 如果返回了 `columns` 和 `rows`，渲染成一个横向可滚动的 HTML 表格。
     - 表头加粗，表格行斑马纹（暗色模式下的对比色）。
   - **执行影响**: 如果是非查询语句，醒目显示“影响行数：X 行”。
3. **交互反馈**:
   - 点击“执行”按钮后，按钮变为“执行中...”并禁用，防止重复提交。
   - 展示一个简单的 Loading 动画。
   - 请求完成后恢复按钮状态，并自动滚动页面到输出区域。

## 5. 配置说明 (`config.py` & `.env`)

- `config.py` 使用 `python-dotenv` 读取 `.env` 文件。
- 读取的变量包括：`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`。
- 提供默认值 (如 Host 默认为 `127.0.0.1`, Port 默认 `3306`)。

## 6. 运行指令

- `requirements.txt` 需包含：`fastapi`, `uvicorn`, `aiomysql`, `python-dotenv`。
- 启动命令需在 `main.py` 底部定义：
  ```python
  if __name__ == "__main__":
      import uvicorn
      # host必须为0.0.0.0以便局域网访问
      uvicorn.run(app, host="0.0.0.0", port=8000)
  ```

## 7. 给 AI Agent 的构建指令

1. 请依次生成上述所有文件。
2. 确保前端 HTML 完整引入 Vue 3 和 Tailwind CSS 的 CDN。
3. 确保 Vue 3 使用 Composition API (`<script>` 内使用 `setup` 语法糖形式或直接全局 Vue.createApp)。
4. 代码需包含必要的中文注释。
5. 最后，输出一份简短的“快速开始指南”，指导用户如何安装依赖、配置 `.env` 以及如何在手机上访问。
