import json

with open('ashan_cn_procurement/ashan_cn_procurement/fixtures/custom_html_block.json', 'r', encoding='utf-8') as f:
    block = json.load(f)

# HTML 结构
html_content = """<div class=\"biz-nav-container\">

  <!-- ============================================================ -->
  <!-- 🌟 顶层看板：我的待办任务 (My Pending Tasks)                -->
  <!-- ============================================================ -->
  <div class=\"my-tasks-section\" id=\"my-tasks-container\">
    <div class=\"tasks-section-header\">
      <div class=\"tasks-title-wrapper\">
        <span class=\"tasks-main-title\">📋 我的待办任务 (今日工作焦点)</span>
        <span class=\"tasks-badge\">开票/报销按归属人隔离 · 入库共享池</span>
      </div>
      <button type=\"button\" class=\"tasks-refresh-btn\" id=\"btn-refresh-tasks\" title=\"刷新待办数据\">
        <span class=\"refresh-icon\">🔄</span> 刷新
      </button>
    </div>

    <!-- 待办任务卡片弹性网格 -->
    <div class=\"tasks-grid\" id=\"tasks-grid-wrapper\">

      <!-- 任务 1：待采购下单 (采购池) -->
      <div class=\"task-card task-card-amber\" id=\"task-card-po\" data-task-perm=\"Purchase Order\" data-doctype=\"Material Request\">
        <div class=\"task-card-top\">
          <div class=\"task-card-icon\">🟡</div>
          <div class=\"task-card-info\">
            <div class=\"task-card-name\">待采购下单</div>
            <div class=\"task-card-desc\">已批需求等待下达订单</div>
          </div>
        </div>
        <div class=\"task-card-bottom\">
          <div class=\"task-count-pill is-loading\" id=\"pill-po\">
            <span class=\"pill-dot\"></span>
            <span class=\"pill-text\" id=\"pill-text-po\">统计中…</span>
          </div>
          <a href=\"/desk/material-request\" class=\"task-action-btn\" id=\"act-po\" data-doctype=\"Material Request\" data-filters='{\"docstatus\":1,\"status\":[\"in\",[\"Submitted\",\"Pending\",\"Partially Ordered\"]}'>
            去下单 ➔
          </a>
        </div>
      </div>

      <!-- 任务 2：待物资入库 (公共仓库入库池：谁有权限谁都可以入库) -->
      <div class=\"task-card task-card-green\" id=\"task-card-pr\" data-task-perm=\"Purchase Receipt\" data-doctype=\"Purchase Order\">
        <div class=\"task-card-top\">
          <div class=\"task-card-icon\">🟢</div>
          <div class=\"task-card-info\">
            <div class=\"task-card-name\">待物资入库</div>
            <div class=\"task-card-desc\">全员订单·公共收货物资池</div>
          </div>
        </div>
        <div class=\"task-card-bottom\">
          <div class=\"task-count-pill is-loading\" id=\"pill-pr\">
            <span class=\"pill-dot\"></span>
            <span class=\"pill-text\" id=\"pill-text-pr\">统计中…</span>
          </div>
          <a href=\"/desk/purchase-order\" class=\"task-action-btn\" id=\"act-pr\" data-doctype=\"Purchase Order\" data-filters='{\"docstatus\":1,\"status\":[\"in\",[\"On Hold\",\"To Receive\",\"To Receive and Bill\"]}'>
            去收货 ➔
          </a>
        </div>
      </div>

      <!-- 任务 3：待采购开票 (A生成订单 -> 仅A计算开票) -->
      <div class=\"task-card task-card-blue\" id=\"task-card-pi\" data-task-perm=\"Purchase Invoice\" data-doctype=\"Purchase Receipt\">
        <div class=\"task-card-top\">
          <div class=\"task-card-icon\">🔵</div>
          <div class=\"task-card-info\">
            <div class=\"task-card-name\">待采购开票</div>
            <div class=\"task-card-desc\">我经手的入库等待录入发票</div>
          </div>
        </div>
        <div class=\"task-card-bottom\">
          <div class=\"task-count-pill is-loading\" id=\"pill-pi\">
            <span class=\"pill-dot\"></span>
            <span class=\"pill-text\" id=\"pill-text-pi\">统计中…</span>
          </div>
          <a href=\"/desk/purchase-receipt\" class=\"task-action-btn\" id=\"act-pi\" data-doctype=\"Purchase Receipt\">
            去开票 ➔
          </a>
        </div>
      </div>

      <!-- 任务 4：待发起报销 (A垫付发票 -> 仅A发起报销) -->
      <div class=\"task-card task-card-orange\" id=\"task-card-reim\" data-task-perm=\"Reimbursement Request\" data-doctype=\"Purchase Invoice\">
        <div class=\"task-card-top\">
          <div class=\"task-card-icon\">🟠</div>
          <div class=\"task-card-info\">
            <div class=\"task-card-name\">待发起报销</div>
            <div class=\"task-card-desc\">我垫付的发票尚未填报销单</div>
          </div>
        </div>
        <div class=\"task-card-bottom\">
          <div class=\"task-count-pill is-loading\" id=\"pill-reim\">
            <span class=\"pill-dot\"></span>
            <span class=\"pill-text\" id=\"pill-text-reim\">统计中…</span>
          </div>
          <a href=\"/desk/purchase-invoice\" class=\"task-action-btn\" id=\"act-reim\" data-doctype=\"Purchase Invoice\">
            去报销 ➔
          </a>
        </div>
      </div>

      <!-- 任务 5：待报销结款 (财务付款池) -->
      <div class=\"task-card task-card-purple\" id=\"task-card-settle\" data-task-perm=\"Payment Entry\" data-doctype=\"Reimbursement Request\">
        <div class=\"task-card-top\">
          <div class=\"task-card-icon\">🟣</div>
          <div class=\"task-card-info\">
            <div class=\"task-card-name\">待报销结款</div>
            <div class=\"task-card-desc\">已审报销等待付清款项</div>
          </div>
        </div>
        <div class=\"task-card-bottom\">
          <div class=\"task-count-pill is-loading\" id=\"pill-settle\">
            <span class=\"pill-dot\"></span>
            <span class=\"pill-text\" id=\"pill-text-settle\">统计中…</span>
          </div>
          <a href=\"/desk/reimbursement-request\" class=\"task-action-btn\" id=\"act-settle\" data-doctype=\"Reimbursement Request\" data-filters='{\"docstatus\":1,\"outstanding_amount\":[\">\",0]}'>
            去付款 ➔
          </a>
        </div>
      </div>

    </div>
  </div>

  <!-- ============================================================ -->
  <!-- 📅 月度看板：我的月度任务 (按公司权限精准隔离)               -->
  <!-- ============================================================ -->
  <div class=\"periodic-tasks-section\" id=\"periodic-tasks-container\">
    <div class=\"tasks-section-header\">
      <div class=\"tasks-title-wrapper\">
        <span class=\"tasks-main-title\">📅 我的月度任务</span>
        <span class=\"tasks-badge\" id=\"periodic-period-badge\">正在核验…</span>
      </div>
      <div class=\"periodic-controls\">
        <select id=\"select-periodic-period\" class=\"periodic-period-select\" title=\"选择核定月份\">
        </select>
        <button type=\"button\" class=\"tasks-refresh-btn\" id=\"btn-refresh-periodic\" title=\"刷新月度任务状态\">
          <span class=\"refresh-icon\">🔄</span> 刷新
        </button>
      </div>
    </div>

    <div class=\"periodic-companies-grid\" id=\"periodic-companies-grid\">
      <!-- 吉众公司卡片 -->
      <div class=\"company-periodic-card\" id=\"company-card-jizhong\">
        <div class=\"company-card-header\">
          <div class=\"company-card-title\">
            <span class=\"company-icon\">🏢</span>
            <span class=\"company-name\">吉众 · 月度报表核定</span>
            <span class=\"company-status-badge\" id=\"jizhong-status-badge\">核定中…</span>
          </div>
          <span class=\"company-subtag\">天津吉众机电设备有限公司</span>
        </div>
        <div class=\"company-items-list\" id=\"jizhong-items-list\">
          <div class=\"periodic-loading\">正在核验月度任务…</div>
        </div>
      </div>

      <!-- 祺富公司卡片 -->
      <div class=\"company-periodic-card\" id=\"company-card-qifu\">
        <div class=\"company-card-header\">
          <div class=\"company-card-title\">
            <span class=\"company-icon\">🏭</span>
            <span class=\"company-name\">祺富 · 月度报表核定</span>
            <span class=\"company-status-badge\" id=\"qifu-status-badge\">核定中…</span>
          </div>
          <span class=\"company-subtag\">天津祺富机械加工有限公司</span>
        </div>
        <div class=\"company-items-list\" id=\"qifu-items-list\">
          <div class=\"periodic-loading\">正在核验月度任务…</div>
        </div>
      </div>
    </div>
  </div>

  <div class=\"biz-divider\" style=\"margin: 20px 0 16px;\"></div>

  <!-- ============================================================ -->
  <!-- 📦 4 大全流程业务场景卡片导航                                -->
  <!-- ============================================================ -->

  <!-- ========== 场景 1：购买申请（常规采购） ========== -->
  <div class=\"biz-scene-block\" id=\"scene-1-container\">
    <div class=\"biz-section-header\">
      <span class=\"biz-title\" style=\"color:#2490ef;\">📦 场景1：购买申请（常规采购）</span>
      <span class=\"biz-subtitle\">订单驱动 | 标准化</span>
    </div>
    <div class=\"biz-scene-note\">说明：常规采购，以购买申请为起点，打印单据为采购申请单据。</div>

    <div class=\"biz-flow-wrapper\">
      <div class=\"step-card step-blue\" data-doctype=\"Material Request\">
        <div class=\"step-header\">1. 采购申请</div>
        <a href=\"/desk/material-request/new\" class=\"my-cmd-btn btn-blue btn-create\" data-doctype=\"Material Request\">
          <span class=\"icon\">+</span> 新建申请
        </a>
        <a href=\"/desk/material-request\" class=\"my-cmd-btn btn-blue-outline btn-view-all\" data-doctype=\"Material Request\">
          <span class=\"icon\">≡</span> 查看全部
        </a>
        <a href=\"/desk/material-request\"
           class=\"stat-row stat-blue is-loading\"
           id=\"stat-req\"
           data-doctype=\"Material Request\"
           data-route=\"material-request\"
           data-filters='{\"docstatus\":1,\"status\":[\"in\",[\"Submitted\",\"Pending\",\"Partially Ordered\"]}'>
          <span class=\"stat-icon\">⏳</span>
          <span class=\"stat-text\" id=\"text-req\">正在统计…</span>
        </a>
      </div>

      <div class=\"flow-arrow\">➔</div>

      <div class=\"step-card step-blue\" data-doctype=\"Purchase Order\">
        <div class=\"step-header\">2. 采购订单</div>
        <a href=\"/desk/purchase-order/new\" class=\"my-cmd-btn btn-blue btn-create\" data-doctype=\"Purchase Order\">
          <span class=\"icon\">+</span> 新建订单
        </a>
        <a href=\"/desk/purchase-order\" class=\"my-cmd-btn btn-blue-outline btn-view-all\" data-doctype=\"Purchase Order\">
          <span class=\"icon\">≡</span> 查看全部
        </a>
        <a href=\"/desk/purchase-order\"
           class=\"stat-row stat-blue is-loading\"
           id=\"stat-po\"
           data-doctype=\"Purchase Order\"
           data-route=\"purchase-order\"
           data-filters='{\"docstatus\":1,\"status\":[\"in\",[\"On Hold\",\"To Receive\",\"To Receive and Bill\"]}'>
          <span class=\"stat-icon\">⏳</span>
          <span class=\"stat-text\" id=\"text-po\">正在统计…</span>
        </a>
      </div>

      <div class=\"flow-arrow\">➔</div>

      <div class=\"step-card step-blue\" data-doctype=\"Purchase Receipt\">
        <div class=\"step-header\">3. 物资入库</div>
        <a href=\"/desk/purchase-receipt/new?custom_biz_mode=常规采购\" class=\"my-cmd-btn btn-blue btn-create\" data-doctype=\"Purchase Receipt\">
          <span class=\"icon\">+</span> 新建入库
        </a>
        <a href=\"/desk/purchase-receipt?custom_biz_mode=常规采购\" class=\"my-cmd-btn btn-blue-outline btn-view-all\" data-doctype=\"Purchase Receipt\">
          <span class=\"icon\">≡</span> 查看全部
        </a>
        <a href=\"/desk/purchase-receipt\"
           class=\"stat-row stat-blue is-loading\"
           id=\"stat-pr-reg\"
           data-doctype=\"Purchase Receipt\"
           data-route=\"purchase-receipt\">
          <span class=\"stat-icon\">⏳</span>
          <span class=\"stat-text\" id=\"text-pr-reg\">正在统计…</span>
        </a>
      </div>

      <div class=\"flow-arrow\">➔</div>

      <div class=\"step-card step-blue\" data-doctype=\"Purchase Invoice\">
        <div class=\"step-header\">4. 采购发票</div>
        <a href=\"/desk/purchase-invoice/new?custom_biz_mode=常规采购\" class=\"my-cmd-btn btn-blue btn-create\" data-doctype=\"Purchase Invoice\">
          <span class=\"icon\">+</span> 新建发票
        </a>
        <a href=\"/desk/purchase-invoice?custom_biz_mode=常规采购\" class=\"my-cmd-btn btn-blue-outline btn-view-all\" data-doctype=\"Purchase Invoice\">
          <span class=\"icon\">≡</span> 查看全部
        </a>
        <a href=\"/desk/purchase-invoice\"
           class=\"stat-row stat-blue is-loading\"
           id=\"stat-pi-reg\"
           data-doctype=\"Purchase Invoice\"
           data-route=\"purchase-invoice\">
          <span class=\"stat-icon\">⏳</span>
          <span class=\"stat-text\" id=\"text-pi-reg\">正在统计…</span>
        </a>
      </div>
    </div>
    <div class=\"biz-divider\"></div>
  </div>

  <!-- ========== 场景 2：现金报销（垫付） ========== -->
  <div class=\"biz-scene-block\" id=\"scene-2-container\">
    <div class=\"biz-section-header\">
      <span class=\"biz-title\" style=\"color:#e67e22;\">🚀 场景2：现金报销（垫付）</span>
      <span class=\"biz-subtitle\">个人垫付 | 快速回款</span>
    </div>
    <div class=\"biz-scene-note\">说明：报销单，打印单据为报销申请单据的整算单</div>

    <div class=\"biz-flow-wrapper\">
      <div class=\"step-card step-orange\" data-doctype=\"Purchase Receipt\">
        <div class=\"step-header\">1. 采购入库</div>
        <a href=\"/desk/purchase-receipt/new?custom_biz_mode=现金报销&supplier=其它供应商\" class=\"my-cmd-btn btn-orange btn-create\" data-doctype=\"Purchase Receipt\">
          <span class=\"icon\">+</span> 新建入库
        </a>
        <a href=\"/desk/purchase-receipt?custom_biz_mode=现金报销\" class=\"my-cmd-btn btn-orange-outline btn-view-all\" data-doctype=\"Purchase Receipt\">
          <span class=\"icon\">≡</span> 查看全部
        </a>
        <a href=\"/desk/purchase-receipt\"
           class=\"stat-row stat-orange is-loading\"
           id=\"stat-reim-pr\"
           data-doctype=\"Purchase Receipt\"
           data-route=\"purchase-receipt\">
          <span class=\"stat-icon\">⏳</span>
          <span class=\"stat-text\" id=\"text-reim-pr\">正在统计…</span>
        </a>
      </div>

      <div class=\"flow-arrow\">➔</div>

      <div class=\"step-card step-orange\" data-doctype=\"Purchase Invoice\">
        <div class=\"step-header\">2. 采购发票</div>
        <a href=\"/desk/purchase-invoice/new?custom_biz_mode=现金报销\" class=\"my-cmd-btn btn-orange btn-create\" data-doctype=\"Purchase Invoice\">
          <span class=\"icon\">+</span> 新建发票
        </a>
        <a href=\"/desk/purchase-invoice?custom_biz_mode=现金报销\" class=\"my-cmd-btn btn-orange-outline btn-view-all\" data-doctype=\"Purchase Invoice\">
          <span class=\"icon\">≡</span> 查看全部
        </a>
        <a href=\"/desk/purchase-invoice\"
           class=\"stat-row stat-orange is-loading\"
           id=\"stat-reim-pi\"
           data-doctype=\"Purchase Invoice\"
           data-route=\"purchase-invoice\">
          <span class=\"stat-icon\">⏳</span>
          <span class=\"stat-text\" id=\"text-reim-pi\">正在统计…</span>
        </a>
      </div>

      <div class=\"flow-arrow\">➔</div>

      <div class=\"step-card step-orange\" data-doctype=\"Reimbursement Request\">
        <div class=\"step-header\">3. 报销申请</div>
        <a href=\"/desk/reimbursement-request/new?custom_biz_mode=现金报销\" class=\"my-cmd-btn btn-orange btn-create\" data-doctype=\"Reimbursement Request\">
          <span class=\"icon\">+</span> 新建报销
        </a>
        <a href=\"/desk/reimbursement-request?custom_biz_mode=现金报销&docstatus=1\" class=\"my-cmd-btn btn-orange-outline btn-view-all\" data-doctype=\"Reimbursement Request\">
          <span class=\"icon\">≡</span> 查看全部
        </a>
        <a href=\"/desk/reimbursement-request\"
           class=\"stat-row stat-orange is-loading\"
           id=\"stat-reim-req\"
           data-doctype=\"Reimbursement Request\"
           data-route=\"reimbursement-request\">
          <span class=\"stat-icon\">⏳</span>
          <span class=\"stat-text\" id=\"text-reim-req\">正在统计…</span>
        </a>
      </div>
    </div>
    <div class=\"biz-divider\"></div>
  </div>

  <!-- ========== 场景 3 & 4（并排） ========== -->
  <div class=\"biz-dual-scenes-row\" style=\"display:flex; gap:20px;\">

    <!-- 场景 3 -->
    <div class=\"biz-scene-block\" id=\"scene-3-container\" style=\"flex:2;\">
      <div class=\"biz-section-header\" style=\"margin-bottom:8px;\">
        <span class=\"biz-title\" style=\"color:#8e44ad; font-size:14px;\">⚡ 场景3：自办电汇（秒结）</span>
      </div>
      <div class=\"biz-scene-note\">说明：为自行电汇采购的流程，需要打印入库的补写的入库单。由于是电汇，必定有发票。</div>

      <div class=\"biz-flow-wrapper\">
        <div class=\"step-card step-purple\" data-doctype=\"Purchase Receipt\">
          <div class=\"step-header\">1. 采购入库</div>
          <a href=\"/desk/purchase-receipt/new?custom_biz_mode=自办电汇\" class=\"my-cmd-btn btn-purple btn-create\" data-doctype=\"Purchase Receipt\">
            <span class=\"icon\">+</span> 新建入库
          </a>
          <a href=\"/desk/purchase-receipt?custom_biz_mode=自办电汇\" class=\"my-cmd-btn btn-purple-outline btn-view-all\" data-doctype=\"Purchase Receipt\">
            <span class=\"icon\">≡</span> 查看全部
          </a>
          <a href=\"/desk/purchase-receipt\"
             class=\"stat-row stat-purple is-loading\"
             id=\"stat-wire-pr\"
             data-doctype=\"Purchase Receipt\"
             data-route=\"purchase-receipt\">
            <span class=\"stat-icon\">⏳</span>
            <span class=\"stat-text\" id=\"text-wire-pr\">正在统计…</span>
          </a>
        </div>

        <div class=\"flow-arrow\">➔</div>

        <div class=\"step-card step-purple\" data-doctype=\"Purchase Invoice\">
          <div class=\"step-header\">2. 发票&支付</div>
          <a href=\"/desk/purchase-invoice/new?custom_biz_mode=自办电汇\" class=\"my-cmd-btn btn-purple btn-create\" data-doctype=\"Purchase Invoice\">
            <span class=\"icon\">+</span> 新建发票
          </a>
          <a href=\"/desk/purchase-invoice?custom_biz_mode=自办电汇\" class=\"my-cmd-btn btn-purple-outline btn-view-all\" data-doctype=\"Purchase Invoice\">
            <span class=\"icon\">≡</span> 查看全部
          </a>
          <a href=\"/desk/purchase-invoice\"
             class=\"stat-row stat-purple is-loading\"
             id=\"stat-wire-pi\"
             data-doctype=\"Purchase Invoice\"
             data-route=\"purchase-invoice\">
            <span class=\"stat-icon\">⏳</span>
            <span class=\"stat-text\" id=\"text-wire-pi\">正在统计…</span>
          </a>
        </div>
      </div>
    </div>

    <!-- 场景 4 -->
    <div class=\"biz-scene-block\" id=\"scene-4-container\" style=\"flex:1; border-left:1px dashed #e2e8f0; padding-left:20px;\">
      <div class=\"biz-section-header\" style=\"margin-bottom:8px;\">
        <span class=\"biz-title\" style=\"color:#00b894; font-size:14px;\">📅 场景4：月结补录</span>
      </div>
      <div class=\"biz-scene-note\">说明：仅用于月结供应商，如聚鑫、金普金等。打印采购入库的补录单，一般无需填写发票。</div>

      <div class=\"biz-flow-wrapper\">
        <div class=\"step-card step-teal\" data-doctype=\"Purchase Receipt\">
          <div class=\"step-header\">1. 采购入库</div>
          <a href=\"/desk/purchase-receipt/new?custom_biz_mode=月结补录\" class=\"my-cmd-btn btn-teal btn-create\" data-doctype=\"Purchase Receipt\">
            <span class=\"icon\">+</span> 新建入库
          </a>
          <a href=\"/desk/purchase-receipt?custom_biz_mode=月结补录\" class=\"my-cmd-btn btn-teal-outline btn-view-all\" data-doctype=\"Purchase Receipt\">
            <span class=\"icon\">≡</span> 查看全部
          </a>
          <a href=\"/desk/purchase-receipt\"
             class=\"stat-row stat-teal is-loading\"
             id=\"stat-mth-pr\"
             data-doctype=\"Purchase Receipt\"
             data-route=\"purchase-receipt\">
            <span class=\"stat-icon\">⏳</span>
            <span class=\"stat-text\" id=\"text-mth-pr\">正在统计…</span>
          </a>
        </div>
      </div>
    </div>

  </div>
</div>
"""

# CSS 样式
css_content = """/* ================= 全局容器 ================= */
.biz-nav-container {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 18px;
  box-sizing: border-box;
  width: 100%;
}

/* ================= 我的待办任务中心 (My Pending Tasks) ================= */
.my-tasks-section {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 14px;
}

.tasks-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.tasks-title-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tasks-main-title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
}

.tasks-badge {
  font-size: 11px;
  color: #475569;
  background: #e2e8f0;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
  transition: all 0.2s ease;
}
.tasks-badge.badge-pending-count {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
  font-weight: 600;
}
.tasks-badge.badge-all-done {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
  font-weight: 600;
}

.tasks-refresh-btn {
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 11px;
  color: #475569;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.15s ease;
}
.tasks-refresh-btn:hover {
  background: #f1f5f9;
  border-color: #94a3b8;
  color: #0f172a;
}

.tasks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.task-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
  min-height: 96px;
  box-sizing: border-box;
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0,0,0,0.06);
}

.task-card-top {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 10px;
}

.task-card-icon {
  font-size: 16px;
  line-height: 1;
}

.task-card-name {
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 2px;
}

.task-card-desc {
  font-size: 11px;
  color: #64748b;
  line-height: 1.3;
}

.task-card-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  padding-top: 6px;
  border-top: 1px solid #f1f5f9;
}

.task-count-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 12px;
  background: #f1f5f9;
  color: #64748b;
}

.pill-dot {
  width: 6px;
  height: 6px;
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

@keyframes pulse-dot {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.8; }
}

.task-action-btn {
  font-size: 11.5px;
  font-weight: 600;
  color: #2563eb;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  padding: 3px 6px;
  border-radius: 4px;
  transition: background 0.12s ease;
}
.task-action-btn:hover {
  background: #eff6ff;
  color: #1d4ed8;
}
.task-action-btn.is-disabled {
  color: #94a3b8;
  pointer-events: none;
  display: none;
}

/* 待办卡片主题边框 */
.task-card-amber { border-left: 4px solid #f59e0b; }
.task-card-green { border-left: 4px solid #10b981; }
.task-card-blue { border-left: 4px solid #3b82f6; }
.task-card-orange { border-left: 4px solid #f97316; }
.task-card-purple { border-left: 4px solid #a855f7; }

/* ================= 月度看板：我的月度任务 (Monthly Tasks) ================= */
.periodic-tasks-section {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 16px;
}

.periodic-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.periodic-period-select {
  height: 28px;
  font-size: 11.5px;
  font-weight: 600;
  color: #1e293b;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 0 8px;
  outline: none;
  cursor: pointer;
}
.periodic-period-select:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.periodic-companies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 14px;
}

/* 单公司卡片时自适应 */
.periodic-companies-grid.single-company {
  grid-template-columns: 1fr;
}

.company-periodic-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 14px 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.15s ease;
}
.company-periodic-card:hover {
  box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}

.company-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f1f5f9;
}

.company-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  font-weight: 700;
  color: #0f172a;
}

.company-status-badge {
  font-size: 10.5px;
  padding: 1px 6px;
  border-radius: 10px;
  font-weight: 600;
  background: #f1f5f9;
  color: #64748b;
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

.company-subtag {
  font-size: 10.5px;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 7px;
  border-radius: 4px;
  font-weight: 500;
}

.company-items-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.periodic-item-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  transition: all 0.15s ease;
}
.periodic-item-row:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
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
  gap: 10px;
}

.periodic-item-icon {
  font-size: 16px;
  line-height: 1;
}

.periodic-item-title {
  font-size: 12.5px;
  font-weight: 700;
  color: #1e293b;
}

.periodic-item-summary {
  font-size: 11.5px;
  color: #64748b;
  margin-top: 2px;
}

.periodic-item-badge-link {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 600;
  text-decoration: none !important;
  transition: all 0.15s ease;
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
  box-shadow: 0 2px 6px rgba(194, 65, 12, 0.15);
}

.badge-settled {
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #dcfce7;
}
.badge-settled:hover {
  background: #dcfce7;
}

.periodic-loading {
  font-size: 11.5px;
  color: #94a3b8;
  padding: 12px;
  text-align: center;
}

/* ================= 业务场景流程部分 ================= */
.biz-section-header { margin-bottom: 8px; display: flex; align-items: baseline; }
.biz-title { font-size: 15px; font-weight: 700; margin-right: 8px; }
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

/* ================= 权限自适应状态 ================= */
.step-hidden { display: none !important; }
.scene-hidden { display: none !important; }
.btn-hidden-perm { display: none !important; }

/* ================= 卡片容器 ================= */
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

.my-cmd-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 14px rgba(15, 23, 42, 0.08); }\n.my-cmd-btn:active { transform: translateY(0); box-shadow: 0 4px 10px rgba(15, 23, 42, 0.06); }\n.my-cmd-btn:focus-visible { outline: 3px solid var(--cmd-ring, rgba(36, 144, 239, 0.25)); outline-offset: 2px; }

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

.stat-row:hover { transform: translateY(-1px); box-shadow: 0 6px 14px rgba(15, 23, 42, 0.08); }\n.stat-row:active { transform: translateY(0); box-shadow: 0 4px 10px rgba(15, 23, 42, 0.06); }\n.stat-row:focus-visible { outline: 3px solid var(--cmd-ring, rgba(36, 144, 239, 0.18)); outline-offset: 2px; }

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

.stat-row.is-loading { opacity: 0.95; }
.stat-row.has-pending { opacity: 1; font-weight: 700; }

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
.step-blue { border-top: 3px solid #2490ef; }
.btn-blue { --cmd-ring: rgba(36, 144, 239, 0.28); background: #eff6ff !important; color: #1d4ed8 !important; border: 1px solid #dbeafe !important; }
.btn-blue:hover { background: #dbeafe !important; }
.btn-blue-outline { --cmd-ring: rgba(36, 144, 239, 0.22); background: #fff !important; color: #64748b !important; border: 1px solid #e2e8f0 !important; }
.btn-blue-outline:hover { background: #f8fafc !important; color: #2490ef !important; border-color: #cbd5e0 !important; }
.stat-blue { --cmd-ring: rgba(36, 144, 239, 0.18); background: #eff6ff !important; color: #2490ef !important; border: 1px solid #dbeafe !important; }

.step-orange { border-top: 3px solid #e67e22; }
.btn-orange { --cmd-ring: rgba(230, 126, 34, 0.28); background: #fff3e0 !important; color: #e65100 !important; border: 1px solid #ffe0b2 !important; }
.btn-orange:hover { background: #ffe0b2 !important; }
.btn-orange-outline { --cmd-ring: rgba(230, 126, 34, 0.22); background: #fff !important; color: #64748b !important; border: 1px solid #e2e8f0 !important; }
.btn-orange-outline:hover { background: #fff8e1 !important; color: #e67e22 !important; border-color: #ffe0b2 !important; }
.stat-orange { --cmd-ring: rgba(230, 126, 34, 0.18); background: #fff3e0 !important; color: #e67e22 !important; border: 1px solid #ffe0b2 !important; }

.step-purple { border-top: 3px solid #8e44ad; }
.btn-purple { --cmd-ring: rgba(142, 68, 173, 0.28); background: #f3e5f5 !important; color: #6a1b9a !important; border: 1px solid #e1bee7 !important; }
.btn-purple:hover { background: #e1bee7 !important; }
.btn-purple-outline { --cmd-ring: rgba(142, 68, 173, 0.22); background: #fff !important; color: #64748b !important; border: 1px solid #e2e8f0 !important; }
.btn-purple-outline:hover { background: #f3e5f5 !important; color: #8e44ad !important; border-color: #e1bee7 !important; }
.stat-purple { --cmd-ring: rgba(142, 68, 173, 0.18); background: #f3e5f5 !important; color: #8e44ad !important; border: 1px solid #e1bee7 !important; }

.step-teal { border-top: 3px solid #00b894; }
.btn-teal { --cmd-ring: rgba(0, 184, 148, 0.28); background: #e0f2f1 !important; color: #00695c !important; border: 1px solid #b2dfdb !important; }
.btn-teal:hover { background: #b2dfdb !important; }
.btn-teal-outline { --cmd-ring: rgba(0, 184, 148, 0.22); background: #fff !important; color: #64748b !important; border: 1px solid #e2e8f0 !important; }
.btn-teal-outline:hover { background: #e0f2f1 !important; color: #00b894 !important; border-color: #b2dfdb !important; }
.stat-teal { --cmd-ring: rgba(0, 184, 148, 0.18); background: #e0f2f1 !important; color: #00b894 !important; border: 1px solid #b2dfdb !important; }
"""

# JS 逻辑
js_content = """(function () {
  const ROOT = (typeof root_element !== \"undefined\" && root_element) ? root_element : document;

  // ============================================================
  // 1. Frappe 官方原生权限与归属人判定工具
  // ============================================================
  function getCurrentUser() {
    return (frappe.session && frappe.session.user) ? frappe.session.user : \"\";
  }

  function isAdminUser() {
    const u = getCurrentUser();
    return u === \"Administrator\" || (frappe.user_roles || []).includes(\"System Manager\");
  }

  function isFinanceUser() {
    if (isAdminUser()) return true;
    const roles = frappe.user_roles || [];
    return roles.includes(\"Accounts User\") || roles.includes(\"Accounts Manager\");
  }

  function userCanRead(doctype) {
    if (!doctype) return false;
    if (isAdminUser()) return true;
    if (frappe.model && typeof frappe.model.can_read === \"function\") {
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
    if (frappe.model && typeof frappe.model.can_create === \"function\") {
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

      if (permTarget === \"Payment Entry\") {
        isVisible = isFinanceUser() && userCanRead(\"Reimbursement Request\");
      } else if (permTarget === \"Purchase Order\") {
        isVisible = userCanCreate(\"Purchase Order\") || userCanRead(\"Material Request\");
      } else if (permTarget === \"Purchase Receipt\") {
        isVisible = userCanCreate(\"Purchase Receipt\") || userCanRead(\"Purchase Order\");
      } else if (permTarget === \"Purchase Invoice\") {
        isVisible = userCanCreate(\"Purchase Invoice\") || userCanRead(\"Purchase Receipt\");
      } else if (permTarget === \"Reimbursement Request\") {
        isVisible = userCanCreate(\"Reimbursement Request\") || userCanRead(\"Purchase Invoice\");
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
        if (typeof v === \"string\" && /^[0-9]+$/.test(v)) {
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
      const p = url.pathname || \"\";
      const m = p.match(/^\\/(?:app|desk)\\/([^\\/?#]+)(?:\\/(new))?\\/?$/);
      if (!m) return null;
      return { route: m[1], is_new: !!m[2] };
    } catch (e) {
      return null;
    }
  }

  const ROUTE_TO_DOCTYPE = {
    \"material-request\": \"Material Request\",
    \"purchase-order\": \"Purchase Order\",
    \"purchase-receipt\": \"Purchase Receipt\",
    \"purchase-invoice\": \"Purchase Invoice\",
    \"reimbursement-request\": \"Reimbursement Request\",
  };

  function guessDoctypeFromRoute(route) {
    return String(route || \"\")
      .split(\"-\")
      .map(s => s ? (s[0].toUpperCase() + s.slice(1)) : s)
      .join(\" \");
  }

  function materializeStatHrefs() {
    const links = ROOT.querySelectorAll('.stat-row[data-route][data-filters]');
    links.forEach((a) => {
      const route = a.getAttribute('data-route');
      const raw = a.getAttribute('data-filters');
      try {
        const filtersObj = JSON.parse(raw || \"{}\");
        a.setAttribute('href', buildListUrl(route, filtersObj));
      } catch (e) {}
    });
  }

  function bindStatRouteButtons() {
    const links = ROOT.querySelectorAll('.stat-row[data-doctype][data-filters], .task-action-btn[data-doctype]');
    links.forEach((a) => {
      if (a.dataset && a.dataset.bizBound === \"1\") return;
      if (a.dataset) a.dataset.bizBound = \"1\";

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
          filtersObj = JSON.parse(raw || \"{}\");
        } catch (err) {
          window.location.href = a.getAttribute('href') || \"/\";
          return;
        }

        frappe.route_options = filtersObj;
        frappe.set_route('List', doctype);
      });
    });
  }

  function bindCmdRouteButtons() {
    const links = ROOT.querySelectorAll('.my-cmd-btn[href^=\"/app/\"], .my-cmd-btn[href^=\"/desk/\"]');
    links.forEach((a) => {
      if (a.dataset && a.dataset.bizCmdBound === \"1\") return;
      if (a.dataset) a.dataset.bizCmdBound = \"1\";

      a.addEventListener(\"click\", (e) => {
        const isNewTab = e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0;
        if (isNewTab) return;

        const href = a.getAttribute(\"href\") || \"\";
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
        frappe.set_route(\"List\", doctype);
      });
    });
  }

  // ============================================================
  // 4. 我的待办任务中心数据驱动逻辑
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
    fetchTaskCardCount('Material Request', { docstatus: 1, status: ['in', ['Submitted', 'Pending', 'Partially Ordered']] }, '#pill-po', '#pill-text-po', '#act-po', '笔申请', false);
    fetchTaskCardCount('Purchase Order', { docstatus: 1, status: ['in', ['On Hold', 'To Receive', 'To Receive and Bill']] }, '#pill-pr', '#pill-text-pr', '#act-pr', '笔订单', false);
    fetchTaskCardCount('Purchase Receipt', { status: ['in', ['Partly Billed', 'To Bill']] }, '#pill-pi', '#pill-text-pi', '#act-pi', '笔入库单', true);
    fetchTaskPendingReimbursement();
    fetchTaskCardCount('Reimbursement Request', { docstatus: 1, outstanding_amount: ['>', 0] }, '#pill-settle', '#pill-text-settle', '#act-settle', '笔报销单', false);
  }

  // ============================================================
  // 5. 月度任务中心数据驱动逻辑 (公司权限严格隔离 + 优雅自适应)
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
      const label = `${y}年${m}月报表`;
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
      container.innerHTML = `<div class=\"periodic-loading\" style=\"color:#94a3b8;\">当前无需要核定的项目</div>`;
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
      const badgeText = isSettled ? '✅ 已核定' : `⚠️ ${it.status_label} · ${it.action_label}`;
      const href = isSettled ? (it.route || 'javascript:void(0)') : (it.route || 'javascript:void(0)');

      return `
        <div class=\"periodic-item-row ${rowClass}\">
          <div class=\"periodic-item-left\">
            <span class=\"periodic-item-icon\">${it.icon || '📌'}</span>
            <div>
              <div class=\"periodic-item-title\">${frappe.utils.escape_html(it.title)}</div>
              <div class=\"periodic-item-summary\">${frappe.utils.escape_html(it.summary_text || '')}</div>
            </div>
          </div>
          <div>
            <a href=\"${href}\" class=\"periodic-item-badge-link ${badgeClass}\" data-route=\"${it.route}\">
              ${badgeText}
            </a>
          </div>
        </div>
      `;
    }).join('');

    container.innerHTML = html;

    // 绑定 SPA 路由
    container.querySelectorAll('.periodic-item-badge-link[data-route]').forEach(a => {
      a.addEventListener('click', (e) => {
        const route = a.getAttribute('data-route');
        if (route && route.startsWith('/desk/')) {
          e.preventDefault();
          const clean = route.replace('/desk/', '');
          frappe.set_route(clean);
        }
      });
    });
  }

  function fetchMonthlySettlementStatus(year, month) {
    const badge = ROOT.querySelector('#periodic-period-badge');
    if (badge) {
      badge.innerText = '核验中…';
      badge.className = 'tasks-badge';
    }

    frappe.call({
      method: 'ashan_cn_procurement.services.periodic_tasks.get_monthly_settlement_status',
      args: { year: year, month: month },
      callback: function (r) {
        if (r && r.message) {
          const data = r.message;
          const comp = data.companies || {};
          const jizhong = comp.jizhong || {};
          const qifu = comp.qifu || {};

          // 更新主标题栏徽章
          if (badge) {
            const pendingCount = (data.total_items || 0) - (data.settled_items || 0);
            if (pendingCount > 0) {
              badge.innerText = `${data.period_label}报表 · ${pendingCount} 项待核定`;
              badge.className = 'tasks-badge badge-pending-count';
            } else if ((data.total_items || 0) > 0 && data.all_done) {
              badge.innerText = `${data.period_label}报表 · 已全部核定 ✅`;
              badge.className = 'tasks-badge badge-all-done';
            } else {
              badge.innerText = `${data.period_label}报表`;
              badge.className = 'tasks-badge';
            }
          }

          const jzCard = ROOT.querySelector('#company-card-jizhong');
          if (jzCard) {
            if (jizhong.visible) {
              jzCard.style.display = 'flex';
              renderPeriodicCompanyItems('#jizhong-items-list', '#jizhong-status-badge', jizhong.items);
            } else {
              jzCard.style.display = 'none';
            }
          }

          const qfCard = ROOT.querySelector('#company-card-qifu');
          if (qfCard) {
            if (qifu.visible) {
              qfCard.style.display = 'flex';
              renderPeriodicCompanyItems('#qifu-items-list', '#qifu-status-badge', qifu.items);
            } else {
              qfCard.style.display = 'none';
            }
          }

          const grid = ROOT.querySelector('#periodic-companies-grid');
          const visibleCount = (jizhong.visible ? 1 : 0) + (qifu.visible ? 1 : 0);
          if (grid) {
            if (visibleCount === 1) {
              grid.classList.add('single-company');
            } else {
              grid.classList.remove('single-company');
            }
          }

          const section = ROOT.querySelector('#periodic-tasks-container');
          if (section) {
            if (visibleCount === 0) {
              section.style.display = 'none';
            } else {
              section.style.display = 'block';
            }
          }
        }
      },
      error: function () {
        if (badge) badge.innerText = '核验失败';
      }
    });
  }

  // ============================================================
  // 6. 场景待办与草稿统计 (归属人智能感知)
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
        method: \"frappe.client.get_list\",
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
  // 7. 初始化执行
  // ============================================================
  applyPermissionAdaptation();
  initPeriodicPeriodSelector();

  materializeStatHrefs();
  setupDraftRows();
  bindStatRouteButtons();
  bindCmdRouteButtons();

  const refreshBtn = ROOT.querySelector('#btn-refresh-tasks');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      reloadAllTasks();
      frappe.show_alert({ message: '今日待办任务已更新', indicator: 'green' }, 3);
    });
  }

  const refreshPeriodicBtn = ROOT.querySelector('#btn-refresh-periodic');
  if (refreshPeriodicBtn) {
    refreshPeriodicBtn.addEventListener('click', () => {
      const sel = ROOT.querySelector('#select-periodic-period');
      const curOpt = sel ? sel.options[sel.selectedIndex] : null;
      if (curOpt) {
        fetchMonthlySettlementStatus(curOpt.dataset.year, curOpt.dataset.month);
      } else {
        fetchMonthlySettlementStatus();
      }
      frappe.show_alert({ message: '月度任务核定状态已刷新', indicator: 'green' }, 3);
    });
  }

  reloadAllTasks();
  fetchMonthlySettlementStatus();

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
"""

block['html'] = html_content
block['style'] = css_content
block['script'] = js_content

with open('ashan_cn_procurement/ashan_cn_procurement/fixtures/custom_html_block.json', 'w', encoding='utf-8') as f:
    json.dump(block, f, ensure_ascii=False, indent=2)

print('Successfully generated upgraded custom_html_block.json!')
