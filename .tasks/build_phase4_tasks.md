# Phase 4: 前端 UI 与交互构建 - 开发计划

## 任务总览

Phase 4 的目标是在 `static/index.html` 中构建一个完整的移动端优先暗色模式单页应用，使用 Vue 3 + Tailwind CSS (CDN)，对接 `POST /api/execute` 接口。共 5 个任务，按依赖顺序执行：

| 序号 | 任务                                                | 产出文件            | 依赖   |
| :--: | :-------------------------------------------------- | :------------------ | :----- |
|  1   | HTML 骨架 + CDN 引入 + Vue 3 应用初始化与响应式状态 | `static/index.html` | 无     |
|  2   | 输入区域：textarea + 快捷标签 + 历史记录            | `static/index.html` | 任务 1 |
|  3   | 执行按钮 + API 调用逻辑 + Loading 状态              | `static/index.html` | 任务 2 |
|  4   | 状态反馈区 + 数据表格渲染                           | `static/index.html` | 任务 3 |
|  5   | 集成打磨：自动滚动 + 边界处理 + 响应式审查          | `static/index.html` | 任务 4 |

---

## 任务 1：HTML 骨架 + CDN 引入 + Vue 3 应用初始化与响应式状态

**目标**：搭建完整的 HTML 文档结构，引入 Vue 3 和 Tailwind CSS CDN，创建 Vue 应用实例并定义所有响应式状态。

**设计要点**：

1. **HTML 文档基础**：
   - `<!DOCTYPE html>` + `<html lang="zh-CN">`
   - `<meta name="viewport" content="width=device-width, initial-scale=1.0">` 确保移动端适配
   - 页面标题：`MySQL Web Console`

2. **CDN 引入**：
   - Tailwind CSS：`<script src="https://cdn.tailwindcss.com"></script>`
   - 配置 Tailwind 暗色模式：`tailwind.config = { darkMode: 'class' }`
   - Vue 3：`<script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>`

3. **全局暗色模式样式**：
   - `<html class="dark">` 强制暗色模式
   - `<body>` 使用 Tailwind 暗色背景类：`bg-gray-900 text-gray-100 min-h-screen`
   - 基础字体：`font-mono` 适合代码/SQL 场景

4. **Vue 3 应用初始化**：
   - 使用 `Vue.createApp()` + `setup()` 返回模式（非 SFC）
   - 在 `<div id="app">` 上挂载

5. **响应式状态定义**（`setup()` 内）：

   ```javascript
   const sql = Vue.ref(""); // 当前 SQL 输入
   const loading = Vue.ref(false); // 是否正在执行
   const result = Vue.ref(null); // 最近一次 API 返回的完整响应对象
   const history = Vue.ref([]); // 历史记录数组（最近 5 条成功 SQL）
   const historyOpen = Vue.ref(false); // 历史记录下拉是否展开
   ```

6. **快捷标签数据**：

   ```javascript
   const quickTags = [
     { label: "SHOW TABLES", sql: "SHOW TABLES;" },
     { label: "SELECT * LIMIT 10", sql: "SELECT * FROM <table> LIMIT 10;" },
     { label: "DESC", sql: "DESC <table>;" },
   ];
   ```

---

## 任务 2：输入区域：textarea + 快捷标签 + 历史记录

**目标**：实现 SQL 输入区域，包括多行文本域、快捷标签栏和历史记录功能。

**设计要点**：

1. **textarea 输入框**：
   - 使用 `v-model="sql"` 双向绑定
   - 行数：`rows="4"`，可适当调整
   - 样式：暗色背景 `bg-gray-800`，边框 `border-gray-700`，圆角，内边距
   - 占位符：`placeholder="输入 SQL 语句..."`
   - 字体：`font-mono` 等宽字体
   - 聚焦时边框高亮：`focus:border-blue-500 focus:ring-1 focus:ring-blue-500`

2. **快捷标签栏**：
   - 位于 textarea 上方或下方，水平排列
   - 每个标签是一个小按钮：`<button @click="sql = tag.sql">`
   - 样式：`bg-gray-700 hover:bg-gray-600 text-sm px-3 py-1 rounded`
   - 点击后将对应 SQL 模板填入 textarea（覆盖当前内容）

3. **历史记录下拉框**：
   - 位于快捷标签栏旁或下方
   - 一个"历史记录"按钮，点击切换 `historyOpen` 状态
   - 展开时显示 `history` 数组中的 SQL 列表（最多 5 条）
   - 每条历史记录可点击，点击后将该 SQL 填入 textarea
   - 样式：暗色下拉面板，`bg-gray-800 border border-gray-700 rounded`
   - 使用 `v-if="historyOpen"` 控制显隐
   - 点击外部关闭（可选，使用 `@click.stop` + document click 监听）

4. **布局结构**：

   ```
   ┌─────────────────────────────────┐
   │ [SHOW TABLES] [SELECT*] [DESC]  │  ← 快捷标签
   │ [📜 历史记录 ▼]                  │  ← 历史按钮
   │   ┌─ 历史下拉 ──────────────┐   │  ← 展开时显示
   │   │ SELECT * FROM users...  │   │
   │   │ SHOW TABLES;            │   │
   │   └─────────────────────────┘   │
   │ ┌─────────────────────────────┐ │
   │ │ textarea                    │ │  ← SQL 输入
   │ │                             │ │
   │ └─────────────────────────────┘ │
   └─────────────────────────────────┘
   ```

---

## 任务 3：执行按钮 + API 调用逻辑 + Loading 状态

**目标**：实现执行按钮及其交互逻辑，包括 API 调用、按钮禁用状态和 Loading 动画。

**设计要点**：

1. **执行按钮**：
   - 大号按钮，便于手机点击：`px-6 py-3 text-lg rounded-lg`
   - 默认状态：`bg-blue-600 hover:bg-blue-500 text-white`
   - 禁用状态：`bg-gray-600 cursor-not-allowed opacity-50`
   - 使用 `:disabled="loading"` 控制禁用
   - 文字：`{{ loading ? '执行中...' : '执行' }}`

2. **Loading 动画**：
   - 在按钮旁显示一个简单的 CSS 旋转动画
   - 使用 `v-if="loading"` 控制显隐
   - 动画实现：一个 `border-2 border-t-transparent rounded-full animate-spin` 的小圆圈
   - Tailwind 内置 `animate-spin` 即可

3. **API 调用函数 `executeSql()`**：

   ```javascript
   async function executeSql() {
     if (!sql.value.trim() || loading.value) return;

     loading.value = true;
     result.value = null;

     try {
       const response = await fetch("/api/execute", {
         method: "POST",
         headers: { "Content-Type": "application/json" },
         body: JSON.stringify({ sql: sql.value.trim() }),
       });
       const data = await response.json();
       result.value = data;

       // 成功时加入历史记录
       if (data.success) {
         addToHistory(sql.value.trim());
       }
     } catch (err) {
       result.value = {
         success: false,
         message: `网络错误: ${err.message}`,
         duration_ms: 0.0,
         columns: [],
         rows: [],
         affected_rows: 0,
       };
     } finally {
       loading.value = false;
     }
   }
   ```

4. **历史记录管理函数 `addToHistory()`**：

   ```javascript
   function addToHistory(sqlStr) {
     // 去重：如果已存在则移到最前
     history.value = history.value.filter((h) => h !== sqlStr);
     history.value.unshift(sqlStr);
     // 最多保留 5 条
     if (history.value.length > 5) {
       history.value = history.value.slice(0, 5);
     }
   }
   ```

5. **键盘快捷键**（可选增强）：
   - `Ctrl+Enter` 或 `Cmd+Enter` 触发执行
   - 在 textarea 上添加 `@keydown` 监听

---

## 任务 4：状态反馈区 + 数据表格渲染

**目标**：实现执行结果的状态提示和数据表格展示。

**设计要点**：

1. **状态提示框**：
   - 使用 `v-if="result"` 控制整体显隐
   - **成功状态**（`result.success === true`）：
     - 绿色背景：`bg-green-900/50 border border-green-700 text-green-300`
     - 查询语句：显示 `"查询成功，耗时 {duration_ms} ms，共 {rows.length} 行"`
     - 非查询语句：显示 `"执行成功，影响 {affected_rows} 行，耗时 {duration_ms} ms"`
   - **失败状态**（`result.success === false`）：
     - 红色背景：`bg-red-900/50 border border-red-700 text-red-300`
     - 显示后端返回的 `result.message`

2. **数据表格**：
   - 使用 `v-if="result.columns && result.columns.length > 0"` 控制显隐
   - 外层容器：`overflow-x-auto` 支持横向滚动
   - **表头**：`<thead>` 内 `<th>` 加粗 `font-bold`，背景 `bg-gray-700`
   - **表体**：`<tbody>` 内 `<tr>` 斑马纹：
     - 偶数行：`bg-gray-800`
     - 奇数行：`bg-gray-850`（Tailwind 无 850，用 `bg-gray-800/50` 或自定义）
     - 实现方式：`:class="{ 'bg-gray-800': index % 2 === 0, 'bg-gray-750': index % 2 !== 0 }"`
     - 或简化为 `even:bg-gray-800/50`（Tailwind 3.x arbitrary）
   - **单元格**：`<td>` 和 `<th>` 添加 `px-4 py-2 whitespace-nowrap`
   - **空值处理**：如果 cell 值为 `null`，显示灰色 `NULL` 文字

3. **影响行数提示**（非查询语句）：
   - 使用 `v-if="result.success && result.affected_rows > 0"` 控制
   - 醒目样式：`text-yellow-400 font-semibold`
   - 显示：`"影响行数：{affected_rows} 行"`

4. **布局结构**：

   ```
   ┌─────────────────────────────────────┐
   │ ✅ 查询成功，耗时 15.2 ms，共 10 行  │  ← 状态提示框
   ├─────────────────────────────────────┤
   │ ┌─────────────────────────────────┐ │
   │ │ id  │ name  │ email            │ │  ← 表头（加粗）
   │ ├─────┼───────┼──────────────────┤ │
   │ │ 1   │ Alice │ alice@test.com   │ │  ← 斑马纹行
   │ │ 2   │ Bob   │ bob@test.com     │ │
   │ └─────┴───────┴──────────────────┘ │
   │          ← 横向可滚动               │
   └─────────────────────────────────────┘
   ```

---

## 任务 5：集成打磨：自动滚动 + 边界处理 + 响应式审查

**目标**：完善交互细节，确保移动端体验流畅。

**设计要点**：

1. **自动滚动到输出区域**：
   - 在 `executeSql()` 的 `finally` 块中（或 `result` 赋值后），使用 `nextTick` 等待 DOM 更新后滚动
   - 给输出区域添加 `ref="outputArea"`
   - 滚动代码：

     ```javascript
     Vue.nextTick(() => {
       const el = document.getElementById("output-area");
       if (el) {
         el.scrollIntoView({ behavior: "smooth", block: "start" });
       }
     });
     ```

2. **边界处理**：
   - **空结果集**：查询成功但 `rows` 为空时，表格不显示，状态框显示"查询成功，共 0 行数据"
   - **长文本单元格**：`whitespace-nowrap` + 横向滚动已覆盖，无需截断
   - **大量行数据**：考虑给表格容器加 `max-h-[60vh] overflow-y-auto`，防止表格过长撑满屏幕
   - **网络错误**：已在任务 3 的 catch 块中处理
   - **历史记录为空**：`v-if="history.length > 0"` 控制历史按钮显隐，或显示"暂无记录"

3. **响应式审查**：
   - 确保所有交互元素在 375px 宽度（iPhone SE）下可用
   - 快捷标签在窄屏下允许换行 `flex-wrap`
   - 表格横向滚动 `overflow-x-auto` 确保不溢出
   - 执行按钮宽度：移动端可占满 `w-full`

4. **页面整体布局**：

   ```
   ┌─────────────────────────────────────┐
   │        MySQL Web Console            │  ← 标题栏
   ├─────────────────────────────────────┤
   │ [SHOW TABLES] [SELECT*] [DESC]      │  ← 快捷标签
   │ [📜 历史记录]                        │
   │ ┌─────────────────────────────────┐ │
   │ │ textarea                        │ │  ← SQL 输入
   │ └─────────────────────────────────┘ │
   │ [        执行        ]              │  ← 执行按钮（全宽）
   ├─────────────────────────────────────┤
   │ ✅ 查询成功，耗时 15.2 ms，共 10 行  │  ← 状态提示
   │ ┌─────────────────────────────────┐ │
   │ │ 数据表格（横向可滚动）           │ │  ← 结果表格
   │ └─────────────────────────────────┘ │
   └─────────────────────────────────────┘
   ```

5. **最终审查清单**：

   | #   | 检查项                            | 预期结果                                                                |
   | --- | :-------------------------------- | :---------------------------------------------------------------------- |
   | 1   | Vue 3 + Tailwind CSS CDN 正确加载 | 页面正常渲染，无控制台报错                                              |
   | 2   | textarea 双向绑定                 | 输入内容与 `sql` 状态同步                                               |
   | 3   | 快捷标签点击填入                  | 点击后 textarea 内容更新为对应 SQL                                      |
   | 4   | 历史记录最多 5 条，去重，最新在前 | 重复执行的 SQL 只出现一次且置顶                                         |
   | 5   | 执行按钮 Loading 状态             | 执行中显示"执行中..."并禁用，旁边有旋转动画                             |
   | 6   | 成功状态绿色提示                  | 显示耗时和行数/影响行数                                                 |
   | 7   | 失败状态红色提示                  | 显示后端返回的错误信息                                                  |
   | 8   | 数据表格斑马纹 + 横向滚动         | 暗色交替行，窄屏可横向滚动查看                                          |
   | 9   | NULL 值显示                       | 灰色 `NULL` 文字                                                        |
   | 10  | 执行后自动滚动到输出区域          | 页面平滑滚动到结果区域                                                  |
   | 11  | 移动端 375px 宽度可用             | 所有元素不溢出，按钮可点击                                              |
   | 12  | API 字段名与后端一致              | `success`, `message`, `duration_ms`, `columns`, `rows`, `affected_rows` |

---

## 文件变更汇总

| 文件                                  | 操作     | 说明                                                           |
| :------------------------------------ | :------- | :------------------------------------------------------------- |
| `mysql_web_console/static/index.html` | **创建** | 从空文件构建完整的 Vue 3 + Tailwind CSS 暗色模式移动端单页应用 |

**变更前**：空文件（0 行）

**变更后**：完整的单页 HTML，包含：

- CDN 引入（Vue 3, Tailwind CSS）
- Vue 3 Composition API 应用（`createApp` + `setup`）
- SQL 输入区（textarea + 快捷标签 + 历史记录）
- 执行按钮（Loading 状态 + 旋转动画）
- 状态反馈区（成功绿/失败红）
- 数据表格（斑马纹 + 横向滚动 + NULL 处理）
- 自动滚动 + 响应式布局
