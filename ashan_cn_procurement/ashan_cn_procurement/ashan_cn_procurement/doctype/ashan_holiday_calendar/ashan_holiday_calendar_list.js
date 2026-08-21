// Copyright (c) 2026, Ashan CN Procurement
// 法定日历与节假日综合中枢 (Ashan Holiday Calendar Workbench)
// 依据国务院最新《全国年节及纪念日放假办法》与《劳动法》：
// 🔴 法定 3 倍工资日：法律强制支付 300% 加班工资，绝对不可倒休/补休替代！
// 🔵 普通公休日/调休放假：支付 200% 加班工资，企业可优先安排倒休/补休。

frappe.listview_settings['Ashan Holiday Calendar'] = {
    hide_name_column: true,
    onload: function(listview) {
        render_holiday_workbench(listview);
    }
};

function render_holiday_workbench(listview) {
    let current_year = 2026;
    let current_view_mode = 'year'; // 'year', 'month', or 'list'
    let current_selected_month = 1; // 1 ~ 12
    let active_tab = 'calendar'; // 'settings' or 'calendar'
    let calendar_cache = null;
    let list_filter = 'all'; // 'all', 'legal_3x', 'shift_off', 'shift_work', 'workday'

    let $page = listview.page.main;
    $page.find('.holiday-workbench-wrapper').remove();

    let $wb = $(`
        <div class="holiday-workbench-wrapper" style="background:#f8fafc; border-bottom:1px solid #e2e8f0; padding:16px 20px; margin:-15px -15px 15px -15px; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
            
            <!-- 1. 顶部 Header 36px 统一高度控制栏 -->
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:16px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="font-size:22px;">📅</div>
                    <div>
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span style="font-size:16px; font-weight:800; color:#0f172a; letter-spacing:-0.02em;">法定日历与节假日综合中枢</span>
                            <span style="font-size:10px; font-weight:700; color:#b91c1c; background:#fee2e2; border:1px solid #fca5a5; padding:1px 8px; border-radius:10px;">国务院最新放假办法 · 3倍/2倍加班与倒休合规</span>
                        </div>
                        <div style="font-size:11px; color:#64748b; margin-top:2px;">法定3倍工资日强制不可倒休 · 调休/公休2倍工资可倒休 · 年/月/列表三视图全景联动</div>
                    </div>
                </div>

                <div style="display:flex; align-items:center; gap:8px;">
                    <!-- 年份切换器 -->
                    <div class="btn-group btn-group-sm" role="group" style="height:34px;">
                        <button type="button" class="btn btn-default" id="btn-prev-year" style="font-weight:600; padding:4px 10px; font-size:12px;">◀ 上一年</button>
                        <button type="button" class="btn btn-default" id="btn-curr-year-display" style="font-weight:800; color:#1d4ed8; background:#eff6ff; font-size:13px; min-width:85px;">${current_year} 年</button>
                        <button type="button" class="btn btn-default" id="btn-next-year" style="font-weight:600; padding:4px 10px; font-size:12px;">下一年 ▶</button>
                    </div>

                    <button class="btn btn-default btn-sm" id="btn-load-template" style="height:34px; font-size:12px; font-weight:600; background:#f0fdf4; color:#15803d; border-color:#bbf7d0;">
                        ⚡ 载入国务院官方模板 (13天法定)
                    </button>
                    <button class="btn btn-default btn-sm" id="btn-refresh-calendar" style="height:34px; font-size:12px; font-weight:600;">
                        🔄 刷新日历
                    </button>
                </div>
            </div>

            <!-- 2. 防抖零位移 Tab 导航栏 -->
            <div class="qifu-tabs-nav" style="display:flex; gap:8px; border-bottom:1px solid #e2e8f0; margin-bottom:16px;">
                <button class="qifu-tab-btn active" data-tab="calendar" style="font-size:12.5px; font-weight:600; color:#1d4ed8; background:#eff6ff; border:none; border-bottom:3px solid #2563eb; padding:8px 16px; cursor:pointer; border-radius:4px 4px 0 0; transition:all 0.15s ease;">
                    🗓️ 1. 全年智能日历中枢 (年视图 / 月视图 / 列表版)
                </button>
                <button class="qifu-tab-btn" data-tab="settings" style="font-size:12.5px; font-weight:600; color:#475569; background:transparent; border:none; border-bottom:3px solid transparent; padding:8px 16px; cursor:pointer; border-radius:4px 4px 0 0; transition:all 0.15s ease;">
                    ✨ 2. 本年法定节假日与调休补班排程 (可视化丝滑配置)
                </button>
            </div>

            <!-- 3. Tab 1 内容：日历与列表视图 -->
            <div id="tab-content-calendar" class="holiday-tab-pane">
                <!-- 4 大核心 KPI 统计卡片 -->
                <div id="holiday-kpi-container" style="display:grid; grid-template-columns: repeat(4, 1fr); gap:12px; margin-bottom:16px;"></div>

                <!-- 视图切换与控制工具栏 -->
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:12px; background:#ffffff; border:1px solid #e2e8f0; border-radius:6px; padding:8px 14px;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="font-size:12px; font-weight:700; color:#334155;">日历视图模式：</span>
                        <div class="btn-group btn-group-xs" role="group">
                            <button type="button" class="btn btn-default btn-view-mode active" data-mode="year" style="font-weight:700; font-size:11.5px; background:#eff6ff; color:#1d4ed8; border-color:#bfdbfe;">📑 全年 12 个月矩阵</button>
                            <button type="button" class="btn btn-default btn-view-mode" data-mode="month" style="font-weight:600; font-size:11.5px;">🔍 单月放大聚焦视图</button>
                            <button type="button" class="btn btn-default btn-view-mode" data-mode="list" style="font-weight:600; font-size:11.5px;">📋 列表明细版 (365天与加班倍率)</button>
                        </div>
                    </div>

                    <!-- 法律与图例说明 -->
                    <div style="display:flex; align-items:center; gap:12px; font-size:11px;">
                        <span style="display:inline-flex; align-items:center; gap:4px;"><span style="width:12px; height:12px; border-radius:2px; background:#fee2e2; border:1px solid #fca5a5; display:inline-block;"></span> <b style="color:#b91c1c;">🔴 法定节日(3倍工资·不可倒休)</b></span>
                        <span style="display:inline-flex; align-items:center; gap:4px;"><span style="width:12px; height:12px; border-radius:2px; background:#eff6ff; border:1px solid #bfdbfe; display:inline-block;"></span> <span style="color:#1d4ed8;">🔵 调休/公休(2倍工资·可倒休)</span></span>
                        <span style="display:inline-flex; align-items:center; gap:4px;"><span style="width:12px; height:12px; border-radius:2px; background:#ffedd5; border:1px solid #fdba74; display:inline-block;"></span> <span style="color:#ea580c;">🟠 调班补班(100%工作日)</span></span>
                        <span style="display:inline-flex; align-items:center; gap:4px;"><span style="width:12px; height:12px; border-radius:2px; background:#ffffff; border:1px solid #e2e8f0; display:inline-block;"></span> ⚪ 正常工作日</span>
                    </div>
                </div>

                <!-- 视图 1: 年视图容器 -->
                <div id="calendar-year-view-box"></div>

                <!-- 视图 2: 月视图容器 -->
                <div id="calendar-month-view-box" style="display:none;"></div>

                <!-- 视图 3: 列表视图容器 -->
                <div id="calendar-list-view-box" style="display:none;"></div>

                <!-- 底部 12 个月标准工作日汇总统计表 -->
                <div id="month-workdays-summary-box" style="margin-top:16px;"></div>
            </div>

            <!-- Tab 2 内容：可视化丝滑排程配置 -->
            <div id="tab-content-settings" class="holiday-tab-pane" style="display:none;">
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:16px; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                    
                    <!-- 顶部提示与操作栏 -->
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px; border-bottom:1px solid #f1f5f9; padding-bottom:12px;">
                        <div>
                            <div style="display:flex; align-items:center; gap:8px;">
                                <span style="font-size:14px; font-weight:800; color:#0f172a;">✨ ${current_year} 年度节假日与补班可视化排程器</span>
                                <span style="font-size:10px; font-weight:700; color:#059669; background:#dcfce7; border:1px solid #86efac; padding:1px 6px; border-radius:4px;">无需手动输入日期串 · 单击胶囊秒切换3倍/2倍</span>
                            </div>
                            <div style="font-size:11.5px; color:#64748b; margin-top:3px;">
                                💡 <b>操作指南</b>：选定放假起止日期后，系统自动切片生成每日胶囊。<b>直接单击日期胶囊</b>即可在 <span style="color:#dc2626; font-weight:700;">🔴 3倍法定(不可倒休)</span> 与 <span style="color:#2563eb; font-weight:700;">🔵 2倍调休(可倒休)</span> 间无缝切换！
                            </div>
                        </div>

                        <div style="display:flex; gap:8px;">
                            <button class="btn btn-default btn-xs" id="btn-add-holiday-card" style="font-weight:700; background:#f0fdf4; color:#166534; border-color:#bbf7d0; padding:5px 12px;">
                                ➕ 新增节假日排程
                            </button>
                        </div>
                    </div>

                    <!-- 动态交互式卡片排程列表 -->
                    <div id="holiday-cards-container" style="display:flex; flex-direction:column; gap:14px;"></div>

                    <!-- 底部保存主按钮 -->
                    <div style="margin-top:20px; padding-top:14px; border-top:1px solid #e2e8f0; display:flex; justify-content:space-between; align-items:center;">
                        <div style="font-size:11.5px; color:#64748b;">
                            ⚡ 保存后系统将毫秒级全自动构建 365 天日历底册、打标 300%/200% 加班倍率并同步更新全系统考勤薪酬 API
                        </div>
                        <button class="btn btn-primary btn-sm" id="btn-save-configs-and-rebuild" style="font-size:12.5px; font-weight:800; background:#059669; border-color:#059669; padding:7px 24px; box-shadow:0 2px 4px rgba(5,150,105,0.2);">
                            🚀 保存配置并全自动生成全年日历底册
                        </button>
                    </div>

                </div>
            </div>

        </div>
    `);

    $page.prepend($wb);

    // =========================================================================
    // 渲染与数据逻辑
    // =========================================================================

    function load_calendar_data() {
        frappe.call({
            method: 'ashan_cn_procurement.services.ashan_holiday_service.get_year_calendar_matrix',
            args: { year: current_year },
            freeze: true,
            freeze_message: `正在加载【${current_year}年度】日历与节假日数据...`,
            callback: function(r) {
                if (r.message) {
                    calendar_cache = r.message;
                    render_kpi_cards(calendar_cache.kpis);
                    render_year_view(calendar_cache.months);
                    render_month_view(calendar_cache.months, current_selected_month);
                    render_list_view(calendar_cache.calendar_list, list_filter);
                    render_month_summary_table(calendar_cache.months);
                }
            }
        });
    }

    function load_config_cards_data() {
        frappe.call({
            method: 'ashan_cn_procurement.services.ashan_holiday_service.get_holiday_configs',
            args: { year: current_year },
            callback: function(r) {
                let configs = r.message || [];
                render_interactive_holiday_cards(configs);
            }
        });
    }

    function render_kpi_cards(kpis) {
        if (!kpis) return;
        let html = `
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:3.5px solid #3b82f6; border-radius:8px; padding:10px 14px; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                <div style="font-size:11px; font-weight:600; color:#64748b;">📅 全年总天数</div>
                <div style="font-size:20px; font-weight:800; color:#0f172a; margin-top:2px;">${kpis.total_days} <span style="font-size:12px; font-weight:500; color:#64748b;">天</span></div>
                <div style="font-size:10.5px; color:#94a3b8; margin-top:1px;">自然日历基准</div>
            </div>
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:3.5px solid #10b981; border-radius:8px; padding:10px 14px; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                <div style="font-size:11px; font-weight:600; color:#059669;">💼 应出勤工作日</div>
                <div style="font-size:20px; font-weight:800; color:#059669; margin-top:2px;">${kpis.total_workdays} <span style="font-size:12px; font-weight:500; color:#059669;">天</span></div>
                <div style="font-size:10.5px; color:#94a3b8; margin-top:1px;">含 ${kpis.total_shift_workdays} 天周末调休上班</div>
            </div>
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:3.5px solid #dc2626; border-radius:8px; padding:10px 14px; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                <div style="font-size:11px; font-weight:700; color:#dc2626; display:flex; justify-content:space-between;">
                    <span>🔴 法定 3 倍节假日</span>
                    <span style="font-size:9.5px; background:#fee2e2; padding:0 4px; border-radius:4px;">不可倒休</span>
                </div>
                <div style="font-size:20px; font-weight:800; color:#dc2626; margin-top:2px;">${kpis.total_legal_3x_holidays} <span style="font-size:12px; font-weight:500; color:#dc2626;">天</span></div>
                <div style="font-size:10.5px; color:#94a3b8; margin-top:1px;">国家法定节日·强制 300% 工资</div>
            </div>
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:3.5px solid #8b5cf6; border-radius:8px; padding:10px 14px; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                <div style="font-size:11px; font-weight:600; color:#7c3aed; display:flex; justify-content:space-between;">
                    <span>🌴 调休与公休 (2倍)</span>
                    <span style="font-size:9.5px; background:#f3e8ff; padding:0 4px; border-radius:4px;">可倒休</span>
                </div>
                <div style="font-size:20px; font-weight:800; color:#7c3aed; margin-top:2px;">${kpis.total_compensable_rest_days} <span style="font-size:12px; font-weight:500; color:#7c3aed;">天</span></div>
                <div style="font-size:10.5px; color:#94a3b8; margin-top:1px;">双休(${kpis.total_weekend_days}) + 调休假(${kpis.total_shift_off_days})</div>
            </div>
        `;
        $wb.find('#holiday-kpi-container').html(html);
    }

    function render_year_view(months) {
        if (!months) return;
        let html = `<div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:12px;">`;

        months.forEach(m => {
            html += `
                <div class="month-card" data-month="${m.month}" style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:10px; box-shadow:0 1px 2px rgba(0,0,0,0.02); cursor:pointer; transition:all 0.15s ease;" title="点击放大查看【${m.month}月】详细日历">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; border-bottom:1px solid #f1f5f9; padding-bottom:4px;">
                        <span style="font-size:13px; font-weight:800; color:#0f172a;">${m.month_name}</span>
                        <div style="display:flex; gap:4px;">
                            ${m.legal_3x_count > 0 ? `<span style="font-size:9.5px; font-weight:700; color:#dc2626; background:#fee2e2; padding:0 4px; border-radius:4px;">3倍 ${m.legal_3x_count}天</span>` : ''}
                            <span style="font-size:9.5px; font-weight:600; color:#059669; background:#dcfce7; padding:0 4px; border-radius:4px;">工作日 ${m.workdays_count}天</span>
                        </div>
                    </div>

                    <!-- 星期表头 -->
                    <div style="display:grid; grid-template-columns: repeat(7, 1fr); gap:2px; text-align:center; font-size:9.5px; font-weight:700; color:#94a3b8; margin-bottom:4px;">
                        <div>一</div><div>二</div><div>三</div><div>四</div><div>五</div><div style="color:#ea580c;">六</div><div style="color:#ea580c;">日</div>
                    </div>

                    <!-- 4~6 周日期网格 -->
                    <div style="display:flex; flex-direction:column; gap:2px;">
            `;

            m.weeks.forEach(w => {
                html += `<div style="display:grid; grid-template-columns: repeat(7, 1fr); gap:2px; text-align:center;">`;
                w.forEach(d => {
                    if (!d.is_current_month) {
                        html += `<div style="height:22px;"></div>`;
                    } else {
                        let bg = "#ffffff";
                        let color = "#1e293b";
                        let border = "1px solid #f1f5f9";
                        let badge = "";

                        if (d.is_legal_holiday) {
                            bg = "#fee2e2";
                            color = "#b91c1c";
                            border = "1px solid #fca5a5";
                            badge = `<span style="font-size:7px; position:absolute; top:0; right:1px; color:#dc2626; font-weight:800;" title="法定3倍工资(不可倒休)">3倍</span>`;
                        } else if (d.is_shift_off) {
                            bg = "#eff6ff";
                            color = "#1d4ed8";
                            border = "1px solid #bfdbfe";
                            badge = `<span style="font-size:7px; position:absolute; top:0; right:1px; color:#2563eb; font-weight:800;" title="调休放假(2倍工资·可倒休)">2倍</span>`;
                        } else if (d.is_shift_work) {
                            bg = "#ffedd5";
                            color = "#c2410c";
                            border = "1px solid #fdba74";
                            badge = `<span style="font-size:7px; position:absolute; top:0; right:1px; color:#ea580c; font-weight:800;">班</span>`;
                        } else if (d.day_type === '周末公休(2倍工资)') {
                            bg = "#f8fafc";
                            color = "#64748b";
                            border = "1px solid #e2e8f0";
                        }

                        let tooltip = `${d.date} (${d.weekday_cn}) · ${d.day_type}\n加班薪资: ${d.overtime_rate}\n倒休规则: ${d.can_compensate_leave}${d.holiday_name ? '\n说明: ' + d.holiday_name : ''}`;
                        html += `
                            <div style="position:relative; height:22px; display:flex; align-items:center; justify-content:center; background:${bg}; color:${color}; border:${border}; border-radius:3px; font-size:10.5px; font-weight:600;" title="${tooltip}">
                                ${d.day}
                                ${badge}
                            </div>
                        `;
                    }
                });
                html += `</div>`;
            });

            html += `
                    </div>
                </div>
            `;
        });

        html += `</div>`;
        $wb.find('#calendar-year-view-box').html(html);
    }

    function render_month_view(months, selected_month) {
        if (!months) return;
        let m_data = months.find(m => m.month === parseInt(selected_month)) || months[0];

        let html = `
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:16px; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <button class="btn btn-default btn-xs" id="btn-prev-month" data-month="${m_data.month}">◀ 上月</button>
                        <span style="font-size:15px; font-weight:800; color:#0f172a;">${current_year} 年 ${m_data.month} 月详细日历</span>
                        <button class="btn btn-default btn-xs" id="btn-next-month" data-month="${m_data.month}">下月 ▶</button>
                    </div>

                    <div style="display:flex; align-items:center; gap:8px; font-size:11.5px; font-weight:700;">
                        <span style="color:#059669; background:#dcfce7; padding:2px 8px; border-radius:6px;">💼 工作日 ${m_data.workdays_count} 天</span>
                        ${m_data.legal_3x_count > 0 ? `<span style="color:#dc2626; background:#fee2e2; border:1px solid #fca5a5; padding:2px 8px; border-radius:6px;">🔴 法定3倍 ${m_data.legal_3x_count} 天(不可倒休)</span>` : ''}
                        ${m_data.shift_off_count > 0 ? `<span style="color:#2563eb; background:#eff6ff; padding:2px 8px; border-radius:6px;">🔵 调休假 ${m_data.shift_off_count} 天(2倍)</span>` : ''}
                        <span style="color:#64748b; background:#f1f5f9; padding:2px 8px; border-radius:6px;">公休 ${m_data.weekends_count} 天</span>
                    </div>
                </div>

                <!-- 星期表头 -->
                <div style="display:grid; grid-template-columns: repeat(7, 1fr); gap:6px; text-align:center; font-size:12px; font-weight:700; color:#475569; background:#f8fafc; padding:8px 0; border-radius:4px; margin-bottom:6px;">
                    <div>星期一</div><div>星期二</div><div>星期三</div><div>星期四</div><div>星期五</div><div style="color:#ea580c;">星期六</div><div style="color:#ea580c;">星期日</div>
                </div>

                <!-- 单月放大日期大网格 -->
                <div style="display:flex; flex-direction:column; gap:6px;">
        `;

        m_data.weeks.forEach(w => {
            html += `<div style="display:grid; grid-template-columns: repeat(7, 1fr); gap:6px;">`;
            w.forEach(d => {
                if (!d.is_current_month) {
                    html += `<div style="min-height:85px; background:#f8fafc; border:1px dashed #e2e8f0; border-radius:6px; opacity:0.4;"></div>`;
                } else {
                    let bg = "#ffffff";
                    let borderColor = "#e2e8f0";
                    let tagHtml = `<span style="font-size:10px; font-weight:600; color:#059669; background:#f0fdf4; padding:1px 5px; border-radius:4px;">正常工作日</span>`;
                    let otBadge = `<span style="font-size:9.5px; color:#64748b;">100%</span>`;

                    if (d.is_legal_holiday) {
                        bg = "#fef2f2";
                        borderColor = "#fca5a5";
                        tagHtml = `<span style="font-size:10px; font-weight:800; color:#dc2626; background:#fee2e2; border:1px solid #fca5a5; padding:1px 5px; border-radius:4px;">🔴 ${d.holiday_name || '法定3倍'}</span>`;
                        otBadge = `<span style="font-size:10px; font-weight:800; color:#dc2626;">300% (不可倒休)</span>`;
                    } else if (d.is_shift_off) {
                        bg = "#f0f9ff";
                        borderColor = "#bae6fd";
                        tagHtml = `<span style="font-size:10px; font-weight:700; color:#0284c7; background:#e0f2fe; padding:1px 5px; border-radius:4px;">🔵 调休放假</span>`;
                        otBadge = `<span style="font-size:10px; font-weight:700; color:#0284c7;">200% (可倒休)</span>`;
                    } else if (d.is_shift_work) {
                        bg = "#fff7ed";
                        borderColor = "#fdba74";
                        tagHtml = `<span style="font-size:10px; font-weight:700; color:#ea580c; background:#ffedd5; padding:1px 5px; border-radius:4px;">🟠 补班上班</span>`;
                        otBadge = `<span style="font-size:9.5px; font-weight:700; color:#ea580c;">工作日出勤</span>`;
                    } else if (d.day_type === '周末公休(2倍工资)') {
                        bg = "#f8fafc";
                        borderColor = "#cbd5e1";
                        tagHtml = `<span style="font-size:10px; font-weight:600; color:#64748b; background:#e2e8f0; padding:1px 5px; border-radius:4px;">周末双休</span>`;
                        otBadge = `<span style="font-size:9.5px; color:#64748b;">200% (可倒休)</span>`;
                    }

                    html += `
                        <div style="min-height:85px; background:${bg}; border:1px solid ${borderColor}; border-radius:6px; padding:6px 8px; display:flex; flex-direction:column; justify-content:space-between; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                                <span style="font-size:16px; font-weight:800; color:#0f172a;">${d.day}</span>
                                <div>${tagHtml}</div>
                            </div>
                            <div style="display:flex; justify-content:space-between; align-items:center; font-size:10px; border-top:1px solid rgba(0,0,0,0.04); padding-top:3px; margin-top:4px;">
                                <span style="color:#94a3b8;">${d.date}</span>
                                <div>${otBadge}</div>
                            </div>
                        </div>
                    `;
                }
            });
            html += `</div>`;
        });

        html += `
                </div>
            </div>
        `;

        $wb.find('#calendar-month-view-box').html(html);
    }

    function render_list_view(calendar_list, filter_type) {
        if (!calendar_list) return;

        let filtered = calendar_list;
        if (filter_type === 'legal_3x') {
            filtered = calendar_list.filter(d => d.is_legal_holiday);
        } else if (filter_type === 'shift_off') {
            filtered = calendar_list.filter(d => d.is_shift_off);
        } else if (filter_type === 'shift_work') {
            filtered = calendar_list.filter(d => d.is_shift_work);
        } else if (filter_type === 'workday') {
            filtered = calendar_list.filter(d => d.is_workday);
        }

        let html = `
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:14px; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <div style="font-size:13px; font-weight:700; color:#0f172a;">📋 ${current_year} 年度 365 天日历明细与法定加班薪酬/倒休对照表 (共 ${filtered.length} 条记录)</div>
                    <div class="btn-group btn-group-xs" role="group">
                        <button type="button" class="btn btn-default btn-list-filter ${filter_type==='all'?'active':''}" data-filter="all" style="${filter_type==='all'?'background:#eff6ff; color:#1d4ed8; font-weight:700;':''}">全部 (365天)</button>
                        <button type="button" class="btn btn-default btn-list-filter ${filter_type==='legal_3x'?'active':''}" data-filter="legal_3x" style="${filter_type==='legal_3x'?'background:#fee2e2; color:#dc2626; font-weight:700;':''}">🔴 法定3倍假 (${calendar_list.filter(d=>d.is_legal_holiday).length}天)</button>
                        <button type="button" class="btn btn-default btn-list-filter ${filter_type==='shift_off'?'active':''}" data-filter="shift_off" style="${filter_type==='shift_off'?'background:#eff6ff; color:#2563eb; font-weight:700;':''}">🔵 调休放假 (${calendar_list.filter(d=>d.is_shift_off).length}天)</button>
                        <button type="button" class="btn btn-default btn-list-filter ${filter_type==='shift_work'?'active':''}" data-filter="shift_work" style="${filter_type==='shift_work'?'background:#ffedd5; color:#ea580c; font-weight:700;':''}">🟠 调班工作日 (${calendar_list.filter(d=>d.is_shift_work).length}天)</button>
                        <button type="button" class="btn btn-default btn-list-filter ${filter_type==='workday'?'active':''}" data-filter="workday" style="${filter_type==='workday'?'background:#f0fdf4; color:#059669; font-weight:700;':''}">💼 全部工作日 (${calendar_list.filter(d=>d.is_workday).length}天)</button>
                    </div>
                </div>

                <div style="max-height:480px; overflow-y:auto; border:1px solid #e2e8f0; border-radius:6px;">
                    <table class="table table-bordered table-condensed" style="margin-bottom:0; font-size:11.5px;">
                        <thead style="background:#f8fafc; position:sticky; top:0; z-index:5;">
                            <tr>
                                <th style="width:45px; text-align:center;">序号</th>
                                <th style="width:105px;">日期</th>
                                <th style="width:65px; text-align:center;">星期</th>
                                <th style="width:160px;">日期属性</th>
                                <th style="width:130px; text-align:center;">加班工资倍率</th>
                                <th style="width:180px;">倒休补休合规规则</th>
                                <th style="min-width:180px;">节日名称与排班说明</th>
                            </tr>
                        </thead>
                        <tbody>
        `;

        filtered.forEach((d, idx) => {
            let trBg = "#ffffff";
            let typeBadge = `<span style="font-weight:600; color:#059669; background:#f0fdf4; padding:1px 6px; border-radius:4px;">正常工作日</span>`;
            let otBadge = `<span style="color:#64748b;">100% 正常计薪</span>`;
            let compBadge = `<span style="color:#64748b;">-</span>`;

            if (d.is_legal_holiday) {
                trBg = "#fff5f5";
                typeBadge = `<span style="font-weight:800; color:#dc2626; background:#fee2e2; border:1px solid #fca5a5; padding:1px 6px; border-radius:4px;">🔴 法定节假日(3倍工资)</span>`;
                otBadge = `<span style="font-weight:800; color:#dc2626; background:#fee2e2; padding:1px 6px; border-radius:4px;">300% (3倍工资)</span>`;
                compBadge = `<span style="font-weight:800; color:#b91c1c; background:#fef2f2; border:1px solid #fecaca; padding:1px 6px; border-radius:4px;">⛔ 强制3倍·严禁倒休替代</span>`;
            } else if (d.is_shift_off) {
                trBg = "#f8fbff";
                typeBadge = `<span style="font-weight:700; color:#0284c7; background:#e0f2fe; padding:1px 6px; border-radius:4px;">🔵 调休放假(2倍工资)</span>`;
                otBadge = `<span style="font-weight:700; color:#0284c7; background:#e0f2fe; padding:1px 6px; border-radius:4px;">200% (2倍工资)</span>`;
                compBadge = `<span style="font-weight:600; color:#059669; background:#f0fdf4; border:1px solid #bbf7d0; padding:1px 6px; border-radius:4px;">🟢 可优先安排倒休补休</span>`;
            } else if (d.is_shift_work) {
                trBg = "#fffaf5";
                typeBadge = `<span style="font-weight:700; color:#ea580c; background:#ffedd5; padding:1px 6px; border-radius:4px;">🟠 调班工作日(补班)</span>`;
                otBadge = `<span style="font-weight:600; color:#ea580c;">100% 正常出勤计薪</span>`;
                compBadge = `<span style="color:#64748b;">正常上班</span>`;
            } else if (d.day_type === '周末公休(2倍工资)') {
                trBg = "#fafafa";
                typeBadge = `<span style="font-weight:600; color:#64748b; background:#f1f5f9; padding:1px 6px; border-radius:4px;">周末公休(2倍工资)</span>`;
                otBadge = `<span style="color:#64748b;">200% (2倍工资)</span>`;
                compBadge = `<span style="font-weight:600; color:#059669; background:#f0fdf4; border:1px solid #bbf7d0; padding:1px 6px; border-radius:4px;">🟢 可优先安排倒休补休</span>`;
            }

            html += `
                <tr style="background:${trBg};">
                    <td style="text-align:center; font-weight:600; color:#94a3b8;">${idx + 1}</td>
                    <td style="font-weight:700; color:#0f172a;">${d.date}</td>
                    <td style="text-align:center; font-weight:600; color:${(d.weekday_cn==='周六'||d.weekday_cn==='周日')?'#ea580c':'#475569'};">${d.weekday_cn}</td>
                    <td>${typeBadge}</td>
                    <td style="text-align:center;">${otBadge}</td>
                    <td>${compBadge}</td>
                    <td style="color:#475569;">${d.holiday_name || '-'}</td>
                </tr>
            `;
        });

        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        $wb.find('#calendar-list-view-box').html(html);
    }

    function render_month_summary_table(months) {
        if (!months) return;
        let html = `
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:12px 14px; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                <div style="font-size:12px; font-weight:700; color:#0f172a; margin-bottom:8px;">📊 ${current_year} 年度各月标准出勤天数、法定3倍假与加班核算基准表</div>
                <div style="overflow-x:auto;">
                    <table class="table table-bordered table-condensed" style="margin-bottom:0; font-size:11px; text-align:center;">
                        <thead style="background:#f8fafc;">
                            <tr>
                                <th style="text-align:left;">指标维度</th>
                                ${months.map(m => `<th>${m.month}月</th>`).join('')}
                                <th style="background:#eff6ff; color:#1d4ed8;">全年合计</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="text-align:left; font-weight:700; color:#059669;">💼 标准应出勤工作日</td>
                                ${months.map(m => `<td style="font-weight:700; color:#059669;">${m.workdays_count}</td>`).join('')}
                                <td style="font-weight:800; background:#f0fdf4; color:#059669;">${months.reduce((acc, m) => acc + m.workdays_count, 0)} 天</td>
                            </tr>
                            <tr style="background:#fff5f5;">
                                <td style="text-align:left; font-weight:700; color:#dc2626;">🔴 法定3倍节假日 (不可倒休)</td>
                                ${months.map(m => `<td style="font-weight:700; color:#dc2626;">${m.legal_3x_count}</td>`).join('')}
                                <td style="font-weight:800; background:#fee2e2; color:#dc2626;">${months.reduce((acc, m) => acc + m.legal_3x_count, 0)} 天</td>
                            </tr>
                            <tr>
                                <td style="text-align:left; color:#0284c7;">🔵 调休放假天数 (2倍·可倒休)</td>
                                ${months.map(m => `<td style="color:#0284c7;">${m.shift_off_count}</td>`).join('')}
                                <td style="font-weight:700; color:#0284c7;">${months.reduce((acc, m) => acc + m.shift_off_count, 0)} 天</td>
                            </tr>
                            <tr>
                                <td style="text-align:left; color:#64748b;">🔵 双休与公休天数 (2倍·可倒休)</td>
                                ${months.map(m => `<td style="color:#64748b;">${m.weekends_count}</td>`).join('')}
                                <td style="font-weight:700; color:#64748b;">${months.reduce((acc, m) => acc + m.weekends_count, 0)} 天</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        $wb.find('#month-workdays-summary-box').html(html);
    }

    // =========================================================================
    // ✨ 丝滑交互式节假日卡片渲染与点选引擎
    // =========================================================================

    function get_dates_between(s_date_str, e_date_str) {
        let dates = [];
        let cur = new Date(s_date_str);
        let end = new Date(e_date_str);
        while (cur <= end) {
            let y = cur.getFullYear();
            let m = String(cur.getMonth() + 1).padStart(2, '0');
            let d = String(cur.getDate()).padStart(2, '0');
            let dateStr = `${y}-${m}-${d}`;
            let wDay = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"][cur.getDay()];
            dates.push({ date: dateStr, monthDay: `${cur.getMonth() + 1}/${cur.getDate()}`, weekday: wDay });
            cur.setDate(cur.getDate() + 1);
        }
        return dates;
    }

    function render_interactive_holiday_cards(configs) {
        let $container = $wb.find('#holiday-cards-container');
        $container.empty();

        if (!configs || configs.length === 0) {
            $container.html(`<div style="text-align:center; color:#94a3b8; padding:30px; background:#f8fafc; border:1px dashed #cbd5e1; border-radius:8px;">暂无配置，请点击右上角“⚡ 载入国务院官方模板”或“➕ 新增节假日排程”</div>`);
            return;
        }

        configs.forEach((cfg, idx) => {
            let s_date = cfg.start_date || `${current_year}-01-01`;
            let e_date = cfg.end_date || `${current_year}-01-03`;
            let legal_dates_set = new Set((cfg.legal_holiday_dates || '').split(',').map(d => d.trim()).filter(Boolean));
            let shift_dates_arr = (cfg.shift_work_dates || '').split(',').map(d => d.trim()).filter(Boolean);

            let all_range_dates = get_dates_between(s_date, e_date);

            let $card = $(`
                <div class="holiday-config-card" data-idx="${idx}" style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:14px 16px; box-shadow:0 1px 3px rgba(0,0,0,0.03); transition:all 0.15s ease;">
                    
                    <!-- 卡片顶部排：序号、假期名称、起止日期、天数、删除 -->
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; border-bottom:1px solid #f1f5f9; padding-bottom:10px;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <span style="font-size:12px; font-weight:800; color:#1d4ed8; background:#eff6ff; width:24px; height:24px; display:inline-flex; align-items:center; justify-content:center; border-radius:50%;">
                                ${idx + 1}
                            </span>
                            
                            <!-- 节假日名称快速选择/输入 -->
                            <div style="display:flex; align-items:center; gap:6px;">
                                <input type="text" class="form-control input-sm card-holiday-name" value="${cfg.holiday_name || ''}" placeholder="节假日名称" style="width:110px; font-weight:700; color:#0f172a; height:30px; font-size:12px;">
                                <div class="btn-group btn-group-xs holiday-quick-picker" role="group">
                                    <button type="button" class="btn btn-default btn-quick-hname" data-val="元旦">元旦</button>
                                    <button type="button" class="btn btn-default btn-quick-hname" data-val="春节">春节</button>
                                    <button type="button" class="btn btn-default btn-quick-hname" data-val="清明节">清明</button>
                                    <button type="button" class="btn btn-default btn-quick-hname" data-val="劳动节">五一</button>
                                    <button type="button" class="btn btn-default btn-quick-hname" data-val="端午节">端午</button>
                                    <button type="button" class="btn btn-default btn-quick-hname" data-val="中秋节">中秋</button>
                                    <button type="button" class="btn btn-default btn-quick-hname" data-val="国庆节">国庆</button>
                                </div>
                            </div>
                        </div>

                        <div style="display:flex; align-items:center; gap:10px;">
                            <!-- 放假起止日期选择器 -->
                            <div style="display:flex; align-items:center; gap:6px; font-size:12px;">
                                <span style="font-weight:600; color:#475569;">放假区间:</span>
                                <input type="date" class="form-control input-sm card-start-date" value="${s_date}" style="width:130px; height:30px; font-size:11.5px;">
                                <span style="color:#94a3b8;">~</span>
                                <input type="date" class="form-control input-sm card-end-date" value="${e_date}" style="width:130px; height:30px; font-size:11.5px;">
                            </div>

                            <!-- 假期总天数与拆分统计 Badge -->
                            <div class="card-summary-badge" style="font-size:11.5px; font-weight:700; padding:4px 10px; border-radius:6px; background:#f8fafc; border:1px solid #cbd5e1; color:#334155;">
                                共 ${all_range_dates.length} 天
                            </div>

                            <!-- 删除按钮 -->
                            <button class="btn btn-default btn-xs btn-del-holiday-card" style="color:#dc2626; border-color:#fca5a5; padding:3px 8px;" title="删除此假期">
                                🗑️ 删除
                            </button>
                        </div>
                    </div>

                    <!-- 卡片中部：放假切片点选区 (🔴 3倍 vs 🔵 2倍 一键单击切换) -->
                    <div style="margin-top:10px; padding:8px 10px; background:#f8fafc; border-radius:6px; border:1px solid #f1f5f9;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <div style="font-size:11px; font-weight:700; color:#475569;">
                                👆 <b>放假天数点选拆分</b>（单击胶囊即刻在 <span style="color:#b91c1c;">🔴 3倍法定</span> 与 <span style="color:#1d4ed8;">🔵 2倍调休</span> 间切换）：
                            </div>
                            <div class="btn-group btn-group-xs" role="group">
                                <button type="button" class="btn btn-default btn-chips-all-3x" style="font-size:10px; padding:1px 6px;">全部设为3倍</button>
                                <button type="button" class="btn btn-default btn-chips-all-2x" style="font-size:10px; padding:1px 6px;">全部设为2倍</button>
                            </div>
                        </div>

                        <!-- 动态胶囊列表 -->
                        <div class="holiday-day-chips-box" style="display:flex; flex-wrap:wrap; gap:6px;">
                            <!-- 由 update_chips_html 动态渲染 -->
                        </div>
                    </div>

                    <!-- 卡片下部：调休补班工作日快捷管理 -->
                    <div style="margin-top:10px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">
                        <div style="display:flex; align-items:center; flex-wrap:wrap; gap:6px;">
                            <span style="font-size:11px; font-weight:700; color:#ea580c; background:#fff7ed; border:1px solid #fdba74; padding:2px 6px; border-radius:4px;">
                                🟠 调休补班(倒休上班)
                            </span>
                            <div class="shift-work-pills-box" style="display:flex; flex-wrap:wrap; gap:4px;">
                                <!-- 由 update_shift_pills 动态渲染 -->
                            </div>
                            <!-- 极速添加补班日期 -->
                            <div style="display:inline-flex; align-items:center; gap:4px;">
                                <input type="date" class="form-control input-xs quick-add-shift-date" style="width:115px; height:24px; font-size:10.5px;">
                                <button type="button" class="btn btn-default btn-xs btn-add-shift-pill" style="height:24px; padding:1px 6px; font-size:10.5px; font-weight:700; color:#ea580c; border-color:#fdba74; background:#fff7ed;">
                                    + 添加补班
                                </button>
                            </div>
                        </div>

                        <!-- 备注说明 -->
                        <div style="flex:1; min-width:220px;">
                            <input type="text" class="form-control input-xs card-remarks" value="${cfg.remarks || ''}" placeholder="备注/放假排班说明" style="height:26px; font-size:11px;">
                        </div>
                    </div>

                </div>
            `);

            // 存入当前状态数据
            $card.data('legal_set', legal_dates_set);
            $card.data('shift_arr', shift_dates_arr);

            $container.append($card);
            update_card_ui($card);
        });
    }

    function update_card_ui($card) {
        let s_date = $card.find('.card-start-date').val();
        let e_date = $card.find('.card-end-date').val();
        if (!s_date || !e_date) return;

        let legal_set = $card.data('legal_set') || new Set();
        let shift_arr = $card.data('shift_arr') || [];
        let all_dates = get_dates_between(s_date, e_date);

        // 1. 渲染放假日期交互胶囊
        let chipsHtml = '';
        let count_3x = 0;
        let count_2x = 0;

        all_dates.forEach(d => {
            let is3x = legal_set.has(d.date);
            if (is3x) {
                count_3x++;
                chipsHtml += `
                    <div class="day-chip is-3x" data-date="${d.date}" style="cursor:pointer; user-select:none; display:inline-flex; align-items:center; gap:5px; padding:3px 10px; border-radius:14px; font-size:11.5px; font-weight:700; background:#fee2e2; border:1.5px solid #ef4444; color:#991b1b; transition:all 0.15s ease;" title="点击切换为2倍调休假">
                        <span>${d.monthDay} (${d.weekday})</span>
                        <span style="font-size:10px; background:#b91c1c; color:#ffffff; padding:0 4px; border-radius:8px;">🔴 3倍法定</span>
                    </div>
                `;
            } else {
                count_2x++;
                chipsHtml += `
                    <div class="day-chip is-2x" data-date="${d.date}" style="cursor:pointer; user-select:none; display:inline-flex; align-items:center; gap:5px; padding:3px 10px; border-radius:14px; font-size:11.5px; font-weight:600; background:#eff6ff; border:1.5px solid #93c5fd; color:#1e40af; transition:all 0.15s ease;" title="点击切换为3倍法定假日">
                        <span>${d.monthDay} (${d.weekday})</span>
                        <span style="font-size:10px; background:#2563eb; color:#ffffff; padding:0 4px; border-radius:8px;">🔵 2倍调休</span>
                    </div>
                `;
            }
        });

        $card.find('.holiday-day-chips-box').html(chipsHtml);

        // 2. 渲染调休补班药丸
        let shiftHtml = '';
        shift_arr.forEach(sDate => {
            let curD = new Date(sDate);
            let wDay = isNaN(curD.getDay()) ? '' : ["(周日)", "(周一)", "(周二)", "(周三)", "(周四)", "(周五)", "(周六)"][curD.getDay()];
            shiftHtml += `
                <span class="shift-pill" data-date="${sDate}" style="display:inline-flex; align-items:center; gap:4px; padding:2px 7px; background:#ffedd5; border:1px solid #fdba74; color:#9a3412; border-radius:4px; font-size:11px; font-weight:700;">
                    ${sDate} ${wDay}
                    <span class="btn-remove-shift-pill" style="cursor:pointer; color:#ea580c; font-weight:800; margin-left:2px;" title="移除此补班日">✕</span>
                </span>
            `;
        });
        if (shift_arr.length === 0) {
            shiftHtml = `<span style="font-size:10.5px; color:#94a3b8;">(暂无补班)</span>`;
        }
        $card.find('.shift-work-pills-box').html(shiftHtml);

        // 3. 更新统计 Badge 与自动排班说明
        let total_days = all_dates.length;
        $card.find('.card-summary-badge').html(`
            共 <b style="color:#0f172a;">${total_days}</b> 天 · 
            <span style="color:#dc2626;">🔴 3倍法定 <b>${count_3x}</b> 天</span> · 
            <span style="color:#2563eb;">🔵 2倍调休 <b>${count_2x}</b> 天</span> · 
            <span style="color:#ea580c;">🟠 补班 <b>${shift_arr.length}</b> 天</span>
        `);
    }

    // =========================================================================
    // 交互事件绑定
    // =========================================================================

    // 1. 年份微调切换
    $wb.on('click', '#btn-prev-year', function() {
        current_year--;
        $wb.find('#btn-curr-year-display').text(`${current_year} 年`);
        load_calendar_data();
        load_config_cards_data();
    });

    $wb.on('click', '#btn-next-year', function() {
        current_year++;
        $wb.find('#btn-curr-year-display').text(`${current_year} 年`);
        load_calendar_data();
        load_config_cards_data();
    });

    // 2. 刷新
    $wb.on('click', '#btn-refresh-calendar', function() {
        load_calendar_data();
        load_config_cards_data();
        listview.refresh();
        frappe.show_alert({ message: '🔄 日历与加班倍率表已刷新', indicator: 'green' });
    });

    // 3. 一键载入国家官方模板
    $wb.on('click', '#btn-load-template', function() {
        frappe.call({
            method: 'ashan_cn_procurement.services.ashan_holiday_service.get_national_holiday_template',
            args: { year: current_year },
            callback: function(r) {
                render_interactive_holiday_cards(r.message || []);
                frappe.show_alert({ message: `⚡ 已载入【${current_year}年度】国务院官方13天法定节假日与调休模板`, indicator: 'green' });
                $wb.find('.qifu-tab-btn[data-tab="settings"]').click();
            }
        });
    });

    // 4. Tab 切换 (防抖零位移)
    $wb.on('click', '.qifu-tab-btn', function() {
        let tab = $(this).attr('data-tab');
        $wb.find('.qifu-tab-btn').removeClass('active').css({
            'color': '#475569',
            'background': 'transparent',
            'border-bottom-color': 'transparent'
        });
        $(this).addClass('active').css({
            'color': '#1d4ed8',
            'background': '#eff6ff',
            'border-bottom-color': '#2563eb'
        });

        $wb.find('.holiday-tab-pane').hide();
        $wb.find(`#tab-content-${tab}`).show();
        active_tab = tab;

        if (tab === 'settings') {
            load_config_cards_data();
        }
    });

    // 5. 视图模式切换 (年视图 vs 月视图 vs 列表明细版)
    $wb.on('click', '.btn-view-mode', function() {
        let mode = $(this).attr('data-mode');
        $wb.find('.btn-view-mode').removeClass('active').css({
            'background': '',
            'color': '',
            'border-color': '',
            'font-weight': '600'
        });
        $(this).addClass('active').css({
            'background': '#eff6ff',
            'color': '#1d4ed8',
            'border-color': '#bfdbfe',
            'font-weight': '700'
        });

        current_view_mode = mode;
        $wb.find('#calendar-year-view-box').hide();
        $wb.find('#calendar-month-view-box').hide();
        $wb.find('#calendar-list-view-box').hide();

        if (mode === 'year') {
            $wb.find('#calendar-year-view-box').show();
        } else if (mode === 'month') {
            $wb.find('#calendar-month-view-box').show();
            if (calendar_cache) {
                render_month_view(calendar_cache.months, current_selected_month);
            }
        } else if (mode === 'list') {
            $wb.find('#calendar-list-view-box').show();
            if (calendar_cache) {
                render_list_view(calendar_cache.calendar_list, list_filter);
            }
        }
    });

    // 6. 列表视图筛选器
    $wb.on('click', '.btn-list-filter', function() {
        let f = $(this).attr('data-filter');
        list_filter = f;
        if (calendar_cache) {
            render_list_view(calendar_cache.calendar_list, list_filter);
        }
    });

    // 7. 年视图中点击卡片放大至单月视图
    $wb.on('click', '.month-card', function() {
        let m = parseInt($(this).attr('data-month'));
        current_selected_month = m;
        $wb.find('.btn-view-mode[data-mode="month"]').click();
    });

    // 8. 月视图中上下月切换
    $wb.on('click', '#btn-prev-month', function() {
        let m = parseInt($(this).attr('data-month'));
        current_selected_month = m > 1 ? m - 1 : 12;
        render_month_view(calendar_cache.months, current_selected_month);
    });

    $wb.on('click', '#btn-next-month', function() {
        let m = parseInt($(this).attr('data-month'));
        current_selected_month = m < 12 ? m + 1 : 1;
        render_month_view(calendar_cache.months, current_selected_month);
    });

    // =========================================================================
    // ✨ 丝滑点选卡片内交互操作
    // =========================================================================

    // 9. 单击日期胶囊：在 🔴 3倍 与 🔵 2倍 间切换
    $wb.on('click', '.day-chip', function() {
        let $chip = $(this);
        let $card = $chip.closest('.holiday-config-card');
        let dStr = $chip.attr('data-date');
        let legal_set = $card.data('legal_set') || new Set();

        if (legal_set.has(dStr)) {
            legal_set.delete(dStr);
        } else {
            legal_set.add(dStr);
        }
        $card.data('legal_set', legal_set);
        update_card_ui($card);
    });

    // 10. 全部设为 3倍 / 全部设为 2倍
    $wb.on('click', '.btn-chips-all-3x', function() {
        let $card = $(this).closest('.holiday-config-card');
        let s_date = $card.find('.card-start-date').val();
        let e_date = $card.find('.card-end-date').val();
        let all_dates = get_dates_between(s_date, e_date);
        let legal_set = new Set(all_dates.map(d => d.date));
        $card.data('legal_set', legal_set);
        update_card_ui($card);
    });

    $wb.on('click', '.btn-chips-all-2x', function() {
        let $card = $(this).closest('.holiday-config-card');
        $card.data('legal_set', new Set());
        update_card_ui($card);
    });

    // 11. 节假日名称快速选择器
    $wb.on('click', '.btn-quick-hname', function() {
        let val = $(this).attr('data-val');
        let $card = $(this).closest('.holiday-config-card');
        $card.find('.card-holiday-name').val(val);
    });

    // 12. 修改放假起止日期：自动重新切片
    $wb.on('change', '.card-start-date, .card-end-date', function() {
        let $card = $(this).closest('.holiday-config-card');
        update_card_ui($card);
    });

    // 13. 添加补班日
    $wb.on('click', '.btn-add-shift-pill', function() {
        let $card = $(this).closest('.holiday-config-card');
        let newShiftDate = $card.find('.quick-add-shift-date').val();
        if (!newShiftDate) {
            frappe.msgprint("请先选择要添加的补班日期！");
            return;
        }
        let shift_arr = $card.data('shift_arr') || [];
        if (!shift_arr.includes(newShiftDate)) {
            shift_arr.push(newShiftDate);
            shift_arr.sort();
            $card.data('shift_arr', shift_arr);
            $card.find('.quick-add-shift-date').val('');
            update_card_ui($card);
        }
    });

    // 14. 移除补班日
    $wb.on('click', '.btn-remove-shift-pill', function(e) {
        e.stopPropagation();
        let $pill = $(this).closest('.shift-pill');
        let $card = $pill.closest('.holiday-config-card');
        let dStr = $pill.attr('data-date');
        let shift_arr = $card.data('shift_arr') || [];
        shift_arr = shift_arr.filter(d => d !== dStr);
        $card.data('shift_arr', shift_arr);
        update_card_ui($card);
    });

    // 15. 新增节假日卡片
    $wb.on('click', '#btn-add-holiday-card', function() {
        let configs = collect_all_cards_data();
        configs.push({
            holiday_name: "新节假日",
            start_date: `${current_year}-01-01`,
            end_date: `${current_year}-01-03`,
            legal_holiday_dates: `${current_year}-01-01`,
            shift_work_dates: "",
            remarks: "放假说明"
        });
        render_interactive_holiday_cards(configs);
    });

    // 16. 删除节假日卡片
    $wb.on('click', '.btn-del-holiday-card', function() {
        $(this).closest('.holiday-config-card').remove();
        // 重新编号
        $wb.find('.holiday-config-card').each(function(i) {
            $(this).find('span:first').text(i + 1);
        });
    });

    function collect_all_cards_data() {
        let configs = [];
        $wb.find('.holiday-config-card').each(function() {
            let $card = $(this);
            let hname = $card.find('.card-holiday-name').val();
            let s_date = $card.find('.card-start-date').val();
            let e_date = $card.find('.card-end-date').val();
            let legal_set = $card.data('legal_set') || new Set();
            let shift_arr = $card.data('shift_arr') || [];
            let remarks = $card.find('.card-remarks').val();

            if (hname && s_date && e_date) {
                configs.push({
                    holiday_name: hname,
                    start_date: s_date,
                    end_date: e_date,
                    legal_holiday_dates: Array.from(legal_set).sort().join(', '),
                    shift_work_dates: shift_arr.join(', '),
                    remarks: remarks
                });
            }
        });
        return configs;
    }

    // 17. 保存配置并重新生成 365 天日历与加班倍率
    $wb.on('click', '#btn-save-configs-and-rebuild', function() {
        let configs = collect_all_cards_data();

        if (configs.length === 0) {
            frappe.msgprint("请至少配置一个有效的节假日！");
            return;
        }

        frappe.call({
            method: 'ashan_cn_procurement.services.ashan_holiday_service.save_holiday_configs_and_rebuild_calendar',
            args: {
                year: current_year,
                configs_json: JSON.stringify(configs)
            },
            freeze: true,
            freeze_message: `正在保存配置并构建【${current_year}年度】365天日历底册与加班倍率表...`,
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({ message: r.message.message, indicator: 'green' });
                    $wb.find('.qifu-tab-btn[data-tab="calendar"]').click();
                    load_calendar_data();
                    listview.refresh();
                }
            }
        });
    });

    load_calendar_data();
}
