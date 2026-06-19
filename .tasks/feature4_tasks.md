# Feature 4：SQL 输入区交互优化 & 结果表导出功能

## 概述

对 SQL 输入区域的按钮布局进行逻辑重组，新增清空按钮，并为结果表添加 Markdown 复制和 CSV 下载功能。

---

## Task 1：新增清空按钮（Clear）

- **文件**：`mysql_web_console/static/index.html`
- **内容**：
  - 在第一行按钮组中，Tab 按钮右侧新增"✕ 清空"按钮
  - 点击后清空 `sql` 变量（`sql.value = ""`）并聚焦 textarea
  - 按钮样式与 Tab 保持一致（`bg-gray-700 hover:bg-gray-600`）
- **涉及区域**：第一行 `flex-wrap gap-2` 按钮组

## Task 2：历史记录按钮移至第二行

- **文件**：`mysql_web_console/static/index.html`
- **内容**：
  - 将历史记录按钮及其下拉菜单从第一行按钮组移除
  - 将其放入第二行按钮组（与 CALL PROC 同行），放在 CALL PROC 左侧
  - 逻辑分组：第一行 = 编辑操作（Tab、清空）；第二行 = 内容填充（历史记录、CALL PROC）
  - 下拉菜单功能不变，仅位置调整

## Task 3：普通结果表添加导出按钮

- **文件**：`mysql_web_console/static/index.html`
- **内容**：
  - 在普通结果表（`result.columns.length > 0` 的 table）下方添加两个按钮：
    - "📋 复制 Markdown"：将结果表转为 Markdown 表格格式，复制到剪贴板
    - "⬇️ 下载 CSV"：将结果表转为 CSV 格式，触发浏览器下载
  - 按钮可见性跟随结果表（`v-if` 条件与结果表一致）
  - 按钮样式：小尺寸，与页面暗色主题一致

## Task 4：OUT 参数表添加导出按钮

- **文件**：`mysql_web_console/static/index.html`
- **内容**：
  - 在 OUT 参数表下方添加两个按钮：
    - "📋 复制 Markdown"：将 OUT 参数表转为 Markdown 表格格式，复制到剪贴板
    - "⬇️ 下载 CSV"：将 OUT 参数表转为 CSV 格式，触发浏览器下载
  - 按钮可见性跟随 OUT 参数表（`v-if` 条件与 OUT 参数表一致）

## Task 5：实现导出工具函数

- **文件**：`mysql_web_console/static/index.html`（Vue setup 内）
- **内容**：
  - `copyAsMarkdown(columns, rows)`：
    - 将列名和行数据拼接为 Markdown 表格字符串
    - 使用 `navigator.clipboard.writeText()` 写入剪贴板
    - 复制成功后显示简短提示（可用临时 toast 或按钮文字变化反馈）
  - `downloadCsv(columns, rows, filename)`：
    - 将列名和行数据转为 CSV 字符串（处理逗号、引号、换行等转义）
    - 创建 Blob 对象，生成临时 URL，触发 `<a>` 标签下载
    - 下载完成后释放 URL
  - `escapeCsvCell(cell)`：CSV 单元格转义辅助函数

---

## 执行顺序

Task 1 → Task 2 → Task 5 → Task 3 → Task 4

先完成按钮布局调整（Task 1、2），再实现导出工具函数（Task 5），最后在两个表格区域接入导出按钮（Task 3、4）。

## 不涉及的变更

- 后端代码无需修改，所有功能均为纯前端实现
- 不引入新的第三方依赖
