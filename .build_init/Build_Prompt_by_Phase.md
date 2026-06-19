# Build Prompt by Phase - 局域网 MySQL Web 控制台

## Phase 1: 项目初始化与配置层构建

### 【参考文档】

在开始本阶段任务前，请先阅读以下文档以了解项目全貌和设计意图：

- **`Construct.md`**：了解项目整体概述、技术栈选型、项目文件结构（第3节）、配置说明（第5节）以及运行指令（第6节）。Phase 1 需要严格按照其中定义的项目结构创建文件。
- **`API_Contract.md`**：了解最终 API 的请求/响应契约，提前把握 `POST /api/execute` 接口的响应 Schema（第2.2.2节），为后续 `config.py` 和 `db.py` 的数据结构设计做铺垫。

### 【项目背景和已完成的工作】

我们正在构建一个"局域网 MySQL Web 控制台"，允许手机在局域网内通过浏览器访问电脑端运行的 Web 服务，执行 SQL 语句。
技术栈为：Python (FastAPI, aiomysql) + 单 HTML (Vue3, Tailwind CSS CDN)。
目前是项目的第一步，还没有任何代码。

### 【当前任务】

请帮我完成项目的初始化和基础配置：

1. 创建项目文件夹结构：包含 `main.py`, `db.py`, `config.py`, `.env.example`, `requirements.txt` 以及 `static/` 目录。
2. 编写 `requirements.txt`，包含依赖：`fastapi`, `uvicorn`, `aiomysql`, `python-dotenv`。
3. 编写 `.env.example`，包含数据库连接变量：`DB_HOST` (默认127.0.0.1), `DB_PORT` (默认3306), `DB_USER`, `DB_PASSWORD`, `DB_NAME`。
4. 编写 `config.py`，使用 `python-dotenv` 读取环境变量，并提供一个配置对象或字典供其他模块使用。
5. 编写 `main.py` 的基础骨架：引入 FastAPI，配置启动命令为 `uvicorn.run(app, host="0.0.0.0", port=8000)`，暂时只写一个根路由 `/` 返回 `{"message": "Server is running"}` 用于测试。

---

## Phase 2: 数据库执行逻辑层构建

### 【参考文档】

在开始本阶段任务前，请重点阅读以下文档中与数据库执行逻辑相关的部分：

- **`API_Contract.md`**：核心参考文档。重点阅读：
  - 第 2.2.2 节「响应格式」：`db.py` 中 `execute_sql()` 的返回值字典必须严格遵循此 Schema，字段名 `success`, `message`, `duration_ms`, `columns`, `rows`, `affected_rows` 必须一一对应。
  - 第 2.2.3 节「响应示例」：参考场景 A（查询成功）、场景 B（非查询成功）、场景 C（执行失败）的 JSON 格式来验证输出。
  - 第 3 节「业务逻辑与安全约束」：SQL 类型判定规则（`SELECT/SHOW/DESC/EXPLAIN` 为查询）、异常捕获要求、单语句限制。
- **`Construct.md`**：参考第 4.1 节「后端 API」中关于 `db.py` 的逻辑要求，确认连接池管理、SQL 类型判断、耗时记录等需求。

### 【项目背景和已完成的工作】

项目已初始化，`config.py` 可以正常读取环境变量，`main.py` 具备基础的 FastAPI 骨架。接下来需要实现核心的数据库操作逻辑。

### 【当前任务】

请编写 `db.py` 文件，实现 MySQL 的异步连接和执行逻辑：

1. 使用 `aiomysql` 创建并管理一个全局连接池（在应用启动时创建，关闭时释放，可通过 FastAPI 的 lifespan 或 startup/shutdown 事件管理，请在 `main.py` 中补充对应事件代码）。
2. 在 `db.py` 中实现一个核心异步函数 `async def execute_sql(sql: str) -> dict`。
3. 该函数需要实现以下逻辑：
   - 记录执行开始时间。
   - 判断 SQL 类型：将 SQL 去除前后空格并转大写，如果以 `SELECT`, `SHOW`, `DESC`, `EXPLAIN` 开头，视为查询；否则视为非查询（DML/DDL）。
   - 如果是查询：执行 `cursor.execute(sql)`，获取 `cursor.description` 组装列名，获取 `cursor.fetchall()` 组装数据行。
   - 如果是非查询：执行后获取 `cursor.rowcount` 作为受影响行数。
   - 计算耗时 `duration_ms`。
   - 返回符合 API 契约的字典格式：`{"success": bool, "message": str, "duration_ms": float, "columns": list, "rows": list, "affected_rows": int}`。
   - 必须使用 `try...except` 捕获所有 `aiomysql` 异常，捕获到异常时返回 `success: False`，并将异常信息放入 `message` 字段。

---

## Phase 3: 后端路由与接口层构建

### 【参考文档】

在开始本阶段任务前，请重点阅读以下文档中与 API 路由和接口定义相关的部分：

- **`API_Contract.md`**：核心参考文档。重点阅读：
  - 第 2.1 节「获取前端页面」：确认 `GET /` 路由的行为，需返回 `static/index.html`。
  - 第 2.2.1 节「请求参数」：确认 `POST /api/execute` 的请求体格式为 `{ "sql": "string" }`。
  - 第 2.2.2 节「响应格式」：确认接口返回的 JSON 结构必须与 `db.execute_sql()` 返回值一致。
  - 第 2.2.3 节「场景 D」：空 SQL 参数的错误返回格式。
  - 第 3 节「业务逻辑与安全约束」第 2 条「空值处理」：前端传入空字符串或纯空格时的处理要求。
- **`Construct.md`**：参考第 4.1 节「后端 API」第 1 条「静态文件服务」和第 2 条「SQL 执行接口」确认路由设计。

### 【项目背景和已完成的工作】

配置层 (`config.py`) 和数据库执行层 (`db.py`) 已完成。现在需要将 `db.py` 中的 `execute_sql` 函数暴露给前端调用，完成 API 接口。

### 【当前任务】

请更新 `main.py`，完成以下工作：

1. 配置 FastAPI 静态文件挂载：将 `/` 路径指向 `static/` 目录下的 `index.html`。
2. 实现 `POST /api/execute` 接口：
   - 接收 JSON 请求体：`{ "sql": "string" }`。
   - 验证 `sql` 不能为空字符串或纯空格。如果为空，直接返回 `{"success": False, "message": "SQL 语句不能为空", ...}`。
   - 调用 `db.execute_sql(sql)` 获取结果。
   - 将结果直接作为 JSON Response 返回。
3. 确保异常不会导致服务崩溃（API 层兜底异常捕获）。

---

## Phase 4: 前端 UI 与交互构建

### 【参考文档】

在开始本阶段任务前，请重点阅读以下文档中与前端 UI 和交互相关的部分：

- **`Construct.md`**：核心参考文档。重点阅读第 4.2 节「前端 UI/UX」，其中详细定义了：
  - 输入区域（多行文本域、快捷标签、历史记录）
  - 输出区域（状态提示框、数据表格、执行影响）
  - 交互反馈（按钮状态、Loading 动画、自动滚动）
- **`API_Contract.md`**：重点阅读第 2.2.2 节「响应格式」和第 2.2.3 节「响应示例」，前端需要根据 `success` 字段判断展示绿色成功框或红色失败框，根据 `columns`/`rows` 渲染数据表格，根据 `affected_rows` 展示影响行数，根据 `duration_ms` 展示耗时。所有字段名必须与后端返回一致。

### 【项目背景和已完成的工作】

后端 API 已全部就绪，`POST /api/execute` 可以正常执行 SQL 并返回结构化数据。现在需要构建移动端友好的前端页面。

### 【当前任务】

请创建 `static/index.html`，使用 Vue 3 和 Tailwind CSS (均通过 CDN 引入)。要求如下：

1. **整体设计**：暗色模式为主，移动端优先，屏幕宽度自适应。
2. **输入区**：
   - 一个多行 `<textarea>` 用于输入 SQL。
   - 快捷标签栏：包含 `SHOW TABLES;`, `SELECT * FROM <table> LIMIT 10;`, `DESC <table>;` 三个按钮，点击后将对应文本填入 textarea。
   - 历史记录下拉框：保存最近 5 次成功提交的 SQL，选择后填入 textarea。
3. **执行按钮**：大号按钮，点击后触发 API 请求。请求期间按钮文字变为“执行中...”并禁用，旁边展示一个简单的 loading 动画。
4. **状态反馈区**：
   - 成功：显示绿色背景框，展示“查询成功，耗时 X ms，共 Y 行”或“执行成功，影响 Z 行”。
   - 失败：显示红色背景框，展示后端返回的 `message`。
5. **数据表格区**：
   - 如果后端返回了 `columns` 和 `rows`，渲染为一个 HTML 表格。
   - 表头加粗，表格行使用暗色斑马纹。
   - 表格需要支持横向滚动（`overflow-x: auto`）以适应手机屏幕。
6. **JS 逻辑**：使用 Vue3 的 `createApp` 或 `setup` 语法，使用 `fetch` 或 `axios` 调用后端接口。请求完成后自动将页面滚动到输出区域。

---

## Phase 5: 集成检查与快速开始指南

### 【参考文档】

在本阶段，请对照以下文档逐一核对，确保实现与设计一致：

- **`API_Contract.md`**：完整核对清单。
  - 第 2.2.2 节「响应格式」：逐字段核对 `success`, `message`, `duration_ms`, `columns`, `rows`, `affected_rows` 的字段名、类型、必填性是否前后端一致。
  - 第 2.2.3 节「响应示例」：用场景 A/B/C/D 的示例数据做端到端验证，确保前端能正确解析每种响应。
  - 第 3 节「业务逻辑与安全约束」：检查异常捕获、空值处理、SQL 类型判定是否正确实现。
- **`Construct.md`**：对照检查清单。
  - 第 3 节「项目结构」：确认所有文件均已创建且路径正确。
  - 第 5 节「配置说明」：确认 `config.py` 正确读取所有环境变量。
  - 第 6 节「运行指令」：确认 `main.py` 底部 `uvicorn.run` 配置正确，`host="0.0.0.0"` 确保局域网可访问。
  - 第 7 节「给 AI Agent 的构建指令」：确认所有指令项均已完成。

### 【项目背景和已完成的工作】

项目的前后端代码均已编写完成。现在需要进行最后的逻辑核对，并输出用户使用指南。

### 【当前任务】

1. 请检查所有代码文件，确保前后端的数据结构字段名完全一致（如 `success`, `message`, `duration_ms`, `columns`, `rows`, `affected_rows`）。
2. 检查 `main.py` 中 FastAPI 的静态文件挂载是否正确，确保访问根目录能返回前端页面。
3. 检查 `db.py` 的连接池初始化是否在 `main.py` 中被正确触发。
4. 最后，请输出一份清晰的“快速开始指南”，包含：
   - 如何创建并激活虚拟环境。
   - 如何安装 `requirements.txt`。
   - 如何配置 `.env` 文件。
   - 如何启动项目 (`python main.py`)。
   - 如何在手机上访问（提示用户查看电脑局域网 IP 并在手机浏览器输入 `http://<IP>:8000`）。
