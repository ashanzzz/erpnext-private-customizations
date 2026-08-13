# ERPNext 16 UI GUIDE

> 目标：让 custom app 的页面现代、清楚、信息密度合理，同时保持 ERPNext / Frappe Desk 的原生操作习惯。

## 1. UI 技术选择

按复杂度逐级选择：

```text
原生 Form / List / Report
↓
Form Script / Dialog
↓
Desk Page
↓
Vue in Desk Page
↓
Frappe UI / 独立复杂前端
```

不要从 Vue 开始。

先判断工作流。

## 2. 原生优先

如果 ERPNext 已经提供：

- Form
- List
- Grid
- Report
- Workspace
- Dialog
- Timeline
- Attachments
- Comments
- Submit / Cancel
- Permission

优先使用这些能力。

自定义 UI 应该是因为业务工作方式不同，而不是为了“看起来像 SaaS”。

## 3. 现代 UI 的定义

推荐：

```text
清楚
数据优先
低视觉噪音
状态明确
容易快速扫描
可以核对依据
操作结果可见
```

避免：

```text
大面积渐变
玻璃效果
过多阴影
每个字段一个卡片
无意义图表
巨大的空白
五个同等级主按钮
只为了效果的动画
```

## 4. 页面结构

推荐：

```text
页面身份
状态
主操作

核心数据

需要用户判断的结果

依据 / evidence

详情

次要操作
```

## 5. 主操作

一个页面通常只保留一个明显的 Primary Action。

例如 AI 发票页面：

```text
[运行匹配]
```

次要：

```text
刷新
打开发票
打开入库单
重新计算
取消
```

不可逆操作要有确认。

## 6. 表格优先于卡片堆叠

ERP 业务通常更适合表格。

例如：

```text
入库单 | 日期 | 供应商 | 金额 | 物料匹配 | 数量匹配 | 可信度 | 状态
```

不要把每一列改成独立卡片。

## 7. AI 结果必须可解释

AI 页面至少显示：

```text
推荐对象
confidence
匹配依据
冲突项
候选项
源单据
人工操作
```

示例：

```text
推荐入库单
MAT-PRE-2026-00118

可信度
94%

依据
供应商       完全一致
金额         完全一致
物料         8/8
数量         7/8
日期差       3 天

冲突
ITEM-003 数量差 1

[打开入库单] [拒绝] [确认关联]
```

## 8. 财务 / 库存 AI UX

默认：

```text
AI 推荐
↓
用户查看
↓
服务器重新验证
↓
ERPNext 执行
```

不要：

```text
AI 猜测
↓
浏览器直接写数据库
```

## 9. Loading / Empty / Error

每个异步区域都应该有：

```text
Idle
Loading
Success
Empty
Error
Retry
```

不要点击按钮后页面没有任何反馈。

## 10. 错误信息

差：

```text
Error
```

好：

```text
无法加载 Purchase Receipt 候选项。

发票
PINV-2026-0012

原因
当前用户没有 Purchase Receipt 读取权限。

[重试]
```

用户 UI 不显示不必要的 Secret 或完整 traceback。

## 11. Desk Page 适用场景

适合：

- 发票匹配中心
- 对账中心
- 批量审批
- 异常处理
- 跨 DocType 审核
- 导入复核
- AI 建议工作台

基础：

```javascript
frappe.pages["invoice-ai"].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Invoice AI"),
        single_column: true,
    });

    page.set_primary_action(__("Run AI Match"), () => {
        run_match();
    });
};
```

## 12. Vue 适用场景

当页面需要大量 reactive state：

- 当前发票
- 多候选入库单
- 筛选
- 分页
- AI evidence
- 多步骤确认
- Background Job 进度
- Retry 状态
- 批量勾选

再使用 Vue。

## 13. Frappe UI

Frappe UI 更适合大型 Vue 前端。

不要假设所有 Desk 页面天然全局存在 `frappe-ui` 组件。

按项目 bundling 配置使用。

## 14. v16 Navigation

v16 引入 persistent sidebar 和 Workspace Sidebar。

原则：

- 不自己重画 ERPNext 全局导航
- 不把旧 `/app` 路由写死
- 优先使用 `frappe.set_route`
- 检查实际 v16 Site 路由
- 自定义 App 的 Workspace / Apps 展示按 v16 官方机制配置

## 15. v16 JS Scope

Reports / Dashboard Charts / Pages 的 JS 在 v16 改为 IIFE 执行。

避免依赖隐式全局变量。

确需全局：

```javascript
window.my_app = window.my_app || {};
```

## 16. 性能

不要一次把几千条 ERPNext Document 全部拉进浏览器。

使用：

```text
服务器过滤
分页
只请求需要字段
background job
渐进加载
```

## 17. 官方设计资料

```text
Page API
https://docs.frappe.io/framework/user/en/api/page

Vue inside Desk
https://docs.frappe.io/framework/using-vue-inside-a-desk-page

Frappe UI
https://ui.frappe.io/docs/introduction

Frappe Design
https://frappe.io/design

Espresso Design System
https://frappe.io/design/espresso

v16 Migration
https://github.com/frappe/frappe/wiki/Migrating-to-version-16
```
