# 功能开发任务清单

## 现有界面设计规范（必须遵循）

| 要素       | 规范                                                                                     |
| ---------- | ---------------------------------------------------------------------------------------- |
| 主题       | 深色模式，三层灰度：`bg-gray-900`(页面) → `bg-gray-800`(容器/输入) → `bg-gray-700`(按钮) |
| 强调色     | 标题 `text-blue-400`，数据库名 `text-emerald-400`，主按钮 `bg-blue-600`                  |
| 布局       | `max-w-3xl mx-auto` 单栏，移动端优先（项目定位：局域网移动端 SQL 控制台）                |
| 字体       | `font-mono`，正文 `text-sm`                                                              |
| 交互模式   | 快速标签 = 小圆角按钮组，下拉菜单 = 自定义浮层（参考历史记录下拉）                       |
| 占位符约定 | 用尖括号标记待填项，如 `<table>`、`<参数名>`                                             |
| 触控目标   | 移动端友好，按钮最小 `py-1` + `px-3`，主操作按钮 `py-3`                                  |
| 过渡动画   | 统一使用 `transition-colors`，下拉箭头用 `transition-transform`                          |

---

## 功能一：Procedure 下拉列表

### 目标

在快速标签栏中新增一个 "CALL PROC" 按钮，点击后弹出自定义下拉浮层，展示当前数据库所有可用 Stored Procedure。选中后自动填充 SQL 输入框，生成 `CALL proc_name(<参数1>, <参数2>, ...)` 格式语句，参数位置用尖括号占位符标记，待用户替换。

### 任务分解

#### 1. 后端 — 新增获取 Procedure 列表函数

- **文件**: `db.py`
- **内容**: 新增 `get_procedures()` 函数
  - 执行 `SHOW PROCEDURE STATUS WHERE Db = %s`，传入当前数据库名
  - 提取 `Name` 字段，返回按字母排序的名称列表
- **返回**: `list[str]`
- **异常处理**: 连接池未初始化或查询失败时返回空列表，不抛异常

#### 2. 后端 — 新增获取 Procedure 参数详情函数

- **文件**: `db.py`
- **内容**: 新增 `get_procedure_params(proc_name: str)` 函数
  - 查询 `information_schema.PARAMETERS`
  - 条件：`SPECIFIC_SCHEMA = 当前库名 AND SPECIFIC_NAME = proc_name AND PARAMETER_MODE IS NOT NULL`
  - 按 `ORDINAL_POSITION` 排序
  - 提取每项的 `PARAMETER_NAME`、`DATA_TYPE`、`PARAMETER_MODE`(IN/OUT/INOUT)
- **返回**: `list[dict]`，每项含 `name`、`type`、`direction`
- **异常处理**: 同上，失败返回空列表

#### 3. 后端 — 注册新路由

- **文件**: `main.py`
- **内容**:
  - `GET /api/procedures` → 调用 `db.get_procedures()`，返回 `{"procedures": [...]}`
  - `GET /api/procedures/{name}/params` → 调用 `db.get_procedure_params(name)`，返回 `{"params": [...]}`
- **注意**: 路由定义须放在 `app.mount("/static", ...)` 之前

#### 4. 前端 — 在快速标签栏添加 "CALL PROC" 按钮

- **文件**: `static/index.html`
- **UI 设计**:
  - 在 `quickTags` 按钮组末尾，新增一个 "CALL PROC" 按钮
  - 样式与现有快速标签一致：`bg-gray-700 hover:bg-gray-600 text-sm px-3 py-1 rounded transition-colors`
  - 右侧带下拉箭头 SVG（复用历史记录按钮的箭头图标），表示可展开
  - 点击后切换 `procDropdownOpen` 状态，显示/隐藏自定义下拉浮层
- **交互逻辑**:
  - 首次点击时调用 `GET /api/procedures` 加载列表，结果缓存到 `procList` 变量，避免重复请求
  - 后续点击直接使用缓存，若列表为空则重新请求
  - 点击页面其他区域关闭下拉（复用现有 `document.addEventListener("click", ...)` 模式）

#### 5. 前端 — Procedure 下拉浮层 UI

- **文件**: `static/index.html`
- **UI 设计**:
  - 浮层样式与历史记录下拉完全一致：`absolute top-full left-0 mt-1 w-72 bg-gray-800 border border-gray-700 rounded shadow-lg z-10`
  - 最大高度 `max-h-60 overflow-y-auto`，procedure 较多时可滚动
  - 顶部增加一个搜索输入框：
    - 样式：`bg-gray-700 border-b border-gray-600 px-3 py-2 text-sm w-full outline-none`，与深色主题融合
    - placeholder: "搜索 Procedure..."
    - 绑定 `procSearch` 变量，实时过滤 `procList`
  - 搜索框下方为 procedure 列表，每项为可点击按钮：
    - 样式：`block w-full text-left px-3 py-2 text-sm hover:bg-gray-700 transition-colors truncate border-b border-gray-700/50 last:border-b-0`
    - 显示 procedure 名称
  - 若过滤后列表为空，显示 "无匹配结果" 提示（`text-gray-500 text-sm px-3 py-2`）

#### 6. 前端 — 选中 Procedure 后自动填充 SQL

- **文件**: `static/index.html`
- **交互逻辑**:
  - 点击某个 procedure 项后：
    1. 调用 `GET /api/procedures/{name}/params` 获取参数列表
    2. 拼接 `CALL` 语句：
       - 无参数：`CALL proc_name();`
       - 有参数：`CALL proc_name(<param1>, <param2>, ...);`
       - IN/INOUT 参数占位符：`<参数名>`
       - OUT 参数占位符：`@<参数名>`
    3. 将拼接结果赋值给 `sql` 变量，自动填入输入框
    4. 关闭下拉浮层，重置搜索框
    5. 聚焦到 textarea，方便用户立即编辑参数
  - 拼接示例：
    - `CALL add_user(<p_name>, <p_age>, @result);`

---

## 功能二：随机数生成器

### 目标

在页面底部增加一个可折叠的随机数生成器卡片，输入大于 1 的整数 N，点击生成后输出 1~N 的随机整数。纯前端实现，不依赖后端。

### 任务分解

#### 7. 前端 — 随机数生成器卡片 UI

- **文件**: `static/index.html`
- **位置**: 结果区域（`#output-area`）之后，页面最底部
- **UI 设计**:
  - 外层容器：`bg-gray-800 border border-gray-700 rounded-lg overflow-hidden`
  - 标题栏（可折叠）：
    - 左侧标题 "🎲 随机数生成器"，样式 `text-sm font-semibold text-gray-300 px-4 py-3 cursor-pointer select-none hover:bg-gray-700/50 transition-colors flex items-center justify-between`
    - 右侧折叠箭头 SVG（复用现有箭头图标），根据 `randOpen` 状态旋转
    - 点击标题栏切换 `randOpen` 折叠状态
    - 默认展开（`randOpen = true`）
  - 内容区（`v-show="randOpen"`）：
    - 输入行：`flex gap-2 px-4 pb-3`
      - 数字输入框：`flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm outline-none focus:border-blue-500 transition-colors`，type="number"，min="2"，placeholder="输入大于1的整数"
      - 生成按钮：`bg-emerald-600 hover:bg-emerald-500 text-sm px-4 py-2 rounded font-semibold transition-colors whitespace-nowrap`
    - 错误提示（`v-if="randError"`）：`text-red-400 text-xs px-4 pb-2`
    - 结果展示区（`v-if="randResult !== null"`）：
      - 居中大字显示随机数：`text-center text-4xl font-bold text-emerald-400 py-4`
      - 下方小字说明：`text-center text-xs text-gray-500 pb-3`，如 "1 ~ 10 范围内的随机数"

#### 8. 前端 — 随机数生成逻辑

- **文件**: `static/index.html`
- **响应式变量**:
  - `randMax` (string) — 输入值
  - `randResult` (number | null) — 结果，默认 null
  - `randError` (string) — 错误提示，默认空
  - `randOpen` (boolean) — 折叠状态，默认 true
- **`generateRandom()` 函数**:
  1. 清除上次结果和错误：`randResult = null; randError = "";`
  2. 校验输入：
     - 非空检查：空值 → `randError = "请输入一个整数"`
     - 整数检查：`!Number.isInteger(Number(randMax))` → `randError = "请输入有效的整数"`
     - 范围检查：`Number(randMax) <= 1` → `randError = "请输入大于1的整数"`
     - 校验不通过时 return
  3. 生成随机数：`Math.floor(Math.random() * Number(randMax)) + 1`
  4. 赋值 `randResult`
- **交互细节**:
  - 输入框按 Enter 键也可触发生成
  - 生成后结果区域有短暂缩放动画（可选，用 CSS `scale` transition）

---

## 执行顺序

| 步骤 | 任务编号   | 说明                                              |
| ---- | ---------- | ------------------------------------------------- |
| 1    | #1, #2     | 后端新增 db 查询函数                              |
| 2    | #3         | 后端注册 API 路由                                 |
| 3    | #4, #5, #6 | 前端 Procedure 下拉列表（按钮 → 浮层 → 自动填充） |
| 4    | #7, #8     | 前端随机数生成器（卡片 UI → 生成逻辑）            |

## 涉及文件

| 文件                                  | 修改类型                |
| ------------------------------------- | ----------------------- |
| `mysql_web_console/db.py`             | 新增 2 个函数           |
| `mysql_web_console/main.py`           | 新增 2 个路由           |
| `mysql_web_console/static/index.html` | 新增 UI 组件 + 交互逻辑 |

## 设计一致性检查清单

- [ ] 所有新增颜色使用 `gray-700/800/900` 三层灰度 + `blue/emerald` 强调色
- [ ] 下拉浮层复用历史记录下拉的样式和交互模式
- [ ] 占位符使用尖括号 `<name>` 格式，与现有 `<table>` 约定一致
- [ ] 按钮触控区域足够大，适配移动端
- [ ] 新增组件在 `max-w-3xl` 单栏布局下不溢出
- [ ] 点击外部关闭下拉的行为与历史记录一致
