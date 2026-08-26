# ERPNext 16 关联单据流转工作台重构与链路追溯系统设计方案 (v1.0)

> **版本**：v1.0.0-rc1  
> **创建日期**：2026-08-26  
> **实施分支**：`feat/related-document-workbenches-v1`  
> **基线标签**：`workbench-relations-v1-baseline-f6b81a3`  
> **设计遵循**：Ashan UI/UX 1.7.0 规范，业务参数与字段存在性动态读取，无装饰性 Emoji，动态计算与严格流转守恒。

---

## 1. 业务背景与重构目标

在 ERPNext 16 自定义采购与结算工作台中，操作员录单时需直接洞察行明细在整条供应链中的闭环状态，防止“重复采购”、“重复收货”或“重复付款”。

本次重构覆盖 6 大核心工作台：
1. **物料申请工作台** (`/desk/material-request-workbench`)：业务起点，展示物料申请下游生成的采购订单与收货单闭环进度。
2. **采购执行工作台** (`/desk/procurement-execution-workbench`)：物料申请到采购订单，追踪申请量、已订购量、待采购缺口与采购草稿占用。
3. **收货入库工作台** (`/desk/material-receipt-workbench`)：采购订单到采购入库，追踪订单量、已收货量、待入库缺口与入库草稿占用（自动排除非库存服务项）。
4. **月结补录工作台** (`/desk/monthly-settlement-picker`)：采购入库到采购发票，追踪入库量/金额、已开票、待开票缺口与开票草稿占用。
5. **报销申请工作台** (`/desk/reimbursement-picker`)：费用发票到报销单再到付款单，追踪个人垫付发票报销结算链路。
6. **自办电汇工作台** (`/desk/wire-transfer-picker`)：采购发票到付款单，追踪对公发票待付余额与支付凭证。

---

## 2. 数量与金额守恒定义 (Strict Quantities & Amounts Contract)

为杜绝重复建单与重复付款，系统严格区分三个量化指标：

1. **业务未完成量 (Business Remaining Qty / Amount)**：
   - 上游单据已提交（`docstatus = 1`）但标准下游已提交单据尚未覆盖的数量或金额。
   - 示例：`申请数量 - 已提交采购数量`。
2. **草稿占用量 (Draft Claim Qty / Amount)**：
   - 已创建下游草稿（`docstatus = 0`）并引用了该行明细，但尚未最终提交的数量或金额。
   - 绝不将草稿数量重复计入 ERPNext 标准的 `ordered_qty` 或 `received_qty`。
3. **当前可新建量 (Actionable Qty / Amount)**：
   $$\text{Actionable} = \max(\text{Business Remaining} - \text{Draft Claim}, 0)$$
   - 当 `Actionable = 0` 且 `Draft Claim > 0` 时，系统标示 `草稿处理中`，提供“继续处理草稿”入口，并禁止重复新建。

---

## 3. 字段事实源规范 (Metadata Truth & Strict Schema)

经实机环境 Metadata 审计：
- **物料规格字段**：`Material Request Item` 的正式规格字段为 `description`，数据库中不存在 `custom_spec_model`；其他子表（PO Item / PR Item / PI Item）采用动态字段探测机制 (`_meta_has`)，禁止硬编码不存在的列名。
- **行级关联主外键**：
  - `Purchase Order Item` $\rightarrow$ `material_request`, `material_request_item`
  - `Purchase Receipt Item` $\rightarrow$ `purchase_order`, `purchase_order_item`, `material_request`, `material_request_item`
  - `Purchase Invoice Item` $\rightarrow$ `purchase_order`, `po_detail`, `purchase_receipt`, `pr_detail`
  - `Payment Entry Reference` $\rightarrow$ `reference_doctype`, `reference_name`

---

## 4. 架构分层与安全边界 (Architecture & Security Boundaries)

1. **共享后端服务 (`document_relation_service.py`)**：
   - 批量列表摘要接口 `get_relation_summaries(stage, rows, company)`：批量聚合 SQL 计算，严禁 N+1 逐行查询。
   - 穿透钻取接口 `get_document_relation_chain(doctype, name, item_name, company)`：白名单校验 DocType，严格校验公司与读取权限。
2. **共享前端组件 (`document_relation_chain.js` / `.css`)**：
   - 双行高密度单元格：上层主关联单号，下层已处理/待处理/草稿占用状态胶囊。
   - 纯净钻取弹窗：树状呈现链路，点击直接跳转标准表单。
   - 保持鼠标滚轮转横向漫游机制，内容区保持原生垂直滚动。

---

## 5. 版本化提交序列与回滚手册 (Commit Pipeline & Rollback Guide)

### 5.1 提交序列
1. `docs(workbenches): define related-document chain architecture`
2. `test(workbenches): add relation summary and draft claim test suite`
3. `feat(workbenches): add shared document relation service`
4. `feat(ui): add shared relation cell and drill-down component`
5. `feat(procurement): add MR to PO relation tracking`
6. `feat(procurement): add PO to PR relation tracking`
7. `feat(procurement): add material request downstream tracking`
8. `feat(settlement): add PR to PI relation tracking`
9. `feat(reimbursement): add reimbursement settlement chain`
10. `refactor(wire-transfer): use shared relation-chain component`
11. `docs(release): add deployment verification and rollback guide`

### 5.2 紧急回滚指南
```bash
# 秒级回滚到基线状态
cd /opt/data/repos/erpnext-private-customizations
git switch main
git reset --hard workbench-relations-v1-baseline-f6b81a3
```
