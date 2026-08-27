# -*- coding: utf-8 -*-
import os
import sys
import json
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paramiko
from sync_to_erpnext import sync

HTML_CONTENT = """<div class="mission-control-container">

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
  <!-- 🏛️ 核心总控舱：三列等高黄金网格 (Mission Control 3-Col Grid)  -->
  <!-- ============================================================ -->
  <div class="mission-main-grid">

    <!-- ========== 第 1 列: 日常待办 (日级流水) ========== -->
    <div class="mission-grid-col col-daily" id="my-tasks-container">
      <div class="panel-card panel-today-tasks">
        <div class="panel-header">
          <div class="panel-title-wrapper">
            <span class="panel-icon">📋</span>
            <span class="panel-title">日常待办</span>
            <span class="panel-badge">工作台穿透 · 秒级处理</span>
          </div>
        </div>

        <div class="today-tasks-subgrid">
          <!-- 任务 1：待采购下单 -->
          <div class="task-pill-card task-card-amber" id="task-card-po" data-task-perm="Purchase Order" data-doctype="Material Request">
            <div class="task-pill-top">
              <span class="task-pill-icon">🟡</span>
              <div class="task-pill-meta">
                <span class="task-pill-name">待采购下单</span>
                <span class="task-pill-sub">已批需求</span>
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
                <span class="task-pill-sub">公共入库池</span>
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
                <span class="task-pill-sub">入库待录票</span>
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
                <span class="task-pill-sub">发票结清</span>
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
                <span class="task-pill-sub">垫付待报</span>
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

    <!-- ========== 第 2 列: 月度任务 (月级核定) ========== -->
    <div class="mission-grid-col col-monthly" id="periodic-tasks-container">
      <div class="panel-card panel-monthly-tasks">
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
    </div>

    <!-- ========== 第 3 列: 周期任务 (合规与证照合同) ========== -->
    <div class="mission-grid-col col-expiry" id="compliance-expiry-container">
      <div class="panel-card panel-expiry-tasks">
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
</div>"""

CSS_CONTENT = """/* ================= 全局容器 ================= */
.mission-control-container {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px 16px;
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
  padding: 8px 12px;
  margin-bottom: 10px;
}

.status-bar-left {
  display: flex;
  align-items: center;
  gap: 10px;
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
  padding: 3px 9px;
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
  gap: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 6px 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.quick-actions-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11.5px;
  font-weight: 700;
  color: #334155;
  margin-right: 2px;
}

.quick-actions-btns {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.quick-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
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

/* ================= 核心三栏总控网格 (Mission Main 3-Column Grid) ================= */
.mission-main-grid {
  display: grid;
  grid-template-columns: 35% 33% 32%;
  gap: 12px;
  align-items: stretch;
}

@media (max-width: 1200px) {
  .mission-main-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 800px) {
  .mission-main-grid {
    grid-template-columns: 1fr;
  }
}

.mission-grid-col {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.panel-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 7px;
  border-bottom: 1px solid #e2e8f0;
}

.panel-title-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  flex-wrap: wrap;
}

.panel-icon {
  font-size: 14px;
}

.panel-title {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  white-space: nowrap;
}

.panel-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 8px;
  background: #e2e8f0;
  color: #475569;
  font-weight: 500;
  white-space: nowrap;
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

/* ================= 1. 日常待办 2x3 紧凑网格 ================= */
.today-tasks-subgrid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  flex: 1;
}

@media (max-width: 480px) {
  .today-tasks-subgrid {
    grid-template-columns: 1fr;
  }
}

.task-pill-card {
  background: #fff;
  border-radius: 8px;
  padding: 8px 9px;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 72px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
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
  gap: 5px;
  margin-bottom: 2px;
}

.task-pill-icon {
  font-size: 12px;
  line-height: 1;
  flex-shrink: 0;
}

.task-pill-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.task-pill-name {
  font-size: 11.5px;
  font-weight: 700;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-pill-sub {
  font-size: 9.5px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-pill-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2px;
  margin-top: 4px;
}

.task-count-pill {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 10.5px;
  color: #475569;
  white-space: nowrap;
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
  font-size: 9.5px;
  font-weight: 700;
  color: #2563eb;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 4px;
  padding: 2px 5px;
  text-decoration: none !important;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
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

/* ================= 2. 月度任务列 ================= */
.panel-monthly-tasks {
  margin-bottom: 0;
}

.monthly-companies-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.comp-subcard {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 7px 9px;
}

.comp-subcard-hdr {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
  padding-bottom: 3px;
  border-bottom: 1px dashed #e2e8f0;
}

.comp-subcard-title {
  font-size: 11.5px;
  font-weight: 700;
  color: #1e293b;
}

.company-status-badge {
  font-size: 9.5px;
  padding: 1px 5px;
  border-radius: 6px;
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
  gap: 4px;
}

.monthly-item-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 6px;
  background: #f8fafc;
  border-radius: 5px;
  border: 1px solid #f1f5f9;
}

.monthly-item-left {
  display: flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
}

.monthly-item-icon {
  font-size: 12px;
  flex-shrink: 0;
}

.monthly-item-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.monthly-item-title {
  font-size: 11px;
  font-weight: 600;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.monthly-item-summary {
  font-size: 9.5px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.monthly-item-action {
  font-size: 9.5px;
  font-weight: 700;
  color: #d97706;
  background: #fef3c7;
  border: 1px solid #fde68a;
  border-radius: 4px;
  padding: 2px 5px;
  text-decoration: none !important;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
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

/* ================= 3. 周期任务列表 ================= */
.panel-expiry-tasks {
  height: 100%;
}

.expiry-items-container {
  display: flex;
  flex-direction: column;
  gap: 5px;
  flex: 1;
  max-height: 480px;
  overflow-y: auto;
  padding-right: 2px;
}

.expiry-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 7px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  gap: 6px;
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
  gap: 6px;
  min-width: 0;
  flex: 1;
}

.expiry-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.expiry-title {
  font-size: 11px;
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expiry-desc {
  font-size: 9.5px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expiry-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.expiry-tag {
  font-size: 9.5px;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 4px;
  white-space: nowrap;
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
  font-size: 9.5px;
  font-weight: 600;
  color: #475569;
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  padding: 2px 5px;
  cursor: pointer;
  white-space: nowrap;
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
}"""

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()
HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')
SITE = os.getenv('ERPNEXT_SITE', 'site1.local')
FIXTURE_PATH = "ashan_cn_procurement/ashan_cn_procurement/fixtures/custom_html_block.json"

def main():
    print("1. Reading JS content from existing fixtures...")
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        existing = json.load(f)
    js_content = existing.get("script", "")

    # Clean up updateTaskPill in JS to output concise '<b>${count}</b> 笔待办'
    js_content = js_content.replace(
        "text.innerHTML = `<b>${count}</b> ${singleUnitLabel}待处理`;",
        "text.innerHTML = `<b>${count}</b> 笔待办`;"
    )
    js_content = js_content.replace(
        "text.innerHTML = `<b>${count}</b> 笔待办待处理`;",
        "text.innerHTML = `<b>${count}</b> 笔待办`;"
    )

    print("2. Writing updated JSON fixture...")
    fixture_data = {
        "doctype": "Custom HTML Block",
        "name": "业务场景导航",
        "html": HTML_CONTENT,
        "style": CSS_CONTENT,
        "script": js_content
    }
    with open(FIXTURE_PATH, "w", encoding="utf-8") as f:
        json.dump(fixture_data, f, ensure_ascii=False, indent=2)

    print("3. Syncing app files to Unraid/ERPNext container...")
    sync(migrate=False, restart=False)

    print("4. Applying to Frappe database via SSH...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)

    db_script = """
import frappe
import json

with open('/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/fixtures/custom_html_block.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

name = data.get('name', '业务场景导航')
if frappe.db.exists('Custom HTML Block', name):
    doc = frappe.get_doc('Custom HTML Block', name)
    doc.html = data.get('html', '')
    doc.script = data.get('script', '')
    doc.style = data.get('style', '')
    doc.save(ignore_permissions=True)
    print(f'Updated existing Custom HTML Block: {name}')
else:
    doc = frappe.get_doc(data)
    doc.insert(ignore_permissions=True)
    print(f'Inserted new Custom HTML Block: {name}')

frappe.db.commit()
"""
    remote_cmd = f"""
    docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python -c "import frappe; frappe.init(site='{SITE}'); frappe.connect(); {db_script}"
    docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site {SITE} clear-cache
    """
    stdin, stdout, stderr = ssh.exec_command(remote_cmd)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    print("STDOUT:\n", out)
    if err:
        print("STDERR:\n", err)

    ssh.close()
    print("[SUCCESS] Scheme A layout applied successfully to ERPNext!")

if __name__ == "__main__":
    main()
