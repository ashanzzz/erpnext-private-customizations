import json

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
          <span class="cap-text" id="cap-text-today">今日待办：计算中…</span>
        </div>
        <div class="status-capsule capsule-month" id="cap-month">
          <span class="cap-dot"></span>
          <span class="cap-text" id="cap-text-month">月度核定：计算中…</span>
        </div>
        <div class="status-capsule capsule-expiry" id="cap-expiry">
          <span class="cap-dot"></span>
          <span class="cap-text" id="cap-text-expiry">临期合规：计算中…</span>
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
  <!-- 🏛️ 核心总控舱：左右分工黄金网格 (Mission Control Grid)        -->
  <!-- ============================================================ -->
  <div class="mission-main-grid">

    <!-- ========== 左侧大栏 (58%): 今日待办任务 ========== -->
    <div class="mission-grid-col col-left" id="my-tasks-container">
      <div class="panel-card panel-today-tasks">
        <div class="panel-header">
          <div class="panel-title-wrapper">
            <span class="panel-icon">📋</span>
            <span class="panel-title">我的待办任务 (今日工作焦点)</span>
            <span class="panel-badge">按经办人隔离 · 入库共享池</span>
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
              <a href="/desk/material-request" class="task-action-btn" id="act-po" data-doctype="Material Request" data-filters='{"docstatus":1,"status":["in",["Submitted","Pending","Partially Ordered"]]}'>
                去下单 ➔
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
              <a href="/desk/purchase-order" class="task-action-btn" id="act-pr" data-doctype="Purchase Order" data-filters='{"docstatus":1,"status":["in",["On Hold","To Receive","To Receive and Bill"]]}'>
                去收货 ➔
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
              <a href="/desk/purchase-receipt" class="task-action-btn" id="act-pi" data-doctype="Purchase Receipt">
                去开票 ➔
              </a>
            </div>
          </div>

          <!-- 任务 4：待发起报销 -->
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
              <a href="/desk/purchase-invoice" class="task-action-btn" id="act-reim" data-doctype="Purchase Invoice">
                去报销 ➔
              </a>
            </div>
          </div>

          <!-- 任务 5：待报销结款 -->
          <div class="task-pill-card task-card-purple" id="task-card-settle" data-task-perm="Payment Entry" data-doctype="Reimbursement Request">
            <div class="task-pill-top">
              <span class="task-pill-icon">🟣</span>
              <div class="task-pill-meta">
                <span class="task-pill-name">待报销结款</span>
                <span class="task-pill-sub">财务付款结清</span>
              </div>
            </div>
            <div class="task-pill-bottom">
              <div class="task-count-pill is-loading" id="pill-settle">
                <span class="pill-dot"></span>
                <span class="pill-text" id="pill-text-settle">统计中…</span>
              </div>
              <a href="/desk/reimbursement-request" class="task-action-btn" id="act-settle" data-doctype="Reimbursement Request" data-filters='{"docstatus":1,"outstanding_amount":[">",0]}'>
                去付款 ➔
              </a>
            </div>
          </div>

        </div>
      </div>
    </div>

    <!-- ========== 右侧协同栏 (40%): 月度任务 + 临期预警 ========== -->
    <div class="mission-grid-col col-right">

      <!-- 模块 1: 我的月度任务 -->
      <div class="panel-card panel-monthly-tasks" id="periodic-tasks-container">
        <div class="panel-header">
          <div class="panel-title-wrapper">
            <span class="panel-icon">📅</span>
            <span class="panel-title">我的月度任务</span>
            <span class="panel-badge" id="periodic-period-badge">核验中…</span>
          </div>
          <div class="panel-ctrls">
            <select id="select-periodic-period" class="period-select-compact" title="切换月份"></select>
          </div>
        </div>

        <div class="monthly-companies-wrap" id="periodic-companies-grid">
          <!-- 吉众 -->
          <div class="comp-subcard" id="company-card-jizhong">
            <div class="comp-subcard-hdr">
              <span class="comp-subcard-title">🏢 吉众 · 报表核定</span>
              <span class="company-status-badge" id="jizhong-status-badge">核定中</span>
            </div>
            <div class="comp-items-box" id="jizhong-items-list">
              <div class="periodic-loading">核定中…</div>
            </div>
          </div>

          <!-- 祺富 -->
          <div class="comp-subcard" id="company-card-qifu">
            <div class="comp-subcard-hdr">
              <span class="comp-subcard-title">🏭 祺富 · 报表核定</span>
              <span class="company-status-badge" id="qifu-status-badge">核定中</span>
            </div>
            <div class="comp-items-box" id="qifu-items-list">
              <div class="periodic-loading">核定中…</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 模块 2: 我的临期预警 -->
      <div class="panel-card panel-expiry-tasks" id="compliance-expiry-container">
        <div class="panel-header">
          <div class="panel-title-wrapper">
            <span class="panel-icon">⏳</span>
            <span class="panel-title">我的临期预警 (合规与证照合同)</span>
            <span class="panel-badge" id="expiry-summary-badge">核验中…</span>
          </div>
        </div>

        <div class="expiry-items-container" id="expiry-items-list">
          <div class="periodic-loading">正在拉取合规与临期倒计时…</div>
        </div>
      </div>

    </div>

  </div>

  <div class="biz-divider" style="margin: 22px 0 18px;"></div>

  <!-- ============================================================ -->
  <!-- 📦 4 大全流程业务管道卡片 (Business Flow Pipelines)            -->
  <!-- ============================================================ -->

  <!-- ========== 场景 1：购买申请（常规采购） ========== -->
  <div class="biz-scene-block" id="scene-1-container">
    <div class="biz-section-header">
      <span class="biz-title" style="color:#2490ef;">📦 场景1：购买申请（常规采购）</span>
      <span class="biz-subtitle">订单驱动 | 标准化</span>
    </div>
    <div class="biz-scene-note">说明：常规采购，以购买申请为起点，打印单据为采购申请单据。</div>

    <div class="biz-flow-wrapper">
      <div class="step-card step-blue" data-doctype="Material Request">
        <div class="step-header">1. 采购申请</div>
        <a href="/desk/material-request/new" class="my-cmd-btn btn-blue btn-create" data-doctype="Material Request">
          <span class="icon">+</span> 新建申请
        </a>
        <a href="/desk/material-request" class="my-cmd-btn btn-blue-outline btn-view-all" data-doctype="Material Request">
          <span class="icon">≡</span> 查看全部
        </a>
        <a href="/desk/material-request"
           class="stat-row stat-blue is-loading"
           id="stat-req"
           data-doctype="Material Request"
           data-route="material-request"
           data-filters='{"docstatus":1,"status":["in",["Submitted","Pending","Partially Ordered"]]}'>
          <span class="stat-icon">⏳</span>
          <span class="stat-text" id="text-req">正在统计…</span>
        </a>
      </div>

      <div class="flow-arrow">➔</div>

      <div class="step-card step-blue" data-doctype="Purchase Order">
        <div class="step-header">2. 采购订单</div>
        <a href="/desk/purchase-order/new" class="my-cmd-btn btn-blue btn-create" data-doctype="Purchase Order">
          <span class="icon">+</span> 新建订单
        </a>
        <a href="/desk/purchase-order" class="my-cmd-btn btn-blue-outline btn-view-all" data-doctype="Purchase Order">
          <span class="icon">≡</span> 查看全部
        </a>
        <a href="/desk/purchase-order"
           class="stat-row stat-blue is-loading"
           id="stat-po"
           data-doctype="Purchase Order"
           data-route="purchase-order"
           data-filters='{"docstatus":1,"status":["in",["On Hold","To Receive","To Receive and Bill"]]}'>
          <span class="stat-icon">⏳</span>
          <span class="stat-text" id="text-po">正在统计…</span>
        </a>
      </div>

      <div class="flow-arrow">➔</div>

      <div class="step-card step-blue" data-doctype="Purchase Receipt">
        <div class="step-header">3. 物资入库</div>
        <a href="/desk/purchase-receipt/new?custom_biz_mode=常规采购" class="my-cmd-btn btn-blue btn-create" data-doctype="Purchase Receipt">
          <span class="icon">+</span> 新建入库
        </a>
        <a href="/desk/purchase-receipt?custom_biz_mode=常规采购" class="my-cmd-btn btn-blue-outline btn-view-all" data-doctype="Purchase Receipt">
          <span class="icon">≡</span> 查看全部
        </a>
        <a href="/desk/purchase-receipt"
           class="stat-row stat-blue is-loading"
           id="stat-pr-reg"
           data-doctype="Purchase Receipt"
           data-route="purchase-receipt">
          <span class="stat-icon">⏳</span>
          <span class="stat-text" id="text-pr-reg">正在统计…</span>
        </a>
      </div>

      <div class="flow-arrow">➔</div>

      <div class="step-card step-blue" data-doctype="Purchase Invoice">
        <div class="step-header">4. 采购发票</div>
        <a href="/desk/purchase-invoice/new?custom_biz_mode=常规采购" class="my-cmd-btn btn-blue btn-create" data-doctype="Purchase Invoice">
          <span class="icon">+</span> 新建发票
        </a>
        <a href="/desk/purchase-invoice?custom_biz_mode=常规采购" class="my-cmd-btn btn-blue-outline btn-view-all" data-doctype="Purchase Invoice">
          <span class="icon">≡</span> 查看全部
        </a>
        <a href="/desk/purchase-invoice"
           class="stat-row stat-blue is-loading"
           id="stat-pi-reg"
           data-doctype="Purchase Invoice"
           data-route="purchase-invoice">
          <span class="stat-icon">⏳</span>
          <span class="stat-text" id="text-pi-reg">正在统计…</span>
        </a>
      </div>
    </div>
    <div class="biz-divider"></div>
  </div>

  <!-- ========== 场景 2：现金报销（垫付） ========== -->
  <div class="biz-scene-block" id="scene-2-container">
    <div class="biz-section-header">
      <span class="biz-title" style="color:#e67e22;">🚀 场景2：现金报销（垫付）</span>
      <span class="biz-subtitle">个人垫付 | 快速回款</span>
    </div>
    <div class="biz-scene-note">说明：报销单，打印单据为报销申请单据的整算单</div>

    <div class="biz-flow-wrapper">
      <div class="step-card step-orange" data-doctype="Purchase Receipt">
        <div class="step-header">1. 采购入库</div>
        <a href="/desk/purchase-receipt/new?custom_biz_mode=现金报销&supplier=其它供应商" class="my-cmd-btn btn-orange btn-create" data-doctype="Purchase Receipt">
          <span class="icon">+</span> 新建入库
        </a>
        <a href="/desk/purchase-receipt?custom_biz_mode=现金报销" class="my-cmd-btn btn-orange-outline btn-view-all" data-doctype="Purchase Receipt">
          <span class="icon">≡</span> 查看全部
        </a>
        <a href="/desk/purchase-receipt"
           class="stat-row stat-orange is-loading"
           id="stat-reim-pr"
           data-doctype="Purchase Receipt"
           data-route="purchase-receipt">
          <span class="stat-icon">⏳</span>
          <span class="stat-text" id="text-reim-pr">正在统计…</span>
        </a>
      </div>

      <div class="flow-arrow">➔</div>

      <div class="step-card step-orange" data-doctype="Purchase Invoice">
        <div class="step-header">2. 采购发票</div>
        <a href="/desk/purchase-invoice/new?custom_biz_mode=现金报销" class="my-cmd-btn btn-orange btn-create" data-doctype="Purchase Invoice">
          <span class="icon">+</span> 新建发票
        </a>
        <a href="/desk/purchase-invoice?custom_biz_mode=现金报销" class="my-cmd-btn btn-orange-outline btn-view-all" data-doctype="Purchase Invoice">
          <span class="icon">≡</span> 查看全部
        </a>
        <a href="/desk/purchase-invoice"
           class="stat-row stat-orange is-loading"
           id="stat-reim-pi"
           data-doctype="Purchase Invoice"
           data-route="purchase-invoice">
          <span class="stat-icon">⏳</span>
          <span class="stat-text" id="text-reim-pi">正在统计…</span>
        </a>
      </div>

      <div class="flow-arrow">➔</div>

      <div class="step-card step-orange" data-doctype="Reimbursement Request">
        <div class="step-header">3. 报销申请</div>
        <a href="/desk/reimbursement-request/new?custom_biz_mode=现金报销" class="my-cmd-btn btn-orange btn-create" data-doctype="Reimbursement Request">
          <span class="icon">+</span> 新建报销
        </a>
        <a href="/desk/reimbursement-request?custom_biz_mode=现金报销&docstatus=1" class="my-cmd-btn btn-orange-outline btn-view-all" data-doctype="Reimbursement Request">
          <span class="icon">≡</span> 查看全部
        </a>
        <a href="/desk/reimbursement-request"
           class="stat-row stat-orange is-loading"
           id="stat-reim-req"
           data-doctype="Reimbursement Request"
           data-route="reimbursement-request">
          <span class="stat-icon">⏳</span>
          <span class="stat-text" id="text-reim-req">正在统计…</span>
        </a>
      </div>
    </div>
    <div class="biz-divider"></div>
  </div>

  <!-- ========== 场景 3 & 4（并排） ========== -->
  <div class="biz-dual-scenes-row" style="display:flex; gap:20px;">

    <!-- 场景 3 -->
    <div class="biz-scene-block" id="scene-3-container" style="flex:2;">
      <div class="biz-section-header" style="margin-bottom:8px;">
        <span class="biz-title" style="color:#8e44ad; font-size:14px;">⚡ 场景3：自办电汇（秒结）</span>
      </div>
      <div class="biz-scene-note">说明：为自行电汇采购的流程，需要打印入库的补写的入库单。由于是电汇，必定有发票。</div>

      <div class="biz-flow-wrapper">
        <div class="step-card step-purple" data-doctype="Purchase Receipt">
          <div class="step-header">1. 采购入库</div>
          <a href="/desk/purchase-receipt/new?custom_biz_mode=自办电汇" class="my-cmd-btn btn-purple btn-create" data-doctype="Purchase Receipt">
            <span class="icon">+</span> 新建入库
          </a>
          <a href="/desk/purchase-receipt?custom_biz_mode=自办电汇" class="my-cmd-btn btn-purple-outline btn-view-all" data-doctype="Purchase Receipt">
            <span class="icon">≡</span> 查看全部
          </a>
          <a href="/desk/purchase-receipt"
             class="stat-row stat-purple is-loading"
             id="stat-wire-pr"
             data-doctype="Purchase Receipt"
             data-route="purchase-receipt">
            <span class="stat-icon">⏳</span>
            <span class="stat-text" id="text-wire-pr">正在统计…</span>
          </a>
        </div>

        <div class="flow-arrow">➔</div>

        <div class="step-card step-purple" data-doctype="Purchase Invoice">
          <div class="step-header">2. 发票&支付</div>
          <a href="/desk/purchase-invoice/new?custom_biz_mode=自办电汇" class="my-cmd-btn btn-purple btn-create" data-doctype="Purchase Invoice">
            <span class="icon">+</span> 新建发票
          </a>
          <a href="/desk/purchase-invoice?custom_biz_mode=自办电汇" class="my-cmd-btn btn-purple-outline btn-view-all" data-doctype="Purchase Invoice">
            <span class="icon">≡</span> 查看全部
          </a>
          <a href="/desk/purchase-invoice"
             class="stat-row stat-purple is-loading"
             id="stat-wire-pi"
             data-doctype="Purchase Invoice"
             data-route="purchase-invoice">
            <span class="stat-icon">⏳</span>
            <span class="stat-text" id="text-wire-pi">正在统计…</span>
          </a>
        </div>
      </div>
    </div>

    <!-- 场景 4 -->
    <div class="biz-scene-block" id="scene-4-container" style="flex:1; border-left:1px dashed #e2e8f0; padding-left:20px;">
      <div class="biz-section-header" style="margin-bottom:8px;">
        <span class="biz-title" style="color:#00b894; font-size:14px;">📅 场景4：月结补录</span>
      </div>
      <div class="biz-scene-note">说明：仅用于月结供应商，如聚鑫、金普金等。打印采购入库的补录单，一般无需填写发票。</div>

      <div class="biz-flow-wrapper">
        <div class="step-card step-teal" data-doctype="Purchase Receipt">
          <div class="step-header">1. 采购入库</div>
          <a href="/desk/purchase-receipt/new?custom_biz_mode=月结补录" class="my-cmd-btn btn-teal btn-create" data-doctype="Purchase Receipt">
            <span class="icon">+</span> 新建入库
          </a>
          <a href="/desk/purchase-receipt?custom_biz_mode=月结补录" class="my-cmd-btn btn-teal-outline btn-view-all" data-doctype="Purchase Receipt">
            <span class="icon">≡</span> 查看全部
          </a>
          <a href="/desk/purchase-receipt"
             class="stat-row stat-teal is-loading"
             id="stat-mth-pr"
             data-doctype="Purchase Receipt"
             data-route="purchase-receipt">
            <span class="stat-icon">⏳</span>
            <span class="stat-text" id="text-mth-pr">正在统计…</span>
          </a>
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
  margin-bottom: 16px;
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
  gap: 6px;
}

.panel-icon {
  font-size: 15px;
}

.panel-title {
  font-size: 13.5px;
  font-weight: 700;
  color: #1e293b;
}

.panel-badge {
  font-size: 10.5px;
  color: #64748b;
  background: #e2e8f0;
  padding: 1px 7px;
  border-radius: 10px;
  font-weight: 500;
}
.panel-badge.badge-pending {
  background: #fff7ed;
  color: #c2410c;
  border: 1px solid #fed7aa;
  font-weight: 600;
}
.panel-badge.badge-done {
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #bbf7d0;
  font-weight: 600;
}

/* ========== 左侧：今日待办卡片网格 ========== */
.today-tasks-subgrid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.task-pill-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 86px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}
.task-pill-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}

.task-pill-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.task-pill-icon {
  font-size: 15px;
  line-height: 1;
}

.task-pill-meta {
  display: flex;
  flex-direction: column;
}

.task-pill-name {
  font-size: 12.5px;
  font-weight: 700;
  color: #1e293b;
}

.task-pill-sub {
  font-size: 10.5px;
  color: #64748b;
}

.task-pill-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  padding-top: 6px;
  border-top: 1px solid #f8fafc;
}

.task-count-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 10px;
  background: #f1f5f9;
  color: #64748b;
}
.task-count-pill .pill-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #94a3b8;
}
.task-count-pill.has-pending {
  background: #fef2f2;
  color: #dc2626;
}
.task-count-pill.has-pending .pill-dot {
  background: #ef4444;
  animation: pulse-dot 1.5s infinite;
}
.task-count-pill.is-done {
  background: #f0fdf4;
  color: #16a34a;
}
.task-count-pill.is-done .pill-dot {
  background: #22c55e;
}

.task-action-btn {
  font-size: 11px;
  font-weight: 600;
  color: #2563eb;
  text-decoration: none !important;
}
.task-action-btn:hover {
  color: #1d4ed8;
  text-decoration: underline !important;
}
.task-action-btn.is-disabled {
  display: none;
}

.task-card-amber { border-left: 3px solid #f59e0b; }
.task-card-green { border-left: 3px solid #10b981; }
.task-card-blue { border-left: 3px solid #3b82f6; }
.task-card-orange { border-left: 3px solid #f97316; }
.task-card-purple { border-left: 3px solid #a855f7; }

/* ========== 右侧：月度任务 ========== */
.panel-monthly-tasks {
  margin-bottom: 12px;
}

.period-select-compact {
  height: 24px;
  font-size: 11px;
  font-weight: 600;
  color: #1e293b;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  background: #fff;
  padding: 0 6px;
  outline: none;
  cursor: pointer;
}

.monthly-companies-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.comp-subcard {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 8px 10px;
}

.comp-subcard-hdr {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.comp-subcard-title {
  font-size: 12px;
  font-weight: 700;
  color: #0f172a;
}

.company-status-badge {
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 8px;
  background: #f1f5f9;
  color: #64748b;
  font-weight: 600;
}
.company-status-badge.has-unsettled {
  background: #fff7ed;
  color: #c2410c;
  border: 1px solid #fed7aa;
}
.company-status-badge.all-settled {
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #bbf7d0;
}

.comp-items-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.periodic-item-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 8px;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
  border-radius: 4px;
  font-size: 11.5px;
}
.periodic-item-row.is-unsettled-row {
  border-left: 3px solid #f97316;
}
.periodic-item-row.is-settled-row {
  border-left: 3px solid #22c55e;
}

.periodic-item-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.periodic-item-icon {
  font-size: 14px;
}

.periodic-item-title {
  font-weight: 600;
  color: #1e293b;
}

.periodic-item-summary {
  font-size: 10.5px;
  color: #64748b;
}

.periodic-item-badge-link {
  font-size: 10.5px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 4px;
  text-decoration: none !important;
  white-space: nowrap;
}
.badge-unsettled {
  background: #fff7ed;
  color: #c2410c;
  border: 1px solid #ffedd5;
}
.badge-unsettled:hover {
  background: #ffedd5;
  color: #9a3412;
}
.badge-settled {
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #dcfce7;
}

/* ========== 右侧：临期预警 ========== */
.panel-expiry-tasks {
  background: #fff;
  border: 1px solid #e2e8f0;
}

.expiry-items-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 220px;
  overflow-y: auto;
  padding-right: 2px;
}

.expiry-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 9px;
  border-radius: 5px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  transition: all 0.12s ease;
}
.expiry-row:hover {
  background: #f1f5f9;
}

.expiry-row.level-danger {
  background: #fef2f2;
  border-color: #fecaca;
  border-left: 3px solid #ef4444;
}
.expiry-row.level-warning {
  background: #fffbeb;
  border-color: #fde68a;
  border-left: 3px solid #f59e0b;
}
.expiry-row.level-info {
  background: #f8fafc;
  border-color: #e2e8f0;
  border-left: 3px solid #3b82f6;
}

.expiry-left {
  display: flex;
  align-items: center;
  gap: 6px;
}
.expiry-icon { font-size: 14px; }
.expiry-meta { display: flex; flex-direction: column; }
.expiry-title { font-size: 11.5px; font-weight: 700; color: #1e293b; }
.expiry-desc { font-size: 10.5px; color: #64748b; }

.expiry-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.expiry-tag {
  font-size: 10.5px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
}
.expiry-tag.tag-danger { background: #fee2e2; color: #b91c1c; }
.expiry-tag.tag-warning { background: #fef3c7; color: #b45309; }
.expiry-tag.tag-info { background: #eff6ff; color: #1d4ed8; }

.expiry-action-btn {
  font-size: 10.5px;
  font-weight: 600;
  color: #2563eb;
  text-decoration: none !important;
  background: #fff;
  border: 1px solid #cbd5e1;
  padding: 2px 6px;
  border-radius: 4px;
  cursor: pointer;
}
.expiry-action-btn:hover {
  background: #eff6ff;
  border-color: #93c5fd;
}

.expiry-all-valid-box {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 6px;
  color: #15803d;
  font-size: 12px;
  font-weight: 600;
}

.periodic-loading {
  font-size: 11px;
  color: #94a3b8;
  text-align: center;
  padding: 8px;
}

/* ================= 业务场景流程部分 ================= */
.biz-section-header { margin-bottom: 8px; display: flex; align-items: baseline; }
.biz-title { font-size: 14.5px; font-weight: 700; margin-right: 8px; }
.biz-subtitle {
  font-size: 11px; color: #94a3b8; background: #f1f5f9;
  padding: 2px 6px; border-radius: 4px;
}

.biz-scene-note {
  margin: 6px 0 12px;
  font-size: 12px;
  color: #64748b;
  background: #f8fafc;
  border: 1px dashed #e2e8f0;
  border-radius: 6px;
  padding: 6px 10px;
}

.biz-divider {
  height: 1px; background: #e2e8f0; margin: 18px 0; border-bottom: 1px dashed #cbd5e0;
}

.biz-flow-wrapper { display: flex; align-items: stretch; gap: 10px; margin-bottom: 8px; }
.flow-arrow { display: flex; align-items: center; color: #cbd5e0; font-size: 16px; user-select: none; }

.step-hidden { display: none !important; }
.scene-hidden { display: none !important; }
.btn-hidden-perm { display: none !important; }

.step-card {
  flex: 1;
  min-width: 120px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px 0;

  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  gap: 8px;
  box-sizing: border-box !important;
  transition: all 0.2s ease;
}

.step-header {
  font-size: 12.5px;
  font-weight: 700;
  color: #334155;
  margin-bottom: 2px;
  text-align: center;
}

.my-cmd-btn {
  width: 90% !important;
  max-width: 90% !important;
  margin: 0 auto !important;
  position: relative !important;
  display: inline-flex !important;
  justify-content: center !important;
  align-items: center !important;
  text-align: center !important;
  padding: 7px 28px !important;
  min-height: 30px;
  font-size: 12px !important;
  font-weight: 600;
  line-height: 1 !important;
  white-space: nowrap;
  border-radius: 6px !important;
  text-decoration: none !important;
  box-sizing: border-box !important;
  transition: all .12s ease;
}
.my-cmd-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 10px rgba(15, 23, 42, 0.08); }
.my-cmd-btn .icon {
  position: absolute !important;
  left: 12px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  width: 16px; height: 16px;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  font-weight: 800;
  pointer-events: none;
}

.stat-row {
  width: 90% !important;
  max-width: 90% !important;
  margin: 0 auto !important;
  margin-top: auto !important;
  text-decoration: none !important;
  position: relative !important;
  display: inline-flex !important;
  justify-content: center !important;
  align-items: center !important;
  text-align: center !important;
  padding: 7px 28px !important;
  min-height: 30px;
  font-size: 11px !important;
  font-weight: 600;
  line-height: 1 !important;
  border-radius: 6px !important;
  box-sizing: border-box !important;
  transition: all .12s ease;
}
.stat-row:hover { transform: translateY(-1px); box-shadow: 0 4px 10px rgba(15, 23, 42, 0.08); }
.stat-row .stat-icon {
  position: absolute !important;
  left: 12px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  width: 16px; height: 16px;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  pointer-events: none;
}

.stat-row.is-loading { opacity: 0.95; }
.stat-row.has-pending { opacity: 1; font-weight: 700; }
.stat-row.is-empty { background: #fff !important; border: 1px solid #e2e8f0 !important; color: #94a3b8 !important; }
.stat-row.is-empty:hover { background: #f8fafc !important; border-color: #cbd5e0 !important; color: #64748b !important; }
.stat-row.is-error { background: #fff !important; border: 1px solid #fecaca !important; color: #b91c1c !important; }

.step-blue { border-top: 3px solid #2490ef; }
.btn-blue { background: #eff6ff !important; color: #1d4ed8 !important; border: 1px solid #dbeafe !important; }
.btn-blue:hover { background: #dbeafe !important; }
.btn-blue-outline { background: #fff !important; color: #64748b !important; border: 1px solid #e2e8f0 !important; }
.btn-blue-outline:hover { background: #f8fafc !important; color: #2490ef !important; border-color: #cbd5e0 !important; }
.stat-blue { background: #eff6ff !important; color: #2490ef !important; border: 1px solid #dbeafe !important; }

.step-orange { border-top: 3px solid #e67e22; }
.btn-orange { background: #fff3e0 !important; color: #e65100 !important; border: 1px solid #ffe0b2 !important; }
.btn-orange:hover { background: #ffe0b2 !important; }
.btn-orange-outline { background: #fff !important; color: #64748b !important; border: 1px solid #e2e8f0 !important; }
.btn-orange-outline:hover { background: #fff8e1 !important; color: #e67e22 !important; border-color: #ffe0b2 !important; }
.stat-orange { background: #fff3e0 !important; color: #e67e22 !important; border: 1px solid #ffe0b2 !important; }

.step-purple { border-top: 3px solid #8e44ad; }
.btn-purple { background: #f3e5f5 !important; color: #6a1b9a !important; border: 1px solid #e1bee7 !important; }
.btn-purple:hover { background: #e1bee7 !important; }
.btn-purple-outline { background: #fff !important; color: #64748b !important; border: 1px solid #e2e8f0 !important; }
.btn-purple-outline:hover { background: #f3e5f5 !important; color: #8e44ad !important; border-color: #e1bee7 !important; }
.stat-purple { background: #f3e5f5 !important; color: #8e44ad !important; border: 1px solid #e1bee7 !important; }

.step-teal { border-top: 3px solid #00b894; }
.btn-teal { background: #e0f2f1 !important; color: #00695c !important; border: 1px solid #b2dfdb !important; }
.btn-teal:hover { background: #b2dfdb !important; }
.btn-teal-outline { background: #fff !important; color: #64748b !important; border: 1px solid #e2e8f0 !important; }
.btn-teal-outline:hover { background: #e0f2f1 !important; color: #00b894 !important; border-color: #b2dfdb !important; }
.stat-teal { background: #e0f2f1 !important; color: #00b894 !important; border: 1px solid #b2dfdb !important; }
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
    return roles.includes("Accounts User") || roles.includes("Accounts Manager");
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
        isVisible = isFinanceUser() && userCanRead("Reimbursement Request");
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

    const stepCards = ROOT.querySelectorAll('.step-card[data-doctype]');
    stepCards.forEach((card) => {
      const doctype = card.getAttribute('data-doctype');
      const canRead = userCanRead(doctype);
      const canCreate = userCanCreate(doctype);

      if (!canRead) {
        card.classList.add('step-hidden');
        const nextArrow = card.nextElementSibling;
        if (nextArrow && nextArrow.classList.contains('flow-arrow')) {
          nextArrow.classList.add('step-hidden');
        }
      } else {
        card.classList.remove('step-hidden');
        const createBtn = card.querySelector('.btn-create');
        if (createBtn) {
          if (!canCreate) {
            createBtn.classList.add('btn-hidden-perm');
          } else {
            createBtn.classList.remove('btn-hidden-perm');
          }
        }
      }
    });

    const sceneBlocks = ROOT.querySelectorAll('.biz-scene-block');
    sceneBlocks.forEach((block) => {
      const cards = block.querySelectorAll('.step-card');
      const visibleCards = Array.from(cards).filter(c => !c.classList.contains('step-hidden'));
      if (visibleCards.length === 0) {
        block.classList.add('scene-hidden');
      } else {
        block.classList.remove('scene-hidden');
      }
    });

    const dualRow = ROOT.querySelector('.biz-dual-scenes-row');
    if (dualRow) {
      const sc3 = ROOT.querySelector('#scene-3-container');
      const sc4 = ROOT.querySelector('#scene-4-container');
      const sc3Hidden = sc3 && sc3.classList.contains('scene-hidden');
      const sc4Hidden = sc4 && sc4.classList.contains('scene-hidden');

      if (sc3Hidden && sc4Hidden) {
        dualRow.classList.add('scene-hidden');
      } else {
        dualRow.classList.remove('scene-hidden');
        if (sc3Hidden && !sc4Hidden) {
          sc4.style.borderLeft = 'none';
          sc4.style.paddingLeft = '0';
        }
      }
    }
  }

  function enc(v) {
    return encodeURIComponent(String(v)).replace(/%20/g, '+');
  }

  function buildQuery(filtersObj) {
    const parts = [];
    Object.keys(filtersObj || {}).forEach((k) => {
      const v = filtersObj[k];
      if (v === undefined) return;

      if (Array.isArray(v)) {
        const json = JSON.stringify(v);
        parts.push(`${enc(k)}=${enc(json)}`);
      } else {
        parts.push(`${enc(k)}=${enc(v)}`);
      }
    });
    return parts.join('&');
  }

  function buildListUrl(route, filtersObj) {
    const q = buildQuery(filtersObj);
    const base = `/desk/${route}`;
    return q ? `${base}?${q}` : base;
  }

  function parseRouteOptionsFromHref(href) {
    try {
      const url = new URL(href, window.location.origin);
      const obj = {};
      url.searchParams.forEach((val, key) => {
        let v = val;
        if (v && (v.startsWith('[') || v.startsWith('{'))) {
          try { v = JSON.parse(v); } catch (e) {}
        }
        if (typeof v === "string" && /^[0-9]+$/.test(v)) {
          v = Number(v);
        }
        obj[key] = v;
      });
      return obj;
    } catch (e) {
      return {};
    }
  }

  function parseAppRoute(href) {
    try {
      const url = new URL(href, window.location.origin);
      const p = url.pathname || "";
      const m = p.match(/^\\/(?:app|desk)\\/([^\\/?#]+)(?:\\/(new))?\\/?$/);
      if (!m) return null;
      return { route: m[1], is_new: !!m[2] };
    } catch (e) {
      return null;
    }
  }

  const ROUTE_TO_DOCTYPE = {
    "material-request": "Material Request",
    "purchase-order": "Purchase Order",
    "purchase-receipt": "Purchase Receipt",
    "purchase-invoice": "Purchase Invoice",
    "reimbursement-request": "Reimbursement Request",
  };

  function guessDoctypeFromRoute(route) {
    return String(route || "")
      .split("-")
      .map(s => s ? (s[0].toUpperCase() + s.slice(1)) : s)
      .join(" ");
  }

  function materializeStatHrefs() {
    const links = ROOT.querySelectorAll('.stat-row[data-route][data-filters]');
    links.forEach((a) => {
      const route = a.getAttribute('data-route');
      const raw = a.getAttribute('data-filters');
      try {
        const filtersObj = JSON.parse(raw || "{}");
        a.setAttribute('href', buildListUrl(route, filtersObj));
      } catch (e) {}
    });
  }

  function bindStatRouteButtons() {
    const links = ROOT.querySelectorAll('.stat-row[data-doctype][data-filters], .task-action-btn[data-doctype]');
    links.forEach((a) => {
      if (a.dataset && a.dataset.bizBound === "1") return;
      if (a.dataset) a.dataset.bizBound = "1";

      a.addEventListener('click', (e) => {
        const isNewTab = e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0;
        if (isNewTab) return;

        const shouldBlockEmpty = a.getAttribute('data-block-empty') === '1' && a.classList.contains('is-empty');
        if (shouldBlockEmpty) {
          e.preventDefault();
          frappe.show_alert({
            message: a.getAttribute('data-empty-msg') || '当前无待办',
            indicator: 'blue'
          }, 4);
          return;
        }

        e.preventDefault();

        const doctype = a.getAttribute('data-doctype');
        const raw = a.getAttribute('data-filters');

        let filtersObj = {};
        try {
          filtersObj = JSON.parse(raw || "{}");
        } catch (err) {
          window.location.href = a.getAttribute('href') || "/";
          return;
        }

        frappe.route_options = filtersObj;
        frappe.set_route('List', doctype);
      });
    });
  }

  function bindCmdRouteButtons() {
    const links = ROOT.querySelectorAll('.my-cmd-btn[href^="/app/"], .my-cmd-btn[href^="/desk/"]');
    links.forEach((a) => {
      if (a.dataset && a.dataset.bizCmdBound === "1") return;
      if (a.dataset) a.dataset.bizCmdBound = "1";

      a.addEventListener("click", (e) => {
        const isNewTab = e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0;
        if (isNewTab) return;

        const href = a.getAttribute("href") || "";
        const info = parseAppRoute(href);
        if (!info) return;

        e.preventDefault();

        const route = info.route;
        const doctype = ROUTE_TO_DOCTYPE[route] || guessDoctypeFromRoute(route);
        const routeOptions = parseRouteOptionsFromHref(href);

        if (info.is_new) {
          frappe.new_doc(doctype, routeOptions || {});
          return;
        }

        frappe.route_options = routeOptions || {};
        frappe.set_route("List", doctype);
      });
    });
  }

  // ============================================================
  // 4. 今日待办数据统计
  // ============================================================
  let todayTotalPending = 0;
  let todayTaskCounts = { po: 0, pr: 0, pi: 0, reim: 0, settle: 0 };

  function checkUpdateTodayCapsule() {
    const cap = ROOT.querySelector('#cap-today');
    const capText = ROOT.querySelector('#cap-text-today');
    if (!cap || !capText) return;

    todayTotalPending = Object.values(todayTaskCounts).reduce((a, b) => a + b, 0);
    if (todayTotalPending > 0) {
      cap.className = 'status-capsule capsule-today has-pending';
      capText.innerHTML = `今日待办：<b>${todayTotalPending}</b> 笔需处理`;
    } else {
      cap.className = 'status-capsule capsule-today all-done';
      capText.innerHTML = '今日待办：已全部清空 ✅';
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
        act.style.display = 'inline-flex';
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

    const act = ROOT.querySelector(actId);
    if (act) {
      act.setAttribute('data-filters', JSON.stringify(actualFilters));
      const route = act.getAttribute('href') ? act.getAttribute('href').split('?')[0].replace('/desk/', '') : '';
      if (route) act.setAttribute('href', buildListUrl(route, actualFilters));
    }

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

  async function fetchTaskPendingReimbursement() {
    if (!userCanRead('Purchase Invoice')) return;

    const pillId = '#pill-reim';
    const textId = '#pill-text-reim';
    const actId = '#act-reim';

    try {
      const piFilters = withOwnerFilter({ docstatus: 1, custom_biz_mode: '现金报销' });

      const piRows = await clientGetList('Purchase Invoice', {
        fields: ['name', 'owner'],
        filters: piFilters,
        limit_page_length: 5000
      });
      const piNames = (piRows || []).map(r => r.name).filter(Boolean);
      let missing = [...piNames];

      if (piNames.length > 0 && userCanRead('Reimbursement Request')) {
        const childRows = await clientGetList('Reimbursement Invoice Item', {
          fields: ['source_pi', 'parent'],
          filters: {
            parenttype: 'Reimbursement Request',
            parentfield: 'invoice_items',
            source_pi: ['in', piNames]
          },
          parent: 'Reimbursement Request',
          limit_page_length: 5000
        });

        const parentNames = [...new Set((childRows || []).map(r => r.parent).filter(Boolean))];
        let activeParents = new Set();

        if (parentNames.length > 0) {
          const rrRows = await clientGetList('Reimbursement Request', {
            fields: ['name'],
            filters: {
              name: ['in', parentNames],
              docstatus: ['!=', 2]
            },
            limit_page_length: 5000
          });
          activeParents = new Set((rrRows || []).map(r => r.name).filter(Boolean));
        }

        const hasReim = new Set(
          (childRows || [])
            .filter(r => activeParents.has(r.parent))
            .map(r => r.source_pi)
            .filter(Boolean)
        );

        missing = piNames.filter(n => !hasReim.has(n));
      }

      const count = missing.length;
      updateTaskPill(pillId, textId, actId, count, '笔发票', '无垫付待报销', 'reim');

      const act = ROOT.querySelector(actId);
      if (act) {
        if (count > 0) {
          const filtersObj = withOwnerFilter({ custom_biz_mode: '现金报销', docstatus: 1, name: ['in', missing] });
          act.setAttribute('data-filters', JSON.stringify(filtersObj));
          act.setAttribute('href', buildListUrl('purchase-invoice', filtersObj));
        } else {
          act.setAttribute('href', '/desk/purchase-invoice?custom_biz_mode=现金报销');
        }
      }

    } catch (e) {
      const pill = ROOT.querySelector(pillId);
      const text = ROOT.querySelector(textId);
      if (pill) pill.classList.remove('is-loading');
      if (text) text.innerText = '统计失败';
    }
  }

  function reloadAllTasks() {
    fetchTaskCardCount('Material Request', { docstatus: 1, status: ['in', ['Submitted', 'Pending', 'Partially Ordered']] }, '#pill-po', '#pill-text-po', '#act-po', '笔申请', false, 'po');
    fetchTaskCardCount('Purchase Order', { docstatus: 1, status: ['in', ['On Hold', 'To Receive', 'To Receive and Bill']] }, '#pill-pr', '#pill-text-pr', '#act-pr', '笔订单', false, 'pr');
    fetchTaskCardCount('Purchase Receipt', { status: ['in', ['Partly Billed', 'To Bill']] }, '#pill-pi', '#pill-text-pi', '#act-pi', '笔入库单', true, 'pi');
    fetchTaskPendingReimbursement();
    fetchTaskCardCount('Reimbursement Request', { docstatus: 1, outstanding_amount: ['>', 0] }, '#pill-settle', '#pill-text-settle', '#act-settle', '笔报销单', false, 'settle');
  }

  // ============================================================
  // 5. 月度任务逻辑
  // ============================================================
  function initPeriodicPeriodSelector() {
    const sel = ROOT.querySelector('#select-periodic-period');
    if (!sel || sel.options.length > 0) return;

    const now = new Date();
    const options = [];
    for (let i = 1; i <= 6; i++) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const y = d.getFullYear();
      const m = d.getMonth() + 1;
      const val = `${y}-${String(m).padStart(2, '0')}`;
      const label = `${y}年${m}月`;
      options.push({ val, y, m, label, isDefault: i === 1 });
    }

    options.forEach(opt => {
      const elOpt = document.createElement('option');
      elOpt.value = opt.val;
      elOpt.dataset.year = opt.y;
      elOpt.dataset.month = opt.m;
      elOpt.innerText = opt.label;
      if (opt.isDefault) elOpt.selected = true;
      sel.appendChild(elOpt);
    });

    sel.addEventListener('change', () => {
      const curOpt = sel.options[sel.selectedIndex];
      if (curOpt) {
        fetchMonthlySettlementStatus(curOpt.dataset.year, curOpt.dataset.month);
      }
    });
  }

  function renderPeriodicCompanyItems(containerId, badgeId, items) {
    const container = ROOT.querySelector(containerId);
    const badge = ROOT.querySelector(badgeId);
    if (!container) return;

    if (!items || items.length === 0) {
      container.innerHTML = `<div class="periodic-loading" style="color:#94a3b8;">当前无核定任务</div>`;
      if (badge) {
        badge.innerText = '暂无任务';
        badge.className = 'company-status-badge';
      }
      return;
    }

    const unsettledCount = items.filter(it => it.status !== 'settled').length;
    if (badge) {
      if (unsettledCount > 0) {
        badge.innerText = `待核定 ${unsettledCount} 项`;
        badge.className = 'company-status-badge has-unsettled';
      } else {
        badge.innerText = '全部完成 ✅';
        badge.className = 'company-status-badge all-settled';
      }
    }

    const html = items.map(it => {
      const isSettled = it.status === 'settled';
      const rowClass = isSettled ? 'is-settled-row' : 'is-unsettled-row';
      const badgeClass = isSettled ? 'badge-settled' : 'badge-unsettled';
      const badgeText = isSettled ? '✅ 已核定' : `⚠️ 去核定 ➔`;
      const href = it.route || 'javascript:void(0)';

      return `
        <div class="periodic-item-row ${rowClass}">
          <div class="periodic-item-left">
            <span class="periodic-item-icon">${it.icon || '📌'}</span>
            <div>
              <div class="periodic-item-title">${frappe.utils.escape_html(it.title)}</div>
              <div class="periodic-item-summary">${frappe.utils.escape_html(it.summary_text || '')}</div>
            </div>
          </div>
          <div>
            <a href="${href}" class="periodic-item-badge-link ${badgeClass}" data-route="${it.route}">
              ${badgeText}
            </a>
          </div>
        </div>
      `;
    }).join('');

    container.innerHTML = html;

    container.querySelectorAll('.periodic-item-badge-link[data-route]').forEach(a => {
      a.addEventListener('click', (e) => {
        const route = a.getAttribute('data-route');
        if (route && route.startsWith('/desk/')) {
          e.preventDefault();
          frappe.set_route(route.replace('/desk/', ''));
        }
      });
    });
  }

  function fetchMonthlySettlementStatus(year, month) {
    const badge = ROOT.querySelector('#periodic-period-badge');
    const capMonth = ROOT.querySelector('#cap-month');
    const capTextMonth = ROOT.querySelector('#cap-text-month');

    frappe.call({
      method: 'ashan_cn_procurement.services.periodic_tasks.get_monthly_settlement_status',
      args: { year: year, month: month },
      callback: function (r) {
        if (r && r.message) {
          const data = r.message;
          const comp = data.companies || {};
          const jizhong = comp.jizhong || {};
          const qifu = comp.qifu || {};

          const pendingCount = (data.total_items || 0) - (data.settled_items || 0);

          if (badge) {
            if (pendingCount > 0) {
              badge.innerText = `${pendingCount} 项待核定`;
              badge.className = 'panel-badge badge-pending';
            } else if ((data.total_items || 0) > 0 && data.all_done) {
              badge.innerText = `已全部核定 ✅`;
              badge.className = 'panel-badge badge-done';
            } else {
              badge.innerText = `${data.period_label}`;
              badge.className = 'panel-badge';
            }
          }

          if (capMonth && capTextMonth) {
            if (pendingCount > 0) {
              capMonth.className = 'status-capsule capsule-month has-pending';
              capTextMonth.innerHTML = `月度核定：<b>${pendingCount}</b> 项待对账`;
            } else {
              capMonth.className = 'status-capsule capsule-month all-done';
              capTextMonth.innerHTML = `月度核定：${data.period_label}全部核定 ✅`;
            }
          }

          const jzCard = ROOT.querySelector('#company-card-jizhong');
          if (jzCard) {
            if (jizhong.visible) {
              jzCard.style.display = 'block';
              renderPeriodicCompanyItems('#jizhong-items-list', '#jizhong-status-badge', jizhong.items);
            } else {
              jzCard.style.display = 'none';
            }
          }

          const qfCard = ROOT.querySelector('#company-card-qifu');
          if (qfCard) {
            if (qifu.visible) {
              qfCard.style.display = 'block';
              renderPeriodicCompanyItems('#qifu-items-list', '#qifu-status-badge', qifu.items);
            } else {
              qfCard.style.display = 'none';
            }
          }

          const section = ROOT.querySelector('#periodic-tasks-container');
          if (section) {
            if (!jizhong.visible && !qifu.visible) {
              section.style.display = 'none';
            } else {
              section.style.display = 'block';
            }
          }
        }
      }
    });
  }

  // ============================================================
  // 6. 临期预警数据驱动逻辑与就地快速核定 Dialog
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
            { label: '✅ 本次已完成检验/处置（快速记录并自动推进下期）', value: 'done' },
            { label: '🛒 尚未检验，发起委托采购申请 (Material Request)', value: 'procure' }
          ],
          default: 'done',
          reqd: 1,
          onchange: function() {
            const v = d.get_value('action_choice');
            d.toggle_display('done_date', v === 'done');
            d.toggle_display('next_due_date', v === 'done');
            d.toggle_display('notes', v === 'done');
          }
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
              capTextExpiry.innerHTML = `临期预警：<b>${data.danger_count}</b> 项已超期 ⚠️`;
            } else if (data.warning_count > 0) {
              capExpiry.className = 'status-capsule capsule-expiry has-pending';
              capTextExpiry.innerHTML = `临期预警：<b>${data.warning_count}</b> 项临期`;
            } else {
              capExpiry.className = 'status-capsule capsule-expiry all-done';
              capTextExpiry.innerHTML = '临期预警：全项合规在期 ✅';
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
            btn.addEventListener('click', (e) => {
              e.preventDefault();
              const idx = parseInt(btn.getAttribute('data-idx'));
              const targetItem = items[idx];
              if (targetItem) {
                openComplianceActionDialog(targetItem);
              }
            });
          });
        }
      }
    });
  }

  // ============================================================
  // 7. 场景待办与草稿统计 (归属人智能感知)
  // ============================================================
  function fetchCount(doctype, filters, textSel, linkSel, labelSuffix, applyOwner) {
    if (!userCanRead(doctype)) return;

    const elText = ROOT.querySelector(textSel);
    const elLink = ROOT.querySelector(linkSel);
    if (!elText || !elLink) return;

    const actualFilters = applyOwner ? withOwnerFilter(filters) : filters;
    const route = elLink.getAttribute('data-route') || guessDoctypeFromRoute(doctype).toLowerCase().replace(/ /g, '-');

    elLink.setAttribute('data-filters', JSON.stringify(actualFilters));
    elLink.setAttribute('href', buildListUrl(route, actualFilters));

    elLink.classList.add('is-loading');
    elLink.classList.remove('has-pending', 'is-empty', 'is-error');

    frappe.db.count(doctype, { filters: actualFilters })
      .then((count) => {
        const icon = elLink.querySelector('.stat-icon');
        elLink.classList.remove('is-loading', 'is-error');

        if ((count || 0) > 0) {
          elLink.classList.remove('is-empty');
          elLink.classList.add('has-pending');
          if (icon) icon.innerText = '🔔';
          elText.innerHTML = `查看待办：<b>${count}</b> · ${labelSuffix}`;
        } else {
          elLink.classList.remove('has-pending');
          elLink.classList.add('is-empty');
          if (icon) icon.innerText = '✅';
          elText.innerHTML = '当前无待办';
        }
      })
      .catch(() => {
        const icon = elLink.querySelector('.stat-icon');
        elLink.classList.remove('is-loading', 'has-pending', 'is-empty');
        elLink.classList.add('is-error');
        if (icon) icon.innerText = '⚠️';
        elText.innerHTML = '统计失败（可点击查看列表）';
      });
  }

  function ensureDraftRow(sourceId, draftId, textId) {
    const source = ROOT.querySelector(`#${sourceId}`);
    if (!source || ROOT.querySelector(`#${draftId}`)) return;

    const clone = source.cloneNode(true);
    clone.id = draftId;
    clone.classList.add('draft-row');
    clone.classList.remove('has-pending', 'is-empty', 'is-error');
    clone.setAttribute('data-block-empty', '0');
    clone.setAttribute('data-empty-msg', '');

    const text = clone.querySelector('.stat-text');
    if (text) {
      text.id = textId;
      text.innerHTML = '正在统计草稿…';
    }

    const icon = clone.querySelector('.stat-icon');
    if (icon) icon.innerText = '📝';

    source.insertAdjacentElement('afterend', clone);
  }

  function setupDraftRows() {
    const configs = [
      { sourceId: 'stat-req', draftId: 'draft-req', textId: 'text-draft-req', dt: 'Material Request' },
      { sourceId: 'stat-po', draftId: 'draft-po', textId: 'text-draft-po', dt: 'Purchase Order' },
      { sourceId: 'stat-pr-reg', draftId: 'draft-pr-reg', textId: 'text-draft-pr-reg', dt: 'Purchase Receipt' },
      { sourceId: 'stat-pi-reg', draftId: 'draft-pi-reg', textId: 'text-draft-pi-reg', dt: 'Purchase Invoice' },
      { sourceId: 'stat-reim-pr', draftId: 'draft-reim-pr', textId: 'text-draft-reim-pr', dt: 'Purchase Receipt' },
      { sourceId: 'stat-reim-pi', draftId: 'draft-reim-pi', textId: 'text-draft-reim-pi', dt: 'Purchase Invoice' },
      { sourceId: 'stat-reim-req', draftId: 'draft-reim-req', textId: 'text-draft-reim-req', dt: 'Reimbursement Request' },
      { sourceId: 'stat-wire-pr', draftId: 'draft-wire-pr', textId: 'text-draft-wire-pr', dt: 'Purchase Receipt' },
      { sourceId: 'stat-wire-pi', draftId: 'draft-wire-pi', textId: 'text-draft-wire-pi', dt: 'Purchase Invoice' },
      { sourceId: 'stat-mth-pr', draftId: 'draft-mth-pr', textId: 'text-draft-mth-pr', dt: 'Purchase Receipt' }
    ];
    configs.forEach(cfg => {
      if (userCanRead(cfg.dt)) {
        ensureDraftRow(cfg.sourceId, cfg.draftId, cfg.textId);
      }
    });
  }

  function fetchDraftCount(doctype, route, filters, textSel, linkSel, applyOwner) {
    if (!userCanRead(doctype)) return;

    const elText = ROOT.querySelector(textSel);
    const elLink = ROOT.querySelector(linkSel);
    if (!elText || !elLink) return;

    const icon = elLink.querySelector('.stat-icon');
    let draftFilters = Object.assign({ docstatus: 0 }, (filters || {}));
    if (applyOwner) {
      draftFilters = withOwnerFilter(draftFilters);
    }

    elLink.classList.add('is-loading');
    elLink.classList.remove('has-pending', 'is-empty', 'is-error');
    elLink.setAttribute('data-doctype', doctype);
    elLink.setAttribute('data-route', route);
    elLink.setAttribute('data-filters', JSON.stringify(draftFilters));
    elLink.setAttribute('href', buildListUrl(route, draftFilters));

    frappe.db.count(doctype, { filters: draftFilters })
      .then((count) => {
        elLink.classList.remove('is-loading', 'is-error');
        if (icon) icon.innerText = '📝';

        if ((count || 0) > 0) {
          elLink.classList.remove('is-empty');
          elLink.classList.add('has-pending');
          elLink.setAttribute('data-block-empty', '0');
          elLink.setAttribute('data-empty-msg', '');
        } else {
          elLink.classList.remove('has-pending');
          elLink.classList.add('is-empty');
          elLink.setAttribute('data-block-empty', '1');
          elLink.setAttribute('data-empty-msg', '当前无草稿');
        }

        elText.innerHTML = `查看草稿（${count || 0}个）`;
      })
      .catch(() => {
        elLink.classList.remove('is-loading', 'has-pending', 'is-empty');
        elLink.classList.add('is-error');
        if (icon) icon.innerText = '⚠️';
        elText.innerHTML = '草稿统计失败';
      });
  }

  function clientGetList(doctype, opts) {
    const args = Object.assign({ doctype }, (opts || {}));
    return new Promise((resolve, reject) => {
      frappe.call({
        method: "frappe.client.get_list",
        args,
        callback: (r) => resolve((r && r.message) ? r.message : []),
        error: (err) => reject(err)
      });
    });
  }

  async function fetchCashPiWithoutReim() {
    if (!userCanRead('Purchase Invoice')) return;

    const textSel = '#text-reim-pi';
    const linkSel = '#stat-reim-pi';
    const elText = ROOT.querySelector(textSel);
    const elLink = ROOT.querySelector(linkSel);
    if (!elText || !elLink) return;

    const icon = elLink.querySelector('.stat-icon');
    const route = elLink.getAttribute('data-route') || 'purchase-invoice';

    elLink.classList.add('is-loading');
    elLink.classList.remove('has-pending', 'is-empty', 'is-error');
    if (icon) icon.innerText = '⏳';
    elText.innerHTML = '正在统计…';

    try {
      const piFilters = withOwnerFilter({ docstatus: 1, custom_biz_mode: '现金报销' });

      const piRows = await clientGetList('Purchase Invoice', {
        fields: ['name'],
        filters: piFilters,
        limit_page_length: 5000
      });
      const piNames = (piRows || []).map(r => r.name).filter(Boolean);
      let missing = [...piNames];

      if (piNames.length > 0 && userCanRead('Reimbursement Request')) {
        const childRows = await clientGetList('Reimbursement Invoice Item', {
          fields: ['source_pi', 'parent'],
          filters: {
            parenttype: 'Reimbursement Request',
            parentfield: 'invoice_items',
            source_pi: ['in', piNames]
          },
          parent: 'Reimbursement Request',
          limit_page_length: 5000
        });

        const parentNames = [...new Set((childRows || []).map(r => r.parent).filter(Boolean))];
        let activeParents = new Set();

        if (parentNames.length > 0) {
          const rrRows = await clientGetList('Reimbursement Request', {
            fields: ['name'],
            filters: {
              name: ['in', parentNames],
              docstatus: ['!=', 2]
            },
            limit_page_length: 5000
          });
          activeParents = new Set((rrRows || []).map(r => r.name).filter(Boolean));
        }

        const hasReim = new Set(
          (childRows || [])
            .filter(r => activeParents.has(r.parent))
            .map(r => r.source_pi)
            .filter(Boolean)
        );

        missing = piNames.filter(n => !hasReim.has(n));
      }

      const count = missing.length;
      elLink.classList.remove('is-loading', 'is-error');

      if (count > 0) {
        const filtersObj = withOwnerFilter({
          custom_biz_mode: '现金报销',
          docstatus: 1,
          name: ['in', missing]
        });
        elLink.setAttribute('data-filters', JSON.stringify(filtersObj));
        elLink.setAttribute('href', buildListUrl(route, filtersObj));
        elLink.setAttribute('data-block-empty', '0');
        elLink.setAttribute('data-empty-msg', '');
        elLink.classList.remove('is-empty');
        elLink.classList.add('has-pending');
        if (icon) icon.innerText = '🔔';
        elText.innerHTML = `<b>${count}</b> 个未申请报销的发票`;
      } else {
        elLink.setAttribute('data-block-empty', '1');
        elLink.setAttribute('data-empty-msg', '当前无未申请报销的发票');
        elLink.setAttribute('href', 'javascript:void(0)');
        elLink.classList.remove('has-pending');
        elLink.classList.add('is-empty');
        if (icon) icon.innerText = '✅';
        elText.innerHTML = '当前无未申请报销的发票';
      }

    } catch (e) {
      elLink.classList.remove('is-loading', 'has-pending', 'is-empty');
      elLink.classList.add('is-error');
      if (icon) icon.innerText = '⚠️';
      elText.innerHTML = '统计失败（可点击查看列表）';
    }
  }

  // ============================================================
  // 8. 统一初始化执行
  // ============================================================
  function initAllMissionHub() {
    applyPermissionAdaptation();
    initPeriodicPeriodSelector();

    materializeStatHrefs();
    setupDraftRows();
    bindStatRouteButtons();
    bindCmdRouteButtons();

    reloadAllTasks();
    fetchMonthlySettlementStatus();
    fetchComplianceExpiryStatus();

    // 场景统计
    fetchCount('Material Request', { docstatus: 1, status: ['in', ['Submitted', 'Pending', 'Partially Ordered']] }, '#text-req', '#stat-req', '待下单', false);
    fetchCount('Purchase Order', { docstatus: 1, status: ['in', ['On Hold', 'To Receive', 'To Receive and Bill']] }, '#text-po', '#stat-po', '待收货', false);
    fetchCount('Purchase Receipt', { custom_biz_mode: '常规采购', status: ['in', ['Partly Billed', 'To Bill']] }, '#text-pr-reg', '#stat-pr-reg', '待开票', true);
    fetchCount('Purchase Invoice', { custom_biz_mode: '常规采购', status: ['in', ['Unpaid', 'Partly Paid', 'Overdue', 'Submitted']] }, '#text-pi-reg', '#stat-pi-reg', '待付款', true);

    fetchCount('Purchase Receipt', { custom_biz_mode: '现金报销', status: ['in', ['Partly Billed', 'To Bill']] }, '#text-reim-pr', '#stat-reim-pr', '待开票', true);
    fetchCashPiWithoutReim();
    fetchCount('Reimbursement Request', { custom_biz_mode: '现金报销', docstatus: 1, outstanding_amount: ['>', 0] }, '#text-reim-req', '#stat-reim-req', '未付完款', true);

    fetchCount('Purchase Receipt', { custom_biz_mode: '自办电汇', status: ['in', ['Partly Billed', 'To Bill']] }, '#text-wire-pr', '#stat-wire-pr', '待开票', true);
    fetchCount('Purchase Invoice', { custom_biz_mode: '自办电汇', status: ['in', ['Submitted', 'Unpaid', 'Partly Paid', 'Overdue']] }, '#text-wire-pi', '#stat-wire-pi', '待付款', true);

    fetchCount('Purchase Receipt', { custom_biz_mode: '月结补录', status: ['in', ['Partly Billed', 'To Bill']] }, '#text-mth-pr', '#stat-mth-pr', '待开票', true);

    fetchDraftCount('Material Request', 'material-request', {}, '#text-draft-req', '#draft-req', false);
    fetchDraftCount('Purchase Order', 'purchase-order', {}, '#text-draft-po', '#draft-po', false);
    fetchDraftCount('Purchase Receipt', 'purchase-receipt', { custom_biz_mode: '常规采购' }, '#text-draft-pr-reg', '#draft-pr-reg', true);
    fetchDraftCount('Purchase Invoice', 'purchase-invoice', { custom_biz_mode: '常规采购' }, '#text-draft-pi-reg', '#draft-pi-reg', true);
    fetchDraftCount('Purchase Receipt', 'purchase-receipt', { custom_biz_mode: '现金报销' }, '#text-draft-reim-pr', '#draft-reim-pr', true);
    fetchDraftCount('Purchase Invoice', 'purchase-invoice', { custom_biz_mode: '现金报销' }, '#text-draft-reim-pi', '#draft-reim-pi', true);
    fetchDraftCount('Reimbursement Request', 'reimbursement-request', { custom_biz_mode: '现金报销' }, '#text-draft-reim-req', '#draft-reim-req', true);
    fetchDraftCount('Purchase Receipt', 'purchase-receipt', { custom_biz_mode: '自办电汇' }, '#text-draft-wire-pr', '#draft-wire-pr', true);
    fetchDraftCount('Purchase Invoice', 'purchase-invoice', { custom_biz_mode: '自办电汇' }, '#text-draft-wire-pi', '#draft-wire-pi', true);
    fetchDraftCount('Purchase Receipt', 'purchase-receipt', { custom_biz_mode: '月结补录' }, '#text-draft-mth-pr', '#draft-mth-pr', true);
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

with open('ashan_cn_procurement/ashan_cn_procurement/fixtures/custom_html_block.json', 'w', encoding='utf-8') as f:
    json.dump(block_data, f, ensure_ascii=False, indent=2)

print('Generated unified mission control custom_html_block.json with inline action dialog!')
