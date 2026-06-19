# Phase 1: 项目初始化与配置层构建 - 开发计划

## 任务总览

Phase 1 的目标是完成项目初始化和基础配置层，共 5 个任务，按依赖顺序执行：

| 序号 | 任务                    | 产出文件                          | 依赖         |
| :--: | :---------------------- | :-------------------------------- | :----------- |
|  1   | 创建项目文件夹结构      | `mysql_web_console/` 目录及空文件 | 无           |
|  2   | 编写 `requirements.txt` | `requirements.txt`                | 任务1        |
|  3   | 编写 `.env.example`     | `.env.example`                    | 任务1        |
|  4   | 编写 `config.py`        | `config.py`                       | 任务1, 任务3 |
|  5   | 编写 `main.py` 基础骨架 | `main.py`                         | 任务1, 任务4 |

---

## 任务 1：创建项目文件夹结构

**目标**：按照 `Construct.md` 第3节定义的结构创建目录和占位文件。

```
mysql_web_console/
├── main.py              # Phase 1 先写骨架
├── db.py                # Phase 1 先创建空文件，Phase 2 填充
├── config.py            # Phase 1 实现
├── .env.example         # Phase 1 实现
├── requirements.txt     # Phase 1 实现
└── static/
    └── index.html       # Phase 1 先创建空文件，Phase 4 填充
```

**注意**：`db.py` 和 `static/index.html` 在本阶段仅创建占位文件，具体实现在后续 Phase 完成。

---

## 任务 2：编写 `requirements.txt`

**目标**：声明 Python 依赖。

**内容**：

```
fastapi
uvicorn
aiomysql
python-dotenv
```

**依据**：`Construct.md` 第6节。

---

## 任务 3：编写 `.env.example`

**目标**：提供数据库连接变量的示例模板，供用户复制为 `.env` 使用。

**内容**：

```
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=your_database
```

**依据**：`Construct.md` 第5节，默认值 `127.0.0.1` 和 `3306`。

---

## 任务 4：编写 `config.py`

**目标**：使用 `python-dotenv` 读取 `.env` 文件，提供一个配置字典供 `db.py` 和 `main.py` 使用。

**设计要点**：

- 调用 `load_dotenv()` 加载 `.env` 文件
- 通过 `os.getenv()` 读取 5 个数据库变量，`DB_HOST` 默认 `127.0.0.1`，`DB_PORT` 默认 `3306`
- 导出一个 `db_config` 字典，键名与 `aiomysql.create_pool()` 的参数对齐（`host`, `port`, `user`, `password`, `db`），方便 Phase 2 直接解包使用
- `port` 转为 `int` 类型

**依据**：`Construct.md` 第5节；`API_Contract.md` 第3节（连接配置需与 aiomysql 驱动参数匹配）。

---

## 任务 5：编写 `main.py` 基础骨架

**目标**：搭建 FastAPI 应用入口，包含根路由和启动命令。

**设计要点**：

- 引入 `FastAPI`，创建 `app` 实例
- 根路由 `GET /` 返回 `{"message": "Server is running"}`（Phase 3 会替换为静态文件服务）
- 底部 `if __name__ == "__main__"` 块中调用 `uvicorn.run(app, host="0.0.0.0", port=8000)`
- 预留 `db.py` 的导入位置（注释标记），为 Phase 2 的连接池生命周期管理做准备

**依据**：`Construct.md` 第6节；当前任务描述第5条。

---

## 验收标准

Phase 1 完成后，应能通过以下验证：

1. ✅ 项目目录结构完整，所有文件存在
2. ✅ `pip install -r requirements.txt` 可正常安装依赖
3. ✅ 复制 `.env.example` 为 `.env` 并填入真实值后，`config.py` 能正确读取配置
4. ✅ `python main.py` 启动后，访问 `http://localhost:8000/` 返回 `{"message": "Server is running"}`
5. ✅ 局域网内其他设备可访问 `http://<电脑IP>:8000/`
