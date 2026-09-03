// Copyright (c) 2026, Ashan CN Procurement
// 天津吉众科技有限公司 · 人事薪酬综合工作台
// 严格对齐《202606吉众人事综合.xlsm》与《员工考勤表-*.xlsx》规范，贯彻 Ashan UI Kit 标准与零Emoji铁律

frappe.pages['jizhong-hr-salary-workbench'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: '吉众人事薪酬工作台',
        single_column: true
    });

    const COMPANY = "天津吉众科技有限公司";
    let current_month = "2026-06";
    let current_tab = "payroll";
    let payroll_view_mode = "all"; // all | accounting | non_accounting

    const html = `
    <div class="jz-wb-wrapper">
        <!-- 顶部 Header -->
        <div class="jz-header">
            <div>
                <div class="jz-title">
                    <span>天津吉众科技有限公司 · 人事薪酬综合中枢</span>
                    <span class="jz-title-badge">动态双工时 · 个税反推 · 现金五档配钞</span>
                </div>
                <div class="jz-subtitle">
                    结构化考勤工时 (正班+1.5x/2.0x/3.0x+倒休抵扣) · 历史税前累计预扣 · 原始凭证受控归档
                </div>
            </div>
            <div class="jz-header-actions">
                <label style="font-size: 13px; font-weight: 600; color: #475569; margin: 0;">核算月份：</label>
                <input type="month" id="jz-month-select" class="form-control" style="width: 140px; display: inline-block; font-weight: 600;" value="2026-06">
                <button class="btn btn-default btn-sm" id="btn-jz-refresh-all">刷新数据</button>
            </div>
        </div>

        <!-- 7大业务 Tab 切换 -->
        <div class="jz-nav-tabs">
            <button class="jz-tab-btn active" data-tab="payroll">1. 月度薪酬核定表</button>
            <button class="jz-tab-btn" data-tab="attendance">2. 考勤工时管理</button>
            <button class="jz-tab-btn" data-tab="cash_bills">3. 现金发放与配钞点钞</button>
            <button class="jz-tab-btn" data-tab="tax">4. 个人所得税台账</button>
            <button class="jz-tab-btn" data-tab="employees">5. 员工薪酬档案</button>
            <button class="jz-tab-btn" data-tab="insurance">6. 社保公积金配置</button>
            <button class="jz-tab-btn" data-tab="history">7. 历史薪资穿透 (421条)</button>
        </div>

        <!-- Tab 1: 月度薪酬核定表 -->
        <div id="jz-tab-payroll" class="jz-tab-content">
            <div class="jz-kpi-grid">
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">核定状态 / 人数</div>
                    <div class="jz-kpi-val" id="jz-kpi-status"><span class="jz-status-badge jz-status-draft">草稿 / 未核定</span></div>
                    <div class="jz-kpi-sub">在职计薪人员: <strong id="jz-kpi-count">0</strong> 人</div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">实发工资总额</div>
                    <div class="jz-kpi-val" style="color:#ea580c;" id="jz-kpi-net">¥ 0.00</div>
                    <div class="jz-kpi-sub">应发总额: <span id="jz-kpi-gross">¥ 0.00</span></div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">代扣税费 (个人部分)</div>
                    <div class="jz-kpi-val" style="color:#d97706;" id="jz-kpi-person-ded">¥ 0.00</div>
                    <div class="jz-kpi-sub">社保个人: <span id="jz-kpi-ss-pers">¥ 0.00</span> | 公积金: <span id="jz-kpi-hf-pers">¥ 0.00</span> | 个税: <span id="jz-kpi-tax">¥ 0.00</span></div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">单位统筹成本</div>
                    <div class="jz-kpi-val" style="color:#059669;" id="jz-kpi-comp-cost">¥ 0.00</div>
                    <div class="jz-kpi-sub">单位社保: <span id="jz-kpi-ss-comp">¥ 0.00</span> | 单位公积金: <span id="jz-kpi-hf-comp">¥ 0.00</span></div>
                </div>
            </div>

            <div class="jz-toolbar">
                <div class="jz-toolbar-left">
                    <div class="jz-segmented-control" id="jz-payroll-filter">
                        <button class="jz-segment-btn active" data-mode="all">全部人员</button>
                        <button class="jz-segment-btn" data-mode="accounting">入账核定 (正式工/返聘/管理)</button>
                        <button class="jz-segment-btn" data-mode="non_accounting">不入账核定 (临时工/兼职)</button>
                    </div>
                    <button class="btn btn-primary btn-sm" id="btn-jz-calc-payroll" style="background:#ea580c; border-color:#ea580c;">执行月度薪酬核算</button>
                    <button class="btn btn-success btn-sm" id="btn-jz-lock-payroll" style="background:#16a34a; border-color:#16a34a;">核定锁定 (只读封账)</button>
                    <button class="btn btn-default btn-sm" id="btn-jz-unlock-payroll" style="display:none; color:#dc2626; border-color:#dc2626;">申请反审核解锁</button>
                </div>
                <div class="jz-toolbar-right">
                    <button class="btn btn-default btn-sm" id="btn-jz-export-payroll">导出本月工资表 (Excel)</button>
                </div>
            </div>

            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-payroll">
                    <thead>
                        <tr>
                            <th class="jz-freeze-1"><div class="jz-th-compound"><span class="jz-th-badge">固定</span><span class="jz-th-title">序号</span></div></th>
                            <th class="jz-freeze-2"><div class="jz-th-compound"><span class="jz-th-badge">固定</span><span class="jz-th-title">工号</span></div></th>
                            <th class="jz-freeze-3"><div class="jz-th-compound"><span class="jz-th-badge">固定</span><span class="jz-th-title">姓名</span></div></th>
                            <th class="jz-freeze-4"><div class="jz-th-compound"><span class="jz-th-badge">身份</span><span class="jz-th-title">用工性质</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">模式</span><span class="jz-th-title">计薪方式</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">标准</span><span class="jz-th-title">基本工资</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">标准</span><span class="jz-th-title">岗位津贴</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">标准</span><span class="jz-th-title">绩效基数</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">工时</span><span class="jz-th-title">出勤工时</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">工时</span><span class="jz-th-title">1.5倍工时</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">工时</span><span class="jz-th-title">2倍工时</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">工时</span><span class="jz-th-title">3倍工时</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">工时</span><span class="jz-th-title">倒休工时</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">考勤</span><span class="jz-th-title">餐补次数</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">薪资</span><span class="jz-th-title">基本工时工资</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">薪资</span><span class="jz-th-title">1.5倍工资</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">薪资</span><span class="jz-th-title">2倍工资</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">薪资</span><span class="jz-th-title">3倍工资</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">薪资</span><span class="jz-th-title">基本补贴工资</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">薪资</span><span class="jz-th-title">绩效工资</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">薪资</span><span class="jz-th-title">餐补工资</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">薪资</span><span class="jz-th-title">工资调整</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">应发</span><span class="jz-th-title">应发薪资合计</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">代扣</span><span class="jz-th-title">社保代扣</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">代扣</span><span class="jz-th-title">公积金代扣</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">代扣</span><span class="jz-th-title">代扣个税</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">扣除</span><span class="jz-th-title">个人扣除合计</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">实发</span><span class="jz-th-title">实发薪资合计</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">现金</span><span class="jz-th-title">现金发放取整</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">单位</span><span class="jz-th-title">社保单位统筹</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">单位</span><span class="jz-th-title">公积金单位缴纳</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">成本</span><span class="jz-th-title">公司成本合计</span></div></th>
                        </tr>
                    </thead>
                    <tbody id="tbody-jz-payroll">
                        <tr><td colspan="32" style="text-align:center; padding:30px; color:#94a3b8;">正在加载吉众薪酬数据...</td></tr>
                    </tbody>
                    <tfoot id="tfoot-jz-payroll"></tfoot>
                </table>
            </div>
        </div>

        <!-- Tab 2: 考勤工时管理 -->
        <div id="jz-tab-attendance" class="jz-tab-content" style="display:none;">
            <div class="jz-kpi-grid">
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">考勤总人次 / 状态</div>
                    <div class="jz-kpi-val" id="jz-att-kpi-count">0 人</div>
                    <div class="jz-kpi-sub" id="jz-att-file-status">原始凭证: 未上传</div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">基本正班总工时</div>
                    <div class="jz-kpi-val" style="color:#0284c7;" id="jz-att-kpi-reg">0.00 h</div>
                    <div class="jz-kpi-sub">倒休抵扣工时: <span id="jz-att-kpi-comp">0.00 h</span></div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">各倍率加班总工时</div>
                    <div class="jz-kpi-val" style="color:#ea580c;" id="jz-att-kpi-ot">0.00 h</div>
                    <div class="jz-kpi-sub">1.5x平日: <span id="jz-att-kpi-ot15">0.0h</span> | 2.0x周末: <span id="jz-att-kpi-ot20">0.0h</span> | 3.0x节假日: <span id="jz-att-kpi-ot30">0.0h</span></div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">订餐补贴总次数</div>
                    <div class="jz-kpi-val" style="color:#16a34a;" id="jz-att-kpi-meals">0 次</div>
                    <div class="jz-kpi-sub">单价: ¥ 15.00 / 份</div>
                </div>
            </div>

            <div class="jz-toolbar">
                <div class="jz-toolbar-left">
                    <button class="btn btn-primary btn-sm" id="btn-jz-upload-attendance" style="background:#0284c7; border-color:#0284c7;">上传吉众月度考勤 (Excel)</button>
                    <button class="btn btn-default btn-sm" id="btn-jz-download-attendance-file" style="display:none;">下载原始考勤凭证</button>
                    <button class="btn btn-default btn-sm" id="btn-jz-sync-calc-payroll" style="color:#ea580c; border-color:#ea580c;">按考勤一键核算当月工资</button>
                </div>
                <div class="jz-toolbar-right">
                    <span style="font-size:12px; color:#64748b;">支持标准5行格式: 班次、作业时间、加班时间、餐补、备注</span>
                </div>
            </div>

            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-attendance">
                    <thead>
                        <tr>
                            <th class="jz-freeze-1"><div class="jz-th-compound"><span class="jz-th-badge">固定</span><span class="jz-th-title">序号</span></div></th>
                            <th class="jz-freeze-2"><div class="jz-th-compound"><span class="jz-th-badge">固定</span><span class="jz-th-title">工号</span></div></th>
                            <th class="jz-freeze-3"><div class="jz-th-compound"><span class="jz-th-badge">固定</span><span class="jz-th-title">姓名</span></div></th>
                            <th class="jz-freeze-4"><div class="jz-th-compound"><span class="jz-th-badge">出勤</span><span class="jz-th-title">整天(天)</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">出勤</span><span class="jz-th-title">半天(天)</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">出勤</span><span class="jz-th-title">缺勤(天)</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">工时</span><span class="jz-th-title">基本正班工时</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">加班</span><span class="jz-th-title">1.5倍平日加班</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">加班</span><span class="jz-th-title">2.0倍周末加班</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">加班</span><span class="jz-th-title">3.0倍节假日加班</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">抵扣</span><span class="jz-th-title">倒休抵扣工时</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">餐饮</span><span class="jz-th-title">餐补次数</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">穿透</span><span class="jz-th-title">每日明细</span></div></th>
                        </tr>
                    </thead>
                    <tbody id="tbody-jz-attendance">
                        <tr><td colspan="13" style="text-align:center; padding:30px; color:#94a3b8;">正在加载吉众考勤工时...</td></tr>
                    </tbody>
                    <tfoot id="tfoot-jz-attendance"></tfoot>
                </table>
            </div>
        </div>

        <!-- Tab 3: 现金发放与配钞点钞 -->
        <div id="jz-tab-cash_bills" class="jz-tab-content" style="display:none;">
            <div class="jz-cash-stat-bar" id="jz-cash-summary-bar">
                <div class="jz-cash-stat-item"><span class="jz-cash-denom-label">现金总盘:</span> <span class="jz-cash-denom-count" id="stat-cash-total">¥ 0.00</span></div>
                <div class="jz-cash-stat-item"><span class="jz-cash-denom-label">100元券:</span> <span class="jz-cash-denom-count" id="stat-b100">0 张</span></div>
                <div class="jz-cash-stat-item"><span class="jz-cash-denom-label">50元券:</span> <span class="jz-cash-denom-count" id="stat-b50">0 张</span></div>
                <div class="jz-cash-stat-item"><span class="jz-cash-denom-label">10元券:</span> <span class="jz-cash-denom-count" id="stat-b10">0 张</span></div>
                <div class="jz-cash-stat-item"><span class="jz-cash-denom-label">5元券:</span> <span class="jz-cash-denom-count" id="stat-b5">0 张</span></div>
                <div class="jz-cash-stat-item"><span class="jz-cash-denom-label">1元券:</span> <span class="jz-cash-denom-count" id="stat-b1">0 张</span></div>
            </div>

            <div class="jz-toolbar">
                <div class="jz-toolbar-left">
                    <button class="btn btn-default btn-sm" id="btn-jz-print-a4-slips">打印 A4 签收工资条</button>
                </div>
                <div class="jz-toolbar-right">
                    <span style="font-size:12px; color:#64748b;">现金取整算法：RoundUp(实发工资, 0)，严格五档贪心拆分平账</span>
                </div>
            </div>

            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-cash">
                    <thead>
                        <tr>
                            <th class="jz-freeze-1"><div class="jz-th-compound"><span class="jz-th-badge">固定</span><span class="jz-th-title">序号</span></div></th>
                            <th class="jz-freeze-2"><div class="jz-th-compound"><span class="jz-th-badge">固定</span><span class="jz-th-title">工号</span></div></th>
                            <th class="jz-freeze-3"><div class="jz-th-compound"><span class="jz-th-badge">固定</span><span class="jz-th-title">姓名</span></div></th>
                            <th class="jz-freeze-4"><div class="jz-th-compound"><span class="jz-th-badge">实发</span><span class="jz-th-title">实发薪资</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">取整</span><span class="jz-th-title">现金发放工资</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">面额</span><span class="jz-th-title">百元 (¥100)</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">面额</span><span class="jz-th-title">五十元 (¥50)</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">面额</span><span class="jz-th-title">十元 (¥10)</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">面额</span><span class="jz-th-title">五元 (¥5)</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">面额</span><span class="jz-th-title">一元 (¥1)</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">平账</span><span class="jz-th-title">现金面额合计</span></div></th>
                            <th><div class="jz-th-compound"><span class="jz-th-badge">签署</span><span class="jz-th-title">收款签字</span></div></th>
                        </tr>
                    </thead>
                    <tbody id="tbody-jz-cash"></tbody>
                    <tfoot id="tfoot-jz-cash"></tfoot>
                </table>
            </div>
        </div>

        <!-- Tab 4: 个人所得税台账 -->
        <div id="jz-tab-tax" class="jz-tab-content" style="display:none;">
            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-tax">
                    <thead>
                        <tr>
                            <th class="jz-freeze-1">序号</th>
                            <th class="jz-freeze-2">工号</th>
                            <th class="jz-freeze-3">姓名</th>
                            <th class="jz-freeze-4">计薪方式</th>
                            <th>应发薪资合计</th>
                            <th>当月个税免征额</th>
                            <th>社保合计p</th>
                            <th>住房公积金p</th>
                            <th>当月专项附加扣除</th>
                            <th>以往税前累计</th>
                            <th>以往免征额累计</th>
                            <th>以往专项扣除累计</th>
                            <th>以往附加扣除累计</th>
                            <th>以往已纳税额累计</th>
                            <th>周期应缴纳所得税</th>
                            <th>当月应缴纳所得税</th>
                            <th>实发薪资合计</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-jz-tax"></tbody>
                </table>
            </div>
        </div>

        <!-- Tab 5: 员工薪酬档案 -->
        <div id="jz-tab-employees" class="jz-tab-content" style="display:none;">
            <div class="jz-toolbar">
                <div class="jz-toolbar-left">
                    <button class="btn btn-primary btn-sm" id="btn-jz-add-emp" style="background:#ea580c; border-color:#ea580c;">新建在职员工档案</button>
                </div>
            </div>
            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-employees">
                    <thead>
                        <tr>
                            <th class="jz-freeze-1">序号</th>
                            <th class="jz-freeze-2">工号</th>
                            <th class="jz-freeze-3">姓名</th>
                            <th class="jz-freeze-4">身份证号</th>
                            <th>用工性质</th>
                            <th>在职状态</th>
                            <th>计薪方式</th>
                            <th>基本工资</th>
                            <th>岗位津贴</th>
                            <th>绩效基数</th>
                            <th>餐补单价</th>
                            <th>社保基数</th>
                            <th>公积金基数</th>
                            <th>专项附加扣除</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-jz-employees"></tbody>
                </table>
            </div>
        </div>

        <!-- Tab 6: 社保公积金配置 -->
        <div id="jz-tab-insurance" class="jz-tab-content" style="display:none;">
            <div style="background:#ffffff; padding:20px; border-radius:8px; border:1px solid #e2e8f0; max-width:800px;">
                <h4 style="margin-top:0; font-weight:700; color:#0f172a;">吉众公司法定社保公积金基数与费率标准</h4>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:16px;">
                    <div><strong>工伤保险单位费率:</strong> 0.55% (特定标准)</div>
                    <div><strong>养老保险比例:</strong> 个人 8.00% / 单位 16.00%</div>
                    <div><strong>医疗保险比例:</strong> 个人 2.00% / 单位 10.00%</div>
                    <div><strong>失业保险比例:</strong> 个人 0.50% / 单位 0.50%</div>
                    <div><strong>生育保险比例:</strong> 单位 0.50%</div>
                    <div><strong>住房公积金比例:</strong> 个人 5.00% / 单位 5.00%</div>
                    <div><strong>大额医疗救助:</strong> 1/4/7/10月为 21.00元，其余月份 22.00元</div>
                    <div><strong>个税基本减除费用:</strong> ¥ 5,000.00 / 月</div>
                </div>
            </div>
        </div>

        <!-- Tab 7: 历史薪资穿透 (421条) -->
        <div id="jz-tab-history" class="jz-tab-content" style="display:none;">
            <div class="jz-toolbar">
                <div class="jz-toolbar-left">
                    <label style="font-size:13px; font-weight:600; margin:0;">过滤历史账期：</label>
                    <select id="jz-history-month-filter" class="form-control" style="width:140px; display:inline-block;">
                        <option value="ALL">全部历史 (421条)</option>
                    </select>
                </div>
            </div>
            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-history">
                    <thead>
                        <tr>
                            <th class="jz-freeze-1">序号</th>
                            <th class="jz-freeze-2">账期</th>
                            <th class="jz-freeze-3">工号</th>
                            <th class="jz-freeze-4">姓名</th>
                            <th>计薪方式</th>
                            <th>基本工资</th>
                            <th>岗位津贴</th>
                            <th>绩效奖金</th>
                            <th>应发薪资合计</th>
                            <th>免征额</th>
                            <th>专项扣除</th>
                            <th>附加扣除</th>
                            <th>代扣个税</th>
                            <th>实发薪资合计</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-jz-history"></tbody>
                </table>
            </div>
        </div>
    </div>
    `;

    page.main.html(html);

    // 金额格式化辅助函数
    function fmtMoney(val) {
        let n = flt(val);
        return '¥ ' + n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function fmtHours(val) {
        let n = flt(val);
        return n.toFixed(2) + ' h';
    }

    // Tab 切换逻辑
    $('.jz-tab-btn').on('click', function() {
        const tab = $(this).data('tab');
        $('.jz-tab-btn').removeClass('active');
        $(this).addClass('active');
        $('.jz-tab-content').hide();
        $(`#jz-tab-${tab}`).show();
        current_tab = tab;

        if (tab === 'payroll') load_payroll_data();
        else if (tab === 'attendance') load_attendance_data();
        else if (tab === 'cash_bills') load_cash_data();
        else if (tab === 'tax') load_tax_data();
        else if (tab === 'employees') load_employees_data();
        else if (tab === 'history') load_history_data();
    });

    // 月份变更
    $('#jz-month-select').on('change', function() {
        current_month = $(this).val();
        refresh_current_view();
    });

    $('#btn-jz-refresh-all').on('click', function() {
        refresh_current_view();
    });

    function refresh_current_view() {
        if (current_tab === 'payroll') load_payroll_data();
        else if (current_tab === 'attendance') load_attendance_data();
        else if (current_tab === 'cash_bills') load_cash_data();
        else if (current_tab === 'tax') load_tax_data();
        else if (current_tab === 'employees') load_employees_data();
        else if (current_tab === 'history') load_history_data();
    }

    // 1. 加载月度薪酬核定表
    let payroll_cache = [];
    function load_payroll_data() {
        frappe.call({
            method: 'ashan_cn_procurement.services.jizhong_payroll_service.get_jizhong_payroll_overview',
            args: { company: COMPANY, period_month: current_month },
            callback: function(r) {
                if (!r.message) return;
                const set = r.message.settlement || {};
                const items = r.message.items || [];
                payroll_cache = items;

                // KPI 渲染
                if (set.locked) {
                    $('#jz-kpi-status').html('<span class="jz-status-badge jz-status-locked">已核定锁定</span>');
                    $('#btn-jz-lock-payroll').hide();
                    $('#btn-jz-unlock-payroll').show();
                } else {
                    $('#jz-kpi-status').html('<span class="jz-status-badge jz-status-draft">草稿 / 可测算</span>');
                    $('#btn-jz-lock-payroll').show();
                    $('#btn-jz-unlock-payroll').hide();
                }

                $('#jz-kpi-count').text(items.length);
                $('#jz-kpi-net').text(fmtMoney(set.total_net_salary || 0));
                $('#jz-kpi-gross').text(fmtMoney(set.total_gross_salary || 0));
                $('#jz-kpi-person-ded').text(fmtMoney((flt(set.total_social_security_person) + flt(set.total_housing_fund_person) + flt(set.total_tax))));
                $('#jz-kpi-ss-pers').text(fmtMoney(set.total_social_security_person || 0));
                $('#jz-kpi-hf-pers').text(fmtMoney(set.total_housing_fund_person || 0));
                $('#jz-kpi-tax').text(fmtMoney(set.total_tax || 0));
                $('#jz-kpi-comp-cost').text(fmtMoney((flt(set.total_social_security_company) + flt(set.total_housing_fund_company))));
                $('#jz-kpi-ss-comp').text(fmtMoney(set.total_social_security_company || 0));
                $('#jz-kpi-hf-comp').text(fmtMoney(set.total_housing_fund_company || 0));

                render_payroll_table();
            }
        });
    }

    // 过滤与渲染 Payroll Table
    function render_payroll_table() {
        const tbody = $('#tbody-jz-payroll');
        tbody.empty();

        let filtered = payroll_cache.filter(it => {
            if (payroll_view_mode === 'accounting') {
                return ['正式工', '其他-管理', '返聘工'].includes(it.employee_type);
            } else if (payroll_view_mode === 'non_accounting') {
                return ['临时工', '兼职'].includes(it.employee_type);
            }
            return true;
        });

        if (filtered.length === 0) {
            tbody.html('<tr><td colspan="32" style="text-align:center; padding:30px; color:#94a3b8;">该期间暂无薪酬结算记录，请点击上方“执行月度薪酬核算”。</td></tr>');
            $('#tfoot-jz-payroll').empty();
            return;
        }

        let tot_basic_hrs = 0, tot_ot_15 = 0, tot_ot_20 = 0, tot_ot_30 = 0, tot_comp = 0, tot_meals = 0;
        let tot_sal_basic = 0, tot_sal_ot15 = 0, tot_sal_ot20 = 0, tot_sal_ot30 = 0, tot_sal_sub = 0;
        let tot_sal_perf = 0, tot_sal_meal = 0, tot_sal_adj = 0, tot_gross = 0;
        let tot_ss_pers = 0, tot_hf_pers = 0, tot_tax = 0, tot_pers_ded = 0, tot_net = 0, tot_cash = 0;
        let tot_ss_comp = 0, tot_hf_comp = 0, tot_comp_cost = 0;

        filtered.forEach((it, idx) => {
            tot_basic_hrs += flt(it.work_hours);
            tot_ot_15 += flt(it.overtime_regular_1_5);
            tot_ot_20 += flt(it.overtime_weekend_2_0);
            tot_ot_30 += flt(it.overtime_holiday_3_0);
            tot_comp += flt(it.leave_compensatory_hours);
            tot_meals += cint(it.meal_count);

            tot_sal_basic += flt(it.salary_basic_hours);
            tot_sal_ot15 += flt(it.salary_overtime_1_5);
            tot_sal_ot20 += flt(it.salary_overtime_2_0);
            tot_sal_ot30 += flt(it.salary_overtime_3_0);
            tot_sal_sub += flt(it.salary_basic_subsidy);
            tot_sal_perf += flt(it.salary_performance);
            tot_sal_meal += flt(it.salary_meal_subsidy);
            tot_sal_adj += flt(it.salary_adjustment);
            tot_gross += flt(it.gross_salary);

            tot_ss_pers += flt(it.ss_person_total);
            tot_hf_pers += flt(it.hf_person_total);
            tot_tax += flt(it.tax_amount);
            tot_pers_ded += flt(it.person_cost_total);
            tot_net += flt(it.net_salary);
            tot_cash += flt(it.cash_pay);

            tot_ss_comp += flt(it.ss_company_total);
            tot_hf_comp += flt(it.hf_company_total);
            tot_comp_cost += flt(it.company_cost_total);

            tbody.append(`
                <tr>
                    <td class="jz-freeze-1">${idx + 1}</td>
                    <td class="jz-freeze-2"><strong>${it.employee_no}</strong></td>
                    <td class="jz-freeze-3"><strong>${it.employee_name}</strong></td>
                    <td class="jz-freeze-4">${it.employee_type || '正式工'}</td>
                    <td>${it.salary_mode}</td>
                    <td class="jz-money-cell">${fmtMoney(it.base_salary)}</td>
                    <td class="jz-money-cell">${fmtMoney(it.post_allowance)}</td>
                    <td class="jz-money-cell">${fmtMoney(it.performance_salary)}</td>
                    <td class="jz-num-cell">${fmtHours(it.work_hours)}</td>
                    <td class="jz-num-cell">${fmtHours(it.overtime_regular_1_5)}</td>
                    <td class="jz-num-cell">${fmtHours(it.overtime_weekend_2_0)}</td>
                    <td class="jz-num-cell">${fmtHours(it.overtime_holiday_3_0)}</td>
                    <td class="jz-num-cell">${fmtHours(it.leave_compensatory_hours)}</td>
                    <td class="jz-num-cell">${it.meal_count} 次</td>
                    <td class="jz-money-cell">${fmtMoney(it.salary_basic_hours)}</td>
                    <td class="jz-money-cell">${fmtMoney(it.salary_overtime_1_5)}</td>
                    <td class="jz-money-cell">${fmtMoney(it.salary_overtime_2_0)}</td>
                    <td class="jz-money-cell">${fmtMoney(it.salary_overtime_3_0)}</td>
                    <td class="jz-money-cell">${fmtMoney(it.salary_basic_subsidy)}</td>
                    <td class="jz-money-cell">${fmtMoney(it.salary_performance)}</td>
                    <td class="jz-money-cell">${fmtMoney(it.salary_meal_subsidy)}</td>
                    <td class="jz-money-cell">${fmtMoney(it.salary_adjustment)}</td>
                    <td class="jz-money-cell" style="font-weight:700; color:#0f172a;">${fmtMoney(it.gross_salary)}</td>
                    <td class="jz-money-cell">${fmtMoney(it.ss_person_total)}</td>
                    <td class="jz-money-cell">${fmtMoney(it.hf_person_total)}</td>
                    <td class="jz-money-cell">${fmtMoney(it.tax_amount)}</td>
                    <td class="jz-money-cell">${fmtMoney(it.person_cost_total)}</td>
                    <td class="jz-money-cell" style="font-weight:700; color:#ea580c;">${fmtMoney(it.net_salary)}</td>
                    <td class="jz-money-cell" style="font-weight:700; color:#0284c7;">${fmtMoney(it.cash_pay)}</td>
                    <td class="jz-money-cell">${fmtMoney(it.ss_company_total)}</td>
                    <td class="jz-money-cell">${fmtMoney(it.hf_company_total)}</td>
                    <td class="jz-money-cell" style="font-weight:700; color:#059669;">${fmtMoney(it.company_cost_total)}</td>
                </tr>
            `);
        });

        // 底部合计
        $('#tfoot-jz-payroll').html(`
            <tr>
                <td class="jz-freeze-1">合计</td>
                <td class="jz-freeze-2">-</td>
                <td class="jz-freeze-3">${filtered.length} 人</td>
                <td class="jz-freeze-4">-</td>
                <td>-</td>
                <td class="jz-money-cell">-</td>
                <td class="jz-money-cell">-</td>
                <td class="jz-money-cell">-</td>
                <td class="jz-num-cell">${fmtHours(tot_basic_hrs)}</td>
                <td class="jz-num-cell">${fmtHours(tot_ot_15)}</td>
                <td class="jz-num-cell">${fmtHours(tot_ot_20)}</td>
                <td class="jz-num-cell">${fmtHours(tot_ot_30)}</td>
                <td class="jz-num-cell">${fmtHours(tot_comp)}</td>
                <td class="jz-num-cell">${tot_meals} 次</td>
                <td class="jz-money-cell">${fmtMoney(tot_sal_basic)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_sal_ot15)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_sal_ot20)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_sal_ot30)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_sal_sub)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_sal_perf)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_sal_meal)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_sal_adj)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_gross)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_ss_pers)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_hf_pers)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_tax)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_pers_ded)}</td>
                <td class="jz-money-cell" style="color:#ea580c;">${fmtMoney(tot_net)}</td>
                <td class="jz-money-cell" style="color:#0284c7;">${fmtMoney(tot_cash)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_ss_comp)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_hf_comp)}</td>
                <td class="jz-money-cell" style="color:#059669;">${fmtMoney(tot_comp_cost)}</td>
            </tr>
        `);
    }

    // 分段控件事件
    $('#jz-payroll-filter .jz-segment-btn').on('click', function() {
        $('#jz-payroll-filter .jz-segment-btn').removeClass('active');
        $(this).addClass('active');
        payroll_view_mode = $(this).data('mode');
        render_payroll_table();
    });

    // 一键测算薪酬
    $('#btn-jz-calc-payroll').on('click', function() {
        frappe.confirm(`确定对吉众公司 ${current_month} 账期执行全员薪酬测算？`, function() {
            frappe.show_alert({ message: '正在测算考勤工时与累计个税...', indicator: 'blue' });
            frappe.call({
                method: 'ashan_cn_procurement.services.jizhong_payroll_service.calculate_jizhong_monthly_payroll',
                args: { company: COMPANY, period_month: current_month },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint(`月度薪资测算完成！共计 ${r.message.total_employees} 人，实发工资总额 ${fmtMoney(r.message.total_net_salary)}。`);
                        load_payroll_data();
                    }
                }
            });
        });
    });

    // 2. 加载考勤工时管理
    let attendance_cache = [];
    function load_attendance_data() {
        frappe.call({
            method: 'ashan_cn_procurement.services.jizhong_attendance_service.get_jizhong_attendance_table',
            args: { company: COMPANY, period_month: current_month },
            callback: function(r) {
                if (!r.message) return;
                const summary = r.message.summary || {};
                const records = r.message.records || [];
                attendance_cache = records;

                $('#jz-att-kpi-count').text((summary.employee_count || 0) + ' 人');
                $('#jz-att-kpi-reg').text(fmtHours(summary.total_work_hours || 0));
                $('#jz-att-kpi-comp').text(fmtHours(summary.total_compensatory || 0));
                $('#jz-att-kpi-ot').text(fmtHours((flt(summary.total_ot_1_5) + flt(summary.total_ot_2_0) + flt(summary.total_ot_3_0))));
                $('#jz-att-kpi-ot15').text(fmtHours(summary.total_ot_1_5 || 0));
                $('#jz-att-kpi-ot20').text(fmtHours(summary.total_ot_2_0 || 0));
                $('#jz-att-kpi-ot30').text(fmtHours(summary.total_ot_3_0 || 0));
                $('#jz-att-kpi-meals').text((summary.total_meals || 0) + ' 次');

                if (summary.attendance_file) {
                    $('#jz-att-file-status').html(`凭证已归档: <a href="${summary.attendance_file}" target="_blank" style="color:#0284c7; text-decoration:underline;">查看文件</a>`);
                    $('#btn-jz-download-attendance-file').show().attr('data-url', summary.attendance_file);
                } else {
                    $('#jz-att-file-status').text('原始凭证: 未上传');
                    $('#btn-jz-download-attendance-file').hide();
                }

                render_attendance_table();
            }
        });
    }

    function render_attendance_table() {
        const tbody = $('#tbody-jz-attendance');
        tbody.empty();

        if (attendance_cache.length === 0) {
            tbody.html('<tr><td colspan="13" style="text-align:center; padding:30px; color:#94a3b8;">该月份尚未上传考勤表，请点击“上传吉众月度考勤 (Excel)”按钮。</td></tr>');
            $('#tfoot-jz-attendance').empty();
            return;
        }

        attendance_cache.forEach((it, idx) => {
            tbody.append(`
                <tr class="jz-att-row" data-no="${it.employee_no}">
                    <td class="jz-freeze-1">${idx + 1}</td>
                    <td class="jz-freeze-2"><strong>${it.employee_no}</strong></td>
                    <td class="jz-freeze-3"><strong>${it.employee_name}</strong></td>
                    <td class="jz-freeze-4 jz-num-cell">${it.attendance_days || 0}</td>
                    <td class="jz-num-cell">${it.half_days || 0}</td>
                    <td class="jz-num-cell">${it.absent_days || 0}</td>
                    <td class="jz-num-cell" style="font-weight:700; color:#0284c7;">${fmtHours(it.work_hours_regular)}</td>
                    <td class="jz-num-cell">${fmtHours(it.overtime_regular_1_5)}</td>
                    <td class="jz-num-cell">${fmtHours(it.overtime_weekend_2_0)}</td>
                    <td class="jz-num-cell">${fmtHours(it.overtime_holiday_3_0)}</td>
                    <td class="jz-num-cell" style="color:#64748b;">${fmtHours(it.leave_compensatory_hours)}</td>
                    <td class="jz-num-cell" style="font-weight:700; color:#16a34a;">${it.meal_count || 0} 次</td>
                    <td style="text-align:center;">
                        <button class="btn btn-default btn-xs btn-toggle-daily" data-no="${it.employee_no}">展开日明细</button>
                    </td>
                </tr>
                <tr class="jz-att-detail-tr" id="detail-${it.employee_no}" style="display:none;">
                    <td colspan="13" style="padding:0; background:#f8fafc;">
                        <div class="jz-attendance-detail-box" id="detail-box-${it.employee_no}"></div>
                    </td>
                </tr>
            `);
        });

        // 展开打卡明细事件
        $('.btn-toggle-daily').on('click', function() {
            const empNo = $(this).data('no');
            const tr = $(`#detail-${empNo}`);
            const btn = $(this);

            if (tr.is(':visible')) {
                tr.hide();
                btn.text('展开日明细');
            } else {
                const emp = attendance_cache.find(e => e.employee_no === empNo);
                if (emp && emp.daily_records_json) {
                    try {
                        const days = JSON.parse(emp.daily_records_json);
                        let cardsHtml = '<div class="jz-day-card-grid">';
                        days.forEach(d => {
                            let cls = 'jz-day-card';
                            if (d.nature.includes('周末') || d.nature.includes('公休')) cls += ' jz-day-card-weekend';
                            if (d.nature.includes('节假日')) cls += ' jz-day-card-holiday';

                            cardsHtml += `
                                <div class="${cls}">
                                    <div class="jz-day-card-num">${d.day}日</div>
                                    <div style="font-size:10px; color:#64748b;">${d.shift || '-'}</div>
                                    <div class="jz-day-card-hours">${d.work_hours > 0 ? d.work_hours + 'h' : '0'}</div>
                                    <div class="jz-day-card-ot">${d.overtime > 0 ? '+' + d.overtime + 'h' : ''}</div>
                                    <div style="font-size:10px; color:#16a34a;">${d.meal > 0 ? d.meal + '餐' : ''}</div>
                                </div>
                            `;
                        });
                        cardsHtml += '</div>';
                        $(`#detail-box-${empNo}`).html(cardsHtml);
                    } catch(e) {}
                }
                tr.show();
                btn.text('收起明细');
            }
        });
    }

    // 上传考勤 Excel 弹窗
    $('#btn-jz-upload-attendance').on('click', function() {
        const d = new frappe.ui.Dialog({
            title: '上传吉众月度考勤表 (Excel)',
            fields: [
                {
                    label: '考勤所属月份',
                    fieldname: 'period_month',
                    fieldtype: 'Data',
                    default: current_month,
                    reqd: 1,
                    description: '格式如 2026-07 或 2026-06'
                },
                {
                    label: '考勤文件 (员工考勤表-*.xlsx)',
                    fieldname: 'file',
                    fieldtype: 'Attach',
                    reqd: 1,
                    description: '支持《员工考勤表-2026年7月.xlsx》等月度全员5行多日打卡表'
                }
            ],
            primary_action_label: '开始解析入库',
            primary_action: function(vals) {
                if (!vals.file) {
                    frappe.msgprint('请先上传考勤 Excel 文件！');
                    return;
                }
                d.hide();
                frappe.show_alert({ message: '正在自动解析考勤打卡工时与倒休抵扣...', indicator: 'blue' });

                frappe.call({
                    method: 'ashan_cn_procurement.services.jizhong_attendance_service.upload_and_parse_attendance',
                    args: {
                        company: COMPANY,
                        period_month: vals.period_month,
                        file_url: vals.file
                    },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint(`考勤解析入库成功！共识别 ${r.message.employee_count} 人，正班工时 ${r.message.total_regular_hours}h，加班 ${r.message.total_ot_1_5 + r.message.total_ot_2_0 + r.message.total_ot_3_0}h，餐补 ${r.message.total_meals} 次。`);
                            current_month = vals.period_month;
                            $('#jz-month-select').val(current_month);
                            load_attendance_data();
                        }
                    }
                });
            }
        });
        d.show();
    });

    $('#btn-jz-download-attendance-file').on('click', function() {
        const url = $(this).attr('data-url');
        if (url) window.open(url);
    });

    // 联动算薪
    $('#btn-jz-sync-calc-payroll').on('click', function() {
        $('.jz-tab-btn[data-tab="payroll"]').click();
        $('#btn-jz-calc-payroll').click();
    });

    // 3. 加载现金发放与配钞点钞表
    function load_cash_data() {
        frappe.call({
            method: 'ashan_cn_procurement.services.jizhong_payroll_service.get_jizhong_payroll_overview',
            args: { company: COMPANY, period_month: current_month },
            callback: function(r) {
                if (!r.message) return;
                const items = r.message.items || [];
                const bSum = r.message.bill_summary || {};

                $('#stat-cash-total').text(fmtMoney(bSum.total_cash || 0));
                $('#stat-b100').text((bSum.bills_100 || 0) + ' 张');
                $('#stat-b50').text((bSum.bills_50 || 0) + ' 张');
                $('#stat-b10').text((bSum.bills_10 || 0) + ' 张');
                $('#stat-b5').text((bSum.bills_5 || 0) + ' 张');
                $('#stat-b1').text((bSum.bills_1 || 0) + ' 张');

                const tbody = $('#tbody-jz-cash');
                tbody.empty();

                let tot_net = 0, tot_cash = 0;
                let t_100 = 0, t_50 = 0, t_10 = 0, t_5 = 0, t_1 = 0;

                items.forEach((it, idx) => {
                    tot_net += flt(it.net_salary);
                    tot_cash += flt(it.cash_pay);
                    t_100 += cint(it.bills_100);
                    t_50 += cint(it.bills_50);
                    t_10 += cint(it.bills_10);
                    t_5 += cint(it.bills_5);
                    t_1 += cint(it.bills_1);

                    tbody.append(`
                        <tr>
                            <td class="jz-freeze-1">${idx + 1}</td>
                            <td class="jz-freeze-2"><strong>${it.employee_no}</strong></td>
                            <td class="jz-freeze-3"><strong>${it.employee_name}</strong></td>
                            <td class="jz-freeze-4 jz-money-cell">${fmtMoney(it.net_salary)}</td>
                            <td class="jz-money-cell" style="font-weight:700; color:#0284c7;">${fmtMoney(it.cash_pay)}</td>
                            <td class="jz-num-cell">${it.bills_100 || 0}</td>
                            <td class="jz-num-cell">${it.bills_50 || 0}</td>
                            <td class="jz-num-cell">${it.bills_10 || 0}</td>
                            <td class="jz-num-cell">${it.bills_5 || 0}</td>
                            <td class="jz-num-cell">${it.bills_1 || 0}</td>
                            <td class="jz-money-cell">${fmtMoney(it.cash_pay)}</td>
                            <td style="color:#cbd5e1; font-style:italic;">[ 签字区 ]</td>
                        </tr>
                    `);
                });

                $('#tfoot-jz-cash').html(`
                    <tr>
                        <td class="jz-freeze-1">合计</td>
                        <td class="jz-freeze-2">-</td>
                        <td class="jz-freeze-3">${items.length} 人</td>
                        <td class="jz-freeze-4 jz-money-cell">${fmtMoney(tot_net)}</td>
                        <td class="jz-money-cell" style="color:#0284c7;">${fmtMoney(tot_cash)}</td>
                        <td class="jz-num-cell">${t_100}</td>
                        <td class="jz-num-cell">${t_50}</td>
                        <td class="jz-num-cell">${t_10}</td>
                        <td class="jz-num-cell">${t_5}</td>
                        <td class="jz-num-cell">${t_1}</td>
                        <td class="jz-money-cell">${fmtMoney(tot_cash)}</td>
                        <td>-</td>
                    </tr>
                `);
            }
        });
    }

    // 4. 加载个人所得税台账
    function load_tax_data() {
        frappe.call({
            method: 'ashan_cn_procurement.services.jizhong_payroll_service.get_jizhong_payroll_overview',
            args: { company: COMPANY, period_month: current_month },
            callback: function(r) {
                if (!r.message) return;
                const items = r.message.items || [];
                const tbody = $('#tbody-jz-tax');
                tbody.empty();

                items.forEach((it, idx) => {
                    tbody.append(`
                        <tr>
                            <td class="jz-freeze-1">${idx + 1}</td>
                            <td class="jz-freeze-2"><strong>${it.employee_no}</strong></td>
                            <td class="jz-freeze-3"><strong>${it.employee_name}</strong></td>
                            <td class="jz-freeze-4">${it.salary_mode}</td>
                            <td class="jz-money-cell">${fmtMoney(it.gross_salary)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.tax_threshold || 5000)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.ss_person_total)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.hf_person_total)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.special_deductions_total)}</td>
                            <td class="jz-money-cell">-</td>
                            <td class="jz-money-cell">-</td>
                            <td class="jz-money-cell">-</td>
                            <td class="jz-money-cell">-</td>
                            <td class="jz-money-cell">-</td>
                            <td class="jz-money-cell">${fmtMoney(it.tax_amount)}</td>
                            <td class="jz-money-cell" style="font-weight:700; color:#d97706;">${fmtMoney(it.tax_amount)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.net_salary)}</td>
                        </tr>
                    `);
                });
            }
        });
    }

    // 5. 加载员工薪酬档案
    function load_employees_data() {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Ashan Employee Salary Profile',
                filters: { company: COMPANY },
                fields: ['*'],
                limit: 100,
                order_by: 'employee_no asc'
            },
            callback: function(r) {
                const list = r.message || [];
                const tbody = $('#tbody-jz-employees');
                tbody.empty();

                list.forEach((it, idx) => {
                    tbody.append(`
                        <tr>
                            <td class="jz-freeze-1">${idx + 1}</td>
                            <td class="jz-freeze-2"><strong>${it.employee_no}</strong></td>
                            <td class="jz-freeze-3"><strong>${it.employee_name}</strong></td>
                            <td class="jz-freeze-4">${it.id_card || '-'}</td>
                            <td>${it.employee_type || '正式工'}</td>
                            <td>${it.employment_status || '在职'}</td>
                            <td>${it.salary_mode}</td>
                            <td class="jz-money-cell">${fmtMoney(it.base_salary)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.post_allowance)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.performance_base)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.meal_allowance || 15)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.social_security_base)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.housing_fund_base)}</td>
                            <td class="jz-money-cell">${fmtMoney(flt(it.deduction_child_education) + flt(it.deduction_continuing_education) + flt(it.deduction_housing_loan) + flt(it.deduction_housing_rent) + flt(it.deduction_elderly_care) + flt(it.deduction_infant_care))}</td>
                        </tr>
                    `);
                });
            }
        });
    }

    // 7. 加载历史薪资穿透 (421条)
    let history_cache = [];
    function load_history_data() {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Ashan Monthly Payroll Settlement',
                filters: { company: COMPANY },
                fields: ['name', 'period_month'],
                order_by: 'period_month desc',
                limit: 50
            },
            callback: function(r) {
                const settlements = r.message || [];
                const select = $('#jz-history-month-filter');
                select.empty();
                select.append('<option value="ALL">全部历史账期</option>');
                settlements.forEach(s => {
                    select.append(`<option value="${s.period_month}">${s.period_month}</option>`);
                });

                fetch_history_items('ALL');
            }
        });
    }

    $('#jz-history-month-filter').on('change', function() {
        fetch_history_items($(this).val());
    });

    function fetch_history_items(selected_month) {
        frappe.call({
            method: 'ashan_cn_procurement.services.jizhong_payroll_service.get_jizhong_history_records',
            args: {
                company: COMPANY,
                period_month: selected_month
            },
            callback: function(r) {
                const items = r.message || [];
                const tbody = $('#tbody-jz-history');
                tbody.empty();

                items.forEach((it, idx) => {
                    const pMonth = it.period_month || (it.parent ? it.parent.replace(`${COMPANY}-`, '') : '');
                    tbody.append(`
                        <tr>
                            <td class="jz-freeze-1">${idx + 1}</td>
                            <td class="jz-freeze-2">${pMonth}</td>
                            <td class="jz-freeze-3"><strong>${it.employee_no}</strong></td>
                            <td class="jz-freeze-4"><strong>${it.employee_name}</strong></td>
                            <td>${it.salary_mode}</td>
                            <td class="jz-money-cell">${fmtMoney(it.base_salary)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.post_allowance)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.performance_salary)}</td>
                            <td class="jz-money-cell" style="font-weight:700;">${fmtMoney(it.gross_salary)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.tax_threshold || 5000)}</td>
                            <td class="jz-money-cell">${fmtMoney(flt(it.ss_person_total) + flt(it.hf_person_total))}</td>
                            <td class="jz-money-cell">${fmtMoney(it.special_deductions_total)}</td>
                            <td class="jz-money-cell" style="color:#d97706;">${fmtMoney(it.tax_amount)}</td>
                            <td class="jz-money-cell" style="color:#ea580c; font-weight:700;">${fmtMoney(it.net_salary)}</td>
                        </tr>
                    `);
                });
            }
        });
    }

    // 默认首帧加载
    load_payroll_data();
};
