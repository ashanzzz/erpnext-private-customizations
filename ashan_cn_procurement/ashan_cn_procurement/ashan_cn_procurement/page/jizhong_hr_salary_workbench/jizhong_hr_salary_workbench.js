frappe.pages['jizhong-hr-salary-workbench'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: '⚡ 吉众人事薪酬工作台*',
        single_column: true
    });

    const COMPANY = "天津吉众科技有限公司";
    let current_month = "2026-06";
    let current_tab = "payroll"; // payroll | employees | insurance | attendance

    const html = `
    <div class="jz-wb-wrapper">
        <!-- 顶部 Header -->
        <div class="jz-header">
            <div>
                <div class="jz-title">
                    <span>⚡ 天津吉众科技有限公司 · 人事薪酬综合中枢</span>
                </div>
                <div class="jz-subtitle">
                    结构化薪资体系 (底薪+岗位津贴+绩效+各项补贴) · 独立工伤社保与公积金 · 月度核定锁定与归档
                </div>
            </div>
            <div style="display: flex; gap: 10px; align-items: center;">
                <label style="font-size: 13px; font-weight: 600; color: #475569; margin: 0;">核算月份：</label>
                <input type="month" id="jz-month-select" class="form-control" style="width: 140px; display: inline-block; font-weight: 600;" value="2026-06">
                <button class="btn btn-default btn-sm" id="btn-jz-refresh-all">🔄 刷新数据</button>
            </div>
        </div>

        <!-- 4大业务 Tab -->
        <div class="jz-nav-tabs">
            <button class="jz-tab-btn active" data-tab="payroll">📊 1. 月度薪酬核定结算</button>
            <button class="jz-tab-btn" data-tab="employees">👥 2. 吉众员工薪酬档案</button>
            <button class="jz-tab-btn" data-tab="insurance">⚙️ 3. 吉众社保公积金配置</button>
            <button class="jz-tab-btn" data-tab="attendance">📅 4. 吉众当月考勤工时</button>
        </div>

        <!-- Tab 1: 月度薪酬核定结算 -->
        <div id="jz-tab-payroll" class="jz-tab-content">
            <!-- 概览 KPI -->
            <div class="jz-kpi-grid">
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">核定状态 / 人数</div>
                    <div class="jz-kpi-val" id="jz-kpi-status"><span class="jz-status-badge jz-status-draft">草稿 / 未核定</span></div>
                    <div class="jz-kpi-sub">共 <strong id="jz-kpi-count">0</strong> 位在职员工</div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">实发工资总盘</div>
                    <div class="jz-kpi-val" style="color:#ea580c;" id="jz-kpi-net">¥ 0.00</div>
                    <div class="jz-kpi-sub">应发总额: <span id="jz-kpi-gross">¥ 0.00</span></div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">五险一金单位统筹</div>
                    <div class="jz-kpi-val" style="color:#059669;" id="jz-kpi-comp-ins">¥ 0.00</div>
                    <div class="jz-kpi-sub">社保(工伤0.35%): <span id="jz-kpi-ss-comp">¥ 0.00</span> | 公积金: <span id="jz-kpi-hf-comp">¥ 0.00</span></div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">代扣税费 (个人部分)</div>
                    <div class="jz-kpi-val" style="color:#d97706;" id="jz-kpi-person-ded">¥ 0.00</div>
                    <div class="jz-kpi-sub">个人社保+公积金+个税</div>
                </div>
            </div>

            <!-- 月度核定工具栏 -->
            <div class="jz-toolbar">
                <div class="jz-toolbar-left">
                    <button class="btn btn-primary btn-sm" id="btn-jz-calc-payroll" style="background:#ea580c; border-color:#ea580c;">⚡ 一键综合测算与生成当月工资表</button>
                    <button class="btn btn-success btn-sm" id="btn-jz-lock-payroll" style="background:#16a34a; border-color:#16a34a;">🔒 确认核定并锁死 (防止篡改)</button>
                    <button class="btn btn-default btn-sm" id="btn-jz-unlock-payroll" style="display:none; color:#dc2626; border-color:#dc2626;">🔓 反审核解锁 (重新调整)</button>
                </div>
                <div class="jz-toolbar-right">
                    <button class="btn btn-default btn-sm" id="btn-jz-print-payroll">🖨️ 打印/导出工资表</button>
                </div>
            </div>

            <!-- 薪酬核定明细表格 -->
            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-payroll">
                    <thead>
                        <tr>
                            <th>工号</th>
                            <th>姓名</th>
                            <th>部门/岗位</th>
                            <th>基本工资</th>
                            <th>岗位津贴</th>
                            <th>绩效基数</th>
                            <th>津贴补贴</th>
                            <th>应发工资</th>
                            <th>社保代扣</th>
                            <th>公积金代扣</th>
                            <th>个税代扣</th>
                            <th>实发工资</th>
                            <th>社保统筹</th>
                            <th>公积金单位</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-jz-payroll">
                        <tr><td colspan="14" style="text-align:center; padding:30px; color:#94a3b8;">请点击上方【⚡ 一键综合测算与生成当月工资表】</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Tab 2: 员工薪酬档案 -->
        <div id="jz-tab-employees" class="jz-tab-content" style="display:none;">
            <div class="jz-toolbar">
                <div class="jz-toolbar-left">
                    <input type="text" class="form-control" id="jz-emp-search" placeholder="🔍 搜索工号、姓名、手机号、部门..." style="width:240px; display:inline-block;">
                </div>
                <div class="jz-toolbar-right">
                    <button class="btn btn-primary btn-sm" id="btn-jz-new-emp" style="background:#ea580c; border-color:#ea580c;">➕ 新增吉众员工</button>
                </div>
            </div>

            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-emp">
                    <thead>
                        <tr>
                            <th>工号</th>
                            <th>姓名</th>
                            <th>部门</th>
                            <th>岗位职务</th>
                            <th>用工性质</th>
                            <th>计薪方式</th>
                            <th>基本工资</th>
                            <th>岗位津贴</th>
                            <th>绩效基数</th>
                            <th>津贴补贴合计</th>
                            <th>社保基数</th>
                            <th>公积金基数</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-jz-emp"></tbody>
                </table>
            </div>
        </div>

        <!-- Tab 3: 社保公积金配置 (含合计显示与设置按钮) -->
        <div id="jz-tab-insurance" class="jz-tab-content" style="display:none;">
            <!-- 比例合计 KPI 卡片 -->
            <div class="jz-kpi-grid" style="margin-bottom: 20px;">
                <div class="jz-kpi-card" style="border-left: 4px solid #ea580c;">
                    <div class="jz-kpi-title">🏢 单位社保合计比例</div>
                    <div class="jz-kpi-val" style="color:#ea580c;" id="jz-ins-kpi-ss-comp">27.35 %</div>
                    <div class="jz-kpi-sub">养老+失业+医疗+其他+工伤(0.35%)</div>
                </div>
                <div class="jz-kpi-card" style="border-left: 4px solid #d97706;">
                    <div class="jz-kpi-title">👤 个人社保合计比例</div>
                    <div class="jz-kpi-val" style="color:#d97706;" id="jz-ins-kpi-ss-pers">10.50 %</div>
                    <div class="jz-kpi-sub">养老+失业+医疗 (+固定月大额救助)</div>
                </div>
                <div class="jz-kpi-card" style="border-left: 4px solid #059669;">
                    <div class="jz-kpi-title">🏠 住房公积金合计比例</div>
                    <div class="jz-kpi-val" style="color:#059669;" id="jz-ins-kpi-hf-tot">10.00 %</div>
                    <div class="jz-kpi-sub">单位: <span id="jz-ins-kpi-hf-c">5%</span> | 个人: <span id="jz-ins-kpi-hf-p">5%</span></div>
                </div>
                <div class="jz-kpi-card" style="border-left: 4px solid #7c3aed;">
                    <div class="jz-kpi-title">💼 综合社保公积金总负担率</div>
                    <div class="jz-kpi-val" style="color:#7c3aed;" id="jz-ins-kpi-overall">47.85 %</div>
                    <div class="jz-kpi-sub">单位+个人五险一金费率总和</div>
                </div>
            </div>

            <!-- 配置工具栏 -->
            <div class="jz-toolbar">
                <div class="jz-toolbar-left">
                    <span style="font-weight: 700; color: #ea580c; font-size: 15px;">⚙️ 天津吉众科技有限公司 · 2026 年度费率与基数配置表</span>
                </div>
                <div class="jz-toolbar-right">
                    <button class="btn btn-primary btn-sm" id="btn-jz-edit-insurance" style="background:#ea580c; border-color:#ea580c; font-weight:600;">
                        ⚙️ 修改社保公积金配置 (编辑比例与基数)
                    </button>
                </div>
            </div>

            <!-- 详细费率卡片 -->
            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:20px;">
                <div style="background:#fff; padding:20px; border-radius:10px; border:1px solid #fed7aa; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; border-bottom:1px solid #ffedd5; padding-bottom:8px;">
                        <h5 style="font-weight:700; color:#ea580c; margin:0;">🛡️ 单位社保缴费比例</h5>
                        <span class="jz-status-badge jz-status-locked" id="jz-badge-ss-comp-tot">合计: 27.35%</span>
                    </div>
                    <div style="line-height:2.0; font-size:13px; color:#334155;">
                        <div style="display:flex; justify-content:space-between;"><span>基本养老保险：</span><strong id="jz-view-ss-comp-pension">16.0 %</strong></div>
                        <div style="display:flex; justify-content:space-between;"><span>失业保险：</span><strong id="jz-view-ss-comp-unemp">0.5 %</strong></div>
                        <div style="display:flex; justify-content:space-between;"><span>基本医疗保险：</span><strong id="jz-view-ss-comp-med">10.0 %</strong></div>
                        <div style="display:flex; justify-content:space-between;"><span>其他医疗补助：</span><strong id="jz-view-ss-comp-other">0.5 %</strong></div>
                        <div style="display:flex; justify-content:space-between;"><span>工伤保险 (吉众独立类属)：</span><strong style="color:#ea580c;" id="jz-view-ss-comp-injury">0.35 %</strong></div>
                        <div style="display:flex; justify-content:space-between; margin-top:8px; border-top:1px dashed #fed7aa; padding-top:6px;">
                            <span>社保最低缴费基数：</span><strong style="color:#0f172a;" id="jz-view-ss-min-base">5,124.00 元</strong>
                        </div>
                    </div>
                </div>

                <div style="background:#fff; padding:20px; border-radius:10px; border:1px solid #fed7aa; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; border-bottom:1px solid #ffedd5; padding-bottom:8px;">
                        <h5 style="font-weight:700; color:#0f172a; margin:0;">👤 个人社保扣缴比例与救助金</h5>
                        <span class="jz-status-badge jz-status-draft" id="jz-badge-ss-pers-tot">合计: 10.50%</span>
                    </div>
                    <div style="line-height:2.0; font-size:13px; color:#334155;">
                        <div style="display:flex; justify-content:space-between;"><span>个人基本养老：</span><strong id="jz-view-ss-pers-pension">8.0 %</strong></div>
                        <div style="display:flex; justify-content:space-between;"><span>个人失业保险：</span><strong id="jz-view-ss-pers-unemp">0.5 %</strong></div>
                        <div style="display:flex; justify-content:space-between;"><span>个人基本医疗：</span><strong id="jz-view-ss-pers-med">2.0 %</strong></div>
                        <div style="margin-top:8px; border-top:1px dashed #fed7aa; padding-top:6px;">
                            <div style="display:flex; justify-content:space-between;">
                                <span>大额医疗救助 (基准金额)：</span>
                                <strong style="color:#d97706;" id="jz-view-med-default">22.00 元/月</strong>
                            </div>
                            <div style="display:flex; justify-content:space-between;">
                                <span>大额医疗救助 (特殊月份)：</span>
                                <strong style="color:#d97706;" id="jz-view-med-special">21.00 元/月</strong>
                            </div>
                            <div style="font-size:12px; color:#64748b; margin-top:2px;">
                                特殊金额生效月份：<span id="jz-view-med-months" style="font-weight:600; color:#ea580c;">3月, 12月</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div style="background:#fff; padding:20px; border-radius:10px; border:1px solid #fed7aa; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; border-bottom:1px solid #ffedd5; padding-bottom:8px;">
                        <h5 style="font-weight:700; color:#0f172a; margin:0;">🏠 住房公积金与个税起征</h5>
                        <span class="jz-status-badge jz-status-locked" id="jz-badge-hf-tot">合计: 10.00%</span>
                    </div>
                    <div style="line-height:2.0; font-size:13px; color:#334155;">
                        <div style="display:flex; justify-content:space-between;"><span>公积金单位比例：</span><strong id="jz-view-hf-comp">5.0 %</strong></div>
                        <div style="display:flex; justify-content:space-between;"><span>公积金个人比例：</span><strong id="jz-view-hf-pers">5.0 %</strong></div>
                        <div style="display:flex; justify-content:space-between;"><span>公积金最低缴费基数：</span><strong style="color:#ea580c;" id="jz-view-hf-min-base">2,320.00 元</strong></div>
                        <div style="display:flex; justify-content:space-between; margin-top:8px; border-top:1px dashed #fed7aa; padding-top:6px;">
                            <span>个税基本减除费用 (起征点)：</span><strong style="color:#0f172a;" id="jz-view-tax-threshold">5,000.00 元/月</strong>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tab 4: 考勤工时 -->
        <div id="jz-tab-attendance" class="jz-tab-content" style="display:none;">
            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-att">
                    <thead>
                        <tr>
                            <th>工号</th>
                            <th>姓名</th>
                            <th>考勤月份</th>
                            <th>出勤天数</th>
                            <th>正常工时(h)</th>
                            <th>平日加班 1.5x(h)</th>
                            <th>周末加班 2.0x(h)</th>
                            <th>节假日加班 3.0x(h)</th>
                            <th>工作餐补助次数</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-jz-att"></tbody>
                </table>
            </div>
        </div>
    </div>
    `;

    $(wrapper).find('.layout-main-section').html(html);
    const $container = $(wrapper);

    let cached_jz_insurance_setting = null;

    function fmtMoney(v) {
        return '¥ ' + (parseFloat(v) || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    // 1. 加载月度核定结算
    function load_payroll_settlement() {
        frappe.call({
            method: 'ashan_cn_procurement.services.payroll_settlement_service.get_payroll_settlement_detail',
            args: {
                company: COMPANY,
                period_month: current_month
            },
            callback: function(r) {
                if (r.message) {
                    render_payroll_view(r.message);
                }
            }
        });
    }

    function render_payroll_view(data) {
        const isLocked = data.locked === 1;
        $("#jz-kpi-count").text(data.total_employees || 0);
        $("#jz-kpi-net").text(fmtMoney(data.total_net_salary));
        $("#jz-kpi-gross").text(fmtMoney(data.total_gross_salary));
        $("#jz-kpi-comp-ins").text(fmtMoney((data.total_social_security_company || 0) + (data.total_housing_fund_company || 0)));
        $("#jz-kpi-ss-comp").text(fmtMoney(data.total_social_security_company));
        $("#jz-kpi-hf-comp").text(fmtMoney(data.total_housing_fund_company));
        $("#jz-kpi-person-ded").text(fmtMoney((data.total_social_security_person || 0) + (data.total_housing_fund_person || 0) + (data.total_tax || 0)));

        if (isLocked) {
            $("#jz-kpi-status").html('<span class="jz-status-badge jz-status-locked">🔒 已核定锁定</span>');
            $("#btn-jz-calc-payroll").prop("disabled", true).text("🔒 已核定锁定 (禁止测算)");
            $("#btn-jz-lock-payroll").hide();
            $("#btn-jz-unlock-payroll").show();
        } else {
            $("#jz-kpi-status").html('<span class="jz-status-badge jz-status-draft">📝 草稿 / 未核定</span>');
            $("#btn-jz-calc-payroll").prop("disabled", false).text("⚡ 一键综合测算与生成当月工资表");
            $("#btn-jz-lock-payroll").show();
            $("#btn-jz-unlock-payroll").hide();
        }

        const items = data.items || [];
        if (items.length === 0) {
            $("#tbody-jz-payroll").html('<tr><td colspan="14" style="text-align:center; padding:30px; color:#94a3b8;">暂无核算数据，请点击【⚡ 一键综合测算与生成当月工资表】</td></tr>');
            return;
        }

        let html = '';
        items.forEach(it => {
            html += `
            <tr>
                <td><strong>${it.employee_no}</strong></td>
                <td><strong style="color:#ea580c;">${it.employee_name}</strong></td>
                <td>${it.department || '—'} / ${it.job_title || '—'}</td>
                <td class="jz-money-cell">${fmtMoney(it.base_salary)}</td>
                <td class="jz-money-cell">${fmtMoney(it.post_allowance)}</td>
                <td class="jz-money-cell">${fmtMoney(it.performance_salary)}</td>
                <td class="jz-money-cell">${fmtMoney(it.allowances_total)}</td>
                <td class="jz-money-cell" style="color:#ea580c;">${fmtMoney(it.gross_salary)}</td>
                <td class="jz-money-cell" style="color:#d97706;">${fmtMoney(it.ss_person_total)}</td>
                <td class="jz-money-cell" style="color:#d97706;">${fmtMoney(it.hf_person_total)}</td>
                <td class="jz-money-cell" style="color:#dc2626;">${fmtMoney(it.tax_amount)}</td>
                <td class="jz-money-cell" style="color:#16a34a; font-size:14px; font-weight:700;">${fmtMoney(it.net_salary)}</td>
                <td class="jz-money-cell">${fmtMoney(it.ss_company_total)}</td>
                <td class="jz-money-cell">${fmtMoney(it.hf_company_total)}</td>
            </tr>
            `;
        });
        $("#tbody-jz-payroll").html(html);
    }

    // 2. 加载吉众员工档案
    function load_jz_employees() {
        frappe.call({
            method: 'ashan_cn_procurement.services.employee_salary_service.get_employee_profiles',
            args: {
                company: COMPANY,
                employee_type: '全部',
                search_text: $("#jz-emp-search").val() || ''
            },
            callback: function(r) {
                if (r.message && r.message.records) {
                    render_employees_table(r.message.records);
                }
            }
        });
    }

    function render_employees_table(records) {
        let html = '';
        records.forEach(r => {
            const allow_sum = (r.meal_allowance || 0) + (r.traffic_allowance || 0) + (r.communication_allowance || 0) + (r.other_allowance || 0);
            html += `
            <tr>
                <td><strong>${r.employee_no}</strong></td>
                <td><strong style="color:#ea580c;">${r.employee_name}</strong></td>
                <td>${r.department || '—'}</td>
                <td>${r.job_title || '—'}</td>
                <td><span class="jz-status-badge jz-status-locked">${r.employee_type || '正式工'}</span></td>
                <td>${r.salary_mode || '税前'}</td>
                <td class="jz-money-cell" style="color:#ea580c;">${fmtMoney(r.base_salary)}</td>
                <td class="jz-money-cell">${fmtMoney(r.post_allowance)}</td>
                <td class="jz-money-cell">${fmtMoney(r.performance_base)}</td>
                <td class="jz-money-cell">${fmtMoney(allow_sum)}</td>
                <td class="jz-money-cell">${fmtMoney(r.social_security_base)}</td>
                <td class="jz-money-cell" style="${r.housing_fund_base > 0 ? 'color:#16a34a; font-weight:700;' : 'color:#94a3b8;'}">${fmtMoney(r.housing_fund_base)}</td>
                <td>
                    <button class="btn btn-default btn-xs btn-jz-edit-emp" data-name="${r.name}" style="color:#ea580c;">✏️ 修改参数</button>
                </td>
            </tr>
            `;
        });
        $("#tbody-jz-emp").html(html);
    }

    // 3. 加载社保配置与合计展示
    function load_jz_insurance_setting() {
        const year = current_month.split("-")[0] || 2026;
        frappe.call({
            method: 'ashan_cn_procurement.services.employee_salary_service.get_insurance_setting',
            args: {
                company: COMPANY,
                year: year
            },
            callback: function(r) {
                if (r.message) {
                    cached_jz_insurance_setting = r.message;
                    render_insurance_view(r.message);
                }
            }
        });
    }

    function render_insurance_view(ins) {
        $("#jz-ins-kpi-ss-comp").text(ins.total_ss_company_rate + " %");
        $("#jz-ins-kpi-ss-pers").text(ins.total_ss_person_rate + " %");
        $("#jz-ins-kpi-hf-tot").text(ins.total_hf_rate + " %");
        $("#jz-ins-kpi-hf-c").text(ins.hf_company_rate + "%");
        $("#jz-ins-kpi-hf-p").text(ins.hf_person_rate + "%");
        $("#jz-ins-kpi-overall").text(ins.total_overall_rate + " %");

        $("#jz-badge-ss-comp-tot").text("合计: " + ins.total_ss_company_rate + "%");
        $("#jz-view-ss-comp-pension").text(ins.ss_company_pension + " %");
        $("#jz-view-ss-comp-unemp").text(ins.ss_company_unemployment + " %");
        $("#jz-view-ss-comp-med").text(ins.ss_company_medical + " %");
        $("#jz-view-ss-comp-other").text(ins.ss_company_other_medical + " %");
        $("#jz-view-ss-comp-injury").text(ins.ss_company_injury + " %");
        $("#jz-view-ss-min-base").text(fmtMoney(ins.ss_min_base));

        $("#jz-badge-ss-pers-tot").text("合计: " + ins.total_ss_person_rate + "%");
        $("#jz-view-ss-pers-pension").text(ins.ss_person_pension + " %");
        $("#jz-view-ss-pers-unemp").text(ins.ss_person_unemployment + " %");
        $("#jz-view-ss-pers-med").text(ins.ss_person_medical + " %");

        $("#jz-view-med-default").text(fmtMoney(ins.big_medical_amount_default) + " /月");
        $("#jz-view-med-special").text(fmtMoney(ins.big_medical_amount_special) + " /月");
        $("#jz-view-med-months").text(ins.big_medical_special_months ? ins.big_medical_special_months + " 月" : "无");

        $("#jz-badge-hf-tot").text("合计: " + ins.total_hf_rate + "%");
        $("#jz-view-hf-comp").text(ins.hf_company_rate + " %");
        $("#jz-view-hf-pers").text(ins.hf_person_rate + " %");
        $("#jz-view-hf-min-base").text(fmtMoney(ins.hf_min_base));
        $("#jz-view-tax-threshold").text(fmtMoney(ins.tax_threshold) + " /月");
    }

    // 4. 打开社保修改弹窗
    function open_insurance_edit_dialog() {
        if (!cached_jz_insurance_setting) return;
        const ins = cached_jz_insurance_setting;
        const year = current_month.split("-")[0] || 2026;

        const d = new frappe.ui.Dialog({
            title: `⚙️ 修改【${COMPANY}】${year} 年度社保公积金配置`,
            size: 'large',
            fields: [
                { fieldtype: 'Section Break', label: '🏢 单位社保缴费比例 (%)' },
                { fieldname: 'ss_company_pension', fieldtype: 'Percent', label: '单位基本养老 (%)', default: ins.ss_company_pension, reqd: 1 },
                { fieldname: 'ss_company_unemployment', fieldtype: 'Percent', label: '单位失业保险 (%)', default: ins.ss_company_unemployment, reqd: 1 },
                { fieldname: 'ss_company_medical', fieldtype: 'Percent', label: '单位基本医疗 (%)', default: ins.ss_company_medical, reqd: 1 },
                { fieldname: 'ss_company_other_medical', fieldtype: 'Percent', label: '单位其他医疗 (%)', default: ins.ss_company_other_medical, reqd: 1 },
                { fieldname: 'ss_company_injury', fieldtype: 'Percent', label: '单位工伤保险 (%)', default: ins.ss_company_injury, reqd: 1 },
                
                { fieldtype: 'Section Break', label: '👤 个人社保扣缴比例与救助金' },
                { fieldname: 'ss_person_pension', fieldtype: 'Percent', label: '个人基本养老 (%)', default: ins.ss_person_pension, reqd: 1 },
                { fieldname: 'ss_person_unemployment', fieldtype: 'Percent', label: '个人失业保险 (%)', default: ins.ss_person_unemployment, reqd: 1 },
                { fieldname: 'ss_person_medical', fieldtype: 'Percent', label: '个人基本医疗 (%)', default: ins.ss_person_medical, reqd: 1 },
                { fieldname: 'big_medical_amount_default', fieldtype: 'Currency', label: '大额医疗基准金额 (元/月)', default: ins.big_medical_amount_default, reqd: 1 },
                { fieldname: 'big_medical_amount_special', fieldtype: 'Currency', label: '大额医疗特殊月份金额 (元/月)', default: ins.big_medical_amount_special, reqd: 1 },
                { fieldname: 'big_medical_special_months', fieldtype: 'Data', label: '特殊金额生效月份 (如: 3,12)', default: ins.big_medical_special_months, reqd: 1 },

                { fieldtype: 'Section Break', label: '🏠 住房公积金与基数起征点' },
                { fieldname: 'hf_company_rate', fieldtype: 'Percent', label: '单位公积金比例 (%)', default: ins.hf_company_rate, reqd: 1 },
                { fieldname: 'hf_person_rate', fieldtype: 'Percent', label: '个人公积金比例 (%)', default: ins.hf_person_rate, reqd: 1 },
                { fieldname: 'ss_min_base', fieldtype: 'Currency', label: '社保最低缴费基数 (元)', default: ins.ss_min_base, reqd: 1 },
                { fieldname: 'hf_min_base', fieldtype: 'Currency', label: '公积金最低缴费基数 (元)', default: ins.hf_min_base, reqd: 1 },
                { fieldname: 'tax_threshold', fieldtype: 'Currency', label: '个税起征点 (元/月)', default: ins.tax_threshold, reqd: 1 }
            ],
            primary_action_label: '💾 保存并即时生效',
            primary_action(values) {
                frappe.call({
                    method: 'ashan_cn_procurement.services.employee_salary_service.save_insurance_setting',
                    type: 'POST',
                    args: {
                        company: COMPANY,
                        year: year,
                        data: JSON.stringify(values)
                    },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint({
                                title: '✅ 保存成功',
                                indicator: 'green',
                                message: r.message.message
                            });
                            d.hide();
                            cached_jz_insurance_setting = r.message.doc;
                            render_insurance_view(r.message.doc);
                        }
                    }
                });
            }
        });
        d.show();
    }

    // 5. 加载考勤数据
    function load_jz_attendance() {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Ashan Monthly Attendance',
                filters: { company: COMPANY, period_month: current_month },
                fields: ['employee_no', 'employee_name', 'period_month', 'attendance_days', 'work_hours_regular', 'overtime_regular_1_5', 'overtime_weekend_2_0', 'overtime_holiday_3_0', 'meal_count'],
                limit_page_length: 100
            },
            callback: function(r) {
                const list = r.message || [];
                if (list.length === 0) {
                    $("#tbody-jz-att").html('<tr><td colspan="9" style="text-align:center; padding:30px; color:#94a3b8;">暂无考勤明细数据</td></tr>');
                    return;
                }
                let html = '';
                list.forEach(it => {
                    html += `
                    <tr>
                        <td><strong>${it.employee_no}</strong></td>
                        <td>${it.employee_name}</td>
                        <td>${it.period_month}</td>
                        <td>${it.attendance_days || 0} 天</td>
                        <td>${it.work_hours_regular || 0} h</td>
                        <td>${it.overtime_regular_1_5 || 0} h</td>
                        <td>${it.overtime_weekend_2_0 || 0} h</td>
                        <td>${it.overtime_holiday_3_0 || 0} h</td>
                        <td>${it.meal_count || 0} 次</td>
                    </tr>
                    `;
                });
                $("#tbody-jz-att").html(html);
            }
        });
    }

    // 事件绑定
    // 1. Tab 切换
    $container.on("click", ".jz-tab-btn", function() {
        $(".jz-tab-btn").removeClass("active");
        $(this).addClass("active");
        const tab = $(this).attr("data-tab");
        $(".jz-tab-content").hide();
        $(`#jz-tab-${tab}`).show();
        current_tab = tab;

        if (tab === 'payroll') load_payroll_settlement();
        if (tab === 'employees') load_jz_employees();
        if (tab === 'insurance') load_jz_insurance_setting();
        if (tab === 'attendance') load_jz_attendance();
    });

    // 2. 月份切换
    $container.on("change", "#jz-month-select", function() {
        current_month = $(this).val();
        load_payroll_settlement();
        if (current_tab === 'insurance') load_jz_insurance_setting();
        if (current_tab === 'attendance') load_jz_attendance();
    });

    // 3. 一键测算生成
    $container.on("click", "#btn-jz-calc-payroll", function() {
        frappe.call({
            method: 'ashan_cn_procurement.services.payroll_settlement_service.calculate_and_generate_payroll',
            type: 'POST',
            args: {
                company: COMPANY,
                period_month: current_month
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({ message: r.message.message, indicator: 'green' });
                    render_payroll_view(r.message.doc);
                }
            }
        });
    });

    // 4. 确认核定锁死
    $container.on("click", "#btn-jz-lock-payroll", function() {
        frappe.confirm(
            `<strong>【🔒 确认核定并锁定当月薪酬】</strong><br><br>将正式核定并锁死【${COMPANY}】${current_month} 的薪酬核定表。<br><br><span style="color:#dc2626; font-weight:600;">锁定后所有明细与参数将冻结只读，防止篡改！</span><br><br>确认核定吗？`,
            function() {
                frappe.call({
                    method: 'ashan_cn_procurement.services.payroll_settlement_service.confirm_and_lock_payroll',
                    type: 'POST',
                    args: {
                        company: COMPANY,
                        period_month: current_month
                    },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint({
                                title: '✅ 核定成功',
                                indicator: 'green',
                                message: r.message.message
                            });
                            render_payroll_view(r.message.doc);
                        }
                    }
                });
            }
        );
    });

    // 5. 反审核解锁
    $container.on("click", "#btn-jz-unlock-payroll", function() {
        frappe.prompt([
            {
                fieldname: 'reason',
                fieldtype: 'Data',
                label: '反审核解锁原因',
                reqd: 1
            }
        ], function(values) {
            frappe.call({
                method: 'ashan_cn_procurement.services.payroll_settlement_service.unlock_payroll',
                type: 'POST',
                args: {
                    company: COMPANY,
                    period_month: current_month,
                    reason: values.reason
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint({
                            title: '🔓 解锁成功',
                            indicator: 'green',
                            message: r.message.message
                        });
                        render_payroll_view(r.message.doc);
                    }
                }
            });
        }, '反审核解锁月度薪酬表', '确认解锁');
    });

    // 6. 打开社保修改弹窗
    $container.on("click", "#btn-jz-edit-insurance", function() {
        open_insurance_edit_dialog();
    });

    // 7. 打印工资表
    $container.on("click", "#btn-jz-print-payroll", function() {
        window.print();
    });

    // 初始化加载
    load_payroll_settlement();
};
