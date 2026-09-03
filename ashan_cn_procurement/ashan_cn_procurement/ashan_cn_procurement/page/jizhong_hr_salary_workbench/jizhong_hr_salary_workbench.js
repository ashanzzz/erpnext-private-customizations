// Copyright (c) 2026, Ashan CN Procurement
// 天津吉众科技有限公司 · 人事薪酬综合工作台
// 严格对齐《202606吉众人事综合.xlsm》与《员工考勤表-*.xlsx》规范，单层纯净表头与精确三列冻结体系

frappe.pages['jizhong-hr-salary-workbench'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: '吉众人事薪酬工作台',
        single_column: true
    });

    const COMPANY = "天津吉众科技有限公司";
    let current_month = "2026-06";
    let current_tab = "payroll";
    let payroll_filter_mode = "all"; // all | accounting | non_accounting
    let payroll_col_view = "summary"; // summary (20列精简财务) | detail (32列全要素工时分项)

    const html = `
    <div class="jz-wb-wrapper">
        <!-- 顶部 Header -->
        <div class="jz-header">
            <div>
                <div class="jz-title">
                    <span>天津吉众科技有限公司 · 人事薪酬综合中枢</span>
                    <span class="jz-title-badge">双基准工时 · 倒休冲抵 · 现金五档配钞</span>
                </div>
                <div class="jz-subtitle">
                    结构化打卡工时 (正班+1.5x/2.0x/3.0x+倒休抵扣) · 历史税前累计预扣 · 原始凭证受控归档
                </div>
            </div>
            <div class="jz-header-actions">
                <label class="jz-label-month">核算月份：</label>
                <input type="month" id="jz-month-select" class="form-control jz-month-input" value="2026-06">
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
                    <div class="jz-kpi-val" id="jz-kpi-status"><span class="jz-status-badge jz-status-draft">草稿 / 可测算</span></div>
                    <div class="jz-kpi-sub">在职计薪人员: <strong id="jz-kpi-count">0</strong> 人</div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">实发工资总额</div>
                    <div class="jz-kpi-val jz-text-primary" id="jz-kpi-net">¥ 0.00</div>
                    <div class="jz-kpi-sub">应发总额: <span id="jz-kpi-gross">¥ 0.00</span></div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">代扣税费 (个人部分)</div>
                    <div class="jz-kpi-val jz-text-warn" id="jz-kpi-person-ded">¥ 0.00</div>
                    <div class="jz-kpi-sub">社保个人: <span id="jz-kpi-ss-pers">¥ 0.00</span> | 公积金: <span id="jz-kpi-hf-pers">¥ 0.00</span> | 个税: <span id="jz-kpi-tax">¥ 0.00</span></div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">单位统筹成本</div>
                    <div class="jz-kpi-val jz-text-success" id="jz-kpi-comp-cost">¥ 0.00</div>
                    <div class="jz-kpi-sub">单位社保: <span id="jz-kpi-ss-comp">¥ 0.00</span> | 单位公积金: <span id="jz-kpi-hf-comp">¥ 0.00</span></div>
                </div>
            </div>

            <div class="jz-toolbar">
                <div class="jz-toolbar-left">
                    <div class="jz-segmented-control" id="jz-payroll-person-filter">
                        <button class="jz-segment-btn active" data-mode="all">全部人员</button>
                        <button class="jz-segment-btn" data-mode="regular">正式员工</button>
                        <button class="jz-segment-btn" data-mode="other">其他员工</button>
                        <button class="jz-segment-btn" data-mode="temporary">临时工</button>
                    </div>

                    <div class="jz-segmented-control" id="jz-payroll-col-toggle">
                        <button class="jz-segment-btn active" data-view="summary">精简财务视图</button>
                        <button class="jz-segment-btn" data-view="detail">全要素工时分项</button>
                    </div>

                    <button class="btn btn-primary btn-sm jz-btn-orange" id="btn-jz-calc-payroll">执行月度薪酬核算</button>
                    <button class="btn btn-success btn-sm jz-btn-green" id="btn-jz-lock-payroll">核定锁定 (只读封账)</button>
                    <button class="btn btn-default btn-sm jz-btn-red jz-hidden" id="btn-jz-unlock-payroll">申请反审核解锁</button>
                </div>
                <div class="jz-toolbar-right">
                    <button class="btn btn-default btn-sm" id="btn-jz-export-payroll">导出本月工资表 (Excel)</button>
                </div>
            </div>

            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-payroll">
                    <thead id="thead-jz-payroll"></thead>
                    <tbody id="tbody-jz-payroll">
                        <tr><td colspan="20" class="jz-empty-cell">正在加载吉众薪酬数据...</td></tr>
                    </tbody>
                    <tfoot id="tfoot-jz-payroll"></tfoot>
                </table>
            </div>
        </div>

        <!-- Tab 2: 考勤工时管理 -->
        <div id="jz-tab-attendance" class="jz-tab-content jz-hidden">
            <div class="jz-kpi-grid">
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">考勤总人次 / 状态</div>
                    <div class="jz-kpi-val" id="jz-att-kpi-count">0 人</div>
                    <div class="jz-kpi-sub" id="jz-att-file-status">原始凭证: 未上传</div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">基本正班总工时</div>
                    <div class="jz-kpi-val jz-text-info" id="jz-att-kpi-reg">0.0 h</div>
                    <div class="jz-kpi-sub">倒休抵扣工时: <span id="jz-att-kpi-comp">0.0 h</span></div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">各倍率加班总工时</div>
                    <div class="jz-kpi-val jz-text-primary" id="jz-att-kpi-ot">0.0 h</div>
                    <div class="jz-kpi-sub">1.5x平日: <span id="jz-att-kpi-ot15">0.0 h</span> | 2.0x周末: <span id="jz-att-kpi-ot20">0.0 h</span> | 3.0x节假日: <span id="jz-att-kpi-ot30">0.0 h</span></div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">订餐补贴总次数</div>
                    <div class="jz-kpi-val jz-text-success" id="jz-att-kpi-meals">0 次</div>
                    <div class="jz-kpi-sub">单价: ¥ 15.00 / 份</div>
                </div>
            </div>

            <div class="jz-toolbar">
                <div class="jz-toolbar-left">
                    <button class="btn btn-primary btn-sm jz-btn-blue" id="btn-jz-upload-attendance">上传吉众月度考勤 (Excel)</button>
                    <button class="btn btn-default btn-sm jz-btn-danger-outline" id="btn-jz-clear-attendance">一键清空本月考勤</button>
                    <button class="btn btn-default btn-sm jz-hidden" id="btn-jz-download-attendance-file">下载原始考勤凭证</button>
                    <button class="btn btn-default btn-sm jz-text-primary" id="btn-jz-sync-calc-payroll">按考勤一键核算当月工资</button>
                </div>
                <div class="jz-toolbar-right">
                    <span class="jz-tip-text">支持标准5行格式: 班次、作业时间、加班时间、餐补、备注</span>
                </div>
            </div>

            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-attendance">
                    <thead>
                        <tr>
                            <th class="jz-col-seq">序号</th>
                            <th class="jz-col-no">工号</th>
                            <th class="jz-col-name">姓名</th>
                            <th class="jz-text-center">整天(天)</th>
                            <th class="jz-text-center">半天(天)</th>
                            <th class="jz-text-center">缺勤(天)</th>
                            <th class="jz-text-right">基本正班工时</th>
                            <th class="jz-text-right">1.5倍平日加班</th>
                            <th class="jz-text-right">2.0倍周末加班</th>
                            <th class="jz-text-right">3.0倍节假日加班</th>
                            <th class="jz-text-right">倒休抵扣工时</th>
                            <th class="jz-text-right">餐补次数</th>
                            <th class="jz-text-center">每日打卡明细</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-jz-attendance">
                        <tr><td colspan="13" class="jz-empty-cell">正在加载吉众考勤工时...</td></tr>
                    </tbody>
                    <tfoot id="tfoot-jz-attendance"></tfoot>
                </table>
            </div>
        </div>

        <!-- Tab 3: 现金发放与配钞点钞 -->
        <div id="jz-tab-cash_bills" class="jz-tab-content jz-hidden">
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
                    <span class="jz-tip-text">现金取整算法：RoundUp(实发工资, 0)，严格五档贪心拆分平账</span>
                </div>
            </div>

            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-cash">
                    <thead>
                        <tr>
                            <th class="jz-col-seq">序号</th>
                            <th class="jz-col-no">工号</th>
                            <th class="jz-col-name">姓名</th>
                            <th class="jz-text-right">实发薪资</th>
                            <th class="jz-text-right">现金发放工资</th>
                            <th class="jz-text-right">百元 (¥100)</th>
                            <th class="jz-text-right">五十元 (¥50)</th>
                            <th class="jz-text-right">十元 (¥10)</th>
                            <th class="jz-text-right">五元 (¥5)</th>
                            <th class="jz-text-right">一元 (¥1)</th>
                            <th class="jz-text-right">现金面额合计</th>
                            <th class="jz-text-center">收款签字</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-jz-cash"></tbody>
                    <tfoot id="tfoot-jz-cash"></tfoot>
                </table>
            </div>
        </div>

        <!-- Tab 4: 个人所得税台账 -->
        <div id="jz-tab-tax" class="jz-tab-content jz-hidden">
            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-tax">
                    <thead>
                        <tr>
                            <th class="jz-col-seq">序号</th>
                            <th class="jz-col-no">工号</th>
                            <th class="jz-col-name">姓名</th>
                            <th>计薪方式</th>
                            <th class="jz-text-right">应发薪资</th>
                            <th class="jz-text-right">基本减除费用</th>
                            <th class="jz-text-right">个人社保代扣</th>
                            <th class="jz-text-right">个人公积金</th>
                            <th class="jz-text-right">专项附加扣除</th>
                            <th class="jz-text-right">代扣个税</th>
                            <th class="jz-text-right">实发工资</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-jz-tax"></tbody>
                </table>
            </div>
        </div>

        <!-- Tab 5: 员工薪酬档案 -->
        <div id="jz-tab-employees" class="jz-tab-content jz-hidden">
            <div class="jz-toolbar">
                <div class="jz-toolbar-left">
                    <button class="btn btn-primary btn-sm jz-btn-orange" id="btn-jz-add-emp">新建在职员工档案</button>
                </div>
            </div>
            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-employees">
                    <thead>
                        <tr>
                            <th class="jz-col-seq">序号</th>
                            <th class="jz-col-no">工号</th>
                            <th class="jz-col-name">姓名</th>
                            <th>身份证号</th>
                            <th>用工性质</th>
                            <th>在职状态</th>
                            <th>计薪方式</th>
                            <th class="jz-text-right">基本工资</th>
                            <th class="jz-text-right">岗位津贴</th>
                            <th class="jz-text-right">绩效基数</th>
                            <th class="jz-text-right">餐补单价</th>
                            <th class="jz-text-right">社保基数</th>
                            <th class="jz-text-right">公积金基数</th>
                            <th class="jz-text-right">专项附加扣除</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-jz-employees"></tbody>
                </table>
            </div>
        </div>

        <!-- Tab 6: 社保公积金配置 -->
        <div id="jz-tab-insurance" class="jz-tab-content jz-hidden">
            <div class="jz-toolbar">
                <div class="jz-toolbar-left">
                    <button class="btn btn-primary btn-sm jz-btn-orange" id="btn-jz-edit-insurance">修改吉众社保公积金费率</button>
                    <button class="btn btn-default btn-sm" id="btn-jz-open-insurance-form">在原生表单中查看</button>
                </div>
                <div class="jz-toolbar-right">
                    <span class="jz-tip-text" id="jz-ins-docname-tip">配置对象：天津吉众科技有限公司-2026</span>
                </div>
            </div>
            <div class="jz-config-box">
                <h4 class="jz-config-title">天津吉众科技有限公司 · 专属社保公积金标准</h4>
                <div class="jz-config-grid" id="jz-ins-grid">
                    <div><strong>工伤保险单位费率:</strong> <span id="jz-ins-injury">0.35%</span></div>
                    <div><strong>养老保险比例:</strong> 个人 <span id="jz-ins-pension-p">8.00%</span> / 单位 <span id="jz-ins-pension-c">16.00%</span></div>
                    <div><strong>医疗保险比例:</strong> 个人 <span id="jz-ins-medical-p">2.00%</span> / 单位 <span id="jz-ins-medical-c">10.00%</span></div>
                    <div><strong>失业保险比例:</strong> 个人 <span id="jz-ins-unemp-p">0.50%</span> / 单位 <span id="jz-ins-unemp-c">0.50%</span></div>
                    <div><strong>生育保险比例:</strong> 单位 <span id="jz-ins-maternity">0.50%</span></div>
                    <div><strong>住房公积金比例:</strong> 个人 <span id="jz-ins-hf-p">5.00%</span> / 单位 <span id="jz-ins-hf-c">5.00%</span></div>
                    <div><strong>大额医疗救助:</strong> 1/4/7/10月为 21.00元，其余月份 22.00元</div>
                    <div><strong>个税基本减除费用:</strong> ¥ 5,000.00 / 月</div>
                </div>
            </div>
        </div>

        <!-- Tab 7: 历史薪资穿透 (421条) -->
        <div id="jz-tab-history" class="jz-tab-content jz-hidden">
            <div class="jz-toolbar">
                <div class="jz-toolbar-left">
                    <label class="jz-filter-label">过滤历史账期：</label>
                    <select id="jz-history-month-filter" class="form-control jz-filter-select">
                        <option value="ALL">全部历史 (421条)</option>
                    </select>
                </div>
            </div>
            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-history">
                    <thead>
                        <tr>
                            <th class="jz-col-seq">序号</th>
                            <th class="jz-col-no jz-text-center">账期</th>
                            <th class="jz-col-no jz-text-center">工号</th>
                            <th class="jz-col-name">姓名</th>
                            <th>计薪方式</th>
                            <th class="jz-text-right">基本工资</th>
                            <th class="jz-text-right">岗位津贴</th>
                            <th class="jz-text-right">绩效奖金</th>
                            <th class="jz-text-right">应发薪资</th>
                            <th class="jz-text-right">免征额</th>
                            <th class="jz-text-right">专项扣除</th>
                            <th class="jz-text-right">附加扣除</th>
                            <th class="jz-text-right">代扣个税</th>
                            <th class="jz-text-right">实发薪资</th>
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
        return n.toFixed(1) + ' h';
    }

    // Tab 切换逻辑
    $('.jz-tab-btn').on('click', function() {
        const tab = $(this).data('tab');
        $('.jz-tab-btn').removeClass('active');
        $(this).addClass('active');
        $('.jz-tab-content').addClass('jz-hidden');
        $(`#jz-tab-${tab}`).removeClass('jz-hidden');
        current_tab = tab;

        if (tab === 'payroll') load_payroll_data();
        else if (tab === 'attendance') load_attendance_data();
        else if (tab === 'cash_bills') load_cash_data();
        else if (tab === 'tax') load_tax_data();
        else if (tab === 'employees') load_employees_data();
        else if (tab === 'insurance') load_insurance_data();
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
        else if (current_tab === 'insurance') load_insurance_data();
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
                    $('#btn-jz-lock-payroll').addClass('jz-hidden');
                    $('#btn-jz-unlock-payroll').removeClass('jz-hidden');
                } else {
                    $('#jz-kpi-status').html('<span class="jz-status-badge jz-status-draft">草稿 / 可测算</span>');
                    $('#btn-jz-lock-payroll').removeClass('jz-hidden');
                    $('#btn-jz-unlock-payroll').addClass('jz-hidden');
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

    // 渲染 Payroll Table 表头与数据行
    function render_payroll_table() {
        const thead = $('#thead-jz-payroll');
        const tbody = $('#tbody-jz-payroll');
        const tfoot = $('#tfoot-jz-payroll');
        thead.empty();
        tbody.empty();
        tfoot.empty();

        const isDetail = (payroll_col_view === 'detail');

        // 1. 单层纯净表头 (严格一行文本，杜绝多层药丸卡片)
        if (isDetail) {
            thead.html(`
                <tr>
                    <th class="jz-col-seq">序号</th>
                    <th class="jz-col-no">工号</th>
                    <th class="jz-col-name">姓名</th>
                    <th>用工性质</th>
                    <th>计薪方式</th>
                    <th class="jz-text-right">基本工资</th>
                    <th class="jz-text-right">岗位津贴</th>
                    <th class="jz-text-right">绩效基数</th>
                    <th class="jz-text-right">出勤工时</th>
                    <th class="jz-text-right">1.5倍工时</th>
                    <th class="jz-text-right">2倍工时</th>
                    <th class="jz-text-right">3倍工时</th>
                    <th class="jz-text-right">倒休工时</th>
                    <th class="jz-text-right">餐补次数</th>
                    <th class="jz-text-right">基本工时工资</th>
                    <th class="jz-text-right">1.5倍工资</th>
                    <th class="jz-text-right">2倍工资</th>
                    <th class="jz-text-right">3倍工资</th>
                    <th class="jz-text-right">基本补贴</th>
                    <th class="jz-text-right">绩效工资</th>
                    <th class="jz-text-right">餐补工资</th>
                    <th class="jz-text-right">工资调整</th>
                    <th class="jz-text-right">应发薪资</th>
                    <th class="jz-text-right">个人社保</th>
                    <th class="jz-text-right">个人公积金</th>
                    <th class="jz-text-right">代扣个税</th>
                    <th class="jz-text-right">个人扣除合计</th>
                    <th class="jz-text-right">实发薪资</th>
                    <th class="jz-text-right">现金发放取整</th>
                    <th class="jz-text-right">单位社保统筹</th>
                    <th class="jz-text-right">单位公积金</th>
                    <th class="jz-text-right">公司成本合计</th>
                </tr>
            `);
        } else {
            // 精简财务视图 (20 列，纯净清爽)
            thead.html(`
                <tr>
                    <th class="jz-col-seq">序号</th>
                    <th class="jz-col-no">工号</th>
                    <th class="jz-col-name">姓名</th>
                    <th>用工性质</th>
                    <th>计薪方式</th>
                    <th class="jz-text-right">基本工资</th>
                    <th class="jz-text-right">出勤工时</th>
                    <th class="jz-text-right">加班费合计</th>
                    <th class="jz-text-right">津贴与绩效</th>
                    <th class="jz-text-right">餐补工资</th>
                    <th class="jz-text-right">工资调整</th>
                    <th class="jz-text-right">应发薪资</th>
                    <th class="jz-text-right">个人社保</th>
                    <th class="jz-text-right">个人公积金</th>
                    <th class="jz-text-right">代扣个税</th>
                    <th class="jz-text-right">个人扣除合计</th>
                    <th class="jz-text-right">实发薪资</th>
                    <th class="jz-text-right">现金发放</th>
                    <th class="jz-text-right">单位统筹</th>
                    <th class="jz-text-right">公司总成本</th>
                </tr>
            `);
        }

        let filtered = payroll_cache.filter(it => {
            const type = String(it.employee_type || '正式工').trim();
            if (payroll_filter_mode === 'regular') {
                // 正式员工：正式工、返聘工（不含带“其他”的工种）
                return (type.includes('正式工') || type.includes('返聘')) && !type.includes('其他');
            } else if (payroll_filter_mode === 'other') {
                // 其他员工：工种带“其他”的 (如 其他-正式工、其他-返聘工、其他-管理 等)
                return type.includes('其他');
            } else if (payroll_filter_mode === 'temporary') {
                // 临时工：临时工、兼职等
                return type.includes('临时') || type.includes('兼职');
            }
            return true; // 全部人员
        });

        const colSpanTotal = isDetail ? 32 : 20;

        if (filtered.length === 0) {
            tbody.html(`<tr><td colspan="${colSpanTotal}" class="jz-empty-cell">该期间暂无薪酬结算记录，请点击上方“执行月度薪酬核算”。</td></tr>`);
            return;
        }

        let tot_basic_hrs = 0, tot_ot_hrs = 0, tot_ot_pay = 0, tot_allow_perf = 0;
        let tot_sal_meal = 0, tot_sal_adj = 0, tot_gross = 0;
        let tot_ss_pers = 0, tot_hf_pers = 0, tot_tax = 0, tot_pers_ded = 0, tot_net = 0, tot_cash = 0;
        let tot_comp_ins = 0, tot_comp_cost = 0;

        // 全要素累加变量
        let tot_ot15_hrs = 0, tot_ot20_hrs = 0, tot_ot30_hrs = 0, tot_comp_hrs = 0, tot_meals = 0;
        let tot_sal_basic = 0, tot_sal_ot15 = 0, tot_sal_ot20 = 0, tot_sal_ot30 = 0;
        let tot_sal_sub = 0, tot_sal_perf = 0, tot_ss_comp = 0, tot_hf_comp = 0;

        filtered.forEach((it, idx) => {
            const bHrs = flt(it.work_hours);
            const ot15 = flt(it.overtime_regular_1_5);
            const ot20 = flt(it.overtime_weekend_2_0);
            const ot30 = flt(it.overtime_holiday_3_0);
            const cLeave = flt(it.leave_compensatory_hours);
            const mCount = cint(it.meal_count);

            const sBasic = flt(it.salary_basic_hours);
            const sOt15 = flt(it.salary_overtime_1_5);
            const sOt20 = flt(it.salary_overtime_2_0);
            const sOt30 = flt(it.salary_overtime_3_0);
            const otPay = flt(sOt15 + sOt20 + sOt30, 2);

            const sSub = flt(it.salary_basic_subsidy);
            const sPerf = flt(it.salary_performance);
            const allowPerf = flt(sSub + sPerf, 2);

            const sMeal = flt(it.salary_meal_subsidy);
            const sAdj = flt(it.salary_adjustment);
            const gross = flt(it.gross_salary);

            const ssP = flt(it.ss_person_total);
            const hfP = flt(it.hf_person_total);
            const tax = flt(it.tax_amount);
            const pCost = flt(it.person_cost_total);
            const net = flt(it.net_salary);
            const cash = flt(it.cash_pay);

            const ssC = flt(it.ss_company_total);
            const hfC = flt(it.hf_company_total);
            const cCost = flt(it.company_cost_total);

            // 汇总
            tot_basic_hrs += bHrs;
            tot_ot_hrs += (ot15 + ot20 + ot30);
            tot_ot_pay += otPay;
            tot_allow_perf += allowPerf;
            tot_sal_meal += sMeal;
            tot_sal_adj += sAdj;
            tot_gross += gross;

            tot_ss_pers += ssP;
            tot_hf_pers += hfP;
            tot_tax += tax;
            tot_pers_ded += pCost;
            tot_net += net;
            tot_cash += cash;
            tot_comp_ins += (ssC + hfC);
            tot_comp_cost += cCost;

            if (isDetail) {
                tot_ot15_hrs += ot15;
                tot_ot20_hrs += ot20;
                tot_ot30_hrs += ot30;
                tot_comp_hrs += cLeave;
                tot_meals += mCount;
                tot_sal_basic += sBasic;
                tot_sal_ot15 += sOt15;
                tot_sal_ot20 += sOt20;
                tot_sal_ot30 += sOt30;
                tot_sal_sub += sSub;
                tot_sal_perf += sPerf;
                tot_ss_comp += ssC;
                tot_hf_comp += hfC;

                tbody.append(`
                    <tr>
                        <td class="jz-col-seq">${idx + 1}</td>
                        <td class="jz-col-no"><strong>${it.employee_no}</strong></td>
                        <td class="jz-col-name"><strong>${it.employee_name}</strong></td>
                        <td>${it.employee_type || '正式工'}</td>
                        <td>${it.salary_mode}</td>
                        <td class="jz-money-cell">${fmtMoney(it.base_salary)}</td>
                        <td class="jz-money-cell">${fmtMoney(it.post_allowance)}</td>
                        <td class="jz-money-cell">${fmtMoney(it.performance_salary)}</td>
                        <td class="jz-num-cell">${fmtHours(bHrs)}</td>
                        <td class="jz-num-cell">${fmtHours(ot15)}</td>
                        <td class="jz-num-cell">${fmtHours(ot20)}</td>
                        <td class="jz-num-cell">${fmtHours(ot30)}</td>
                        <td class="jz-num-cell">${fmtHours(cLeave)}</td>
                        <td class="jz-num-cell">${mCount} 次</td>
                        <td class="jz-money-cell">${fmtMoney(sBasic)}</td>
                        <td class="jz-money-cell">${fmtMoney(sOt15)}</td>
                        <td class="jz-money-cell">${fmtMoney(sOt20)}</td>
                        <td class="jz-money-cell">${fmtMoney(sOt30)}</td>
                        <td class="jz-money-cell">${fmtMoney(sSub)}</td>
                        <td class="jz-money-cell">${fmtMoney(sPerf)}</td>
                        <td class="jz-money-cell">${fmtMoney(sMeal)}</td>
                        <td class="jz-money-cell">${fmtMoney(sAdj)}</td>
                        <td class="jz-money-cell jz-money-bold">${fmtMoney(gross)}</td>
                        <td class="jz-money-cell">${fmtMoney(ssP)}</td>
                        <td class="jz-money-cell">${fmtMoney(hfP)}</td>
                        <td class="jz-money-cell">${fmtMoney(tax)}</td>
                        <td class="jz-money-cell">${fmtMoney(pCost)}</td>
                        <td class="jz-money-cell jz-money-primary">${fmtMoney(net)}</td>
                        <td class="jz-money-cell jz-money-cash">${fmtMoney(cash)}</td>
                        <td class="jz-money-cell">${fmtMoney(ssC)}</td>
                        <td class="jz-money-cell">${fmtMoney(hfC)}</td>
                        <td class="jz-money-cell jz-money-cost">${fmtMoney(cCost)}</td>
                    </tr>
                `);
            } else {
                tbody.append(`
                    <tr>
                        <td class="jz-col-seq">${idx + 1}</td>
                        <td class="jz-col-no"><strong>${it.employee_no}</strong></td>
                        <td class="jz-col-name"><strong>${it.employee_name}</strong></td>
                        <td>${it.employee_type || '正式工'}</td>
                        <td>${it.salary_mode}</td>
                        <td class="jz-money-cell">${fmtMoney(it.base_salary)}</td>
                        <td class="jz-num-cell">${fmtHours(bHrs)}</td>
                        <td class="jz-money-cell">${fmtMoney(otPay)}</td>
                        <td class="jz-money-cell">${fmtMoney(allowPerf)}</td>
                        <td class="jz-money-cell">${fmtMoney(sMeal)}</td>
                        <td class="jz-money-cell">${fmtMoney(sAdj)}</td>
                        <td class="jz-money-cell jz-money-bold">${fmtMoney(gross)}</td>
                        <td class="jz-money-cell">${fmtMoney(ssP)}</td>
                        <td class="jz-money-cell">${fmtMoney(hfP)}</td>
                        <td class="jz-money-cell">${fmtMoney(tax)}</td>
                        <td class="jz-money-cell">${fmtMoney(pCost)}</td>
                        <td class="jz-money-cell jz-money-primary">${fmtMoney(net)}</td>
                        <td class="jz-money-cell jz-money-cash">${fmtMoney(cash)}</td>
                        <td class="jz-money-cell">${fmtMoney(ssC + hfC)}</td>
                        <td class="jz-money-cell jz-money-cost">${fmtMoney(cCost)}</td>
                    </tr>
                `);
            }
        });

        // 底部合计行
        if (isDetail) {
            tfoot.html(`
                <tr>
                    <td colspan="3" class="jz-col-foot-label">合计 · 本表 ${filtered.length} 人</td>
                    <td>-</td>
                    <td>-</td>
                    <td class="jz-money-cell">-</td>
                    <td class="jz-money-cell">-</td>
                    <td class="jz-money-cell">-</td>
                    <td class="jz-num-cell">${fmtHours(tot_basic_hrs)}</td>
                    <td class="jz-num-cell">${fmtHours(tot_ot15_hrs)}</td>
                    <td class="jz-num-cell">${fmtHours(tot_ot20_hrs)}</td>
                    <td class="jz-num-cell">${fmtHours(tot_ot30_hrs)}</td>
                    <td class="jz-num-cell">${fmtHours(tot_comp_hrs)}</td>
                    <td class="jz-num-cell">${tot_meals} 次</td>
                    <td class="jz-money-cell">${fmtMoney(tot_sal_basic)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_sal_ot15)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_sal_ot20)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_sal_ot30)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_sal_sub)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_sal_perf)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_sal_meal)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_sal_adj)}</td>
                    <td class="jz-money-cell jz-money-bold">${fmtMoney(tot_gross)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_ss_pers)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_hf_pers)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_tax)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_pers_ded)}</td>
                    <td class="jz-money-cell jz-money-primary">${fmtMoney(tot_net)}</td>
                    <td class="jz-money-cell jz-money-cash">${fmtMoney(tot_cash)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_ss_comp)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_hf_comp)}</td>
                    <td class="jz-money-cell jz-money-cost">${fmtMoney(tot_comp_cost)}</td>
                </tr>
            `);
        } else {
            tfoot.html(`
                <tr>
                    <td colspan="3" class="jz-col-foot-label">合计 · 本表 ${filtered.length} 人</td>
                    <td>-</td>
                    <td>-</td>
                    <td class="jz-money-cell">-</td>
                    <td class="jz-num-cell">${fmtHours(tot_basic_hrs)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_ot_pay)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_allow_perf)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_sal_meal)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_sal_adj)}</td>
                    <td class="jz-money-cell jz-money-bold">${fmtMoney(tot_gross)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_ss_pers)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_hf_pers)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_tax)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_pers_ded)}</td>
                    <td class="jz-money-cell jz-money-primary">${fmtMoney(tot_net)}</td>
                    <td class="jz-money-cell jz-money-cash">${fmtMoney(tot_cash)}</td>
                    <td class="jz-money-cell">${fmtMoney(tot_comp_ins)}</td>
                    <td class="jz-money-cell jz-money-cost">${fmtMoney(tot_comp_cost)}</td>
                </tr>
            `);
        }
    }

    // 分段控件事件绑定
    $('#jz-payroll-person-filter .jz-segment-btn').on('click', function() {
        $('#jz-payroll-person-filter .jz-segment-btn').removeClass('active');
        $(this).addClass('active');
        payroll_filter_mode = $(this).data('mode');
        render_payroll_table();
    });

    $('#jz-payroll-col-toggle .jz-segment-btn').on('click', function() {
        $('#jz-payroll-col-toggle .jz-segment-btn').removeClass('active');
        $(this).addClass('active');
        payroll_col_view = $(this).data('view');
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
                    $('#jz-att-file-status').html(`凭证已归档: <a href="${summary.attendance_file}" target="_blank" class="jz-text-info">查看文件</a>`);
                    $('#btn-jz-download-attendance-file').removeClass('jz-hidden').attr('data-url', summary.attendance_file);
                } else {
                    $('#jz-att-file-status').text('原始凭证: 未上传');
                    $('#btn-jz-download-attendance-file').addClass('jz-hidden');
                }

                if (records.length === 0) {
                    $('#btn-jz-clear-attendance').prop('disabled', true).addClass('disabled');
                } else {
                    $('#btn-jz-clear-attendance').prop('disabled', false).removeClass('disabled');
                }

                render_attendance_table();
            }
        });
    }

    function render_attendance_table() {
        const tbody = $('#tbody-jz-attendance');
        tbody.empty();

        if (attendance_cache.length === 0) {
            tbody.html('<tr><td colspan="13" class="jz-empty-cell">该月份尚未上传考勤表，请点击“上传吉众月度考勤 (Excel)”按钮。</td></tr>');
            $('#tfoot-jz-attendance').empty();
            return;
        }

        let tot_reg = 0, tot_15 = 0, tot_20 = 0, tot_30 = 0, tot_comp = 0, tot_m = 0;

        attendance_cache.forEach((it, idx) => {
            tot_reg += flt(it.work_hours_regular);
            tot_15 += flt(it.overtime_regular_1_5);
            tot_20 += flt(it.overtime_weekend_2_0);
            tot_30 += flt(it.overtime_holiday_3_0);
            tot_comp += flt(it.leave_compensatory_hours);
            tot_m += cint(it.meal_count);

            tbody.append(`
                <tr class="jz-att-row" data-no="${it.employee_no}">
                    <td class="jz-col-seq">${idx + 1}</td>
                    <td class="jz-col-no"><strong>${it.employee_no}</strong></td>
                    <td class="jz-col-name"><strong>${it.employee_name}</strong></td>
                    <td class="jz-text-center">${it.attendance_days || 0}</td>
                    <td class="jz-text-center">${it.half_days || 0}</td>
                    <td class="jz-text-center">${it.absent_days || 0}</td>
                    <td class="jz-num-cell jz-text-info">${fmtHours(it.work_hours_regular)}</td>
                    <td class="jz-num-cell">${fmtHours(it.overtime_regular_1_5)}</td>
                    <td class="jz-num-cell">${fmtHours(it.overtime_weekend_2_0)}</td>
                    <td class="jz-num-cell">${fmtHours(it.overtime_holiday_3_0)}</td>
                    <td class="jz-num-cell jz-text-muted">${fmtHours(it.leave_compensatory_hours)}</td>
                    <td class="jz-num-cell jz-text-success">${it.meal_count || 0} 次</td>
                    <td class="jz-text-center">
                        <button class="btn btn-default btn-xs btn-toggle-daily" data-no="${it.employee_no}">展开明细</button>
                    </td>
                </tr>
                <tr class="jz-att-detail-tr jz-hidden" id="detail-${it.employee_no}">
                    <td colspan="13" class="jz-detail-td">
                        <div class="jz-attendance-detail-box" id="detail-box-${it.employee_no}"></div>
                    </td>
                </tr>
            `);
        });

        $('#tfoot-jz-attendance').html(`
            <tr>
                <td colspan="3" class="jz-col-foot-label">合计 (${attendance_cache.length}人)</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td class="jz-num-cell jz-text-info">${fmtHours(tot_reg)}</td>
                <td class="jz-num-cell">${fmtHours(tot_15)}</td>
                <td class="jz-num-cell">${fmtHours(tot_20)}</td>
                <td class="jz-num-cell">${fmtHours(tot_30)}</td>
                <td class="jz-num-cell">${fmtHours(tot_comp)}</td>
                <td class="jz-num-cell jz-text-success">${tot_m} 次</td>
                <td>-</td>
            </tr>
        `);

        // 展开打卡明细事件
        $('.btn-toggle-daily').on('click', function() {
            const empNo = $(this).data('no');
            const tr = $(`#detail-${empNo}`);
            const btn = $(this);

            if (!tr.hasClass('jz-hidden')) {
                tr.addClass('jz-hidden');
                btn.text('展开明细');
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
                                    <div class="jz-tip-text">${d.shift || '-'}</div>
                                    <div class="jz-day-card-hours">${d.work_hours > 0 ? flt(d.work_hours).toFixed(1) + 'h' : '0'}</div>
                                    <div class="jz-day-card-ot">${d.overtime > 0 ? '+' + flt(d.overtime).toFixed(1) + 'h' : ''}</div>
                                    <div class="jz-text-success">${d.meal > 0 ? d.meal + '餐' : ''}</div>
                                </div>
                            `;
                        });
                        cardsHtml += '</div>';
                        $(`#detail-box-${empNo}`).html(cardsHtml);
                    } catch(e) {}
                }
                tr.removeClass('jz-hidden');
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

    // 一键清空当月考勤记录
    $('#btn-jz-clear-attendance').on('click', function() {
        if (!current_month) {
            frappe.msgprint('请先选择考勤月份！');
            return;
        }
        if (!attendance_cache || attendance_cache.length === 0) {
            frappe.msgprint(`当前月份（${current_month}）暂无考勤记录，无需清空。`);
            return;
        }

        frappe.confirm(
            `确定要一键清空【${current_month}】的全部考勤工时记录吗？<br><br><span class="text-danger">注意：此操作将清空该月份所有员工（共 ${attendance_cache.length} 人）的正班工时、加班工时、倒休抵扣、餐补及每日打卡明细，清空后可重新上传新的考勤 Excel。</span>`,
            function() {
                frappe.call({
                    method: 'ashan_cn_procurement.services.jizhong_attendance_service.clear_jizhong_attendance_month',
                    args: {
                        company: COMPANY,
                        period_month: current_month
                    },
                    freeze: true,
                    freeze_message: '正在清空本月考勤工时记录...',
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.show_alert({
                                message: `已成功清空 ${current_month} 月考勤记录（共删除 ${r.message.deleted_count} 条）！现在可以重新上传考勤 Excel。`,
                                indicator: 'green'
                            }, 5);
                            load_attendance_data();
                        }
                    }
                });
            }
        );
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
                            <td class="jz-col-seq">${idx + 1}</td>
                            <td class="jz-col-no"><strong>${it.employee_no}</strong></td>
                            <td class="jz-col-name"><strong>${it.employee_name}</strong></td>
                            <td class="jz-money-cell">${fmtMoney(it.net_salary)}</td>
                            <td class="jz-money-cell jz-money-cash">${fmtMoney(it.cash_pay)}</td>
                            <td class="jz-num-cell">${it.bills_100 || 0}</td>
                            <td class="jz-num-cell">${it.bills_50 || 0}</td>
                            <td class="jz-num-cell">${it.bills_10 || 0}</td>
                            <td class="jz-num-cell">${it.bills_5 || 0}</td>
                            <td class="jz-num-cell">${it.bills_1 || 0}</td>
                            <td class="jz-money-cell jz-money-bold">${fmtMoney(it.cash_pay)}</td>
                            <td class="jz-sign-cell">[ 签字区 ]</td>
                        </tr>
                    `);
                });

                $('#tfoot-jz-cash').html(`
                    <tr>
                        <td colspan="3" class="jz-col-foot-label">合计 (${items.length}人)</td>
                        <td class="jz-money-cell">${fmtMoney(tot_net)}</td>
                        <td class="jz-money-cell jz-money-cash">${fmtMoney(tot_cash)}</td>
                        <td class="jz-num-cell">${t_100}</td>
                        <td class="jz-num-cell">${t_50}</td>
                        <td class="jz-num-cell">${t_10}</td>
                        <td class="jz-num-cell">${t_5}</td>
                        <td class="jz-num-cell">${t_1}</td>
                        <td class="jz-money-cell jz-money-bold">${fmtMoney(tot_cash)}</td>
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
                            <td class="jz-col-seq">${idx + 1}</td>
                            <td class="jz-col-no"><strong>${it.employee_no}</strong></td>
                            <td class="jz-col-name"><strong>${it.employee_name}</strong></td>
                            <td>${it.salary_mode}</td>
                            <td class="jz-money-cell jz-money-bold">${fmtMoney(it.gross_salary)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.tax_threshold || 5000)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.ss_person_total)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.hf_person_total)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.special_deductions_total)}</td>
                            <td class="jz-money-cell jz-text-warn">${fmtMoney(it.tax_amount)}</td>
                            <td class="jz-money-cell jz-money-primary">${fmtMoney(it.net_salary)}</td>
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
                            <td class="jz-col-seq">${idx + 1}</td>
                            <td class="jz-col-no"><strong>${it.employee_no}</strong></td>
                            <td class="jz-col-name"><strong>${it.employee_name}</strong></td>
                            <td>${it.id_card || '-'}</td>
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
                select.append('<option value="ALL">全部历史 (421条)</option>');
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
                            <td class="jz-col-seq">${idx + 1}</td>
                            <td class="jz-col-no jz-text-center">${pMonth}</td>
                            <td class="jz-col-no jz-text-center jz-hist-col-empno"><strong>${it.employee_no}</strong></td>
                            <td class="jz-col-name jz-hist-col-empname"><strong>${it.employee_name}</strong></td>
                            <td>${it.salary_mode}</td>
                            <td class="jz-money-cell">${fmtMoney(it.base_salary)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.post_allowance)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.performance_salary)}</td>
                            <td class="jz-money-cell jz-money-bold">${fmtMoney(it.gross_salary)}</td>
                            <td class="jz-money-cell">${fmtMoney(it.tax_threshold || 5000)}</td>
                            <td class="jz-money-cell">${fmtMoney(flt(it.ss_person_total) + flt(it.hf_person_total))}</td>
                            <td class="jz-money-cell">${fmtMoney(it.special_deductions_total)}</td>
                            <td class="jz-money-cell jz-text-warn">${fmtMoney(it.tax_amount)}</td>
                            <td class="jz-money-cell jz-money-primary">${fmtMoney(it.net_salary)}</td>
                        </tr>
                    `);
                });
            }
        });
    }

    // 6. 加载吉众专属社保公积金配置
    let jz_insurance_cache = null;
    function load_insurance_data() {
        const year = current_month ? current_month.split('-')[0] : '2026';
        frappe.call({
            method: 'ashan_cn_procurement.services.jizhong_payroll_service.get_jizhong_insurance_setting',
            args: { year: year },
            callback: function(r) {
                if (!r.message) return;
                jz_insurance_cache = r.message;
                const d = r.message;
                $('#jz-ins-docname-tip').text(`配置对象：${d.name || COMPANY + '-' + year}`);
                $('#jz-ins-injury').text(flt(d.ss_company_injury, 2) + '%');
                $('#jz-ins-pension-p').text(flt(d.ss_person_pension, 2) + '%');
                $('#jz-ins-pension-c').text(flt(d.ss_company_pension, 2) + '%');
                $('#jz-ins-medical-p').text(flt(d.ss_person_medical, 2) + '%');
                $('#jz-ins-medical-c').text(flt(d.ss_company_medical, 2) + '%');
                $('#jz-ins-unemp-p').text(flt(d.ss_person_unemployment, 2) + '%');
                $('#jz-ins-unemp-c').text(flt(d.ss_company_unemployment, 2) + '%');
                $('#jz-ins-maternity').text(flt(d.ss_company_other_medical, 2) + '%');
                $('#jz-ins-hf-p').text(flt(d.hf_person_rate, 2) + '%');
                $('#jz-ins-hf-c').text(flt(d.hf_company_rate, 2) + '%');
            }
        });
    }

    $('#btn-jz-open-insurance-form').on('click', function() {
        if (jz_insurance_cache && jz_insurance_cache.name) {
            frappe.set_route('Form', 'Ashan Insurance Setting', jz_insurance_cache.name);
        }
    });

    $('#btn-jz-edit-insurance').on('click', function() {
        if (!jz_insurance_cache) return;
        const d = jz_insurance_cache;
        const dlg = new frappe.ui.Dialog({
            title: `修改吉众专属社保公积金费率 (${d.effective_year || 2026}年)`,
            fields: [
                { fieldname: 'ss_company_injury', fieldtype: 'Percent', label: '单位工伤保险比例 (%)', default: d.ss_company_injury },
                { fieldname: 'ss_company_pension', fieldtype: 'Percent', label: '单位基本养老比例 (%)', default: d.ss_company_pension },
                { fieldname: 'ss_person_pension', fieldtype: 'Percent', label: '个人基本养老比例 (%)', default: d.ss_person_pension },
                { fieldname: 'ss_company_medical', fieldtype: 'Percent', label: '单位基本医疗比例 (%)', default: d.ss_company_medical },
                { fieldname: 'ss_person_medical', fieldtype: 'Percent', label: '个人基本医疗比例 (%)', default: d.ss_person_medical },
                { fieldname: 'hf_company_rate', fieldtype: 'Percent', label: '单位公积金比例 (%)', default: d.hf_company_rate },
                { fieldname: 'hf_person_rate', fieldtype: 'Percent', label: '个人公积金比例 (%)', default: d.hf_person_rate }
            ],
            primary_action_label: '保存费率',
            primary_action: function(vals) {
                dlg.hide();
                frappe.call({
                    method: 'ashan_cn_procurement.services.jizhong_payroll_service.update_jizhong_insurance_setting',
                    args: {
                        year: d.effective_year || 2026,
                        values: JSON.stringify(vals)
                    },
                    callback: function(res) {
                        if (res.message && res.message.success) {
                            frappe.msgprint('吉众专属社保公积金费率已成功保存并立即生效！');
                            load_insurance_data();
                        }
                    }
                });
            }
        });
        dlg.show();
    });

    // 默认首帧加载
    load_payroll_data();
};
