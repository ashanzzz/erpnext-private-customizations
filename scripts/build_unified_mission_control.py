# -*- coding: utf-8 -*-
import json
import os

html = """<div class="mission-control-container">

  <!-- ============================================================ -->
  <!-- 🌟 顶层总控条：三维任务健康状态总览 (Mission Status Bar)       -->
  <!-- ============================================================ -->
  <div class="mission-status-bar">
    <div class="status-bar-left">
      <span class="mission-logo-tag">🎯 总控中枢</span>
      <div class="status-capsules-group">
        <div class="status-capsule capsule-today" id="cap-today">
          <span class="cap-dot"></span>
          <span class="cap-text" id="cap-text-today">日常待办：计算中…</span>
        </div>
        <div class="status-capsule capsule-month" id="cap-month">
          <span class="cap-dot"></span>
          <span class="cap-text" id="cap-text-month">月度任务：计算中…</span>
        </div>
        <div class="status-capsule capsule-expiry" id="cap-expiry">
          <span class="cap-dot"></span>
          <span class="cap-text" id="cap-text-expiry">周期任务：计算中…</span>
        </div>
      </div>
    </div>
    <div class="status-bar-right">
      <button type="button" class="btn-refresh-all" id="btn-refresh-all-data" title="刷新全看板动态数据">
        <span class="icon-spin">🔄</span> 刷新全盘
      </button>
    </div>
  </div>

  <!-- ============================================================ -->
  <!-- 🚀 极速录单与业务直达通道 (Fast-Entry Action Strip)            -->
  <!-- ============================================================ -->
  <div class="mission-quick-actions-strip">
    <div class="quick-actions-label">
      <span class="quick-actions-icon">⚡</span>
      <span class="quick-actions-text">极速业务通道:</span>
    </div>
    <div class="quick-actions-btns">
      <a href="/desk/material-request-workbench" class="quick-action-btn btn-qa-blue" data-workbench-route="material-request-workbench">
        <span class="qa-icon">➕</span> 提物料申请
      </a>
      <a href="/desk/wire-transfer-picker" class="quick-action-btn btn-qa-purple" data-workbench-route="wire-transfer-picker">
        <span class="qa-icon">⚡</span> 自办电汇录单
      </a>
      <a href="/desk/monthly-settlement-picker" class="quick-action-btn btn-qa-teal" data-workbench-route="monthly-settlement-picker">
        <span class="qa-icon">📅</span> 月结补录录单
      </a>
      <a href="/desk/reimbursement-picker" class="quick-action-btn btn-qa-orange" data-workbench-route="reimbursement-picker">
        <span class="qa-icon">📑</span> 员工报销申请
      </a>
      <a href="/desk/oil-card-refuel-log/new" class="quick-action-btn btn-qa-slate" data-route="oil-card-refuel-log/new">
        <span class="qa-icon">⛽</span> 加油能耗登记
      </a>
      <a href="/desk/qifu-payroll-center" class="quick-action-btn btn-qa-indigo" data-workbench-route="qifu-payroll-center">
        <span class="qa-icon">🛡️</span> 祺富薪酬中心
      </a>
    </div>
  </div>

  <!-- ============================================================ -->
  <!-- 🏛️ 核心总控舱：左右分工黄金网格 (Mission Control Grid)        -->
  <!-- ============================================================ -->
  <div class="mission-main-grid">

    <!-- ========== 左侧大栏 (58%): 日常待办 ========== -->
    <div class="mission-grid-col col-left" id="my-tasks-container">
      <div class="panel-card panel-today-tasks">
        <div class="panel-header">
          <div class="panel-title-wrapper">
            <span class="panel-icon">📋</span>
            <span class="panel-title">日常待办</span>
            <span class="panel-badge">工作台穿透 · 批量秒级处理</span>
          </div>
        </div>

        <div class="today-tasks-subgrid">
          <!-- 任务 1：待采购下单 -->
          <div class="task-pill-card task-card-amber" id="task-card-po" data-task-perm="Purchase Order" data-doctype="Material Request">
            <div class="task-pill-top">
              <span class="task-pill-icon">🟡</span>
              <div class="task-pill-meta">
                <span class="task-pill-name">待采购下单</span>
                <span class="task-pill-sub">已批采购需求</span>
              </div>
            </div>
            <div class="task-pill-bottom">
              <div class="task-count-pill is-loading" id="pill-po">
                <span class="pill-dot"></span>
                <span class="pill-text" id="pill-text-po">统计中…</span>
              </div>
              <a href="/desk/procurement-execution-workbench#stage=mr_to_po" class="task-action-btn" id="act-po" data-workbench-route="procurement-execution-workbench#stage=mr_to_po">
                去采购 ➔
              </a>
            </div>
          </div>

          <!-- 任务 2：待物资入库 -->
          <div class="task-pill-card task-card-green" id="task-card-pr" data-task-perm="Purchase Receipt" data-doctype="Purchase Order">
            <div class="task-pill-top">
              <span class="task-pill-icon">🟢</span>
              <div class="task-pill-meta">
                <span class="task-pill-name">待物资入库</span>
                <span class="task-pill-sub">全员公共入库池</span>
              </div>
            </div>
            <div class="task-pill-bottom">
              <div class="task-count-pill is-loading" id="pill-pr">
                <span class="pill-dot"></span>
                <span class="pill-text" id="pill-text-pr">统计中…</span>
              </div>
              <a href="/desk/material-receipt-workbench" class="task-action-btn" id="act-pr" data-workbench-route="material-receipt-workbench">
                去入库 ➔
              </a>
            </div>
          </div>

          <!-- 任务 3：待采购开票 -->
          <div class="task-pill-card task-card-blue" id="task-card-pi" data-task-perm="Purchase Invoice" data-doctype="Purchase Receipt">
            <div class="task-pill-top">
              <span class="task-pill-icon">🔵</span>
              <div class="task-pill-meta">
                <span class="task-pill-name">待采购开票</span>
                <span class="task-pill-sub">入库待录发票</span>
              </div>
            </div>
            <div class="task-pill-bottom">
              <div class="task-count-pill is-loading" id="pill-pi">
                <span class="pill-dot"></span>
                <span class="pill-text" id="pill-text-pi">统计中…</span>
              </div>
              <a href="/desk/procurement-execution-workbench#stage=pr_to_pi" class="task-action-btn" id="act-pi" data-workbench-route="procurement-execution-workbench#stage=pr_to_pi">
                去开票 ➔
              </a>
            </div>
          </div>

          <!-- 任务 4：待整算审批 -->
          <div class="task-pill-card task-card-purple" id="task-card-rr" data-task-perm="Reimbursement Request" data-doctype="Reimbursement Request">
            <div class="task-pill-top">
              <span class="task-pill-icon">🟣</span>
              <div class="task-pill-meta">
                <span class="task-pill-name">待整算审批</span>
                <span class="task-pill-sub">发票关联整算</span>
              </div>
            </div>
            <div class="task-pill-bottom">
              <div class="task-count-pill is-loading" id="pill-rr">
                <span class="pill-dot"></span>
                <span class="pill-text" id="pill-text-rr">统计中…</span>
              </div>
              <a href="/desk/procurement-execution-workbench#stage=pi_to_rr" class="task-action-btn" id="act-rr" data-workbench-route="procurement-execution-workbench#stage=pi_to_rr">
                去整算 ➔
              </a>
            </div>
          </div>

          <!-- 任务 5：待对公付款 -->
          <div class="task-pill-card task-card-red" id="task-card-pay" data-task-perm="Payment Entry" data-doctype="Purchase Invoice">
            <div class="task-pill-top">
              <span class="task-pill-icon">🔴</span>
              <div class="task-pill-meta">
                <span class="task-pill-name">待对公付款</span>
                <span class="task-pill-sub">采购发票结清</span>
              </div>
            </div>
            <div class="task-pill-bottom">
              <div class="task-count-pill is-loading" id="pill-pay">
                <span class="pill-dot"></span>
                <span class="pill-text" id="pill-text-pay">统计中…</span>
              </div>
              <a href="/desk/procurement-execution-workbench#stage=pi_to_pay" class="task-action-btn" id="act-pay" data-workbench-route="procurement-execution-workbench#stage=pi_to_pay">
                去付款 ➔
              </a>
            </div>
          </div>

          <!-- 任务 6：待发起报销 -->
          <div class="task-pill-card task-card-orange" id="task-card-reim" data-task-perm="Reimbursement Request" data-doctype="Purchase Invoice">
            <div class="task-pill-top">
              <span class="task-pill-icon">🟠</span>
              <div class="task-pill-meta">
                <span class="task-pill-name">待发起报销</span>
                <span class="task-pill-sub">我垫付的发票</span>
              </div>
            </div>
            <div class="task-pill-bottom">
              <div class="task-count-pill is-loading" id="pill-reim">
                <span class="pill-dot"></span>
                <span class="pill-text" id="pill-text-reim">统计中…</span>
              </div>
              <a href="/desk/reimbursement-picker" class="task-action-btn" id="act-reim" data-workbench-route="reimbursement-picker">
                去报销 ➔
              </a>
            </div>
          </div>

        </div>
      </div>
    </div>

    <!-- ========== 右侧协同栏 (40%): 月度任务 + 周期任务 ========== -->
    <div class="mission-grid-col col-right">

      <!-- 模块 1: 月度任务 -->
      <div class="panel-card panel-monthly-tasks" id="periodic-tasks-container">
        <div class="panel-header">
          <div class="panel-title-wrapper">
            <span class="panel-icon">📅</span>
            <span class="panel-title">月度任务</span>
            <span class="panel-badge" id="periodic-period-badge">各事项按月自动感知</span>
          </div>
        </div>

        <div class="monthly-companies-wrap" id="periodic-companies-grid">
          <!-- 吉众 -->
          <div class="comp-subcard" id="company-card-jizhong">
            <div class="comp-subcard-hdr">
              <span class="comp-subcard-title" id="jizhong-subcard-title">🏢 吉众 · 月度核定</span>
              <span class="company-status-badge" id="jizhong-status-badge">核定中</span>
            </div>
            <div class="comp-items-box" id="jizhong-items-list">
              <div class="periodic-loading">核定中…</div>
            </div>
          </div>

          <!-- 祺富 -->
          <div class="comp-subcard" id="company-card-qifu">
            <div class="comp-subcard-hdr">
              <span class="comp-subcard-title" id="qifu-subcard-title">🏭 祺富 · 月度核定</span>
              <span class="company-status-badge" id="qifu-status-badge">核定中</span>
            </div>
            <div class="comp-items-box" id="qifu-items-list">
              <div class="periodic-loading">核定中…</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 模块 2: 周期任务 (合规与证照合同) -->
      <div class="panel-card panel-expiry-tasks" id="compliance-expiry-container">
        <div class="panel-header">
          <div class="panel-title-wrapper">
            <span class="panel-icon">⏳</span>
            <span class="panel-title">周期任务</span>
            <span class="panel-badge" id="expiry-summary-badge">核验中…</span>
          </div>
        </div>

        <div class="expiry-items-container" id="expiry-items-list">
          <div class="periodic-loading">正在拉取合规与周期检测倒计时…</div>
        </div>
      </div>

    </div>

  </div>
</div>
"""

css = """/* ================= 全局容器 ================= */
.mission-control-container {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px 20px;
  box-sizing: border-box;
  width: 100%;
}

/* ================= 顶层总控条 (Mission Status Bar) ================= */
.mission-status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 14px;
  margin-bottom: 12px;
}

.status-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.mission-logo-tag {
  font-size: 13px;
  font-weight: 800;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-capsules-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.status-capsule {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #cbd5e1;
  color: #475569;
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}

.status-capsule .cap-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #94a3b8;
}

.status-capsule.has-pending {
  background: #fef2f2;
  color: #dc2626;
  border-color: #fca5a5;
}
.status-capsule.has-pending .cap-dot {
  background: #ef4444;
  animation: pulse-dot 1.5s infinite;
}

.status-capsule.all-done {
  background: #f0fdf4;
  color: #16a34a;
  border-color: #86efac;
}
.status-capsule.all-done .cap-dot {
  background: #22c55e;
}

.btn-refresh-all {
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.15s ease;
}
.btn-refresh-all:hover {
  background: #f8fafc;
  border-color: #94a3b8;
  color: #0f172a;
}

/* ================= 🚀 极速录单通道条 (Quick Actions Strip) ================= */
.mission-quick-actions-strip {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 7px 12px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.quick-actions-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 700;
  color: #334155;
  margin-right: 4px;
}

.quick-actions-btns {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.quick-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 6px;
  text-decoration: none !important;
  transition: all 0.15s ease;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}

.btn-qa-blue {
  background: #eff6ff;
  color: #1d4ed8 !important;
  border: 1px solid #bfdbfe;
}
.btn-qa-blue:hover {
  background: #1d4ed8;
  color: #fff !important;
  border-color: #1d4ed8;
}

.btn-qa-purple {
  background: #fbf5ff;
  color: #7e22ce !important;
  border: 1px solid #e9d5ff;
}
.btn-qa-purple:hover {
  background: #7e22ce;
  color: #fff !important;
  border-color: #7e22ce;
}

.btn-qa-teal {
  background: #f0fdfa;
  color: #0f766e !important;
  border: 1px solid #99f6e4;
}
.btn-qa-teal:hover {
  background: #0f766e;
  color: #fff !important;
  border-color: #0f766e;
}

.btn-qa-orange {
  background: #fff7ed;
  color: #c2410c !important;
  border: 1px solid #fed7aa;
}
.btn-qa-orange:hover {
  background: #c2410c;
  color: #fff !important;
  border-color: #c2410c;
}

.btn-qa-slate {
  background: #f1f5f9;
  color: #334155 !important;
  border: 1px solid #cbd5e1;
}
.btn-qa-slate:hover {
  background: #334155;
  color: #fff !important;
  border-color: #334155;
}

.btn-qa-indigo {
  background: #eef2ff;
  color: #4338ca !important;
  border: 1px solid #c7d2fe;
}
.btn-qa-indigo:hover {
  background: #4338ca;
  color: #fff !important;
  border-color: #4338ca;
}

/* ================= 核心双栏总控网格 (Mission Main Grid) ================= */
.mission-main-grid {
  display: grid;
  grid-template-columns: 58% 40%;
  gap: 16px;
  align-items: start;
}

@media (max-width: 1200px) {
  .mission-main-grid {
    grid-template-columns: 1fr;
  }
}

.panel-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px;
  box-sizing: border-box;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
}

.panel-title-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-icon {
  font-size: 14px;
}

.panel-title {
  font-size: 13.5px;
  font-weight: 700;
  color: #0f172a;
}

.panel-badge {
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 10px;
  background: #e2e8f0;
  color: #475569;
  font-weight: 500;
}
.panel-badge.badge-pending {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
  font-weight: 600;
}
.panel-badge.badge-done {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
  font-weight: 600;
}

/* ================= 日常待办 6 宫格子网格 ================= */
.today-tasks-subgrid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

@media (max-width: 900px) {
  .today-tasks-subgrid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.task-pill-card {
  background: #fff;
  border-radius: 8px;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 82px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
  transition: all 0.15s ease;
}
.task-pill-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 6px rgba(0,0,0,0.04);
}

.task-card-amber { border-left: 3.5px solid #f59e0b; }
.task-card-green { border-left: 3.5px solid #10b981; }
.task-card-blue  { border-left: 3.5px solid #3b82f6; }
.task-card-purple{ border-left: 3.5px solid #8b5cf6; }
.task-card-red   { border-left: 3.5px solid #ef4444; }
.task-card-orange{ border-left: 3.5px solid #f97316; }

.task-pill-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.task-pill-icon {
  font-size: 13px;
}

.task-pill-meta {
  display: flex;
  flex-direction: column;
}

.task-pill-name {
  font-size: 12px;
  font-weight: 700;
  color: #1e293b;
}

.task-pill-sub {
  font-size: 10px;
  color: #64748b;
}

.task-pill-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-count-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #475569;
}
.task-count-pill .pill-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #94a3b8;
}
.task-count-pill.has-pending {
  color: #dc2626;
  font-weight: 600;
}
.task-count-pill.has-pending .pill-dot {
  background: #ef4444;
}
.task-count-pill.is-done {
  color: #16a34a;
}
.task-count-pill.is-done .pill-dot {
  background: #22c55e;
}

.task-action-btn {
  font-size: 10.5px;
  font-weight: 700;
  color: #2563eb;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 4px;
  padding: 2px 7px;
  text-decoration: none !important;
  cursor: pointer;
  transition: all 0.15s ease;
}
.task-action-btn:hover {
  background: #2563eb;
  color: #fff !important;
}
.task-action-btn.is-disabled {
  opacity: 0.5;
  pointer-events: none;
}

/* ================= 右侧月度任务与周期任务 ================= */
.panel-monthly-tasks {
  margin-bottom: 14px;
}

.monthly-companies-wrap {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.comp-subcard {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 12px;
}

.comp-subcard-hdr {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.comp-subcard-title {
  font-size: 12px;
  font-weight: 700;
  color: #1e293b;
}

.company-status-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 8px;
  background: #f1f5f9;
  color: #475569;
  font-weight: 600;
}
.company-status-badge.badge-pending {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}
.company-status-badge.badge-done {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}

.comp-items-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.monthly-item-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #f1f5f9;
}

.monthly-item-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.monthly-item-meta {
  display: flex;
  flex-direction: column;
}

.monthly-item-title {
  font-size: 11.5px;
  font-weight: 600;
  color: #0f172a;
}

.monthly-item-summary {
  font-size: 10px;
  color: #64748b;
}

.monthly-item-action {
  font-size: 10.5px;
  font-weight: 700;
  color: #d97706;
  background: #fef3c7;
  border: 1px solid #fde68a;
  border-radius: 4px;
  padding: 2px 7px;
  text-decoration: none !important;
  cursor: pointer;
  transition: all 0.15s ease;
}
.monthly-item-action:hover {
  background: #d97706;
  color: #fff !important;
}
.monthly-item-action.action-done {
  color: #16a34a;
  background: #dcfce7;
  border-color: #bbf7d0;
}

/* ================= 周期任务列表 ================= */
.expiry-items-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 220px;
  overflow-y: auto;
}

.expiry-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  transition: all 0.15s ease;
}
.expiry-row.level-danger {
  border-left: 3px solid #ef4444;
  background: #fffafb;
}
.expiry-row.level-warning {
  border-left: 3px solid #f59e0b;
  background: #fffdfa;
}
.expiry-row.level-info {
  border-left: 3px solid #3b82f6;
}

.expiry-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.expiry-meta {
  display: flex;
  flex-direction: column;
}

.expiry-title {
  font-size: 11.5px;
  font-weight: 600;
  color: #1e293b;
}

.expiry-desc {
  font-size: 10px;
  color: #64748b;
}

.expiry-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.expiry-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
}
.expiry-tag.tag-danger {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}
.expiry-tag.tag-warning {
  background: #fffbeb;
  color: #d97706;
  border: 1px solid #fde68a;
}
.expiry-tag.tag-info {
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
}

.expiry-action-btn {
  font-size: 10px;
  font-weight: 600;
  color: #475569;
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  padding: 2px 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.expiry-action-btn:hover {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}

@keyframes pulse-dot {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.4); opacity: 0.6; }
  100% { transform: scale(1); opacity: 1; }
}

.step-hidden {
  display: none !important;
}
"""

js = """(function () {
  const ROOT = (typeof root_element !== "undefined" && root_element) ? root_element : document;

  function getCurrentUser() {
    return (frappe.session && frappe.session.user) ? frappe.session.user : "";
  }

  function isAdminUser() {
    const u = getCurrentUser();
    return u === "Administrator" || (frappe.user_roles || []).includes("System Manager");
  }

  function isFinanceUser() {
    if (isAdminUser()) return true;
    const roles = frappe.user_roles || [];
    return roles.includes("Accounts User") || roles.includes("Accounts Manager") || roles.includes("财务经理");
  }

  function userCanRead(doctype) {
    if (!doctype) return false;
    if (isAdminUser()) return true;
    if (frappe.model && typeof frappe.model.can_read === "function") {
      return frappe.model.can_read(doctype);
    }
    if (frappe.boot && frappe.boot.user && Array.isArray(frappe.boot.user.can_read)) {
      return frappe.boot.user.can_read.includes(doctype);
    }
    return true;
  }

  function userCanCreate(doctype) {
    if (!doctype) return false;
    if (isAdminUser()) return true;
    if (frappe.model && typeof frappe.model.can_create === "function") {
      return frappe.model.can_create(doctype);
    }
    if (frappe.boot && frappe.boot.user && Array.isArray(frappe.boot.user.can_create)) {
      return frappe.boot.user.can_create.includes(doctype);
    }
    return true;
  }

  function withOwnerFilter(filters) {
    const base = Object.assign({}, (filters || {}));
    if (!isAdminUser()) {
      base.owner = getCurrentUser();
    }
    return base;
  }

  function applyPermissionAdaptation() {
    const taskCards = ROOT.querySelectorAll('.task-pill-card[data-task-perm]');
    taskCards.forEach((card) => {
      const permTarget = card.getAttribute('data-task-perm');
      let isVisible = false;

      if (permTarget === "Payment Entry") {
        isVisible = isFinanceUser() && userCanRead("Purchase Invoice");
      } else if (permTarget === "Purchase Order") {
        isVisible = userCanCreate("Purchase Order") || userCanRead("Material Request");
      } else if (permTarget === "Purchase Receipt") {
        isVisible = userCanCreate("Purchase Receipt") || userCanRead("Purchase Order");
      } else if (permTarget === "Purchase Invoice") {
        isVisible = userCanCreate("Purchase Invoice") || userCanRead("Purchase Receipt");
      } else if (permTarget === "Reimbursement Request") {
        isVisible = userCanCreate("Reimbursement Request") || userCanRead("Purchase Invoice");
      } else {
        isVisible = userCanRead(permTarget);
      }

      if (!isVisible) {
        card.classList.add('step-hidden');
      } else {
        card.classList.remove('step-hidden');
      }
    });
  }

  // ============================================================
  // 3. 通用路由与点击跳转拦截 (支持工作台直通与原生路由)
  // ============================================================
  function bindAllWorkbenchAndRouteLinks() {
    const wbLinks = ROOT.querySelectorAll('[data-workbench-route]');
    wbLinks.forEach((a) => {
      if (a.dataset && a.dataset.wbBound === "1") return;
      if (a.dataset) a.dataset.wbBound = "1";

      a.addEventListener('click', (e) => {
        const isNewTab = e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0;
        if (isNewTab) return;

        e.preventDefault();
        const wbRoute = a.getAttribute('data-workbench-route');
        if (wbRoute) {
          const parts = wbRoute.split('#');
          const routeName = parts[0];
          const hashParam = parts[1] || '';
          if (hashParam) {
            window.location.hash = hashParam;
          }
          frappe.set_route(routeName);
        }
      });
    });
  }

  // ============================================================
  // 4. 日常待办数据统计 (6 大任务实时计算)
  // ============================================================
  let todayTotalPending = 0;
  let todayTaskCounts = { po: 0, pr: 0, pi: 0, rr: 0, pay: 0, reim: 0 };

  function checkUpdateTodayCapsule() {
    const cap = ROOT.querySelector('#cap-today');
    const capText = ROOT.querySelector('#cap-text-today');
    if (!cap || !capText) return;

    todayTotalPending = Object.values(todayTaskCounts).reduce((a, b) => a + b, 0);
    if (todayTotalPending > 0) {
      cap.className = 'status-capsule capsule-today has-pending';
      capText.innerHTML = `日常待办：<b>${todayTotalPending}</b> 笔需处理`;
    } else {
      cap.className = 'status-capsule capsule-today all-done';
      capText.innerHTML = '日常待办：已全部清空 ✅';
    }
  }

  function updateTaskPill(pillId, textId, actId, count, singleUnitLabel, zeroLabel, taskKey) {
    const pill = ROOT.querySelector(pillId);
    const text = ROOT.querySelector(textId);
    const act = ROOT.querySelector(actId);
    if (!pill || !text) return;

    pill.classList.remove('is-loading', 'is-done', 'has-pending');
    todayTaskCounts[taskKey] = count || 0;
    checkUpdateTodayCapsule();

    if ((count || 0) > 0) {
      pill.classList.add('has-pending');
      text.innerHTML = `<b>${count}</b> ${singleUnitLabel}待处理`;
      if (act) {
        act.classList.remove('is-disabled');
      }
    } else {
      pill.classList.add('is-done');
      text.innerHTML = zeroLabel || '已全部处理';
      if (act) {
        act.classList.add('is-disabled');
      }
    }
  }

  function fetchTaskCardCount(doctype, filters, pillId, textId, actId, unitLabel, applyOwner, taskKey) {
    if (!userCanRead(doctype)) return;
    const actualFilters = applyOwner ? withOwnerFilter(filters) : filters;

    frappe.db.count(doctype, { filters: actualFilters })
      .then((count) => {
        updateTaskPill(pillId, textId, actId, count, unitLabel, '已全部处理', taskKey);
      })
      .catch(() => {
        const pill = ROOT.querySelector(pillId);
        const text = ROOT.querySelector(textId);
        if (pill) pill.classList.remove('is-loading');
        if (text) text.innerText = '统计失败';
      });
  }

  function fetchTaskPendingReimbursement() {
    if (!userCanRead('Purchase Invoice')) return;

    const pillId = '#pill-reim';
    const textId = '#pill-text-reim';
    const actId = '#act-reim';

    frappe.call({
      method: 'ashan_cn_procurement.services.periodic_tasks.get_pending_reimbursement_count',
      callback: function(r) {
        const count = (r && r.message) ? (r.message.count || 0) : 0;
        updateTaskPill(pillId, textId, actId, count, '笔发票', '无垫付待报销', 'reim');
      },
      error: function() {
        const pill = ROOT.querySelector(pillId);
        const text = ROOT.querySelector(textId);
        if (pill) pill.classList.remove('is-loading');
        if (text) text.innerText = '0 笔待报销';
      }
    });
  }

  function reloadAllTasks() {
    // 1. 待采购下单
    fetchTaskCardCount('Material Request', { docstatus: 1, status: ['in', ['Submitted', 'Pending', 'Partially Ordered']] }, '#pill-po', '#pill-text-po', '#act-po', '笔申请', false, 'po');
    // 2. 待物资入库
    fetchTaskCardCount('Purchase Order', { docstatus: 1, status: ['in', ['On Hold', 'To Receive', 'To Receive and Bill']] }, '#pill-pr', '#pill-text-pr', '#act-pr', '笔订单', false, 'pr');
    // 3. 待采购开票
    fetchTaskCardCount('Purchase Receipt', { status: ['in', ['Partly Billed', 'To Bill']] }, '#pill-pi', '#pill-text-pi', '#act-pi', '笔入库单', true, 'pi');
    // 4. 待整算审批
    fetchTaskCardCount('Purchase Invoice', { docstatus: 1, custom_biz_mode: ['in', ['现金报销', '综合采购']], outstanding_amount: ['>', 0] }, '#pill-rr', '#pill-text-rr', '#act-rr', '笔发票', false, 'rr');
    // 5. 待对公付款
    fetchTaskCardCount('Purchase Invoice', { docstatus: 1, custom_biz_mode: ['!=', '自办电汇'], outstanding_amount: ['>', 0] }, '#pill-pay', '#pill-text-pay', '#act-pay', '笔发票', false, 'pay');
    // 6. 待发起报销
    fetchTaskPendingReimbursement();
  }

  // ============================================================
  // 5. 发票月度核定关账 Dialog
  // ============================================================
  function openInvoiceClosingDialog(company, period, periodLabel) {
    frappe.call({
      method: 'ashan_cn_procurement.services.invoice_closing_service.get_invoice_closing_data',
      args: { company: company, period: period },
      callback: function(r) {
        if (!r || !r.message) return;
        const d_data = r.message;
        const isLocked = d_data.is_locked;

        const d = new frappe.ui.Dialog({
          title: `🧾 发票月度核定关账 · ${company}`,
          fields: [
            {
              fieldtype: 'HTML',
              fieldname: 'stats_html',
              options: `
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px; margin-bottom:12px;">
                  <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="font-size:13px; font-weight:700; color:#1e293b;">核定账期：${periodLabel || period} (${period})</span>
                    <span style="font-size:12px; font-weight:700; color:${isLocked ? '#16a34a' : '#d97706'};">
                      ${isLocked ? '🔒 已核定关账锁定' : '🟡 草稿 / 未关账'}
                    </span>
                  </div>
                  <div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:8px; font-size:12px;">
                    <div>已录入发票：<b>${d_data.invoice_count}</b> 笔</div>
                    <div>价税总额：<b style="color:#2563eb;">¥ ${format_currency(d_data.total_grand_total)}</b></div>
                    <div>不含税金额：<b>¥ ${format_currency(d_data.total_net_amount)}</b></div>
                    <div>进项税额：<b>¥ ${format_currency(d_data.total_tax_amount)}</b></div>
                  </div>
                  ${isLocked ? `
                    <div style="margin-top:8px; padding-top:8px; border-top:1px dashed #cbd5e1; font-size:11px; color:#64748b;">
                      核定人：${d_data.locked_by || '-'} ｜ 核定时间：${d_data.locked_at || '-'}
                    </div>
                  ` : ''}
                </div>
                ${!isLocked ? `
                  <div style="background:#fffbeb; border:1px solid #fde68a; border-radius:6px; padding:8px 10px; font-size:11.5px; color:#b45309; margin-bottom:12px;">
                    ⚠️ <b>核定锁定说明：</b>核定关账后，系统将<b>严密禁止</b>新增、修改或提交发票日期/记账日期为 <b>${periodLabel || period}</b> 的任何发票！
                  </div>
                ` : ''}
              `
            },
            ...(isLocked ? [
              {
                fieldtype: 'Small Text',
                fieldname: 'unlock_reason',
                label: '反审核解锁原因 (必填)',
                reqd: 1
              }
            ] : [
              {
                fieldtype: 'Small Text',
                fieldname: 'notes',
                label: '核准备注 (选填)'
              }
            ])
          ],
          primary_action_label: isLocked ? '🔓 反审核解锁' : '🔒 确认核定并关账锁定',
          primary_action: function(values) {
            d.get_primary_btn().prop('disabled', true);
            if (isLocked) {
              // 反审核解锁
              frappe.call({
                method: 'ashan_cn_procurement.services.invoice_closing_service.unlock_monthly_invoice_closing',
                args: {
                  company: company,
                  period: period,
                  unlock_reason: values.unlock_reason
                },
                callback: function(res) {
                  d.get_primary_btn().prop('disabled', false);
                  if (res && res.message && res.message.success) {
                    d.hide();
                    frappe.show_alert({ message: res.message.message, indicator: 'orange' }, 5);
                    fetchMonthlySettlementStatus();
                  } else {
                    frappe.msgprint(res.message ? res.message.error : '操作失败');
                  }
                }
              });
            } else {
              // 确认核定关账
              frappe.call({
                method: 'ashan_cn_procurement.services.invoice_closing_service.lock_monthly_invoice_closing',
                args: {
                  company: company,
                  period: period,
                  notes: values.notes
                },
                callback: function(res) {
                  d.get_primary_btn().prop('disabled', false);
                  if (res && res.message && res.message.success) {
                    d.hide();
                    frappe.show_alert({ message: res.message.message, indicator: 'green' }, 5);
                    fetchMonthlySettlementStatus();
                  } else {
                    frappe.msgprint(res.message ? res.message.error : '操作失败');
                  }
                }
              });
            }
          },
          secondary_action_label: '查看当月发票列表 ➔',
          secondary_action: function() {
            d.hide();
            frappe.route_options = {
              company: company,
              posting_date: ['between', [`${period}-01`, `${period}-31`]]
            };
            frappe.set_route('List', 'Purchase Invoice');
          }
        });

        d.show();
      }
    });
  }

  // ============================================================
  // 6. 月度任务逻辑 (每个小项目自适应探测最早未核定月份)
  // ============================================================
  function renderPeriodicCompanyItems(containerSel, badgeSel, titleSel, companyPrefix, items) {
    const box = ROOT.querySelector(containerSel);
    const badge = ROOT.querySelector(badgeSel);
    const titleEl = ROOT.querySelector(titleSel);
    if (!box) return;

    if (titleEl) {
      titleEl.innerText = `${companyPrefix} · 月度核定`;
    }

    if (!items || items.length === 0) {
      box.innerHTML = '<div class="periodic-item-empty">当前无需核定事项</div>';
      if (badge) {
        badge.innerText = '无待办';
        badge.className = 'company-status-badge';
      }
      return;
    }

    const allDone = items.every(i => i.status === 'settled');
    const pendingCount = items.filter(i => i.status !== 'settled').length;

    if (badge) {
      if (allDone) {
        badge.innerText = '全部核定 ✅';
        badge.className = 'company-status-badge badge-done';
      } else {
        badge.innerText = `待核定 ${pendingCount} 项`;
        badge.className = 'company-status-badge badge-pending';
      }
    }

    const html = items.map(it => {
      const isSettled = it.status === 'settled';
      const actionClass = isSettled ? 'monthly-item-action action-done' : 'monthly-item-action';
      const actionText = isSettled ? (it.status_label || '已核定') : (it.action_label || '去核定 ➔');

      const isInvAction = it.is_invoice_action ? 'data-is-inv="1"' : '';
      const compAttr = it.company_name ? `data-comp="${frappe.utils.escape_html(it.company_name)}"` : '';
      const periodAttr = it.target_period ? `data-period="${frappe.utils.escape_html(it.target_period)}"` : '';
      const periodLblAttr = it.target_period_label ? `data-period-label="${frappe.utils.escape_html(it.target_period_label)}"` : '';

      return `
        <div class="monthly-item-row">
          <div class="monthly-item-left">
            <span class="monthly-item-icon">${it.icon || '📌'}</span>
            <div class="monthly-item-meta">
              <span class="monthly-item-title">${frappe.utils.escape_html(it.title)}</span>
              <span class="monthly-item-summary">${frappe.utils.escape_html(it.summary_text || '')}</span>
            </div>
          </div>
          <a href="${it.route || '#'}" class="${actionClass}" data-route="${(it.route || '').replace('/desk/', '')}" ${isInvAction} ${compAttr} ${periodAttr} ${periodLblAttr}>
            ${actionText}
          </a>
        </div>
      `;
    }).join('');

    box.innerHTML = html;

    box.querySelectorAll('a[data-is-inv="1"]').forEach(a => {
      a.addEventListener('click', (e) => {
        e.preventDefault();
        const comp = a.getAttribute('data-comp');
        const period = a.getAttribute('data-period');
        const periodLabel = a.getAttribute('data-period-label');
        openInvoiceClosingDialog(comp, period, periodLabel);
      });
    });

    box.querySelectorAll('a[data-route]:not([data-is-inv="1"])').forEach(a => {
      a.addEventListener('click', (e) => {
        const isNewTab = e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0;
        if (isNewTab) return;
        const r = a.getAttribute('data-route');
        if (r && r !== '#') {
          e.preventDefault();
          frappe.set_route(r);
        }
      });
    });
  }

  function fetchMonthlySettlementStatus() {
    const badge = ROOT.querySelector('#periodic-period-badge');
    const capMonth = ROOT.querySelector('#cap-month');
    const capTextMonth = ROOT.querySelector('#cap-text-month');

    frappe.call({
      method: 'ashan_cn_procurement.services.periodic_tasks.get_monthly_settlement_status',
      callback: function (r) {
        if (r && r.message) {
          const data = r.message;
          const comp = data.companies || {};
          const jizhong = comp.jizhong || {};
          const qifu = comp.qifu || {};

          const pendingCount = (data.total_items || 0) - (data.settled_items || 0);

          if (badge) {
            if (pendingCount > 0) {
              badge.innerText = `待核定 ${pendingCount} 项`;
              badge.className = 'panel-badge badge-pending';
            } else if ((data.total_items || 0) > 0 && data.all_done) {
              badge.innerText = '全部核定 ✅';
              badge.className = 'panel-badge badge-done';
            } else {
              badge.innerText = '月度事项全景感知';
              badge.className = 'panel-badge';
            }
          }

          if (capMonth && capTextMonth) {
            if (pendingCount > 0) {
              capMonth.className = 'status-capsule capsule-month has-pending';
              capTextMonth.innerHTML = `月度任务：<b>${pendingCount} 项</b>待核定`;
            } else {
              capMonth.className = 'status-capsule capsule-month all-done';
              capTextMonth.innerHTML = '月度任务：全部核定 ✅';
            }
          }

          const jzCard = ROOT.querySelector('#company-card-jizhong');
          if (jzCard) {
            if (jizhong.visible) {
              jzCard.style.display = 'block';
              renderPeriodicCompanyItems('#jizhong-items-list', '#jizhong-status-badge', '#jizhong-subcard-title', '🏢 吉众', jizhong.items);
            } else {
              jzCard.style.display = 'none';
            }
          }

          const qfCard = ROOT.querySelector('#company-card-qifu');
          if (qfCard) {
            if (qifu.visible) {
              qfCard.style.display = 'block';
              renderPeriodicCompanyItems('#qifu-items-list', '#qifu-status-badge', '#qifu-subcard-title', '🏭 祺富', qifu.items);
            } else {
              qfCard.style.display = 'none';
            }
          }
        }
      }
    });
  }

  // ============================================================
  // 7. 周期任务 (合规与证照特种设备)
  // ============================================================
  function openComplianceActionDialog(item) {
    const d = new frappe.ui.Dialog({
      title: `${item.icon || '📌'} ${item.category || '合规'}核定 · ${item.title}`,
      fields: [
        {
          fieldtype: 'HTML',
          fieldname: 'info_html',
          options: `
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:10px 12px; margin-bottom:12px; font-size:12px;">
              <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span style="color:#64748b;">归属主体：<b>${frappe.utils.escape_html(item.company || '')}</b></span>
                <span style="color:#64748b;">预设周期：<b>每 ${item.cycle_months || 3} 个月</b></span>
              </div>
              <div style="display:flex; justify-content:space-between;">
                <span style="color:#64748b;">原到期日：<b style="color:#0f172a;">${item.due_date}</b></span>
                <span style="color:${item.level === 'danger' ? '#dc2626' : '#d97706'}; font-weight:700;">${item.status_text}</span>
              </div>
            </div>
          `
        },
        {
          fieldtype: 'Select',
          fieldname: 'action_choice',
          label: '处理方式',
          options: [
            { label: '已完成外部检验/检测（更新下期到期日）', value: 'done_inspection' },
            { label: '需要发起采购申请委托第三方处理', value: 'procure' }
          ],
          default: 'done_inspection'
        },
        {
          fieldtype: 'Date',
          fieldname: 'done_date',
          label: '本次检验/处置完成日期',
          default: frappe.datetime.get_today(),
          reqd: 1,
          onchange: function() {
            const doneD = d.get_value('done_date');
            if (doneD && item.cycle_months) {
              const nextD = frappe.datetime.add_months(doneD, parseInt(item.cycle_months) || 3);
              d.set_value('next_due_date', nextD);
            }
          }
        },
        {
          fieldtype: 'Date',
          fieldname: 'next_due_date',
          label: '下期检验/到期日 (系统根据周期自动推算，支持微调)',
          default: item.suggested_next_due || frappe.datetime.add_months(frappe.datetime.get_today(), parseInt(item.cycle_months) || 3),
          reqd: 1
        },
        {
          fieldtype: 'Small Text',
          fieldname: 'notes',
          label: '执行备注 / 报告编号 (选填)'
        }
      ],
      primary_action_label: '确认并更新台账',
      primary_action: function(values) {
        if (values.action_choice === 'procure') {
          d.hide();
          frappe.new_doc('Material Request', {
            material_request_type: 'Purchase',
            company: item.company === '祺富' ? '天津祺富机械加工有限公司' : '天津吉众机电设备有限公司',
            schedule_date: item.due_date
          });
          return;
        }

        d.get_primary_btn().prop('disabled', true);
        frappe.call({
          method: 'ashan_cn_procurement.services.periodic_tasks.record_compliance_inspection',
          args: {
            doctype: item.doctype,
            docname: item.docname,
            done_date: values.done_date,
            next_due_date: values.next_due_date,
            notes: values.notes
          },
          callback: function(r) {
            d.get_primary_btn().prop('disabled', false);
            if (r && r.message && r.message.success) {
              d.hide();
              frappe.show_alert({
                message: `✅ 已成功记录！下期到期日已更新至: ${r.message.next_due_date}`,
                indicator: 'green'
              }, 5);
              fetchComplianceExpiryStatus();
            } else {
              frappe.msgprint(r.message ? r.message.error : '更新失败');
            }
          }
        });
      },
      secondary_action_label: '查看台账原表单 ➔',
      secondary_action: function() {
        d.hide();
        if (item.route) {
          frappe.set_route(item.route.replace('/desk/', ''));
        }
      }
    });

    d.show();
  }

  function fetchComplianceExpiryStatus() {
    const list = ROOT.querySelector('#expiry-items-list');
    const badge = ROOT.querySelector('#expiry-summary-badge');
    const capExpiry = ROOT.querySelector('#cap-expiry');
    const capTextExpiry = ROOT.querySelector('#cap-text-expiry');

    if (!list) return;

    frappe.call({
      method: 'ashan_cn_procurement.services.periodic_tasks.get_compliance_expiry_status',
      callback: function (r) {
        if (r && r.message) {
          const data = r.message;
          const items = data.items || [];

          if (badge) {
            if (data.danger_count > 0) {
              badge.innerText = `${data.danger_count} 项已超期 ⚠️`;
              badge.className = 'panel-badge badge-pending';
            } else if (data.warning_count > 0) {
              badge.innerText = `${data.warning_count} 项临期关注`;
              badge.className = 'panel-badge badge-pending';
            } else {
              badge.innerText = `全项合规 ✅`;
              badge.className = 'panel-badge badge-done';
            }
          }

          if (capExpiry && capTextExpiry) {
            if (data.danger_count > 0) {
              capExpiry.className = 'status-capsule capsule-expiry has-pending';
              capTextExpiry.innerHTML = `周期任务：<b>${data.danger_count}</b> 项已超期 ⚠️`;
            } else if (data.warning_count > 0) {
              capExpiry.className = 'status-capsule capsule-expiry has-pending';
              capTextExpiry.innerHTML = `周期任务：<b>${data.warning_count}</b> 项临期`;
            } else {
              capExpiry.className = 'status-capsule capsule-expiry all-done';
              capTextExpiry.innerHTML = '周期任务：全项合规在期 ✅';
            }
          }

          if (items.length === 0) {
            list.innerHTML = `
              <div class="expiry-all-valid-box">
                <span>🛡️</span> 当前无临期或超期事项，各合同与特种证照运转良好
              </div>
            `;
            return;
          }

          const html = items.map((it, idx) => {
            const levelClass = `level-${it.level || 'info'}`;
            const tagClass = `tag-${it.level || 'info'}`;

            return `
              <div class="expiry-row ${levelClass}" data-idx="${idx}">
                <div class="expiry-left">
                  <span class="expiry-icon">${it.icon || '📌'}</span>
                  <div class="expiry-meta">
                    <span class="expiry-title">${frappe.utils.escape_html(it.title)}</span>
                    <span class="expiry-desc">${frappe.utils.escape_html(it.company || '')} · 到期日: ${it.due_date}</span>
                  </div>
                </div>
                <div class="expiry-right">
                  <span class="expiry-tag ${tagClass}">${frappe.utils.escape_html(it.status_text)}</span>
                  <button type="button" class="expiry-action-btn btn-open-dialog" data-idx="${idx}">
                    ${frappe.utils.escape_html(it.action_label || '记录核定 ➔')}
                  </button>
                </div>
              </div>
            `;
          }).join('');

          list.innerHTML = html;

          list.querySelectorAll('.btn-open-dialog').forEach(btn => {
            btn.addEventListener('click', () => {
              const idx = parseInt(btn.getAttribute('data-idx'));
              const item = items[idx];
              if (item) openComplianceActionDialog(item);
            });
          });
        }
      }
    });
  }

  // ============================================================
  // 8. 统一初始化执行
  // ============================================================
  function initAllMissionHub() {
    applyPermissionAdaptation();
    bindAllWorkbenchAndRouteLinks();

    reloadAllTasks();
    fetchMonthlySettlementStatus();
    fetchComplianceExpiryStatus();
  }

  const refreshAllBtn = ROOT.querySelector('#btn-refresh-all-data');
  if (refreshAllBtn) {
    refreshAllBtn.addEventListener('click', () => {
      initAllMissionHub();
      frappe.show_alert({ message: '总控中枢全盘数据已刷新', indicator: 'green' }, 3);
    });
  }

  initAllMissionHub();

})();
"""

block_data = {
    "doctype": "Custom HTML Block",
    "name": "业务场景导航",
    "html": html,
    "style": css,
    "script": js,
    "private": 0
}

target_path = "ashan_cn_procurement/ashan_cn_procurement/fixtures/custom_html_block.json"
os.makedirs(os.path.dirname(target_path), exist_ok=True)
with open(target_path, "w", encoding="utf-8") as f:
    json.dump(block_data, f, ensure_ascii=False, indent=2)

print("[OK] Upgraded custom_html_block.json regenerated with autonomous per-item earliest unsettled month detection!")
