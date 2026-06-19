# 聚焦与键盘弹出行为修复任务

## 问题描述

1. **收藏按钮和 CALL PROC 按钮被按下时不应获得焦点**：当前时有时无，行为不一致
2. **CALL 指令填入含待填写部分时应自动弹键盘**：当前能自动选中第一个 `<...>` 占位符，但不弹键盘

## 根因分析

### 问题1：按钮获得焦点

- `focus:outline-none` 仅移除视觉轮廓，不阻止元素获得焦点
- 移动端按钮获得焦点可能导致意外高亮或键盘行为
- 需要在 mousedown 阶段阻止默认行为（`preventDefault`），从而阻止按钮获得焦点

### 问题2：键盘不弹出

- `selectProcedure()` 是 async 函数，内部 `await fetch()` 导致用户手势上下文丢失
- 移动端浏览器要求 `focus()` 必须在用户手势的同步调用链中才能触发虚拟键盘
- `focusTextarea()` 内部使用 `nextTick`，进一步脱离了用户手势上下文
- `fillSelect/fillInsert/fillUpdate/fillDelete` 虽然是同步的，但 `nextTick` 延迟也可能打断手势链

---

## 任务列表

### Task 1: 为收藏按钮和 CALL PROC 按钮添加防止聚焦机制

**文件**: `mysql_web_console/static/index.html`

**修改内容**:

- 收藏按钮（⭐ 收藏）：添加 `@mousedown.prevent` 事件修饰符，阻止 mousedown 默认行为（即阻止焦点转移）
- CALL PROC 按钮：同样添加 `@mousedown.prevent`
- textarea 内的星号收藏按钮：同样添加 `@mousedown.prevent`
- 检查所有其他辅助按钮（Tab、清空、SELECT/INSERT/UPDATE/DELETE、复制 Markdown、下载 CSV 等），对不需要聚焦的按钮统一添加 `@mousedown.prevent`
- 保留 `focus:outline-none` 作为视觉兜底

**预期效果**: 点击这些按钮时，按钮本身不会获得焦点，不会出现蓝色高亮框，也不会因焦点变化导致键盘意外弹出或收起

---

### Task 2: 修复 focusTextarea() 函数，确保在用户手势上下文中调用

**文件**: `mysql_web_console/static/index.html`

**修改内容**:

- 重写 `focusTextarea()` 函数：
  - 移除 `nextTick` 包裹，改为直接同步调用 `ta.focus()`
  - 在 `ta.focus()` 之后，使用 `requestAnimationFrame` 或短延时 `setTimeout(0)` 来设置 `selectionStart/selectionEnd`（选区设置不需要用户手势上下文，但 focus 需要）
  - 如果 `ta.focus()` 返回后需要确认焦点已生效，可增加 `ta.click()` 作为移动端兼容方案
- 确保函数返回一个可链式调用的结构，方便调用方判断是否成功聚焦

**预期效果**: `focusTextarea()` 在同步用户手势链中调用时能可靠弹出键盘

---

### Task 3: 修复 selectProcedure() 中的键盘弹出问题

**文件**: `mysql_web_console/static/index.html`

**修改内容**:

- 在 `selectProcedure()` 函数中，将 `focusTextarea()` 的调用时机提前到 fetch 之前
- 具体策略：
  1. 在 fetch 之前先调用 `ta.focus()`（此时仍在用户手势上下文中），确保键盘弹出
  2. fetch 完成后设置 `sql.value`
  3. 再通过 `requestAnimationFrame` 设置选区（选中第一个 `<...>` 占位符）
- 或者采用替代方案：先同步设置一个临时的 `sql.value`（如 `CALL name(...)` 占位），立即 `focusTextarea()`，然后再 fetch 更新参数详情

**预期效果**: 选择 Procedure 后，textarea 获得焦点并弹出键盘，同时正确选中第一个待填写占位符

---

### Task 4: 修复 fillSelect/fillInsert/fillUpdate/fillDelete 中的键盘弹出

**文件**: `mysql_web_console/static/index.html`

**修改内容**:

- 这些函数已经是同步的，问题在于 `focusTextarea()` 内部的 `nextTick`
- Task 2 修复 `focusTextarea()` 后，这些函数应自动受益
- 验证这四个函数在移动端点击 SELECT/INSERT/UPDATE/DELETE 按钮后键盘能正常弹出

**预期效果**: 点击表操作按钮后，textarea 获得焦点、键盘弹出、占位符被选中

---

### Task 5: 全面测试与边界情况处理

**测试场景**:

1. 点击收藏按钮 → 按钮不应获得焦点，不应弹键盘
2. 点击 CALL PROC 按钮 → 按钮不应获得焦点，下拉菜单正常展开
3. 选择一个有 IN 参数的 Procedure → textarea 获得焦点，键盘弹出，第一个 `<参数名>` 被选中
4. 选择一个无参数的 Procedure → textarea 获得焦点，键盘弹出，光标在末尾
5. 点击 SELECT/INSERT/UPDATE/DELETE → textarea 获得焦点，键盘弹出，第一个 `<...>` 被选中
6. 点击 textarea 内的星号收藏按钮 → 按钮不应获得焦点，收藏功能正常
7. 在已有焦点状态下操作 → 行为一致，无闪烁
8. iOS Safari 和 Android Chrome 分别测试键盘弹出行为

**边界情况**:

- 快速连续点击按钮
- 网络延迟导致 fetch 较慢时键盘行为
- 从收藏列表选择 SQL 后的焦点状态

---

## 实施优先级

1. **Task 1** - 防止按钮聚焦（独立，无依赖）
2. **Task 2** - 修复 focusTextarea（核心修复，Task 3/4 依赖）
3. **Task 3** - 修复 selectProcedure 键盘弹出（依赖 Task 2）
4. **Task 4** - 验证 fill 系列函数（依赖 Task 2）
5. **Task 5** - 全面测试（依赖所有前置任务）
