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

        <!-- 7大业务 Tab 切换 (档案前置 -> 考勤打卡 -> 税费基数 -> 综合核算 -> 现金配钞 -> 历史归档) -->
        <div class="jz-nav-tabs">
            <button class="jz-tab-btn active" data-tab="employees">1. 员工薪资信息表</button>
            <button class="jz-tab-btn" data-tab="attendance">2. 考勤工时与打卡底册</button>
            <button class="jz-tab-btn" data-tab="insurance">3. 社保公积金配置</button>
            <button class="jz-tab-btn" data-tab="tax">4. 个人所得税台账</button>
            <button class="jz-tab-btn" data-tab="payroll">5. 月度工资核定表</button>
            <button class="jz-tab-btn" data-tab="cash_bills">6. 现金发放与配钞点钞</button>
            <button class="jz-tab-btn" data-tab="history">7. 历史薪资穿透 (421条)</button>
        </div>

        <!-- Tab 1: 员工薪资信息表 (对应 Excel [人员薪资信息] sheets) -->
        <div id="jz-tab-employees" class="jz-tab-content">
            <div class="jz-kpi-grid">
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">在册员工总数 / 状态</div>
                    <div class="jz-kpi-val" id="jz-emp-kpi-count">0 人</div>
                    <div class="jz-kpi-sub">基准底册: <span class="jz-text-success">已建立</span></div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">基本工资总基数</div>
                    <div class="jz-kpi-val jz-text-info" id="jz-emp-kpi-base">¥ 0.00</div>
                    <div class="jz-kpi-sub">动态基本工资底册合计</div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">岗位津贴与绩效总盘</div>
                    <div class="jz-kpi-val jz-text-primary" id="jz-emp-kpi-allowance">¥ 0.00</div>
                    <div class="jz-kpi-sub">津贴: <span id="jz-emp-kpi-post">¥ 0.00</span> | 绩效: <span id="jz-emp-kpi-perf">¥ 0.00</span></div>
                </div>
                <div class="jz-kpi-card">
                    <div class="jz-kpi-title">社保与公积金申报基数</div>
                    <div class="jz-kpi-val jz-text-success" id="jz-emp-kpi-ins">¥ 0.00</div>
                    <div class="jz-kpi-sub">社险基数: <span id="jz-emp-kpi-ss">¥ 0.00</span> | 公积金: <span id="jz-emp-kpi-hf">¥ 0.00</span></div>
                </div>
            </div>

            <div class="jz-toolbar">
                <div class="jz-toolbar-left">
                    <button class="btn btn-primary btn-sm jz-btn-blue" id="btn-jz-add-emp">新建员工薪酬档案</button>
                    <button class="btn btn-default btn-sm" id="btn-jz-export-employees">导出薪资信息表 (Excel)</button>
                    <div class="jz-segmented-control" id="jz-emp-type-filter">
                        <button class="jz-segment-btn active" data-type="all">全部人员</button>
                        <button class="jz-segment-btn" data-type="regular">正式工</button>
                        <button class="jz-segment-btn" data-type="other">其他</button>
                    </div>
                </div>
                <div class="jz-toolbar-right">
                    <input type="text" class="form-control input-sm jz-search-input" id="jz-emp-search" placeholder="快速筛选工号、姓名或计薪方式...">
                </div>
            </div>

            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-employees">
                    <thead>
                        <tr>
                            <th class="jz-col-seq jz-col-sticky-1">序号</th>
                            <th class="jz-col-no jz-col-sticky-2">工号</th>
                            <th class="jz-col-name jz-col-sticky-3">姓名</th>
                            <th>证件号码</th>
                            <th>用工性质</th>
                            <th>计薪方式</th>
                            <th class="jz-text-right">实发约定净薪</th>
                            <th class="jz-text-right">基本工资</th>
                            <th class="jz-text-right">基本补贴</th>
                            <th class="jz-text-right">绩效奖金</th>
                            <th class="jz-text-right">职位津贴</th>
                            <th class="jz-text-right">餐补单价</th>
                            <th class="jz-text-right">社险基数</th>
                            <th class="jz-text-right">公积金基数</th>
                            <th class="jz-text-right">专项附加扣除</th>
                            <th class="jz-text-center">在职状态</th>
                            <th class="jz-col-action">操作</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-jz-employees">
                        <tr><td colspan="17" class="jz-empty-cell">正在加载员工薪资信息档案...</td></tr>
                    </tbody>
                    <tfoot id="tfoot-jz-employees"></tfoot>
                </table>
            </div>
        </div>

        <!-- Tab 2: 考勤工时与打卡底册 (对应 Excel [考勤表] sheets) -->
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

            <!-- 考勤工时与底册操作栏 -->
            <div class="jz-toolbar">
                <div class="jz-toolbar-left">
                    <button class="btn btn-primary btn-sm jz-btn-blue" id="btn-jz-upload-attendance">上传月度考勤 (Excel)</button>
                    <button class="btn btn-default btn-sm jz-btn-danger-outline" id="btn-jz-clear-attendance">一键清空本月考勤</button>
                    <button class="btn btn-default btn-sm jz-text-primary" id="btn-jz-sync-calc-payroll">按考勤一键核算当月工资</button>
                    <button class="btn btn-default btn-sm jz-hidden" id="btn-jz-download-attendance-file">下载原始考勤凭证</button>

                    <!-- 双视角原位分段控件 -->
                    <div class="jz-segmented-control" id="jz-att-view-mode">
                        <button class="jz-segment-btn active" data-mode="raw">原始打卡底册矩阵</button>
                        <button class="jz-segment-btn" data-mode="summary">工时分类结算汇总</button>
                    </div>
                </div>
                <div class="jz-toolbar-right">
                    <!-- 原始矩阵维度的过滤分段控件 -->
                    <div class="jz-segmented-control" id="jz-raw-filter-metric">
                        <button class="jz-segment-btn active" data-metric="all">全部5行维度</button>
                        <button class="jz-segment-btn" data-metric="shifts">仅班次</button>
                        <button class="jz-segment-btn" data-metric="work">仅作业工时</button>
                        <button class="jz-segment-btn" data-metric="ot">仅加班工时</button>
                        <button class="jz-segment-btn" data-metric="meal">仅订餐</button>
                        <button class="jz-segment-btn" data-metric="remark">仅备注</button>
                    </div>
                    <button class="btn btn-default btn-sm" id="btn-jz-export-raw-attendance">导出打卡底册 (Excel)</button>
                    <button class="btn btn-default btn-sm jz-hidden" id="btn-jz-export-summary-attendance">导出结算汇总 (Excel)</button>
                </div>
            </div>

            <!-- 视图 1: 原始打卡底册矩阵大宽表 (以原始数据为准，默认首选) -->
            <div class="jz-table-box jz-raw-table-box" id="box-jz-view-raw">
                <table class="jz-table jz-raw-matrix-table" id="table-jz-raw-attendance">
                    <thead id="thead-jz-raw-attendance"></thead>
                    <tbody id="tbody-jz-raw-attendance">
                        <tr><td class="jz-empty-cell">正在加载吉众原始考勤打卡底册矩阵...</td></tr>
                    </tbody>
                </table>
            </div>

            <!-- 视图 2: 工时分类结算汇总表 (纯净财务核算单行表，彻底消除虚构列) -->
            <div class="jz-table-box jz-hidden" id="box-jz-view-summary">
                <table class="jz-table" id="table-jz-attendance">
                    <thead>
                        <tr>
                            <th class="jz-col-seq">序号</th>
                            <th class="jz-col-no">工号</th>
                            <th class="jz-col-name">姓名</th>
                            <th class="jz-text-center">出勤天数</th>
                            <th class="jz-text-right">出勤正班工时</th>
                            <th class="jz-text-right">平日加班 (1.5x)</th>
                            <th class="jz-text-right">周末加班 (2.0x)</th>
                            <th class="jz-text-right">节日加班 (3.0x)</th>
                            <th class="jz-text-right">加班工时合计</th>
                            <th class="jz-text-right">倒休冲抵工时</th>
                            <th class="jz-text-right">实际计薪加班</th>
                            <th class="jz-text-right">订餐补贴次数</th>
                            <th>打卡备注与请假汇总</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-jz-attendance">
                        <tr><td colspan="13" class="jz-empty-cell">正在加载考勤工时结算汇总...</td></tr>
                    </tbody>
                    <tfoot id="tfoot-jz-attendance"></tfoot>
                </table>
            </div>
        </div>

        <!-- Tab 3: 社保公积金配置 (对应 Excel [本月社会保险] / [本月住房公积金] sheets) -->
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

        <!-- Tab 4: 个人所得税台账 (对应 Excel [本月个人所得税] sheets) -->
        <div id="jz-tab-tax" class="jz-tab-content jz-hidden">
            <div class="jz-toolbar">
                <div class="jz-toolbar-left">
                    <span class="jz-tip-text">累计预扣法：5000元/月基本减除费用 + 专项附加扣除 + 7级累计超额累进税率</span>
                </div>
                <div class="jz-toolbar-right">
                    <button class="btn btn-default btn-sm" id="btn-jz-export-tax">导出个税台账 (Excel)</button>
                </div>
            </div>
            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-tax">
                    <thead>
                        <tr>
                            <th class="jz-col-seq">序号</th>
                            <th class="jz-col-no">工号</th>
                            <th class="jz-col-name">姓名</th>
                            <th>计薪方式</th>
                            <th class="jz-text-right">应发薪资</th>
                            <th class="jz-text-right">免征额</th>
                            <th class="jz-text-right">社保个人合计</th>
                            <th class="jz-text-right">公积金个人</th>
                            <th class="jz-text-right">专项附加扣除</th>
                            <th class="jz-text-right">当月预扣个税</th>
                            <th class="jz-text-right">实发工资</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-jz-tax"></tbody>
                </table>
            </div>
        </div>

        <!-- Tab 5: 月度工资核定表 (最后工资表 / 对应 Excel [本月工资核定表] sheets) -->
        <div id="jz-tab-payroll" class="jz-tab-content jz-hidden">
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
                        <button class="jz-segment-btn" data-mode="regular">正式工</button>
                        <button class="jz-segment-btn" data-mode="other">其他</button>
                    </div>

                    <div class="jz-segmented-control" id="jz-payroll-col-toggle">
                        <button class="jz-segment-btn active" data-view="summary">精简财务视图</button>
                        <button class="jz-segment-btn" data-view="detail">全要素工时分项</button>
                    </div>

                    <button class="btn btn-primary btn-sm jz-btn-orange" id="btn-jz-calc-payroll">一键重新计算全员薪酬</button>
                    <button class="btn btn-success btn-sm jz-btn-green" id="btn-jz-lock-payroll">核定锁定 (只读封账)</button>
                    <button class="btn btn-default btn-sm jz-btn-red jz-hidden" id="btn-jz-unlock-payroll">申请反审核解锁</button>
                </div>
                <div class="jz-toolbar-right">
                    <button class="btn btn-default btn-sm" id="btn-jz-export-payroll">导出最后工资表 (Excel)</button>
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

        <!-- Tab 6: 现金发放与配钞点钞 (对应 Excel [工资条-A4] / [工资条-信封] sheets) -->
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
                    <button class="btn btn-default btn-sm" id="btn-jz-export-cash">导出配钞明细 (Excel)</button>
                </div>
                <div class="jz-toolbar-right">
                    <span class="jz-tip-text">现金五档配钞点钞：贪心算法自适应最优张数 (RoundUp 到元)</span>
                </div>
            </div>

            <div class="jz-table-box">
                <table class="jz-table" id="table-jz-cash">
                    <thead>
                        <tr>
                            <th class="jz-col-seq">序号</th>
                            <th class="jz-col-no">工号</th>
                            <th class="jz-col-name">姓名</th>
                            <th class="jz-text-right">实发总额</th>
                            <th class="jz-text-right">现金实发</th>
                            <th class="jz-text-center">100元</th>
                            <th class="jz-text-center">50元</th>
                            <th class="jz-text-center">10元</th>
                            <th class="jz-text-center">5元</th>
                            <th class="jz-text-center">1元</th>
                            <th class="jz-text-right">合计金额</th>
                            <th class="jz-text-center">签收</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-jz-cash"></tbody>
                    <tfoot id="tfoot-jz-cash"></tfoot>
                </table>
            </div>
        </div>

        <!-- Tab 7: 历史薪资穿透 (421条 / 对应 Excel [历史数据] sheets) -->
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
                return type === '正式工';
            } else if (payroll_filter_mode === 'other') {
                return type === '其他' || type.includes('其他');
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

                render_raw_attendance_table();
                render_attendance_table();
            }
        });
    }

    function render_attendance_table() {
        const tbody = $('#tbody-jz-attendance');
        tbody.empty();

        if (attendance_cache.length === 0) {
            tbody.html('<tr><td colspan="13" class="jz-empty-cell">该月份尚未上传考勤表，请点击“上传月度考勤 (Excel)”按钮。</td></tr>');
            $('#tfoot-jz-attendance').empty();
            return;
        }

        let tot_reg = 0, tot_15 = 0, tot_20 = 0, tot_30 = 0, tot_comp = 0, tot_m = 0, tot_ot_all = 0, tot_payable_ot_all = 0;

        attendance_cache.forEach((it, idx) => {
            const wReg = flt(it.work_hours_regular);
            const ot15 = flt(it.overtime_regular_1_5);
            const ot20 = flt(it.overtime_weekend_2_0);
            const ot30 = flt(it.overtime_holiday_3_0);
            const cLeave = flt(it.leave_compensatory_hours);
            const mCount = cint(it.meal_count);

            const tot_ot_emp = ot15 + ot20 + ot30;
            const actual_payable_ot = ot15 + Math.max(0, ot20 - cLeave) + ot30;

            tot_reg += wReg;
            tot_15 += ot15;
            tot_20 += ot20;
            tot_30 += ot30;
            tot_comp += cLeave;
            tot_m += mCount;
            tot_ot_all += tot_ot_emp;
            tot_payable_ot_all += actual_payable_ot;

            // 从原始每日打卡记录中提取真实请假与异常打卡备注汇总
            let remark_counts = {};
            let rest_days = 0;
            if (it.daily_records_json) {
                try {
                    const days = JSON.parse(it.daily_records_json);
                    days.forEach(d => {
                        if (d.remark) {
                            const rm = d.remark.trim();
                            if (rm === '休') {
                                rest_days++;
                            } else if (rm) {
                                remark_counts[rm] = (remark_counts[rm] || 0) + 1;
                            }
                        }
                    });
                } catch(e) {}
            }
            let rText = [];
            if (rest_days > 0) rText.push(`公休 ${rest_days}天`);
            for (const [rm, count] of Object.entries(remark_counts)) {
                let label = rm;
                if (rm === '事') label = '事假';
                else if (rm === '病') label = '病假';
                rText.push(`${label} ${count}天`);
            }
            const final_r = rText.length > 0 ? rText.join(' · ') : '-';

            tbody.append(`
                <tr class="jz-att-row" data-no="${it.employee_no}">
                    <td class="jz-col-seq">${idx + 1}</td>
                    <td class="jz-col-no"><strong>${it.employee_no}</strong></td>
                    <td class="jz-col-name"><strong>${it.employee_name}</strong></td>
                    <td class="jz-text-center">${it.attendance_days || 0} 天</td>
                    <td class="jz-num-cell jz-text-info">${fmtHours(wReg)}</td>
                    <td class="jz-num-cell">${fmtHours(ot15)}</td>
                    <td class="jz-num-cell">${fmtHours(ot20)}</td>
                    <td class="jz-num-cell">${fmtHours(ot30)}</td>
                    <td class="jz-num-cell jz-text-primary">${fmtHours(tot_ot_emp)}</td>
                    <td class="jz-num-cell jz-text-muted">${fmtHours(cLeave)}</td>
                    <td class="jz-num-cell jz-text-primary"><strong>${fmtHours(actual_payable_ot)}</strong></td>
                    <td class="jz-num-cell jz-text-success">${mCount} 次</td>
                    <td class="jz-tip-text">${final_r}</td>
                </tr>
            `);
        });

        $('#tfoot-jz-attendance').html(`
            <tr>
                <td colspan="3" class="jz-col-foot-label">合计 (${attendance_cache.length}人)</td>
                <td class="jz-text-center">-</td>
                <td class="jz-num-cell jz-text-info">${fmtHours(tot_reg)}</td>
                <td class="jz-num-cell">${fmtHours(tot_15)}</td>
                <td class="jz-num-cell">${fmtHours(tot_20)}</td>
                <td class="jz-num-cell">${fmtHours(tot_30)}</td>
                <td class="jz-num-cell jz-text-primary">${fmtHours(tot_ot_all)}</td>
                <td class="jz-num-cell jz-text-muted">${fmtHours(tot_comp)}</td>
                <td class="jz-num-cell jz-text-primary"><strong>${fmtHours(tot_payable_ot_all)}</strong></td>
                <td class="jz-num-cell jz-text-success">${tot_m} 次</td>
                <td class="jz-text-muted">-</td>
            </tr>
        `);
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

    // ==========================================
    // 2.1 考勤双视角（原始打卡底册矩阵 vs 分类结算汇总）
    // ==========================================
    let raw_metric_filter = 'all';

    // Tab 2 双视角原位分段切换
    $('#jz-att-view-mode .jz-segment-btn').on('click', function() {
        $('#jz-att-view-mode .jz-segment-btn').removeClass('active');
        $(this).addClass('active');
        const mode = $(this).data('mode');
        if (mode === 'raw') {
            $('#box-jz-view-raw').removeClass('jz-hidden');
            $('#box-jz-view-summary').addClass('jz-hidden');
            $('#jz-raw-filter-metric').removeClass('jz-hidden');
            $('#btn-jz-export-raw-attendance').removeClass('jz-hidden');
            $('#btn-jz-export-summary-attendance').addClass('jz-hidden');
        } else {
            $('#box-jz-view-raw').addClass('jz-hidden');
            $('#box-jz-view-summary').removeClass('jz-hidden');
            $('#jz-raw-filter-metric').addClass('jz-hidden');
            $('#btn-jz-export-raw-attendance').addClass('jz-hidden');
            $('#btn-jz-export-summary-attendance').removeClass('jz-hidden');
        }
    });

    // 原始打卡矩阵维度过滤
    $('#jz-raw-filter-metric .jz-segment-btn').on('click', function() {
        $('#jz-raw-filter-metric .jz-segment-btn').removeClass('active');
        $(this).addClass('active');
        raw_metric_filter = $(this).data('metric');
        render_raw_attendance_table();
    });

    function render_raw_attendance_table() {
        const thead = $('#thead-jz-raw-attendance');
        const tbody = $('#tbody-jz-raw-attendance');
        thead.empty();
        tbody.empty();

        if (!attendance_cache || attendance_cache.length === 0) {
            tbody.html('<tr><td colspan="45" class="jz-empty-cell">当前月份尚未上传考勤表，请点击“上传月度考勤 (Excel)”按钮。</td></tr>');
            return;
        }

        // 提取打卡日历天数
        let days = [];
        for (let i = 0; i < attendance_cache.length; i++) {
            if (attendance_cache[i].daily_records_json) {
                try {
                    const parsed = JSON.parse(attendance_cache[i].daily_records_json);
                    if (parsed && parsed.length > 0) {
                        days = parsed;
                        break;
                    }
                } catch(e) {}
            }
        }

        if (!days || days.length === 0) {
            tbody.html('<tr><td colspan="45" class="jz-empty-cell">该月份无每日结构化打卡明细。</td></tr>');
            return;
        }

        // 1. 构建表头
        let thHtml = `
            <tr>
                <th class="jz-col-seq jz-col-sticky-1">序号</th>
                <th class="jz-col-no jz-col-sticky-2">工号</th>
                <th class="jz-col-name jz-col-sticky-3">姓名</th>
                <th class="jz-raw-col-metric jz-col-sticky-4">打卡项目</th>
        `;

        days.forEach(d => {
            let cls = 'jz-raw-day-th';
            let tag = '班';
            const nat = d.nature || '';
            if (nat.includes('周末') || nat.includes('公休')) {
                cls += ' jz-th-weekend';
                tag = '休';
            } else if (nat.includes('节假日')) {
                cls += ' jz-th-holiday';
                tag = '节';
            }
            thHtml += `
                <th class="${cls}">
                    <div class="jz-th-daynum">${d.day}日</div>
                    <div class="jz-th-tag">${tag}</div>
                </th>
            `;
        });

        thHtml += `
                <th class="jz-text-right">正班工时</th>
                <th class="jz-text-right">平日加班</th>
                <th class="jz-text-right">周末加班</th>
                <th class="jz-text-right">节日加班</th>
                <th class="jz-text-right">倒休工时</th>
                <th class="jz-text-right">餐补次数</th>
            </tr>
        `;
        thead.html(thHtml);

        // 2. 筛选展示的打卡项目
        const allMetrics = [
            { key: 'shifts', label: '班次', badgeCls: 'jz-mb-shift' },
            { key: 'work', label: '作业工时', badgeCls: 'jz-mb-work' },
            { key: 'ot', label: '加班工时', badgeCls: 'jz-mb-ot' },
            { key: 'meal', label: '订餐', badgeCls: 'jz-mb-meal' },
            { key: 'remark', label: '备注', badgeCls: 'jz-mb-remark' }
        ];

        let activeMetrics = allMetrics;
        if (raw_metric_filter !== 'all') {
            activeMetrics = allMetrics.filter(m => m.key === raw_metric_filter);
        }
        const rSpan = activeMetrics.length;

        // 3. 逐人渲染行
        attendance_cache.forEach((emp, idx) => {
            let empDays = [];
            try {
                if (emp.daily_records_json) empDays = JSON.parse(emp.daily_records_json);
            } catch(e) {}
            const dayMap = {};
            empDays.forEach(d => { dayMap[d.day] = d; });

            activeMetrics.forEach((m, mIdx) => {
                const isFirst = (mIdx === 0);
                const isLast = (mIdx === rSpan - 1);
                let rowCls = isLast ? 'jz-raw-row-boundary' : '';

                let trHtml = `<tr class="${rowCls}">`;

                if (isFirst) {
                    trHtml += `
                        <td class="jz-col-seq jz-col-sticky-1" rowspan="${rSpan}">${idx + 1}</td>
                        <td class="jz-col-no jz-col-sticky-2" rowspan="${rSpan}"><strong>${emp.employee_no}</strong></td>
                        <td class="jz-col-name jz-col-sticky-3" rowspan="${rSpan}"><strong>${emp.employee_name}</strong></td>
                    `;
                }

                trHtml += `
                    <td class="jz-raw-col-metric jz-col-sticky-4">
                        <span class="jz-metric-badge ${m.badgeCls}">${m.label}</span>
                    </td>
                `;

                // 逐日单元格
                days.forEach(d => {
                    const dayRec = dayMap[d.day] || {};
                    let cellVal = '-';
                    let cellCls = '';
                    const nat = d.nature || '';
                    if (nat.includes('周末') || nat.includes('公休')) cellCls += ' jz-cell-weekend';
                    else if (nat.includes('节假日')) cellCls += ' jz-cell-holiday';

                    if (m.key === 'shifts') {
                        cellVal = dayRec.shift || '-';
                        cellCls += ' jz-raw-val-shift';
                    } else if (m.key === 'work') {
                        const wh = flt(dayRec.work_hours);
                        cellVal = wh > 0 ? wh.toFixed(1) : '-';
                        cellCls += ' jz-raw-val-work';
                    } else if (m.key === 'ot') {
                        const ot = flt(dayRec.overtime);
                        cellVal = ot > 0 ? '+' + ot.toFixed(1) : '-';
                        cellCls += ' jz-raw-val-ot';
                    } else if (m.key === 'meal') {
                        const ml = cint(dayRec.meal);
                        cellVal = ml > 0 ? ml : '-';
                        cellCls += ' jz-raw-val-meal';
                    } else if (m.key === 'remark') {
                        cellVal = dayRec.remark || '-';
                        cellCls += ' jz-raw-val-remark';
                    }

                    trHtml += `<td class="${cellCls}">${cellVal}</td>`;
                });

                if (isFirst) {
                    trHtml += `
                        <td class="jz-num-cell jz-text-info" rowspan="${rSpan}">${fmtHours(emp.work_hours_regular)}</td>
                        <td class="jz-num-cell" rowspan="${rSpan}">${fmtHours(emp.overtime_regular_1_5)}</td>
                        <td class="jz-num-cell" rowspan="${rSpan}">${fmtHours(emp.overtime_weekend_2_0)}</td>
                        <td class="jz-num-cell" rowspan="${rSpan}">${fmtHours(emp.overtime_holiday_3_0)}</td>
                        <td class="jz-num-cell jz-text-muted" rowspan="${rSpan}">${fmtHours(emp.leave_compensatory_hours)}</td>
                        <td class="jz-num-cell jz-text-success" rowspan="${rSpan}">${emp.meal_count || 0} 次</td>
                    `;
                }

                trHtml += '</tr>';
                tbody.append(trHtml);
            });
        });
    }

    // 导出原始考勤表 (Excel / CSV)
    $('#btn-jz-export-raw-attendance').on('click', function() {
        if (!attendance_cache || attendance_cache.length === 0) {
            frappe.msgprint('当前月份暂无考勤数据可导出');
            return;
        }
        let days = [];
        for (let i = 0; i < attendance_cache.length; i++) {
            if (attendance_cache[i].daily_records_json) {
                try {
                    days = JSON.parse(attendance_cache[i].daily_records_json);
                    if (days && days.length > 0) break;
                } catch(e) {}
            }
        }
        let csv = '\uFEFF序号,工号,姓名,打卡项目,' + days.map(d => `${d.day}日(${d.nature || ''})`).join(',') + ',正班工时,平日加班,周末加班,节日加班,倒休工时,餐补次数\n';
        attendance_cache.forEach((emp, idx) => {
            let empDays = [];
            try {
                if (emp.daily_records_json) empDays = JSON.parse(emp.daily_records_json);
            } catch(e) {}
            const dayMap = {};
            empDays.forEach(d => { dayMap[d.day] = d; });

            const metricDefs = [
                { key: 'shifts', label: '班次' },
                { key: 'work', label: '作业工时' },
                { key: 'ot', label: '加班工时' },
                { key: 'meal', label: '订餐' },
                { key: 'remark', label: '备注' }
            ];

            metricDefs.forEach((m, mIdx) => {
                let row = [
                    mIdx === 0 ? (idx + 1) : '',
                    mIdx === 0 ? emp.employee_no : '',
                    mIdx === 0 ? `"${emp.employee_name}"` : '',
                    m.label
                ];
                days.forEach(d => {
                    const dayRec = dayMap[d.day] || {};
                    let v = '';
                    if (m.key === 'shifts') v = dayRec.shift || '';
                    else if (m.key === 'work') v = dayRec.work_hours > 0 ? flt(dayRec.work_hours).toFixed(1) : '';
                    else if (m.key === 'ot') v = dayRec.overtime > 0 ? flt(dayRec.overtime).toFixed(1) : '';
                    else if (m.key === 'meal') v = dayRec.meal > 0 ? dayRec.meal : '';
                    else if (m.key === 'remark') v = (dayRec.remark || '').replace(/"/g, '""');
                    row.push(`"${v}"`);
                });
                if (mIdx === 0) {
                    row.push(flt(emp.work_hours_regular).toFixed(1));
                    row.push(flt(emp.overtime_regular_1_5).toFixed(1));
                    row.push(flt(emp.overtime_weekend_2_0).toFixed(1));
                    row.push(flt(emp.overtime_holiday_3_0).toFixed(1));
                    row.push(flt(emp.leave_compensatory_hours).toFixed(1));
                    row.push(emp.meal_count || 0);
                } else {
                    row.push('', '', '', '', '', '');
                }
                csv += row.join(',') + '\n';
            });
        });

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.setAttribute('download', `吉众原始打卡考勤表_${current_month}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // 导出结算汇总表 (CSV / Excel)
    $('#btn-jz-export-summary-attendance').on('click', function() {
        if (!attendance_cache || attendance_cache.length === 0) {
            frappe.msgprint('当前月份暂无考勤数据可导出');
            return;
        }
        let csv = '\uFEFF序号,工号,姓名,出勤天数,出勤正班工时,平日加班(1.5x),周末加班(2.0x),节日加班(3.0x),加班工时合计,倒休冲抵工时,实际计薪加班,订餐补贴次数,打卡备注与请假汇总\n';
        attendance_cache.forEach((it, idx) => {
            const wReg = flt(it.work_hours_regular);
            const ot15 = flt(it.overtime_regular_1_5);
            const ot20 = flt(it.overtime_weekend_2_0);
            const ot30 = flt(it.overtime_holiday_3_0);
            const cLeave = flt(it.leave_compensatory_hours);
            const mCount = cint(it.meal_count);

            const tot_ot_emp = ot15 + ot20 + ot30;
            const actual_payable_ot = ot15 + Math.max(0, ot20 - cLeave) + ot30;

            let remark_counts = {};
            let rest_days = 0;
            if (it.daily_records_json) {
                try {
                    const days = JSON.parse(it.daily_records_json);
                    days.forEach(d => {
                        if (d.remark) {
                            const rm = d.remark.trim();
                            if (rm === '休') {
                                rest_days++;
                            } else if (rm) {
                                remark_counts[rm] = (remark_counts[rm] || 0) + 1;
                            }
                        }
                    });
                } catch(e) {}
            }
            let rText = [];
            if (rest_days > 0) rText.push(`公休 ${rest_days}天`);
            for (const [rm, count] of Object.entries(remark_counts)) {
                let label = rm;
                if (rm === '事') label = '事假';
                else if (rm === '病') label = '病假';
                rText.push(`${label} ${count}天`);
            }
            const final_r = rText.length > 0 ? rText.join(' · ') : '-';

            csv += `${idx + 1},${it.employee_no},"${it.employee_name}",${it.attendance_days || 0},${wReg.toFixed(1)},${ot15.toFixed(1)},${ot20.toFixed(1)},${ot30.toFixed(1)},${tot_ot_emp.toFixed(1)},${cLeave.toFixed(1)},${actual_payable_ot.toFixed(1)},${mCount},"${final_r}"\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.setAttribute('download', `吉众月度工时分类结算汇总_${current_month}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // 4. 加载现金发放与配钞点钞表
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

    // 1. 加载员工薪资信息表 (对应 Excel [人员薪资信息] sheets)
    let employees_cache = [];

    function load_employees_data() {
        frappe.call({
            method: 'ashan_cn_procurement.services.jizhong_payroll_service.get_jizhong_employee_profiles',
            args: { company: COMPANY },
            callback: function(r) {
                employees_cache = r.message || [];
                render_employees_table();
            }
        });
    }

    function render_employees_table() {
        const tbody = $('#tbody-jz-employees');
        tbody.empty();

        const searchKw = ($('#jz-emp-search').val() || '').trim().toLowerCase();
        const typeFilter = $('#jz-emp-type-filter .jz-segment-btn.active').data('type') || 'all';

        let filtered = employees_cache.filter(it => {
            if (searchKw) {
                const matchKw = (it.employee_no || '').toLowerCase().includes(searchKw) ||
                                (it.employee_name || '').toLowerCase().includes(searchKw) ||
                                (it.id_card || '').toLowerCase().includes(searchKw) ||
                                (it.salary_mode || '').toLowerCase().includes(searchKw);
                if (!matchKw) return false;
            }
            if (typeFilter === 'regular') return it.employee_type === '正式工';
            if (typeFilter === 'other') return it.employee_type !== '正式工' || (it.employee_type && it.employee_type.includes('其他'));
            return true;
        });

        if (filtered.length === 0) {
            tbody.html('<tr><td colspan="17" class="jz-empty-cell">暂无符合条件的员工薪资档案</td></tr>');
            $('#tfoot-jz-employees').empty();
            return;
        }

        let tot_base = 0, tot_sub = 0, tot_perf = 0, tot_post = 0, tot_ss = 0, tot_hf = 0, tot_ded = 0;

        filtered.forEach((it, idx) => {
            const bSal = flt(it.base_salary);
            const bSub = flt(it.house_rent_allowance) || flt(it.other_allowance) || 0;
            const perf = flt(it.performance_base);
            const post = flt(it.post_allowance);
            const meal = flt(it.meal_allowance);
            const ssBase = flt(it.social_security_base);
            const hfBase = flt(it.housing_fund_base);
            const dedTotal = flt(it.deduction_child_education) + flt(it.deduction_continuing_education) +
                             flt(it.deduction_housing_loan) + flt(it.deduction_housing_rent) +
                             flt(it.deduction_elderly_care) + flt(it.deduction_infant_care) + flt(it.deduction_serious_illness);

            tot_base += bSal;
            tot_sub += bSub;
            tot_perf += perf;
            tot_post += post;
            tot_ss += ssBase;
            tot_hf += hfBase;
            tot_ded += dedTotal;

            const isMgmt = it.salary_mode && it.salary_mode.includes('税后管理');
            const netAgreed = isMgmt ? fmtMoney(it.fixed_salary) : '-';

            tbody.append(`
                <tr class="jz-emp-row jz-row-clickable" data-name="${it.name}" data-empno="${it.employee_no}">
                    <td class="jz-col-seq jz-col-sticky-1">${idx + 1}</td>
                    <td class="jz-col-no jz-col-sticky-2"><strong>${it.employee_no}</strong></td>
                    <td class="jz-col-name jz-col-sticky-3"><strong>${it.employee_name}</strong></td>
                    <td class="jz-font-mono">${it.id_card || '-'}</td>
                    <td><span class="jz-tag">${it.employee_type || '正式工'}</span></td>
                    <td>${it.salary_mode || '税前动态工资'}</td>
                    <td class="jz-money-cell ${isMgmt ? 'jz-money-bold jz-text-primary' : ''}">${netAgreed}</td>
                    <td class="jz-money-cell jz-text-info">${fmtMoney(bSal)}</td>
                    <td class="jz-money-cell">${fmtMoney(bSub)}</td>
                    <td class="jz-money-cell">${fmtMoney(perf)}</td>
                    <td class="jz-money-cell">${fmtMoney(post)}</td>
                    <td class="jz-money-cell">${meal > 0 ? fmtMoney(meal) + ' / 份' : '-'}</td>
                    <td class="jz-money-cell">${fmtMoney(ssBase)}</td>
                    <td class="jz-money-cell">${fmtMoney(hfBase)}</td>
                    <td class="jz-money-cell jz-text-warn">${dedTotal > 0 ? fmtMoney(dedTotal) : '-'}</td>
                    <td class="jz-text-center"><span class="jz-status-badge jz-status-submitted">${it.employment_status || '在职'}</span></td>
                    <td class="jz-col-action"><a href="javascript:void(0)" class="jz-btn-action jz-btn-edit-emp" data-empno="${it.employee_no}">编辑</a></td>
                </tr>
            `);
        });

        // 绑定行点击与编辑按钮事件
        tbody.find('.jz-btn-edit-emp').on('click', function(e) {
            e.stopPropagation();
            const empNo = $(this).data('empno');
            const emp = employees_cache.find(it => it.employee_no === empNo);
            if (emp) open_jizhong_employee_edit_dialog(emp, false);
        });

        tbody.find('.jz-emp-row').on('click', function() {
            const empNo = $(this).data('empno');
            const emp = employees_cache.find(it => it.employee_no === empNo);
            if (emp) open_jizhong_employee_edit_dialog(emp, false);
        });

        // 汇总卡片更新
        $('#jz-emp-kpi-count').text(`${filtered.length} 人`);
        $('#jz-emp-kpi-base').text(fmtMoney(tot_base));
        $('#jz-emp-kpi-allowance').text(fmtMoney(tot_sub + tot_perf + tot_post));
        $('#jz-emp-kpi-post').text(fmtMoney(tot_post));
        $('#jz-emp-kpi-perf').text(fmtMoney(tot_perf));
        $('#jz-emp-kpi-ins').text(fmtMoney(tot_ss + tot_hf));
        $('#jz-emp-kpi-ss').text(fmtMoney(tot_ss));
        $('#jz-emp-kpi-hf').text(fmtMoney(tot_hf));

        // 底部合计行
        $('#tfoot-jz-employees').html(`
            <tr>
                <td colspan="3" class="jz-col-foot-label">合计 (${filtered.length}人)</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td class="jz-money-cell jz-text-info">${fmtMoney(tot_base)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_sub)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_perf)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_post)}</td>
                <td>-</td>
                <td class="jz-money-cell">${fmtMoney(tot_ss)}</td>
                <td class="jz-money-cell">${fmtMoney(tot_hf)}</td>
                <td class="jz-money-cell jz-text-warn">${fmtMoney(tot_ded)}</td>
                <td class="jz-text-center">-</td>
                <td class="jz-col-action">-</td>
            </tr>
        `);
    }

    // 员工档案编辑与明细修改弹窗 (对标祺富工作台高质量交互)
    function open_jizhong_employee_edit_dialog(emp_data, is_new) {
        emp_data = emp_data || {};
        const isEdit = !is_new && emp_data.employee_no;

        const d = new frappe.ui.Dialog({
            title: isEdit ? `修改员工薪资档案 · ${emp_data.employee_name} (${emp_data.employee_no})` : `新增吉众员工薪酬档案`,
            size: 'large',
            fields: [
                { fieldtype: 'Section Break', label: '基本身份与用工' },
                { fieldtype: 'Data', fieldname: 'employee_no', label: '工号', reqd: 1, default: emp_data.employee_no || '', read_only: isEdit ? 1 : 0 },
                { fieldtype: 'Data', fieldname: 'employee_name', label: '员工姓名', reqd: 1, default: emp_data.employee_name || '' },
                { fieldtype: 'Select', fieldname: 'certificate_type', label: '证件类型', options: ['居民身份证','护照','港澳台居民居住证/通行证','外国人永久居留身份证','其他'], default: emp_data.certificate_type || '居民身份证' },
                { fieldtype: 'Data', fieldname: 'id_card', label: '证件号码', default: emp_data.id_card || '' },
                { fieldtype: 'Button', fieldname: 'btn_parse_id_card', label: '自动识别身份证性别出生日期' },
                { fieldtype: 'Column Break' },
                { fieldtype: 'Select', fieldname: 'gender', label: '性别', options: ['','男','女'], default: emp_data.gender || '' },
                { fieldtype: 'Date', fieldname: 'birth_date', label: '出生日期', default: emp_data.birth_date || '' },
                { fieldtype: 'Data', fieldname: 'mobile', label: '手机号', default: emp_data.mobile || '' },
                { fieldtype: 'Select', fieldname: 'employee_type', label: '用工性质', options: ['正式工','其他'], default: (emp_data.employee_type === '正式工' ? '正式工' : (emp_data.employee_type ? '其他' : '正式工')) },
                { fieldtype: 'Select', fieldname: 'employment_status', label: '在职状态', options: ['在职','离职'], default: emp_data.employment_status || '在职' },

                { fieldtype: 'Section Break', label: '薪酬长期要素' },
                { fieldtype: 'Select', fieldname: 'salary_mode', label: '计薪方式', options: ['税前动态工资','税后管理工资'], default: emp_data.salary_mode || '税前动态工资' },
                { fieldtype: 'Currency', fieldname: 'fixed_salary', label: '实发约定净薪 (元)', default: emp_data.fixed_salary || 0, description: '税后管理岗如陈亮、苏锡成约定实发金额' },
                { fieldtype: 'Currency', fieldname: 'base_salary', label: '基本工资 (元)', default: emp_data.base_salary || 0, reqd: 1 },
                { fieldtype: 'Column Break' },
                { fieldtype: 'Currency', fieldname: 'house_rent_allowance', label: '基本补贴 (元)', default: emp_data.house_rent_allowance || 0 },
                { fieldtype: 'Currency', fieldname: 'performance_base', label: '绩效奖金 (元)', default: emp_data.performance_base || 0 },
                { fieldtype: 'Currency', fieldname: 'post_allowance', label: '职位津贴 (元)', default: emp_data.post_allowance || 0 },
                { fieldtype: 'Currency', fieldname: 'meal_allowance', label: '餐补单价 (元/餐)', default: emp_data.meal_allowance || 15.0 },

                { fieldtype: 'Section Break', label: '社保与公积金申报基数' },
                { fieldtype: 'Currency', fieldname: 'social_security_base', label: '社险申报基数 (元)', default: emp_data.social_security_base || 5124.0 },
                { fieldtype: 'Column Break' },
                { fieldtype: 'Currency', fieldname: 'housing_fund_base', label: '公积金申报基数 (元)', default: emp_data.housing_fund_base || 2520.0 },

                { fieldtype: 'Section Break', label: '7项个税专项附加扣除详情 (元/月)' },
                { fieldtype: 'Currency', fieldname: 'deduction_child_education', label: '子女教育', default: emp_data.deduction_child_education || 0 },
                { fieldtype: 'Currency', fieldname: 'deduction_continuing_education', label: '继续教育', default: emp_data.deduction_continuing_education || 0 },
                { fieldtype: 'Currency', fieldname: 'deduction_serious_illness', label: '大病医疗', default: emp_data.deduction_serious_illness || 0 },
                { fieldtype: 'Currency', fieldname: 'deduction_housing_loan', label: '住房贷款利息', default: emp_data.deduction_housing_loan || 0 },
                { fieldtype: 'Column Break' },
                { fieldtype: 'Currency', fieldname: 'deduction_housing_rent', label: '住房租金', default: emp_data.deduction_housing_rent || 0 },
                { fieldtype: 'Currency', fieldname: 'deduction_elderly_care', label: '赡养老人', default: emp_data.deduction_elderly_care || 0 },
                { fieldtype: 'Currency', fieldname: 'deduction_infant_care', label: '3岁以下婴幼儿照护', default: emp_data.deduction_infant_care || 0 },

                { fieldtype: 'Section Break', label: '银行卡与备注' },
                { fieldtype: 'Data', fieldname: 'bank_name', label: '开户银行', default: emp_data.bank_name || '' },
                { fieldtype: 'Data', fieldname: 'bank_account', label: '银行卡号', default: emp_data.bank_account || '' },
                { fieldtype: 'Column Break' },
                { fieldtype: 'Small Text', fieldname: 'notes', label: '备注说明', default: emp_data.notes || '' }
            ],
            primary_action_label: isEdit ? '保存修改' : '立即创建',
            primary_action(vals) {
                vals.company = COMPANY;
                if (isEdit) {
                    vals.name = emp_data.name;
                }
                frappe.call({
                    method: 'ashan_cn_procurement.services.jizhong_payroll_service.save_jizhong_employee_profile',
                    type: 'POST',
                    args: { data: JSON.stringify(vals) },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.show_alert({ message: r.message.message, indicator: 'green' });
                            d.hide();
                            load_employees_data();
                        }
                    }
                });
            }
        });

        // 识别身份证号码获取出生日期和性别
        function parse_and_apply_id_card(silent) {
            const certType = d.get_value('certificate_type') || '居民身份证';
            if (certType !== '居民身份证') {
                if (!silent) {
                    frappe.msgprint('当前证件类型非居民身份证，无法自动识别，请手动选择性别与出生日期。');
                }
                return;
            }
            const idVal = (d.get_value('id_card') || '').trim().toUpperCase();
            if (!idVal) {
                if (!silent) frappe.msgprint('请先输入居民身份证号码。');
                return;
            }
            if (idVal.length === 18 && /^\d{17}[\dXx]$/.test(idVal)) {
                const year = idVal.substring(6, 10);
                const month = idVal.substring(10, 12);
                const day = idVal.substring(12, 14);
                const birthDate = `${year}-${month}-${day}`;
                const genderCode = parseInt(idVal.substring(16, 17), 10);
                const gender = (genderCode % 2 === 1) ? '男' : '女';

                d.set_value('birth_date', birthDate);
                d.set_value('gender', gender);
                if (!silent) {
                    frappe.show_alert({
                        message: `身份证识别成功：${gender}性，出生日期 ${birthDate}`,
                        indicator: 'green'
                    });
                }
            } else if (idVal.length === 15 && /^\d{15}$/.test(idVal)) {
                const year = '19' + idVal.substring(6, 8);
                const month = idVal.substring(8, 10);
                const day = idVal.substring(10, 12);
                const birthDate = `${year}-${month}-${day}`;
                const genderCode = parseInt(idVal.substring(14, 15), 10);
                const gender = (genderCode % 2 === 1) ? '男' : '女';

                d.set_value('birth_date', birthDate);
                d.set_value('gender', gender);
                if (!silent) {
                    frappe.show_alert({
                        message: `身份证识别成功：${gender}性，出生日期 ${birthDate}`,
                        indicator: 'green'
                    });
                }
            } else if (!silent) {
                frappe.msgprint('请输入有效的18位居民身份证号码。');
            }
        }

        d.show();

        // 绑定按钮事件与失去焦点自动识别
        if (d.fields_dict.btn_parse_id_card) {
            const $btn = d.fields_dict.btn_parse_id_card.$input || $(d.fields_dict.btn_parse_id_card.input);
            $btn.on('click', function() {
                parse_and_apply_id_card(false);
            });
        }
        if (d.fields_dict.id_card && d.fields_dict.id_card.$input) {
            d.fields_dict.id_card.$input.on('blur', function() {
                if ((d.get_value('certificate_type') || '居民身份证') === '居民身份证') {
                    const val = (d.get_value('id_card') || '').trim();
                    if (val.length === 18 && (!d.get_value('birth_date') || !d.get_value('gender'))) {
                        parse_and_apply_id_card(true);
                    }
                }
            });
        }
    }

    // 新建员工薪资档案按钮事件绑定
    $('#btn-jz-add-emp').on('click', function() {
        open_jizhong_employee_edit_dialog(null, true);
    });

    // 搜索与过滤事件绑定
    $('#jz-emp-search').on('input', function() {
        render_employees_table();
    });

    $('#jz-emp-type-filter .jz-segment-btn').on('click', function() {
        $('#jz-emp-type-filter .jz-segment-btn').removeClass('active');
        $(this).addClass('active');
        render_employees_table();
    });

    // 导出员工薪资信息表 (Excel CSV 带 UTF-8 BOM)
    $('#btn-jz-export-employees').on('click', function() {
        if (!employees_cache || employees_cache.length === 0) {
            frappe.msgprint('暂无员工薪资信息可导出');
            return;
        }
        let csv = '\uFEFF序号,工号,姓名,身份证号,用工性质,计薪方式,实发约定净薪,基本工资,基本补贴,绩效奖金,职位津贴,餐补单价,社险基数,公积金基数,专项附加扣除,在职状态\n';
        employees_cache.forEach((it, idx) => {
            const bSal = flt(it.base_salary);
            const bSub = flt(it.house_rent_allowance) || flt(it.other_allowance) || 0;
            const perf = flt(it.performance_base);
            const post = flt(it.post_allowance);
            const meal = flt(it.meal_allowance);
            const ssBase = flt(it.social_security_base);
            const hfBase = flt(it.housing_fund_base);
            const dedTotal = flt(it.deduction_child_education) + flt(it.deduction_continuing_education) +
                             flt(it.deduction_housing_loan) + flt(it.deduction_housing_rent) +
                             flt(it.deduction_elderly_care) + flt(it.deduction_infant_care) + flt(it.deduction_serious_illness);
            const isMgmt = it.salary_mode && it.salary_mode.includes('税后管理');
            const netAgreed = isMgmt ? flt(it.fixed_salary).toFixed(2) : '-';

            csv += `${idx + 1},${it.employee_no},"${it.employee_name}","${it.id_card || ''}",${it.employee_type || '正式工'},${it.salary_mode || '税前动态工资'},${netAgreed},${bSal.toFixed(2)},${bSub.toFixed(2)},${perf.toFixed(2)},${post.toFixed(2)},${meal > 0 ? meal.toFixed(2) : '-'},${ssBase.toFixed(2)},${hfBase.toFixed(2)},${dedTotal.toFixed(2)},${it.employment_status || '在职'}\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.setAttribute('download', `吉众员工薪资信息底册_${frappe.datetime.now_date()}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // 新建员工薪酬档案
    $('#btn-jz-add-emp').on('click', function() {
        frappe.new_doc('Ashan Employee Salary Profile', { company: COMPANY });
    });

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

    // 默认首帧激活 Tab 1: 员工薪资信息表
    current_tab = 'employees';
    load_employees_data();
};
