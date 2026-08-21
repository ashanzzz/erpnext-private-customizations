# -*- coding: utf-8 -*-
import os
import paramiko
import json

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
USER_SSH = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER_SSH, password=PASSWORD, timeout=10)

HTML_CONTENT = r'''<div class="biz-nav-container">

  <!-- ============================================================ -->
  <!-- 🌟 顶层看板：我的待办任务 (My Pending Tasks)                -->
  <!-- ============================================================ -->
  <div class="my-tasks-section" id="my-tasks-container">
    <div class="tasks-section-header">
      <div class="tasks-title-wrapper">
        <span class="tasks-main-title">📋 我的待办任务 (今日工作焦点)</span>
        <span class="tasks-badge">开票/报销按归属人隔离 · 入库共享池</span>
      </div>
      <button type="button" class="tasks-refresh-btn" id="btn-refresh-tasks" title="刷新待办数据">
        <span class="refresh-icon">🔄</span> 刷新
      </button>
    </div>

    <!-- 待办任务卡片弹性网格 -->
    <div class="tasks-grid" id="tasks-grid-wrapper">

      <!-- 任务 1：待采购下单 (采购池) -->
      <div class="task-card task-card-amber" id="task-card-po" data-task-perm="Purchase Order" data-doctype="Material Request">
        <div class="task-card-top">
          <div class="task-card-icon">🟡</div>
          <div class="task-card-info">
            <div class="task-card-name">待采购下单</div>
            <div class="task-card-desc">已批需求等待下达订单</div>
          </div>
        </div>
        <div class="task-card-bottom">
          <div class="task-count-pill is-loading" id="pill-po">
            <span class="pill-dot"></span>
            <span class="pill-text" id="pill-text-po">统计中…</span>
          </div>
          <a href="/desk/material-request" class="task-action-btn" id="act-po" data-doctype="Material Request" data-filters='{"docstatus":1,"status":["in",["Submitted","Pending","Partially Ordered"]]}'>
            去下单 ➔
          </a>
        </div>
      </div>

      <!-- 任务 2：待物资入库 (公共仓库入库池：谁有权限谁都可以入库) -->
      <div class="task-card task-card-green" id="task-card-pr" data-task-perm="Purchase Receipt" data-doctype="Purchase Order">
        <div class="task-card-top">
          <div class="task-card-icon">🟢</div>
          <div class="task-card-info">
            <div class="task-card-name">待物资入库</div>
            <div class="task-card-desc">全员订单·公共收货物资池</div>
          </div>
        </div>
        <div class="task-card-bottom">
          <div class="task-count-pill is-loading" id="pill-pr">
            <span class="pill-dot"></span>
            <span class="pill-text" id="pill-text-pr">统计中…</span>
          </div>
          <a href="/desk/purchase-order" class="task-action-btn" id="act-pr" data-doctype="Purchase Order" data-filters='{"docstatus":1,"status":["in",["On Hold","To Receive","To Receive and Bill"]]}'>
            去收货 ➔
          </a>
        </div>
      </div>

      <!-- 任务 3：待采购开票 (A生成订单 -> 仅A计算开票) -->
      <div class="task-card task-card-blue" id="task-card-pi" data-task-perm="Purchase Invoice" data-doctype="Purchase Receipt">
        <div class="task-card-top">
          <div class="task-card-icon">🔵</div>
          <div class="task-card-info">
            <div class="task-card-name">待采购开票</div>
            <div class="task-card-desc">我经手的入库等待录入发票</div>
          </div>
        </div>
        <div class="task-card-bottom">
          <div class="task-count-pill is-loading" id="pill-pi">
            <span class="pill-dot"></span>
            <span class="pill-text" id="pill-text-pi">统计中…</span>
          </div>
          <a href="/desk/purchase-receipt" class="task-action-btn" id="act-pi" data-doctype="Purchase Receipt">
            去开票 ➔
          </a>
        </div>
      </div>

      <!-- 任务 4：待发起报销 (A垫付发票 -> 仅A发起报销) -->
      <div class="task-card task-card-orange" id="task-card-reim" data-task-perm="Reimbursement Request" data-doctype="Purchase Invoice">
        <div class="task-card-top">
          <div class="task-card-icon">🟠</div>
          <div class="task-card-info">
            <div class="task-card-name">待发起报销</div>
            <div class="task-card-desc">我垫付的发票尚未填报销单</div>
          </div>
        </div>
        <div class="task-card-bottom">
          <div class="task-count-pill is-loading" id="pill-reim">
            <span class="pill-dot"></span>
            <span class="pill-text" id="pill-text-reim">统计中…</span>
          </div>
          <a href="/desk/purchase-invoice" class="task-action-btn" id="act-reim" data-doctype="Purchase Invoice">
            去报销 ➔
          </a>
        </div>
      </div>

      <!-- 任务 5：待报销结款 (财务付款池) -->
      <div class="task-card task-card-purple" id="task-card-settle" data-task-perm="Payment Entry" data-doctype="Reimbursement Request">
        <div class="task-card-top">
          <div class="task-card-icon">🟣</div>
          <div class="task-card-info">
            <div class="task-card-name">待报销结款</div>
            <div class="task-card-desc">已审报销等待付清款项</div>
          </div>
        </div>
        <div class="task-card-bottom">
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

  <div class="biz-divider" style="margin: 20px 0 16px;"></div>

  <!-- ============================================================ -->
  <!-- 📦 4 大全流程业务场景卡片导航                                -->
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
'''

JS_CONTENT = r'''(function () {
  const ROOT = (typeof root_element !== "undefined" && root_element) ? root_element : document;

  // ============================================================
  // 1. Frappe 官方原生权限与归属人判定工具
  // ============================================================
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

  // 辅助：为经办人 A 专属单据追加 owner 过滤（管理员看全员）
  function withOwnerFilter(filters) {
    const base = Object.assign({}, (filters || {}));
    if (!isAdminUser()) {
      base.owner = getCurrentUser();
    }
    return base;
  }

  // ============================================================
  // 2. 权限自适应剪裁与降级 (Layered Adaptive UX)
  // ============================================================
  function applyPermissionAdaptation() {
    // A. 待办任务中心权限剪裁
    const taskCards = ROOT.querySelectorAll('.task-card[data-task-perm]');
    taskCards.forEach((card) => {
      const permTarget = card.getAttribute('data-task-perm');
      let isVisible = false;

      if (permTarget === "Payment Entry") {
        isVisible = isFinanceUser() && userCanRead("Reimbursement Request");
      } else if (permTarget === "Purchase Order") {
        isVisible = userCanCreate("Purchase Order") || userCanRead("Material Request");
      } else if (permTarget === "Purchase Receipt") {
        // 入库：谁有权限都可以做
        isVisible = userCanCreate("Purchase Receipt") || userCanRead("Purchase Order");
      } else if (permTarget === "Purchase Invoice") {
        // 开票：A 生成订单 -> 仅 A 计算其待开票
        isVisible = userCanCreate("Purchase Invoice") || userCanRead("Purchase Receipt");
      } else if (permTarget === "Reimbursement Request") {
        // 报销：A 垫付 -> 仅 A 发起报销
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

    const myTasksSec = ROOT.querySelector('#my-tasks-container');
    if (myTasksSec) {
      const visibleTasks = Array.from(ROOT.querySelectorAll('.task-card')).filter(c => !c.classList.contains('step-hidden'));
      if (visibleTasks.length === 0) {
        myTasksSec.classList.add('scene-hidden');
      } else {
        myTasksSec.classList.remove('scene-hidden');
      }
    }

    // B. 场景节点级别与动作级别适配
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

    // C. 场景级空场景智能收起
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

    // 检查并排双场景容器（场景3与场景4）
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

  // ============================================================
  // 3. 路由与 URL 构建工具 (兼容 /desk 与 /app)
  // ============================================================
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
      const m = p.match(/^\/(?:app|desk)\/([^\/?#]+)(?:\/(new))?\/?$/);
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
  // 4. 我的待办任务中心数据驱动逻辑 (归属人隔离 + 入库共享池)
  // ============================================================
  function updateTaskPill(pillId, textId, actId, count, singleUnitLabel, zeroLabel) {
    const pill = ROOT.querySelector(pillId);
    const text = ROOT.querySelector(textId);
    const act = ROOT.querySelector(actId);
    if (!pill || !text) return;

    pill.classList.remove('is-loading', 'is-done', 'has-pending');

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

  function fetchTaskCardCount(doctype, filters, pillId, textId, actId, unitLabel, applyOwner) {
    if (!userCanRead(doctype)) return;

    const actualFilters = applyOwner ? withOwnerFilter(filters) : filters;

    // 同步动作按钮的过滤条件
    const act = ROOT.querySelector(actId);
    if (act) {
      act.setAttribute('data-filters', JSON.stringify(actualFilters));
      const route = act.getAttribute('href') ? act.getAttribute('href').split('?')[0].replace('/desk/', '') : '';
      if (route) act.setAttribute('href', buildListUrl(route, actualFilters));
    }

    frappe.db.count(doctype, { filters: actualFilters })
      .then((count) => {
        updateTaskPill(pillId, textId, actId, count, unitLabel, '已全部处理');
      })
      .catch(() => {
        const pill = ROOT.querySelector(pillId);
        const text = ROOT.querySelector(textId);
        if (pill) pill.classList.remove('is-loading');
        if (text) text.innerText = '统计失败';
      });
  }

  // 待办任务 4：垫付待报销 (采购发票动态差集 · 仅统计 A 垫付的发票)
  async function fetchTaskPendingReimbursement() {
    if (!userCanRead('Purchase Invoice')) return;

    const pillId = '#pill-reim';
    const textId = '#pill-text-reim';
    const actId = '#act-reim';

    try {
      // 归属人过滤：非管理员仅拉取自己垫付的发票
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
      updateTaskPill(pillId, textId, actId, count, '笔发票', '无垫付待报销');

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
    // 任务1：待下单 (Material Request 待转 PO，采购共享池)
    fetchTaskCardCount('Material Request', { docstatus: 1, status: ['in', ['Submitted', 'Pending', 'Partially Ordered']] }, '#pill-po', '#pill-text-po', '#act-po', '笔申请', false);

    // 任务2：待收货 (PO 待转 PR，入库共享池：谁有权限都可以做)
    fetchTaskCardCount('Purchase Order', { docstatus: 1, status: ['in', ['On Hold', 'To Receive', 'To Receive and Bill']] }, '#pill-pr', '#pill-text-pr', '#act-pr', '笔订单', false);

    // 任务3：待开票 (PR 待转 PI，A生成的采购 -> 仅A计算其待开票)
    fetchTaskCardCount('Purchase Receipt', { status: ['in', ['Partly Billed', 'To Bill']] }, '#pill-pi', '#pill-text-pi', '#act-pi', '笔入库单', true);

    // 任务4：待报销 (A垫付发票 -> 仅A发起报销)
    fetchTaskPendingReimbursement();

    // 任务5：待结款 (财务统一付款池)
    fetchTaskCardCount('Reimbursement Request', { docstatus: 1, outstanding_amount: ['>', 0] }, '#pill-settle', '#pill-text-settle', '#act-settle', '笔报销单', false);
  }

  // ============================================================
  // 5. 场景待办与草稿统计 (归属人智能感知)
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

  /*
    场景2-采购发票：统计“未写报销申请”的 Purchase Invoice (差集 · 仅看 A 垫付的发票)
  */
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
  // 6. 初始化执行
  // ============================================================
  applyPermissionAdaptation();

  materializeStatHrefs();
  setupDraftRows();
  bindStatRouteButtons();
  bindCmdRouteButtons();

  const refreshBtn = ROOT.querySelector('#btn-refresh-tasks');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      reloadAllTasks();
      frappe.show_alert({ message: '待办任务已更新', indicator: 'green' }, 3);
    });
  }

  reloadAllTasks();

  // ===== 执行场景统计：场景1 =====
  fetchCount('Material Request', { docstatus: 1, status: ['in', ['Submitted', 'Pending', 'Partially Ordered']] }, '#text-req', '#stat-req', '待下单', false);
  fetchCount('Purchase Order', { docstatus: 1, status: ['in', ['On Hold', 'To Receive', 'To Receive and Bill']] }, '#text-po', '#stat-po', '待收货', false);
  fetchCount('Purchase Receipt', { custom_biz_mode: '常规采购', status: ['in', ['Partly Billed', 'To Bill']] }, '#text-pr-reg', '#stat-pr-reg', '待开票', true);
  fetchCount('Purchase Invoice', { custom_biz_mode: '常规采购', status: ['in', ['Unpaid', 'Partly Paid', 'Overdue', 'Submitted']] }, '#text-pi-reg', '#stat-pi-reg', '待付款', true);

  // ===== 执行场景统计：场景2 =====
  fetchCount('Purchase Receipt', { custom_biz_mode: '现金报销', status: ['in', ['Partly Billed', 'To Bill']] }, '#text-reim-pr', '#stat-reim-pr', '待开票', true);
  fetchCashPiWithoutReim();
  fetchCount('Reimbursement Request', { custom_biz_mode: '现金报销', docstatus: 1, outstanding_amount: ['>', 0] }, '#text-reim-req', '#stat-reim-req', '未付完款', true);

  // ===== 场景3 =====
  fetchCount('Purchase Receipt', { custom_biz_mode: '自办电汇', status: ['in', ['Partly Billed', 'To Bill']] }, '#text-wire-pr', '#stat-wire-pr', '待开票', true);
  fetchCount('Purchase Invoice', { custom_biz_mode: '自办电汇', status: ['in', ['Submitted', 'Unpaid', 'Partly Paid', 'Overdue']] }, '#text-wire-pi', '#stat-wire-pi', '待付款', true);

  // ===== 场景4 =====
  fetchCount('Purchase Receipt', { custom_biz_mode: '月结补录', status: ['in', ['Partly Billed', 'To Bill']] }, '#text-mth-pr', '#stat-mth-pr', '待开票', true);

  // ===== 草稿统计 (经办人私有草稿) =====
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

})();
'''

# CSS 保持不变 (引用现有的 CSS_CONTENT)
from deploy_tasks_and_scenes import CSS_CONTENT

py_code = f"""# -*- coding: utf-8 -*-
import frappe
import json

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

BLOCK_NAME = "业务场景导航"

html_c = {repr(HTML_CONTENT)}
js_c = {repr(JS_CONTENT)}
css_c = {repr(CSS_CONTENT)}

if not frappe.db.exists("Custom HTML Block", BLOCK_NAME):
    doc = frappe.get_doc({{
        "doctype": "Custom HTML Block",
        "name": BLOCK_NAME,
        "html": html_c,
        "script": js_c,
        "style": css_c,
        "private": 0
    }})
    doc.insert(ignore_permissions=True)
else:
    doc = frappe.get_doc("Custom HTML Block", BLOCK_NAME)
    doc.html = html_c
    doc.script = js_c
    doc.style = css_c
    doc.private = 0
    doc.save(ignore_permissions=True)

frappe.db.commit()
frappe.clear_cache()
print("[OK] Owner-Scattered Pending Tasks deployed to DB!")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/deploy_owner_isolated_tasks.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/deploy_owner_isolated_tasks.py erpnext16:/tmp/deploy_owner_isolated_tasks.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/deploy_owner_isolated_tasks.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

# 更新本地 fixture
fixture_data = {
    "doctype": "Custom HTML Block",
    "name": "业务场景导航",
    "html": HTML_CONTENT,
    "script": JS_CONTENT,
    "style": CSS_CONTENT,
    "private": 0
}
with open("ashan_cn_procurement/ashan_cn_procurement/fixtures/custom_html_block.json", "w", encoding="utf-8") as f:
    json.dump(fixture_data, f, ensure_ascii=False, indent=2)

print("[OK] Local fixture custom_html_block.json updated with owner isolation!")

sftp.close()
ssh.close()
