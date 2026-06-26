# 收藏 & PROC 合并选择页 开发计划

## 概述

将「⭐ 收藏」和「CALL PROC」两个独立下拉合并为一个按钮，点击后进入全屏选择页面。页面内上方为收藏列表，下方为 PROC 列表，按条目数量动态分配空间（较窄者不小于 3 条高度）。点击条目后自动返回主页并填入 SQL。

---

## Phase 1：状态与数据准备

- [x] 1.1 新增 Vue data 属性 `pickerView: false`，控制选择页的显示/隐藏
- [x] 1.2 确认 `favorites`、`filteredFavorites`、`favSearch`、`procList`、`filteredProcList`、`procSearch` 等数据属性已存在且可用
- [x] 1.3 新增 computed 属性 `pickerFavFlex` 和 `pickerProcFlex`，根据条目数量计算两区域 flex 比例：
  - 按条目数比例分配
  - 较窄区域最小高度 = 3 条 × 条目行高（约 44px），即 flex 最小值不低于 3 对应的比例
  - 若某列表为空，另一列表占满（保留空状态提示的最小高度）

## Phase 2：合并入口按钮

- [x] 2.1 将原来两行的「⭐ 收藏」按钮和「CALL PROC」按钮替换为单个按钮，文案如「📋 收藏 / PROC」
  - 样式与现有下拉按钮保持一致
  - 点击后设置 `pickerView = true`
- [x] 2.2 删除原来的两行下拉按钮 HTML（收藏下拉、PROC 下拉）
- [x] 2.3 删除 `favOpen`、`procDropdownOpen` 相关的下拉开关逻辑（保留数据本身）

## Phase 3：选择页面 UI

- [x] 3.1 页面结构（全屏覆盖，与现有 favNameDialog 的 fixed 模式一致）：
  ```
  fixed inset-0 bg-gray-900 z-40
  ├── 顶部导航栏：返回按钮 + 标题「收藏 & Procedure」
  ├── 收藏区域（flex 动态高度）
  │   ├── Section 标题 + 搜索框
  │   └── 条目列表（独立滚动）
  ├── PROC 区域（flex 动态高度）
  │   ├── Section 标题 + 搜索框
  │   └── 条目列表（独立滚动）
  ```
- [x] 3.2 顶部导航栏：
  - 左侧返回按钮「← 返回」，点击 `pickerView = false`
  - 中间标题
  - 与主页 header 风格统一
- [x] 3.3 收藏区域：
  - Section 标题「⭐ 收藏」+ 条目计数
  - 搜索框（绑定 favSearch，与现有一致）
  - 条目列表：每条显示名称 + SQL 预览，右侧删除按钮（与现有一致）
  - 点击条目 → `sql = fav.sql; pickerView = false; favSearch = ''`
  - 空状态提示与现有一致
- [x] 3.4 PROC 区域：
  - Section 标题「CALL PROC」+ 条目计数
  - 搜索框（绑定 procSearch，与现有一致）
  - 条目列表：每条显示 procedure 名称（与现有一致）
  - 点击条目 → 调用 `selectProcedure(name)` 并 `pickerView = false`
  - 空状态提示与现有一致
- [x] 3.5 高度分配逻辑：
  - 两区域使用 flex 布局，通过 `flex` 值动态分配
  - 各区域内部列表 `overflow-y: auto` 独立滚动
  - 较窄区域最小高度保证 3 条目可滚动

## Phase 4：交互细节

- [x] 4.1 进入选择页时，自动聚焦收藏搜索框（方便快速筛选）
- [x] 4.2 选择条目后清空搜索词，避免下次进入残留
- [x] 4.3 返回时同样清空搜索词
- [x] 4.4 收藏删除操作留在选择页内完成，不跳转（与现有一致）
- [x] 4.5 favNameDialog（收藏命名弹窗）仍从 textarea 旁的星号按钮触发，不受影响

## Phase 5：清理与验证

- [x] 5.1 删除不再使用的 `favOpen`、`procDropdownOpen` data 属性及相关逻辑
- [x] 5.2 删除原来下拉菜单的 HTML 代码
- [ ] 5.3 验证移动端布局：条目高度、滚动、返回、填入均正常
- [ ] 5.4 验证桌面端布局：同样可用且美观
- [ ] 5.5 验证边界情况：空收藏 + 空 PROC、仅一方有数据、搜索无结果
