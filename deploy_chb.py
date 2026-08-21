# -*- coding: utf-8 -*-
import os
import paramiko

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

HTML_CONTENT = r'''<!--
修改日志：
- 2026-01-05
  1) 场景1：补齐 Purchase Receipt / Purchase Invoice 的 /new 链接参数 custom_biz_mode=常规采购，
     使“新建单据”默认带出业务模式（配合 JS 的 frappe.new_doc(route_options)）。
影响范围：仅 Custom HTML Block；不改任何业务单据与权限。
-->

<div class="biz-nav-container">

  <!-- ========== 场景 1 ========== -->
  <div class="biz-section-header">
    <span class="biz-title" style="color:#2490ef;">📦 场景1：购买申请（常规采购）</span>
    <span class="biz-subtitle">订单驱动 | 标准化</span>
  </div>
  <div class="biz-scene-note">说明：常规采购，以购买申请为起点，打印单据为采购申请单据。</div>

  <div class="biz-flow-wrapper">
    <div class="step-card step-blue">
      <div class="step-header">1. 采购申请</div>
      <a href="/app/material-request/new" class="my-cmd-btn btn-blue">
        <span class="icon">+</span> 新建申请
      </a>
      <a href="/app/material-request" class="my-cmd-btn btn-blue-outline">
        <span class="icon">≡</span> 查看全部
      </a>

      <a href="/app/material-request/view/list"
         class="stat-row stat-blue is-loading"
         id="stat-req"
         data-doctype="Material Request"
         data-route="material-request"
         data-filters='{"docstatus":1,"status":["in",["Submitted","Pending","Partially Ordered"]]}' >
        <span class="stat-icon">⏳</span>
        <span class="stat-text" id="text-req">正在统计…</span>
      </a>
    </div>

    <div class="flow-arrow">➔</div>

    <div class="step-card step-blue">
      <div class="step-header">2. 采购订单</div>
      <a href="/app/purchase-order/new" class="my-cmd-btn btn-blue">
        <span class="icon">+</span> 新建订单
      </a>
      <a href="/app/purchase-order" class="my-cmd-btn btn-blue-outline">
        <span class="icon">≡</span> 查看全部
      </a>

      <a href="/app/purchase-order/view/list"
         class="stat-row stat-blue is-loading"
         id="stat-po"
         data-doctype="Purchase Order"
         data-route="purchase-order"
         data-filters='{"docstatus":1,"status":["in",["On Hold","To Receive","To Receive and Bill"]]}' >
        <span class="stat-icon">⏳</span>
        <span class="stat-text" id="text-po">正在统计…</span>
      </a>
    </div>

    <div class="flow-arrow">➔</div>

    <div class="step-card step-blue">
      <div class="step-header">3. 物资入库</div>
      <a href="/app/purchase-receipt/new?custom_biz_mode=常规采购" class="my-cmd-btn btn-blue">
        <span class="icon">+</span> 新建入库
      </a>
      <a href="/app/purchase-receipt?custom_biz_mode=常规采购" class="my-cmd-btn btn-blue-outline">
        <span class="icon">≡</span> 查看全部
      </a>

      <a href="/app/purchase-receipt/view/list"
         class="stat-row stat-blue is-loading"
         id="stat-pr-reg"
         data-doctype="Purchase Receipt"
         data-route="purchase-receipt"
         data-filters='{"custom_biz_mode":"常规采购","status":["in",["Partly Billed","To Bill"]]}' >
        <span class="stat-icon">⏳</span>
        <span class="stat-text" id="text-pr-reg">正在统计…</span>
      </a>
    </div>

    <div class="flow-arrow">➔</div>

    <div class="step-card step-blue">
      <div class="step-header">4. 采购发票</div>
      <a href="/app/purchase-invoice/new?custom_biz_mode=常规采购" class="my-cmd-btn btn-blue">
        <span class="icon">+</span> 新建发票
      </a>
      <a href="/app/purchase-invoice?custom_biz_mode=常规采购" class="my-cmd-btn btn-blue-outline">
        <span class="icon">≡</span> 查看全部
      </a>

      <a href="/app/purchase-invoice/view/list"
         class="stat-row stat-blue is-loading"
         id="stat-pi-reg"
         data-doctype="Purchase Invoice"
         data-route="purchase-invoice"
         data-filters='{"custom_biz_mode":"常规采购","status":["in",["Unpaid","Partly Paid","Overdue","Submitted"]]}' >
        <span class="stat-icon">⏳</span>
        <span class="stat-text" id="text-pi-reg">正在统计…</span>
      </a>
    </div>
  </div>

  <div class="biz-divider"></div>

  <!-- ========== 场景 2 ========== -->
  <div class="biz-section-header">
    <span class="biz-title" style="color:#e67e22;">🚀 场景2：现金报销（垫付）</span>
    <span class="biz-subtitle">个人垫付 | 快速回款</span>
  </div>
  <div class="biz-scene-note">说明：报销单，打印单据为报销申请单据的整算单</div>

  <div class="biz-flow-wrapper">
    <div class="step-card step-orange">
      <div class="step-header">1. 采购入库</div>
      <a href="/app/purchase-receipt/new?custom_biz_mode=现金报销&supplier=其它供应商" class="my-cmd-btn btn-orange">
        <span class="icon">+</span> 新建入库
      </a>

      <a href="/app/purchase-receipt?custom_biz_mode=现金报销" class="my-cmd-btn btn-orange-outline">
        <span class="icon">≡</span> 查看全部
      </a>

      <a href="/app/purchase-receipt/view/list"
         class="stat-row stat-orange is-loading"
         id="stat-reim-pr"
         data-doctype="Purchase Receipt"
         data-route="purchase-receipt"
         data-filters='{"custom_biz_mode":"现金报销","status":["in",["Partly Billed","To Bill"]]}' >
        <span class="stat-icon">⏳</span>
        <span class="stat-text" id="text-reim-pr">正在统计…</span>
      </a>
    </div>

    <div class="flow-arrow">➔</div>

    <div class="step-card step-orange">
      <div class="step-header">2. 采购发票</div>
      <a href="/app/purchase-invoice/new?custom_biz_mode=现金报销" class="my-cmd-btn btn-orange">
        <span class="icon">+</span> 新建发票
      </a>
      <a href="/app/purchase-invoice?custom_biz_mode=现金报销" class="my-cmd-btn btn-orange-outline">
        <span class="icon">≡</span> 查看全部
      </a>

      <a href="/app/purchase-invoice/view/list"
         class="stat-row stat-orange is-loading"
         id="stat-reim-pi"
         data-doctype="Purchase Invoice"
         data-route="purchase-invoice"
         data-filters='{"custom_biz_mode":"现金报销","docstatus":1}' >
        <span class="stat-icon">⏳</span>
        <span class="stat-text" id="text-reim-pi">正在统计…</span>
      </a>
    </div>

    <div class="flow-arrow">➔</div>

    <div class="step-card step-orange">
      <div class="step-header">3. 报销申请</div>
      <a href="/app/reimbursement-request/new?custom_biz_mode=现金报销" class="my-cmd-btn btn-orange">
        <span class="icon">+</span> 新建报销
      </a>
      <a href="/app/reimbursement-request?custom_biz_mode=现金报销&docstatus=1" class="my-cmd-btn btn-orange-outline">
        <span class="icon">≡</span> 查看全部
      </a>

      <a href="/app/reimbursement-request/view/list"
         class="stat-row stat-orange is-loading"
         id="stat-reim-req"
         data-doctype="Reimbursement Request"
         data-route="reimbursement-request"
         data-filters='{"custom_biz_mode":"现金报销","docstatus":1,"outstanding_amount":[">",0]}' >
        <span class="stat-icon">⏳</span>
        <span class="stat-text" id="text-reim-req">正在统计…</span>
      </a>
    </div>
  </div>

  <div class="biz-divider"></div>

  <!-- ========== 场景 3 & 4（并排） ========== -->
  <div style="display:flex; gap:20px;">

    <!-- 场景 3 -->
    <div style="flex:2;">
      <div class="biz-section-header" style="margin-bottom:8px;">
        <span class="biz-title" style="color:#8e44ad; font-size:14px;">⚡ 场景3：自办电汇（秒结）</span>
      </div>
      <div class="biz-scene-note">说明：为自行电汇采购的流程，需要打印入库的补写的入库单。由于是电汇，必定有发票。</div>

      <div class="biz-flow-wrapper">
        <div class="step-card step-purple">
          <div class="step-header">1. 采购入库</div>
          <a href="/app/purchase-receipt/new?custom_biz_mode=自办电汇" class="my-cmd-btn btn-purple">
            <span class="icon">+</span> 新建入库
          </a>
          <a href="/app/purchase-receipt?custom_biz_mode=自办电汇" class="my-cmd-btn btn-purple-outline">
            <span class="icon">≡</span> 查看全部
          </a>

          <a href="/app/purchase-receipt/view/list"
             class="stat-row stat-purple is-loading"
             id="stat-wire-pr"
             data-doctype="Purchase Receipt"
             data-route="purchase-receipt"
             data-filters='{"custom_biz_mode":"自办电汇","status":["in",["Partly Billed","To Bill"]]}' >
            <span class="stat-icon">⏳</span>
            <span class="stat-text" id="text-wire-pr">正在统计…</span>
          </a>
        </div>

        <div class="flow-arrow">➔</div>

        <div class="step-card step-purple">
          <div class="step-header">2. 发票&支付</div>
          <a href="/app/purchase-invoice/new?custom_biz_mode=自办电汇" class="my-cmd-btn btn-purple">
            <span class="icon">+</span> 新建发票
          </a>
          <a href="/app/purchase-invoice?custom_biz_mode=自办电汇" class="my-cmd-btn btn-purple-outline">
            <span class="icon">≡</span> 查看全部
          </a>

          <a href="/app/purchase-invoice/view/list"
             class="stat-row stat-purple is-loading"
             id="stat-wire-pi"
             data-doctype="Purchase Invoice"
             data-route="purchase-invoice"
             data-filters='{"custom_biz_mode":"自办电汇","status":["in",["Submitted","Unpaid","Partly Paid","Overdue"]]}' >
            <span class="stat-icon">⏳</span>
            <span class="stat-text" id="text-wire-pi">正在统计…</span>
          </a>
        </div>
      </div>
    </div>

    <!-- 场景 4 -->
    <div style="flex:1; border-left:1px dashed #e2e8f0; padding-left:20px;">
      <div class="biz-section-header" style="margin-bottom:8px;">
        <span class="biz-title" style="color:#00b894; font-size:14px;">📅 场景4：月结补录</span>
      </div>
      <div class="biz-scene-note">说明：仅用于月结供应商，如聚鑫、金普金等。打印采购入库的补录单，一般无需填写发票。</div>

      <div class="biz-flow-wrapper">
        <div class="step-card step-teal">
          <div class="step-header">1. 采购入库</div>
          <a href="/app/purchase-receipt/new?custom_biz_mode=月结补录" class="my-cmd-btn btn-teal">
            <span class="icon">+</span> 新建入库
          </a>
          <a href="/app/purchase-receipt?custom_biz_mode=月结补录" class="my-cmd-btn btn-teal-outline">
            <span class="icon">≡</span> 查看全部
          </a>

          <a href="/app/purchase-receipt/view/list"
             class="stat-row stat-teal is-loading"
             id="stat-mth-pr"
             data-doctype="Purchase Receipt"
             data-route="purchase-receipt"
             data-filters='{"custom_biz_mode":"月结补录","status":["in",["Partly Billed","To Bill"]]}' >
            <span class="stat-icon">⏳</span>
            <span class="stat-text" id="text-mth-pr">正在统计…</span>
          </a>
        </div>
      </div>
    </div>

  </div>
</div>
'''

JS_CONTENT = r'''/*
修改日志：
- 2026-01-05
  1) 场景2-采购发票待办：统计“现金报销模式下已提交的 Purchase Invoice 中，未被任何 Reimbursement Request.invoice_items(source_pi) 引用”的数量；
     文案：0=当前无待办，>0=<b>X</b> 个未写报销申请；点击进入 Purchase Invoice 列表并筛选这些发票（name IN [...]）。
  2) 场景2-报销申请待办：统计“已提交(docstatus=1) 且 outstanding_amount > 0”的 Reimbursement Request；点击进入报销申请列表并筛选未付完款。
  3) 修复 Workspace 报错：不再对 frappe.desk.reportview.get_list 传顶层 parent 参数（否则触发 TypeError）；
     子表查询统一改为 frappe.client.get_list（该接口支持 parent 用于权限检查）。
  4) 当差集为空时，不再设置 name IN []（避免点击进入空列表）；改为回落到基础筛选（现金报销 + 已提交）。
  5) 兼容 Frappe 16 /desk 与 /app 双路由前缀。
影响范围：仅 Custom HTML Block 前端脚本；不改任何单据数据与权限。
*/

(function () {
  const ROOT = (typeof root_element !== "undefined" && root_element) ? root_element : document;

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
      // 同时兼容 /app/ 与 /desk/
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
    const links = ROOT.querySelectorAll('.stat-row[data-doctype][data-filters]');
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

  function fetchCount(doctype, filters, textSel, linkSel, labelSuffix) {
    const elText = ROOT.querySelector(textSel);
    const elLink = ROOT.querySelector(linkSel);
    if (!elText || !elLink) return;

    elLink.classList.add('is-loading');
    elLink.classList.remove('has-pending', 'is-empty', 'is-error');

    frappe.db.count(doctype, { filters: filters })
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
      { sourceId: 'stat-req', draftId: 'draft-req', textId: 'text-draft-req' },
      { sourceId: 'stat-po', draftId: 'draft-po', textId: 'text-draft-po' },
      { sourceId: 'stat-pr-reg', draftId: 'draft-pr-reg', textId: 'text-draft-pr-reg' },
      { sourceId: 'stat-pi-reg', draftId: 'draft-pi-reg', textId: 'text-draft-pi-reg' },
      { sourceId: 'stat-reim-pr', draftId: 'draft-reim-pr', textId: 'text-draft-reim-pr' },
      { sourceId: 'stat-reim-pi', draftId: 'draft-reim-pi', textId: 'text-draft-reim-pi' },
      { sourceId: 'stat-reim-req', draftId: 'draft-reim-req', textId: 'text-draft-reim-req' },
      { sourceId: 'stat-wire-pr', draftId: 'draft-wire-pr', textId: 'text-draft-wire-pr' },
      { sourceId: 'stat-wire-pi', draftId: 'draft-wire-pi', textId: 'text-draft-wire-pi' },
      { sourceId: 'stat-mth-pr', draftId: 'draft-mth-pr', textId: 'text-draft-mth-pr' }
    ];
    configs.forEach(cfg => ensureDraftRow(cfg.sourceId, cfg.draftId, cfg.textId));
  }

  function fetchDraftCount(doctype, route, filters, textSel, linkSel) {
    const elText = ROOT.querySelector(textSel);
    const elLink = ROOT.querySelector(linkSel);
    if (!elText || !elLink) return;

    const icon = elLink.querySelector('.stat-icon');
    const draftFilters = Object.assign({ docstatus: 0 }, (filters || {}));

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

  // ============================================================
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
    场景2-采购发票：统计“未写报销申请”的 Purchase Invoice
    - PI 集合：Purchase Invoice (docstatus=1, custom_biz_mode=现金报销)
    - 已写报销集合：Reimbursement Invoice Item.source_pi
      这些子表行必须属于 Reimbursement Request(docstatus=1, custom_biz_mode=现金报销)
    - 差集集合：PI - 已写报销
  */
  async function fetchCashPiWithoutReim() {
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
      const piRows = await clientGetList('Purchase Invoice', {
        fields: ['name'],
        filters: { docstatus: 1, custom_biz_mode: '现金报销' },
        limit_page_length: 5000
      });
      const piNames = (piRows || []).map(r => r.name).filter(Boolean);

      let missing = [...piNames];

      if (piNames.length > 0) {
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
        const filtersObj = {
          custom_biz_mode: '现金报销',
          docstatus: 1,
          name: ['in', missing]
        };
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

  // ===== 初始化 =====
  materializeStatHrefs();
  setupDraftRows();
  bindStatRouteButtons();
  bindCmdRouteButtons();

  // ===== 执行统计：场景1 =====
  fetchCount(
    'Material Request',
    { docstatus: 1, status: ['in', ['Submitted', 'Pending', 'Partially Ordered']] },
    '#text-req', '#stat-req', '待下单'
  );

  fetchCount(
    'Purchase Order',
    { docstatus: 1, status: ['in', ['On Hold', 'To Receive', 'To Receive and Bill']] },
    '#text-po', '#stat-po', '待收货'
  );

  fetchCount(
    'Purchase Receipt',
    { custom_biz_mode: '常规采购', status: ['in', ['Partly Billed', 'To Bill']] },
    '#text-pr-reg', '#stat-pr-reg', '待开票'
  );

  fetchCount(
    'Purchase Invoice',
    { custom_biz_mode: '常规采购', status: ['in', ['Unpaid', 'Partly Paid', 'Overdue', 'Submitted']] },
    '#text-pi-reg', '#stat-pi-reg', '待付款'
  );

  // ===== 执行统计：场景2 =====
  fetchCount(
    'Purchase Receipt',
    { custom_biz_mode: '现金报销', status: ['in', ['Partly Billed', 'To Bill']] },
    '#text-reim-pr', '#stat-reim-pr', '待开票'
  );

  // ✅ 场景2：采购发票“未写报销申请”（动态差集）
  fetchCashPiWithoutReim();

  // ✅ 场景2：报销申请“未付完款”
  fetchCount(
    'Reimbursement Request',
    { custom_biz_mode: '现金报销', docstatus: 1, outstanding_amount: ['>', 0] },
    '#text-reim-req', '#stat-reim-req', '未付完款'
  );

  // ===== 场景3 =====
  fetchCount(
    'Purchase Receipt',
    { custom_biz_mode: '自办电汇', status: ['in', ['Partly Billed', 'To Bill']] },
    '#text-wire-pr', '#stat-wire-pr', '待开票'
  );

  fetchCount(
    'Purchase Invoice',
    { custom_biz_mode: '自办电汇', status: ['in', ['Submitted', 'Unpaid', 'Partly Paid', 'Overdue']] },
    '#text-wire-pi', '#stat-wire-pi', '待付款'
  );

  // ===== 场景4 =====
  fetchCount(
    'Purchase Receipt',
    { custom_biz_mode: '月结补录', status: ['in', ['Partly Billed', 'To Bill']] },
    '#text-mth-pr', '#stat-mth-pr', '待开票'
  );

  // ===== 草稿统计 =====
  fetchDraftCount(
    'Material Request', 'material-request', {},
    '#text-draft-req', '#draft-req'
  );

  fetchDraftCount(
    'Purchase Order', 'purchase-order', {},
    '#text-draft-po', '#draft-po'
  );

  fetchDraftCount(
    'Purchase Receipt', 'purchase-receipt', { custom_biz_mode: '常规采购' },
    '#text-draft-pr-reg', '#draft-pr-reg'
  );

  fetchDraftCount(
    'Purchase Invoice', 'purchase-invoice', { custom_biz_mode: '常规采购' },
    '#text-draft-pi-reg', '#draft-pi-reg'
  );

  fetchDraftCount(
    'Purchase Receipt', 'purchase-receipt', { custom_biz_mode: '现金报销' },
    '#text-draft-reim-pr', '#draft-reim-pr'
  );

  fetchDraftCount(
    'Purchase Invoice', 'purchase-invoice', { custom_biz_mode: '现金报销' },
    '#text-draft-reim-pi', '#draft-reim-pi'
  );

  fetchDraftCount(
    'Reimbursement Request', 'reimbursement-request', { custom_biz_mode: '现金报销' },
    '#text-draft-reim-req', '#draft-reim-req'
  );

  fetchDraftCount(
    'Purchase Receipt', 'purchase-receipt', { custom_biz_mode: '自办电汇' },
    '#text-draft-wire-pr', '#draft-wire-pr'
  );

  fetchDraftCount(
    'Purchase Invoice', 'purchase-invoice', { custom_biz_mode: '自办电汇' },
    '#text-draft-wire-pi', '#draft-wire-pi'
  );

  fetchDraftCount(
    'Purchase Receipt', 'purchase-receipt', { custom_biz_mode: '月结补录' },
    '#text-draft-mth-pr', '#draft-mth-pr'
  );

})();
'''

CSS_CONTENT = r'''/* 修改日志：
- 2026-01-01
  1) 无待办（.is-empty）保持按钮 outline 形态，统一交互与布局。
影响范围：仅 Custom HTML Block 样式；不影响系统全局主题。
*/

/* ================= 全局容器 ================= */
.biz-nav-container {
  font-family: "Inter", sans-serif;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  box-sizing: border-box;
  width: 100%;
}

.biz-section-header { margin-bottom: 8px; display: flex; align-items: baseline; }
.biz-title { font-size: 15px; font-weight: 700; margin-right: 8px; }
.biz-subtitle {
  font-size: 11px; color: #94a3b8; background: #f1f5f9;
  padding: 2px 6px; border-radius: 4px;
}

.biz-scene-note{
  margin: 6px 0 12px;
  font-size: 12px;
  color: #64748b;
  background: #f8fafc;
  border: 1px dashed #e2e8f0;
  border-radius: 6px;
  padding: 6px 10px;
}

.biz-divider {
  height: 1px; background: #e2e8f0; margin: 20px 0; border-bottom: 1px dashed #cbd5e0;
}

.biz-flow-wrapper { display: flex; align-items: stretch; gap: 10px; margin-bottom: 15px; }
.flow-arrow { display: flex; align-items: center; color: #cbd5e0; font-size: 16px; }

/* ================= 卡片容器 ================= */
.step-card {
  flex: 1;
  min-width: 120px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 12px 0;

  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  gap: 8px;
  box-sizing: border-box !important;
}

.step-header {
  font-size: 12px;
  font-weight: 700;
  color: #475569;
  margin-bottom: 2px;
  text-align: center;
}

/* ================= 新建/查看按钮 my-cmd-btn ================= */
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

  transition: background-color .12s ease, color .12s ease, border-color .12s ease,
              transform .08s ease, box-shadow .12s ease, filter .12s ease;
}

.my-cmd-btn:hover { transform: translateY(-1px); box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08); }
.my-cmd-btn:active { transform: translateY(0); box-shadow: 0 6px 14px rgba(15, 23, 42, 0.06); }
.my-cmd-btn:focus-visible { outline: 3px solid var(--cmd-ring, rgba(36, 144, 239, 0.25)); outline-offset: 2px; }

.my-cmd-btn .icon {
  position: absolute !important;
  left: 12px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;

  width: 16px;
  height: 16px;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;

  margin: 0 !important;
  font-weight: 800;
  line-height: 1;
  pointer-events: none;
}

/* ================= 待办按钮 stat-row ================= */
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

  transition: background-color .12s ease, color .12s ease, border-color .12s ease,
              transform .08s ease, box-shadow .12s ease, filter .12s ease;
}

.stat-row:hover { transform: translateY(-1px); box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08); }
.stat-row:active { transform: translateY(0); box-shadow: 0 6px 14px rgba(15, 23, 42, 0.06); }
.stat-row:focus-visible { outline: 3px solid var(--cmd-ring, rgba(36, 144, 239, 0.18)); outline-offset: 2px; }

.stat-row .stat-icon {
  position: absolute !important;
  left: 12px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;

  width: 16px;
  height: 16px;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;

  margin: 0 !important;
  line-height: 1;
  pointer-events: none;
}

/* 状态细化 */
.stat-row.is-loading { opacity: 0.95; }
.stat-row.has-pending { opacity: 1; }

/* 无待办：保持按钮 outline 形态 */
.stat-row.is-empty {
  background: #fff !important;
  border: 1px solid #e2e8f0 !important;
  color: #94a3b8 !important;
}
.stat-row.is-empty:hover {
  background: #f8fafc !important;
  border-color: #cbd5e0 !important;
  color: #64748b !important;
}

.stat-row.is-error {
  background: #fff !important;
  border: 1px solid #fecaca !important;
  color: #b91c1c !important;
}

/* ================= 颜色主题 ================= */
/* 蓝色系 */
.step-blue { border-top: 3px solid #2490ef; }
.btn-blue { --cmd-ring: rgba(36, 144, 239, 0.28); background: #eff6ff !important; color: #1d4ed8 !important; border: 1px solid #dbeafe !important; }
.btn-blue:hover { background: #dbeafe !important; }
.btn-blue-outline { --cmd-ring: rgba(36, 144, 239, 0.22); background: #fff !important; color: #64748b !important; border: 1px solid #e2e8f0 !important; }
.btn-blue-outline:hover { background: #f8fafc !important; color: #2490ef !important; border-color: #cbd5e0 !important; }
.stat-blue { --cmd-ring: rgba(36, 144, 239, 0.18); background: #eff6ff !important; color: #2490ef !important; border: 1px solid #dbeafe !important; }

/* 橙色系 */
.step-orange { border-top: 3px solid #e67e22; }
.btn-orange { --cmd-ring: rgba(230, 126, 34, 0.28); background: #fff3e0 !important; color: #e65100 !important; border: 1px solid #ffe0b2 !important; }
.btn-orange:hover { background: #ffe0b2 !important; }
.btn-orange-outline { --cmd-ring: rgba(230, 126, 34, 0.22); background: #fff !important; color: #64748b !important; border: 1px solid #e2e8f0 !important; }
.btn-orange-outline:hover { background: #fff8e1 !important; color: #e67e22 !important; border-color: #ffe0b2 !important; }
.stat-orange { --cmd-ring: rgba(230, 126, 34, 0.18); background: #fff3e0 !important; color: #e67e22 !important; border: 1px solid #ffe0b2 !important; }

/* 紫色系 */
.step-purple { border-top: 3px solid #8e44ad; }
.btn-purple { --cmd-ring: rgba(142, 68, 173, 0.28); background: #f3e5f5 !important; color: #6a1b9a !important; border: 1px solid #e1bee7 !important; }
.btn-purple:hover { background: #e1bee7 !important; }
.btn-purple-outline { --cmd-ring: rgba(142, 68, 173, 0.22); background: #fff !important; color: #64748b !important; border: 1px solid #e2e8f0 !important; }
.btn-purple-outline:hover { background: #f3e5f5 !important; color: #8e44ad !important; border-color: #e1bee7 !important; }
.stat-purple { --cmd-ring: rgba(142, 68, 173, 0.18); background: #f3e5f5 !important; color: #8e44ad !important; border: 1px solid #e1bee7 !important; }

/* 青色系 */
.step-teal { border-top: 3px solid #00b894; }
.btn-teal { --cmd-ring: rgba(0, 184, 148, 0.28); background: #e0f2f1 !important; color: #00695c !important; border: 1px solid #b2dfdb !important; }
.btn-teal:hover { background: #b2dfdb !important; }
.btn-teal-outline { --cmd-ring: rgba(0, 184, 148, 0.22); background: #fff !important; color: #64748b !important; border: 1px solid #e2e8f0 !important; }
.btn-teal-outline:hover { background: #e0f2f1 !important; color: #00b894 !important; border-color: #b2dfdb !important; }
.stat-teal { --cmd-ring: rgba(0, 184, 148, 0.18); background: #e0f2f1 !important; color: #00b894 !important; border: 1px solid #b2dfdb !important; }
'''

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
    print("Created Custom HTML Block:", BLOCK_NAME)
else:
    doc = frappe.get_doc("Custom HTML Block", BLOCK_NAME)
    doc.html = html_c
    doc.script = js_c
    doc.style = css_c
    doc.private = 0
    doc.save(ignore_permissions=True)
    print("Updated Custom HTML Block:", BLOCK_NAME)

# 挂载到 Home 工作区顶部（在快捷入口之前或之后）
home_ws = frappe.get_doc("Workspace", "Home")
content_list = json.loads(home_ws.content or "[]")

# 检查是否已包含 custom_html_block
has_block = any(item.get("type") == "custom_html_block" and item.get("data", {{}}).get("custom_html_block_name") == BLOCK_NAME for item in content_list)

if not has_block:
    # 插入到第 2 项（主标题下方）
    block_item = {{
        "id": "chb_biz_scenes_nav",
        "type": "custom_html_block",
        "data": {{
            "custom_html_block_name": BLOCK_NAME,
            "col": 12
        }}
    }}
    content_list.insert(1, block_item)
    home_ws.content = json.dumps(content_list, ensure_ascii=False)
    home_ws.save(ignore_permissions=True)
    print("Mounted Custom HTML Block to Home Workspace!")
else:
    print("Custom HTML Block already present in Home Workspace.")

frappe.db.commit()
frappe.clear_cache()
print("[OK] 业务场景导航 Block 配置并挂载完成！")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/deploy_chb.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/deploy_chb.py erpnext16:/tmp/deploy_chb.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/deploy_chb.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
