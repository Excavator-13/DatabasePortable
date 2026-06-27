# MySQL Web Console 优化开发计划

## Task 1: 修复 SQL 拼接注入风险 ✅

**优先级**: 🔴 高
**涉及文件**: `mysql_web_console/db.py`

**问题**:

- `DESC` 语句使用 f-string 拼接表名: `f"DESC \`{table_name}\`"`
- `SET` 语句使用 f-string 拼接变量值: `f"SET {var_name} = {value}"`
- CALL 语句重构时也用了 f-string: `f"CALL \`{proc_name}\`({', '.join(modified_args)})"`

**优化方案**:

- 对 `table_name` 增加白名单校验，仅允许 `[a-zA-Z0-9_]` 字符
- 对 `proc_name` 同样增加白名单校验
- 对 `var_name`（`@xxx_auto` 格式）增加正则校验
- 对 `SET` 语句中的 `value`，使用参数化查询替代 f-string 拼接
- 对 `modified_args` 中的用户输入部分做安全过滤

**验收标准**:

- 所有动态拼接的 SQL 片段都经过输入校验或参数化处理
- 不影响现有功能（DESC、CALL、SET 均正常工作）

**实施记录**:

- 新增 `_validate_identifier()` 和 `_validate_session_var()` 校验函数
- `describe_table()` 增加 `table_name` 白名单校验
- `execute_sql()` CALL 分支增加 `proc_name` 和 `var_name` 校验
- SET 语句改为参数化查询: `cursor.execute(f"SET {var_name} = %s", (value,))`
- OUT 参数回读 SELECT 增加 `var_name` 和 `original_name` 校验

---

## Task 2: 增强 Token 认证机制 ✅

**优先级**: 🟡 中
**涉及文件**: `mysql_web_console/main.py`, `mysql_web_console/config.py`, `mysql_web_console/.env.example`

**问题**:

- Token 存储在内存 `dict[str, None]` 中，语义不清晰
- 无 Token 过期机制，一旦签发永久有效
- 服务重启后所有 Token 失效（可接受，但需文档说明）

**优化方案**:

- 将 `_tokens: dict[str, None]` 改为 `_tokens: dict[str, float]`，value 存储签发时间戳
- 增加 Token 过期机制：中间件校验时检查是否超过可配置的过期时长（默认 24 小时）
- 在 `.env` 和 `config.py` 中新增 `TOKEN_EXPIRE_HOURS` 配置项，默认 24
- 在 `.env.example` 中补充示例

**验收标准**:

- Token 存储签发时间，语义清晰
- Token 超过配置时长后自动失效，返回 401
- 登录/登出/鉴权流程不受影响

**实施记录**:

- `_tokens` 类型改为 `dict[str, float]`，登录时存储 `time.time()`
- 认证中间件增加过期检查，超时返回 401 "Token 已过期，请重新登录"
- `config.py` 新增 `token_expire_hours` 配置项，默认 24
- `.env.example` 新增 `TOKEN_EXPIRE_HOURS=24`

---

## Task 3: 添加 CORS 中间件配置 ✅

**优先级**: 🟡 中
**涉及文件**: `mysql_web_console/main.py`, `mysql_web_console/config.py`, `mysql_web_console/.env.example`

**问题**:

- 当前无 CORS 配置，若前端部署在不同域/端口会遇到跨域问题
- 作为 API 服务缺少跨域支持不够灵活

**优化方案**:

- 在 `main.py` 中添加 FastAPI 的 `CORSMiddleware`
- 在 `.env` 中新增 `CORS_ORIGINS` 配置项，默认为 `*`（局域网场景下可接受）
- 在 `config.py` 中读取该配置
- 在 `.env.example` 中补充示例

**验收标准**:

- 可通过环境变量控制允许的跨域来源
- 默认配置下不影响现有使用方式

**实施记录**:

- `main.py` 导入并添加 `CORSMiddleware`，支持逗号分隔的多域名配置
- `config.py` 新增 `cors_origins` 配置项，默认 `*`
- `.env.example` 新增 `CORS_ORIGINS=*`

---

## Task 4: 锁定依赖版本号 ✅

**优先级**: 🟢 低
**涉及文件**: `mysql_web_console/requirements.txt`

**问题**:

- 当前依赖未锁定版本，如 `fastapi`、`aiomysql` 等
- 未来依赖大版本更新可能导致不兼容

**优化方案**:

- 查询当前 venv 中已安装包的版本
- 将 `requirements.txt` 中的依赖锁定为当前可用的具体版本号
- 格式: `package==x.y.z`

**验收标准**:

- `requirements.txt` 中所有依赖均带有确切版本号
- `pip install -r requirements.txt` 可正常安装

**实施记录**:

- 查询 venv 中已安装版本，锁定为:
  - fastapi==0.137.2
  - uvicorn==0.49.0
  - aiomysql==0.3.2
  - python-dotenv==1.2.2
  - cryptography==49.0.0
