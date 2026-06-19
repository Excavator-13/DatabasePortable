# 开发任务：移除预制SQL & 添加Tab按钮

## 现状分析

当前 `mysql_web_console/static/index.html` 工具栏区域包含：

- **3个预制SQL按钮**：`SHOW TABLES`、`SELECT * LIMIT 10`、`DESC` — 由 `quickTags` 数组驱动，通过 `v-for` 渲染
- **历史记录下拉**：点击展开最近5条执行记录
- **CALL PROC下拉**：搜索并选择存储过程

## 任务清单

### Task 1：移除预制SQL按钮

- 删除模板中 `quickTags` 的 `v-for` 渲染块
- 删除 JS 中 `quickTags` 常量定义
- 从 `return` 对象中移除 `quickTags` 导出

### Task 2：添加 Tab 插入按钮

- 在 textarea 上方工具栏（历史记录和 PROC 按钮旁边）新增一个「Tab」按钮
- 点击后在 textarea 光标位置插入制表符，并保持光标在插入点之后
- 实现辅助方法 `insertTab()`，通过 `textarea.selectionStart` / `selectionEnd` 精确定位光标，插入后重新设定光标位置
- 按钮样式与现有按钮保持一致（`bg-gray-700 hover:bg-gray-600`），使用 `⇥` 或 `Tab` 作为标签
- 在 `onKeydown` 中拦截 `e.key === "Tab"`，调用同一个 `insertTab()` 方法，避免 Tab 键跳转焦点

### Task 3：界面微调与验证

- 确认移除预制按钮后工具栏布局正常（flex-wrap 自动排列）
- 确认 Tab 按钮在手机端触摸友好（大小与现有按钮一致）
- 确认 Tab 插入在 textarea 中正确工作（光标位置、多行缩进场景）

## 涉及文件

| 文件                                  | 改动类型           |
| ------------------------------------- | ------------------ |
| `mysql_web_console/static/index.html` | 模板 + JS 逻辑修改 |

后端无需改动，所有变更集中在前端单文件。
