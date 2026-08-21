frappe.pages['qifu-hr-salary-workbench'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: '🏢 祺富人事薪酬工作台*',
        single_column: true
    });

    const COMPANY = "天津祺富机械加工有限公司";
    let current_month = "2026-07";
    let current_tab = "employees"; // 默认第 1 个 Tab: 员工薪酬档案 (权威母表底册)
    let current_tax_view_mode = "full_68"; // 默认直接进入 68 列全量法定申报大宽表
    let cached_insurance_setting = null;

    const html = `
    <style>
        /* 隐藏 Frappe 原生重复的灰黑 Page Head 标题 */
        .page-head {
            display: none !important;
        }
        .page-body {
            padding-top: 10px !important;
        }
        .qifu-wb-wrapper {
            padding: 0 0 20px 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        /* 尊贵深邃深蓝渐变主 Header */
        .qifu-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 45%, #2563eb 100%);
            color: #ffffff !important;
            padding: 22px 28px;
            border-radius: 14px;
            margin-bottom: 18px;
            box-shadow: 0 10px 25px -5px rgba(30, 58, 138, 0.3), 0 8px 10px -6px rgba(30, 58, 138, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.15);
        }
        .qifu-title {
            font-size: 21px;
            font-weight: 800;
            letter-spacing: -0.3px;
            color: #ffffff !important;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .qifu-subtitle {
            font-size: 13px;
            color: #e0e7ff !important;
            opacity: 0.95;
            margin-top: 6px;
            letter-spacing: 0.2px;
            line-height: 1.5;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        }
        .qifu-header-controls {
            display: flex;
            gap: 12px;
            align-items: center;
            background: rgba(255, 255, 255, 0.12);
            padding: 8px 14px;
            border-radius: 10px;
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .qifu-header-controls label {
            font-size: 13.5px;
            font-weight: 700;
            color: #ffffff !important;
            margin: 0;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        }
        .qifu-month-input {
            width: 145px !important;
            display: inline-block;
            font-weight: 700 !important;
            color: #1e3a8a !important;
            background: #ffffff !important;
            border: 1.5px solid #bfdbfe !important;
            border-radius: 6px !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
        }
        .qifu-btn-refresh-header {
            background: rgba(255, 255, 255, 0.2) !important;
            color: #ffffff !important;
            border: 1.5px solid rgba(255, 255, 255, 0.45) !important;
            font-weight: 700 !important;
            border-radius: 6px !important;
            padding: 5px 12px !important;
            transition: all 0.2s ease !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        }
        .qifu-btn-refresh-header:hover {
            background: #ffffff !important;
            color: #1e3a8a !important;
            border-color: #ffffff !important;
            text-shadow: none !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15) !important;
        }
        .qifu-nav-tabs {
            display: flex;
            gap: 2px;
            border-bottom: 2px solid #e2e8f0;
            margin-bottom: 12px;
            padding-bottom: 0px;
            overflow-x: auto;
            flex-wrap: nowrap;
            align-items: flex-end;
        }
        .qifu-tab-btn {
            background: transparent;
            border: none;
            border-bottom: 3px solid transparent;
            padding: 7px 13px;
            font-size: 12.5px;
            font-weight: 600;
            color: #475569;
            cursor: pointer;
            border-radius: 6px 6px 0 0;
            transition: color 0.1s ease, background-color 0.1s ease, border-color 0.1s ease;
            white-space: nowrap;
            margin-bottom: -2px;
            position: relative;
            transform: none !important;
            box-shadow: none !important;
            flex-shrink: 0;
        }
        .qifu-tab-btn:hover {
            color: #1e40af;
            background: #f8fafc;
            transform: none !important;
        }
        .qifu-tab-btn.active {
            color: #1d4ed8;
            background: #eff6ff;
            font-weight: 600;
            border-bottom: 3px solid #2563eb;
            transform: none !important;
        }
        .qifu-kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 14px;
            margin-bottom: 18px;
        }
        .qifu-kpi-card {
            background: #fff;
            padding: 16px 18px;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            transition: transform 0.15s ease;
        }
        .qifu-kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08);
        }
        .qifu-toolbar {
            background: #fff;
            padding: 12px 16px;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            margin-bottom: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }
        .qifu-toolbar-left, .qifu-toolbar-right {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        
        /* ============================================================ */
        /* 🌟 表格吸顶冻结表头与左侧前三列冻结标准样式 (Supreme Frozen Table) */
        /* ============================================================ */
        .qifu-table-box {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
            overflow-x: auto !important;
            overflow-y: auto !important;
            position: relative;
            max-height: calc(100vh - 270px);
            margin-bottom: 0px;
        }
        .qifu-table-box::-webkit-scrollbar {
            height: 12px;
            width: 12px;
        }
        .qifu-table-box::-webkit-scrollbar-track {
            background: #f1f5f9;
            border-radius: 6px;
        }
        .qifu-table-box::-webkit-scrollbar-thumb {
            background: #94a3b8;
            border-radius: 6px;
            border: 2px solid #f1f5f9;
        }
        .qifu-table-box::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        .qifu-table {
            width: 100%;
            border-collapse: separate !important;
            border-spacing: 0 !important;
            font-size: 12px;
        }

        /* 单层表头吸顶 */
        .qifu-table thead th {
            position: sticky !important;
            top: 0 !important;
            z-index: 10 !important;
            background: #f8fafc;
            color: #334155;
            font-weight: 700;
            padding: 9px 12px;
            border-top: 1px solid #e2e8f0;
            border-bottom: 2px solid #cbd5e1 !important;
            border-right: 1px solid #f1f5f9;
            white-space: nowrap;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }

        /* 双层表头第一行 (大类分组) */
        .qifu-table thead tr:first-child th {
            position: sticky !important;
            top: 0 !important;
            z-index: 12 !important;
        }

        /* 双层表头第二行 (具体字段) */
        .qifu-table thead tr:nth-child(2) th {
            position: sticky !important;
            top: 31px !important;
            z-index: 11 !important;
            background: #f8fafc;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }

        /* 单元格样式 */
        .qifu-table td {
            padding: 8px 12px;
            border-bottom: 1px solid #f1f5f9;
            border-right: 1px solid rgba(0,0,0,0.03);
            color: #1e293b;
            vertical-align: middle;
            white-space: nowrap;
            background: #ffffff;
        }
        .qifu-table tr:hover td {
            background: #f8fafc !important;
        }

        /* 左侧前三列 (序号、工号、姓名) 强制冻结 */
        .qifu-table thead tr th.sticky-col-1,
        .qifu-table thead tr th:first-child {
            position: sticky !important;
            left: 0 !important;
            z-index: 25 !important;
            background: #f8fafc;
        }
        .qifu-table thead tr th.sticky-col-2,
        .qifu-table thead tr th:nth-child(2) {
            position: sticky !important;
            left: 42px !important;
            z-index: 25 !important;
            background: #f8fafc;
        }
        .qifu-table thead tr th.sticky-col-3,
        .qifu-table thead tr th:nth-child(3) {
            position: sticky !important;
            left: 115px !important;
            z-index: 25 !important;
            background: #f8fafc;
            box-shadow: 2px 0 5px rgba(0,0,0,0.06);
        }

        .qifu-table tbody tr td.sticky-col-1,
        .qifu-table tbody tr td:first-child {
            position: sticky !important;
            left: 0 !important;
            z-index: 5 !important;
            background: #ffffff;
        }
        .qifu-table tbody tr td.sticky-col-2,
        .qifu-table tbody tr td:nth-child(2) {
            position: sticky !important;
            left: 42px !important;
            z-index: 5 !important;
            background: #ffffff;
        }
        .qifu-table tbody tr td.sticky-col-3,
        .qifu-table tbody tr td:nth-child(3) {
            position: sticky !important;
            left: 115px !important;
            z-index: 5 !important;
            background: #ffffff;
            box-shadow: 2px 0 5px rgba(0,0,0,0.06);
        }

        .qifu-table tbody tr:hover td.sticky-col-1,
        .qifu-table tbody tr:hover td.sticky-col-2,
        .qifu-table tbody tr:hover td.sticky-col-3,
        .qifu-table tbody tr:hover td:first-child,
        .qifu-table tbody tr:hover td:nth-child(2),
        .qifu-table tbody tr:hover td:nth-child(3) {
            background: #f8fafc !important;
        }

        /* 底部合计行吸底 (tfoot) */
        .qifu-table tfoot th,
        .qifu-table tfoot td {
            position: sticky !important;
            bottom: 0 !important;
            z-index: 9 !important;
            background: #f8fafc !important;
            border-top: 2px solid #cbd5e1 !important;
            font-weight: 700;
            box-shadow: 0 -1px 3px rgba(0, 0, 0, 0.05);
        }
        .qifu-table tfoot td:first-child {
            position: sticky !important;
            left: 0 !important;
            z-index: 15 !important;
            background: #f8fafc !important;
        }
        .qifu-table tfoot td:nth-child(2) {
            position: sticky !important;
            left: 42px !important;
            z-index: 15 !important;
            background: #f8fafc !important;
        }
        .qifu-table tfoot td:nth-child(3) {
            position: sticky !important;
            left: 115px !important;
            z-index: 15 !important;
            background: #f8fafc !important;
            box-shadow: 2px 0 5px rgba(0,0,0,0.06);
        }

        .qifu-money-cell {
            text-align: right !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
            font-variant-numeric: tabular-nums;
        }
        .qifu-status-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11.5px;
            font-weight: 600;
        }
        .qifu-status-locked {
            background: #dcfce7;
            color: #15803d;
        }
        .qifu-status-draft {
            background: #fef3c7;
            color: #b45309;
        }
        .qifu-upload-dropzone {
            border: 2px dashed #2563eb;
            background: #eff6ff;
            border-radius: 12px;
            padding: 22px;
            text-align: center;
            position: relative;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .qifu-upload-dropzone:hover {
            background: #dbeafe;
            border-color: #1d4ed8;
        }
        .qifu-upload-dropzone input[type="file"] {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            opacity: 0;
            cursor: pointer;
        }

        /* 动态超大报表预览模态框 */
        .modal.fade .modal-dialog {
            width: 92vw !important;
            max-width: 1720px !important;
            min-width: 1000px !important;
            margin: 20px auto !important;
        }
        .modal-body {
            padding: 16px 20px !important;
        }
        .qifu-modal-table-scroll {
            width: 100%;
            height: calc(80vh - 120px) !important;
            min-height: 480px !important;
            max-height: 750px !important;
            overflow-x: auto !important;
            overflow-y: auto !important;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
    </style>
    <div class="qifu-wb-wrapper">
        <!-- 顶部 Header -->
        <div class="qifu-header">
            <div>
                <div class="qifu-title">
                    <span>🏢 天津祺富机械加工有限公司 · 人事薪酬综合中枢</span>
                </div>
                <div class="qifu-subtitle">
                    权威员工档案库 · 外部实发表智能解析与发放 · 社保/公积金独立台账 · 个人所得税依法预扣 · 综合税后倒推税前一体化
                </div>
            </div>
            <div class="qifu-header-controls">
                <label>核算月份：</label>
                <input type="month" id="qifu-month-select" class="form-control qifu-month-input" value="2026-07">
                <button class="btn btn-sm qifu-btn-refresh-header" id="btn-qifu-refresh-all">🔄 刷新数据</button>
            </div>
        </div>

        <!-- 月度人事薪酬核定全流程任务中枢与核验看板 (多维精细化卡片体系) -->
        <div class="qifu-workflow-hub" style="background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:12px 16px; margin-bottom:14px; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; border-bottom:1px solid #f1f5f9; padding-bottom:8px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:13px; font-weight:800; color:#0f172a;">📋 月度人事薪酬核定全流程任务中枢</span>
                    <span class="badge" id="workflow-overall-badge" style="background:#eff6ff; color:#1d4ed8; font-weight:600; font-size:11px; padding:2px 8px; border-radius:10px; border:1px solid #bfdbfe;">
                        核定账期: <span id="workflow-period-text">2026-07</span>
                    </span>
                </div>
                <div id="workflow-lock-status-badge" style="font-size:11.5px; font-weight:700;">
                    <span style="color:#059669; background:#dcfce7; border:1px solid #bbf7d0; padding:2px 8px; border-radius:10px;">📝 草稿状态 (待核定)</span>
                </div>
            </div>

            <!-- 5 大核心任务统一规范卡片栅格 (高信息密度与科学排版) -->
            <div class="qifu-workflow-steps" style="display:grid; grid-template-columns: repeat(5, 1fr); gap:10px;">
                
                <!-- 卡片 1: 👥 权威母表底册 -->
                <div class="workflow-step-card" id="wf-step-1" style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:10px 12px; display:flex; flex-direction:column; justify-content:space-between; min-height:130px; box-shadow:0 1px 2px rgba(0,0,0,0.02); transition:all 0.15s ease;">
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-size:11px; font-weight:700; color:#64748b;">第 1 步 · 员工底册</span>
                            <span id="wf-step1-tag" style="font-size:10px; font-weight:600; color:#059669; background:#dcfce7; border:1px solid #bbf7d0; padding:0 5px; border-radius:8px;">权威底册</span>
                        </div>
                        <div style="font-size:12.5px; font-weight:700; color:#0f172a; display:flex; align-items:center; gap:5px;">
                            <span id="wf-step1-icon">🟡</span> 母表档案核实
                        </div>
                        <div style="font-size:12px; font-weight:700; color:#1e293b; margin-top:3px;" id="wf-step1-main">
                            数据加载中...
                        </div>
                        <div style="font-size:10.5px; color:#64748b; margin-top:2px; line-height:1.3;" id="wf-step1-sub">
                            正在读取在册档案底册
                        </div>
                    </div>
                    <div style="margin-top:8px;">
                        <button class="btn btn-default btn-xs wf-goto-tab" data-tab="employees" style="width:100%; font-size:11px; font-weight:600; padding:3px 6px; color:#1e293b; background:#f8fafc; border-color:#cbd5e1;">👥 查看档案底册</button>
                    </div>
                </div>

                <!-- 卡片 2: 📤 车间实发工资导入 -->
                <div class="workflow-step-card" id="wf-step-2" title="支持 .xlsx / .xlsm / .xls 车间实发表，系统自动提取考勤工时、加班达标率，并执行税后实发倒推税前应发与代扣个税" style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:10px 12px; display:flex; flex-direction:column; justify-content:space-between; min-height:130px; box-shadow:0 1px 2px rgba(0,0,0,0.02); transition:all 0.15s ease;">
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-size:11px; font-weight:700; color:#64748b;">第 2 步 · 车间实发</span>
                            <span id="wf-step2-file-badge" class="wf-file-pill btn-wf-download-file" data-type="excel" style="display:none; font-size:10.5px; font-weight:600; color:#2563eb; background:#eff6ff; border:1px solid #bfdbfe; padding:1px 6px; border-radius:10px; cursor:pointer;" title="点击下载上传的车间原始外部工资表原件 (.xlsx/.xls)">📥 凭证文件</span>
                        </div>
                        <div style="font-size:12.5px; font-weight:700; color:#0f172a; display:flex; align-items:center; gap:5px;">
                            <span id="wf-step2-icon">🟡</span> 外部实发导入
                        </div>
                        <div style="font-size:12px; font-weight:700; color:#1e293b; margin-top:3px;" id="wf-step2-main">
                            数据加载中...
                        </div>
                        <div style="font-size:10.5px; color:#64748b; margin-top:2px; line-height:1.3;" id="wf-step2-sub">
                            正在检查车间实操台账
                        </div>
                    </div>
                    <div style="margin-top:8px;">
                        <button class="btn btn-default btn-xs" id="btn-wf-upload-salary" style="width:100%; font-size:11px; font-weight:700; padding:3px 6px; background:#eff6ff; color:#1d4ed8; border-color:#bfdbfe;">📤 上传车间实发表</button>
                        <div style="font-size:9.5px; color:#94a3b8; text-align:center; margin-top:3px;">支持 .xlsx / .xls 格式</div>
                    </div>
                </div>

                <!-- 卡片 3: 🛡️ 社保缴费申报表 PDF -->
                <div class="workflow-step-card" id="wf-step-3" title="支持电子税务局社保缴费申报表 PDF 或 ZIP，系统自动解析金额并比对公司与个人承担" style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:10px 12px; display:flex; flex-direction:column; justify-content:space-between; min-height:130px; box-shadow:0 1px 2px rgba(0,0,0,0.02); transition:all 0.15s ease;">
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-size:11px; font-weight:700; color:#64748b;">第 3 步 · 社保申报</span>
                            <span id="wf-step3-file-badge" class="wf-file-pill btn-wf-download-file" data-type="ss" style="display:none; font-size:10.5px; font-weight:600; color:#2563eb; background:#eff6ff; border:1px solid #bfdbfe; padding:1px 6px; border-radius:10px; cursor:pointer;" title="点击下载已归档的税务局社保申报表原件 (PDF)">📥 凭证文件</span>
                        </div>
                        <div style="font-size:12.5px; font-weight:700; color:#0f172a; display:flex; align-items:center; gap:5px;">
                            <span id="wf-step3-icon">🟡</span> 社保申报核验
                        </div>
                        <div style="font-size:12px; font-weight:700; color:#1e293b; margin-top:3px;" id="wf-step3-main">
                            数据加载中...
                        </div>
                        <div style="font-size:10.5px; color:#64748b; margin-top:2px; line-height:1.3;" id="wf-step3-sub">
                            正在同步社保申报状态
                        </div>
                    </div>
                    <div style="margin-top:8px;">
                        <button class="btn btn-default btn-xs" id="btn-wf-upload-ss" style="width:100%; font-size:11px; font-weight:700; padding:3px 6px; background:#eff6ff; color:#1d4ed8; border-color:#bfdbfe;">📤 上传社保凭证</button>
                        <div style="font-size:9.5px; color:#94a3b8; text-align:center; margin-top:3px;">支持 .pdf / .zip 格式</div>
                    </div>
                </div>

                <!-- 卡片 4: 🏛️ 公积金缴存凭证 ZIP/PDF -->
                <div class="workflow-step-card" id="wf-step-4" title="支持公积金中心 ZIP 压缩包或 PDF 凭证，ZIP 后台自动解压仅保留归档 PDF 原件并比对金额" style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:10px 12px; display:flex; flex-direction:column; justify-content:space-between; min-height:130px; box-shadow:0 1px 2px rgba(0,0,0,0.02); transition:all 0.15s ease;">
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-size:11px; font-weight:700; color:#64748b;">第 4 步 · 公积金凭证</span>
                            <span id="wf-step4-file-badge" class="wf-file-pill btn-wf-download-file" data-type="hf" style="display:none; font-size:10.5px; font-weight:600; color:#2563eb; background:#eff6ff; border:1px solid #bfdbfe; padding:1px 6px; border-radius:10px; cursor:pointer;" title="点击下载已归档的公积金缴存凭证原件 (PDF)">📥 凭证文件</span>
                        </div>
                        <div style="font-size:12.5px; font-weight:700; color:#0f172a; display:flex; align-items:center; gap:5px;">
                            <span id="wf-step4-icon">🟡</span> 公积金凭证核验
                        </div>
                        <div style="font-size:12px; font-weight:700; color:#1e293b; margin-top:3px;" id="wf-step4-main">
                            数据加载中...
                        </div>
                        <div style="font-size:10.5px; color:#64748b; margin-top:2px; line-height:1.3;" id="wf-step4-sub">
                            正在同步公积金凭证状态
                        </div>
                    </div>
                    <div style="margin-top:8px;">
                        <button class="btn btn-default btn-xs" id="btn-wf-upload-hf" style="width:100%; font-size:11px; font-weight:700; padding:3px 6px; background:#eff6ff; color:#1d4ed8; border-color:#bfdbfe;">📤 上传公积金凭证</button>
                        <div style="font-size:9.5px; color:#94a3b8; text-align:center; margin-top:3px;">支持 .pdf / .zip 格式</div>
                    </div>
                </div>

                <!-- 卡片 5: 🔒 薪酬综合核定与封账 -->
                <div class="workflow-step-card" id="wf-step-5" style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:10px 12px; display:flex; flex-direction:column; justify-content:space-between; min-height:130px; box-shadow:0 1px 2px rgba(0,0,0,0.02); transition:all 0.15s ease;">
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-size:11px; font-weight:700; color:#64748b;">第 5 步 · 综合核定</span>
                            <span id="wf-step5-lock-badge" style="font-size:10.5px; font-weight:600; color:#64748b; background:#f1f5f9; border:1px solid #e2e8f0; padding:1px 6px; border-radius:10px;">加载中</span>
                        </div>
                        <div style="font-size:12.5px; font-weight:700; color:#0f172a; display:flex; align-items:center; gap:5px;">
                            <span id="wf-step5-icon">🟡</span> 薪酬核定与封账
                        </div>
                        <div style="font-size:11.5px; font-weight:700; color:#1e293b; margin-top:3px;" id="wf-step5-main">
                            数据加载中...
                        </div>
                        <div style="font-size:10.5px; color:#64748b; font-weight:600; margin-top:2px; line-height:1.3;" id="wf-step5-sub">
                            正在汇总企业综合用工成本
                        </div>
                    </div>
                    <div style="margin-top:8px;">
                        <button class="btn btn-default btn-xs" id="btn-wf-lock-action" style="width:100%; font-size:11px; font-weight:700; padding:3px 6px; background:#f8fafc; color:#64748b; border-color:#cbd5e1;">🔒 执行最终核定封账</button>
                    </div>
                </div>

            </div>
        </div>

        <!-- 全新 6 大黄金业务 Tab 体系 -->
        <div class="qifu-nav-tabs">
            <button class="qifu-tab-btn active" data-tab="employees">👥 1. 员工薪酬档案 (母表底册)</button>
            <button class="qifu-tab-btn" data-tab="import">📤 2. 外部实发与发放表 (24列)</button>
            <button class="qifu-tab-btn" data-tab="social_insurance">🛡️ 3. 社会保险台账与配置</button>
            <button class="qifu-tab-btn" data-tab="housing_fund">🏛️ 4. 住房公积金台账与配置</button>
            <button class="qifu-tab-btn" data-tab="tax">⚖️ 5. 个人所得税申报台账</button>
            <button class="qifu-tab-btn" data-tab="settlement">📊 6. 月度薪酬综合结算</button>
        </div>

        <!-- ========================================== -->
        <!-- Tab 1: 👥 1. 祺富员工薪酬档案 (权威母表底册 - 精简11列标准结构) -->
        <!-- 序号 工号 姓名 证件号码 岗位职务 用工性质 计薪方式 固定/车间薪资 社保基数 公积金基数 专项扣除 操作 -->
        <!-- ========================================== -->
        <div id="qifu-tab-employees" class="qifu-tab-content">
            <div class="qifu-kpi-grid">
                <div class="qifu-kpi-card" style="border-left: 4px solid #3b82f6;">
                    <div style="font-size:13px; font-weight:700; color:#1e40af;">👥 在册员工总数</div>
                    <div style="font-size:22px; font-weight:800; color:#0f172a; margin-top:4px;" id="tab1-emp-total">26 人</div>
                    <div style="font-size:12px; color:#64748b;">权威薪酬母表档案底册</div>
                </div>
                <div class="qifu-kpi-card" style="border-left: 4px solid #10b981;">
                    <div style="font-size:13px; font-weight:700; color:#065f46;">🛡️ 正式在保人员 (五险一金)</div>
                    <div style="font-size:22px; font-weight:800; color:#059669; margin-top:4px;" id="tab1-emp-insured">19 人</div>
                    <div style="font-size:12px; color:#64748b;">参保五险一金正式工</div>
                </div>
                <div class="qifu-kpi-card" style="border-left: 4px solid #f59e0b;">
                    <div style="font-size:13px; font-weight:700; color:#92400e;">👴 退休返聘人员</div>
                    <div style="font-size:22px; font-weight:800; color:#d97706; margin-top:4px;" id="tab1-emp-rehire">0 人</div>
                    <div style="font-size:12px; color:#64748b;">免缴社保/仅发薪资与补贴</div>
                </div>
                <div class="qifu-kpi-card" style="border-left: 4px solid #ef4444;">
                    <div style="font-size:13px; font-weight:700; color:#b91c1c;">🚪 本月离职人员</div>
                    <div style="font-size:22px; font-weight:800; color:#dc2626; margin-top:4px;" id="tab1-emp-resigned">0 人</div>
                    <div style="font-size:12px; color:#64748b;">正常发薪个税/次月社保公积金减员</div>
                </div>
                <div class="qifu-kpi-card" style="border-left: 4px solid #6366f1;">
                    <div style="font-size:13px; font-weight:700; color:#3730a3;">🏷️ 其他用工 (临时/外籍/劳务)</div>
                    <div style="font-size:22px; font-weight:800; color:#4f46e5; margin-top:4px;" id="tab1-emp-other">7 人</div>
                    <div style="font-size:12px; color:#64748b;">非正式用工或劳务派遣</div>
                </div>
            </div>

            <!-- 工具栏 -->
            <div class="qifu-toolbar">
                <div class="qifu-toolbar-left">
                    <input type="text" class="form-control" id="qifu-emp-search" placeholder="🔍 搜索工号、姓名、证件号、岗位..." style="width:230px; display:inline-block;">
                    <button class="btn btn-default btn-sm" id="btn-batch-resign" style="color: #dc2626; border-color: #f87171; font-weight: 600;">
                        🚪 批量办理离职
                    </button>
                    <button class="btn btn-default btn-sm" id="btn-qifu-hf-min" style="color: #059669; border-color: #059669; font-weight: 600;">
                        ⚡ 一键全员公积金 (最低基数)
                    </button>
                    <button class="btn btn-default btn-sm" id="btn-qifu-hf-zero" style="color: #64748b; border-color: #cbd5e1; font-weight: 600;">
                        🚫 一键取消全员公积金 (设为0)
                    </button>
                </div>
                <div class="qifu-toolbar-right">
                    <button class="btn btn-primary btn-sm" id="btn-qifu-new-emp" style="background:#2563eb; border-color:#2563eb; font-weight:600;">
                        ➕ 新增祺富员工档案
                    </button>
                </div>
            </div>

            <!-- 母表数据列表 (精确按用户指定11列标准呈现，新增勾选与离职操作) -->
            <div class="qifu-table-box">
                <table class="qifu-table" id="table-qifu-emp">
                    <thead>
                        <tr>
                            <th style="width:36px; min-width:36px; max-width:36px; text-align:center;"><input type="checkbox" id="check-all-tab1-employees" title="全选/反选"></th>
                            <th style="width:44px; min-width:44px; max-width:44px; text-align:center;">序号</th>
                            <th style="width:75px; min-width:75px; max-width:75px; text-align:center;">工号</th>
                            <th style="width:90px; min-width:90px; max-width:90px; text-align:left;">姓名</th>
                            <th style="min-width:170px; text-align:center;">证件号码</th>
                            <th style="min-width:90px; text-align:left;">岗位职务</th>
                            <th style="min-width:95px; text-align:center;">用工性质</th>
                            <th style="min-width:100px; text-align:center;">计薪方式</th>
                            <th style="min-width:110px; text-align:right;">固定/车间薪资</th>
                            <th style="min-width:100px; text-align:right;">社保基数</th>
                            <th style="min-width:100px; text-align:right;">公积金基数</th>
                            <th style="min-width:100px; text-align:right;">专项扣除</th>
                            <th style="width:130px; min-width:130px; text-align:center;">操作</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-qifu-emp"></tbody>
                </table>
            </div>
        </div>

        <!-- ========================================== -->
        <!-- Tab 2: 📤 2. 外部实发导入与薪资发放表 (老板娘实发表·24列) -->
        <!-- 序号 工号 姓名 作业天数 作业小时 天工资 小时工资 全勤费 加班小时 加班费 国勤天数 国勤工资 达标率 达标工资 扣除 考勤绩效工资合计 职位补贴 房/车补 补贴工资合计 应发工资合计 工资调整 实发工资合计 签字 备考 -->
        <!-- ========================================== -->
        <div id="qifu-tab-import" class="qifu-tab-content" style="display:none;">
            <!-- 上传拖拽与操作区 -->
            <div style="background:#fff; border-radius:12px; border:1px solid #e2e8f0; padding:18px 22px; margin-bottom:16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <div>
                        <h4 style="font-weight:700; color:#1e3a8a; margin:0 0 4px 0;">📤 外部实发工资表导入与智能解析</h4>
                        <div style="font-size:12.5px; color:#64748b;">支持直接上传车间/老板娘本地 <code>.xlsx/.xlsm</code> 实发工资表，系统自动提取出勤工时、加班考勤与车间实发，并生成 24 列标准薪资发放台账！</div>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-primary btn-sm" id="btn-tab2-export-dist" style="background:#059669; border-color:#059669; font-weight:600;">
                            📥 导出薪资发放表 Excel
                        </button>
                        <button class="btn btn-default btn-sm" id="btn-tab2-print-dist" style="font-weight:600;">
                            🖨️ 打印 / 导出 PDF
                        </button>
                    </div>
                </div>

                <div class="qifu-upload-dropzone" id="qifu-dropzone-tab2">
                    <input type="file" id="qifu-file-input-tab2" accept=".xlsx, .xlsm, .xls">
                    <div style="font-size: 28px; margin-bottom: 4px;">📂</div>
                    <div style="font-size: 14px; font-weight: 700; color: #1e40af;" id="qifu-filename-display-tab2">
                        点击或将车间实发 Excel 文件拖拽至此处上传
                    </div>
                    <div style="font-size: 11.5px; color: #64748b; margin-top: 2px;">
                        支持 .xlsx, .xlsm 格式 (自动识别考勤天数、工时、加班费、达标率与实发金额)
                    </div>
                </div>

                <div id="qifu-import-preview-tab2" style="display:none; margin-top:14px;">
                    <div id="qifu-import-badge-tab2" class="qifu-detected-badge" style="padding:10px 14px; border-radius:8px; background:#eff6ff; border:1px solid #bfdbfe; color:#1e40af; font-size:13px;">
                        🔍 正在预检文件数据...
                    </div>
                    <div style="margin-top:10px; display:flex; gap:10px; justify-content:flex-end;">
                        <button class="btn btn-default btn-sm" id="btn-import-cancel-tab2">重选文件</button>
                        <button class="btn btn-primary btn-sm" id="btn-import-confirm-tab2" style="background:#059669; border-color:#059669; font-weight:700;">
                            ⚡ 立即导入并融合核算 (生成24列薪资发放表)
                        </button>
                    </div>
                </div>
            </div>

            <!-- 24 列标准薪资发放台账表格 -->
            <div class="qifu-table-box">
                <table class="qifu-table table-bordered" id="table-tab2-dist-sheet" style="font-size:11.5px; margin-bottom:0; min-width:1800px;">
                    <thead style="position:sticky; top:0; background:#f8fafc; z-index:1;">
                        <tr>
                            <th style="width:36px;">序号</th>
                            <th>工号</th>
                            <th>姓名</th>
                            <th>作业天数</th>
                            <th>作业小时</th>
                            <th>天工资</th>
                            <th>小时工资</th>
                            <th>全勤费</th>
                            <th>加班小时</th>
                            <th>加班费</th>
                            <th>国勤天数</th>
                            <th>国勤工资</th>
                            <th>达标率</th>
                            <th>达标工资</th>
                            <th>扣除</th>
                            <th style="background:#eff6ff;">考勤绩效工资合计</th>
                            <th style="background:#fef3c7;">职位补贴</th>
                            <th style="background:#fef3c7;">房/车补</th>
                            <th style="background:#fef3c7;">补贴工资合计</th>
                            <th style="background:#dbeafe; color:#1e40af;">应发工资合计</th>
                            <th>工资调整</th>
                            <th style="background:#dcfce7; color:#166534;">实发工资合计</th>
                            <th>签字</th>
                            <th>备考</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-tab2-dist-sheet">
                        <tr><td colspan="24" style="text-align:center; padding:30px; color:#94a3b8;">暂无当月实发表数据，请点击上方区域上传车间实发 Excel</td></tr>
                    </tbody>
                    <tfoot id="tfoot-tab2-dist-sheet" style="background:#f8fafc; font-weight:700;"></tfoot>
                </table>
            </div>
        </div>

        <!-- ========================================== -->
        <!-- Tab 3: 🛡️ 3. 祺富社会保险台账与配置 (19列) -->
        <!-- ========================================== -->
        <div id="qifu-tab-social_insurance" class="qifu-tab-content" style="display:none;">
            <!-- 比例卡片 -->
            <div class="qifu-kpi-grid">
                <div class="qifu-kpi-card" style="border-left: 4px solid #2563eb;">
                    <div style="font-size:13px; font-weight:700; color:#1e40af;">🏢 单位社保合计比例</div>
                    <div style="font-size:22px; font-weight:800; color:#2563eb; margin-top:4px;" id="ins-tab3-ss-comp">27.55 %</div>
                    <div style="font-size:12px; color:#64748b;">养老16% + 失业0.5% + 医疗10% + 其他0.5% + 工伤0.55%</div>
                </div>
                <div class="qifu-kpi-card" style="border-left: 4px solid #10b981;">
                    <div style="font-size:13px; font-weight:700; color:#065f46;">👤 个人社保扣缴比例</div>
                    <div style="font-size:22px; font-weight:800; color:#059669; margin-top:4px;" id="ins-tab3-ss-pers">10.50 %</div>
                    <div style="font-size:12px; color:#64748b;">养老8% + 失业0.5% + 医疗2% (+大额救助22元/21元)</div>
                </div>
                <div class="qifu-kpi-card" style="border-left: 4px solid #f59e0b;">
                    <div style="font-size:13px; font-weight:700; color:#92400e;">📊 参保总盘与基数下限</div>
                    <div style="font-size:22px; font-weight:800; color:#d97706; margin-top:4px;" id="ins-tab3-ss-base">5,013.00 元</div>
                    <div style="font-size:12px; color:#64748b;">在保员工最低基数标准</div>
                </div>
                <div class="qifu-kpi-card" style="border-left: 4px solid #7c3aed;">
                    <div style="font-size:13px; font-weight:700; color:#5b21b6;">🛡️ 当期社保核定总额</div>
                    <div style="font-size:22px; font-weight:800; color:#7c3aed; margin-top:4px;" id="ins-tab3-ss-grand">¥ 37,461.92</div>
                    <div style="font-size:12px; color:#64748b;" id="ins-tab3-ss-sub">单位: ¥ 26,821.54 | 个人: ¥ 10,640.38</div>
                </div>
            </div>

            <!-- 工具栏 -->
            <div class="qifu-toolbar">
                <div class="qifu-toolbar-left">
                    <button class="btn btn-default btn-sm" id="btn-qifu-edit-ss-setting" style="color:#1e40af; border-color:#93c5fd; font-weight:600;">
                        ⚙️ 修改社保费率与基数配置
                    </button>
                    <button class="btn btn-default btn-sm" id="btn-qifu-ss-batch-min" style="color:#059669; border-color:#a7f3d0; font-weight:600;">
                        ⚡ 一键全员社保最低基数 (5124元)
                    </button>
                    <button class="btn btn-default btn-sm" id="btn-tab3-add-ss-adj" style="color:#b45309; border-color:#fde68a; background:#fef3c7; font-weight:600;">
                        ➕ 登记特殊多月补缴 / 滞纳金
                    </button>
                </div>
                <div class="qifu-toolbar-right">
                    <button class="btn btn-primary btn-sm" id="btn-tab3-export-ss" style="background:#059669; border-color:#059669; font-weight:600;">
                        📥 导出社保明细 Excel
                    </button>
                    <button class="btn btn-default btn-sm" id="btn-tab3-print-ss" style="font-weight:600;">
                        🖨️ 打印 / 导出 PDF
                    </button>
                </div>
            </div>

            <!-- 19 列双层表头社保明细大表 -->
            <div class="qifu-table-box">
                <table class="qifu-table table-bordered" id="table-tab3-ss-sheet" style="font-size:11.5px; margin-bottom:0;">
                    <thead>
                        <tr style="background:#f1f5f9; text-align:center; font-weight:700;">
                            <th colspan="7" style="background:#e0e7ff; color:#3730a3;">员工基本信息</th>
                            <th colspan="6" style="background:#dbeafe; color:#1e40af;">单位缴纳 (27.55%)</th>
                            <th colspan="5" style="background:#dcfce7; color:#166534;">个人缴纳 (10.50%)</th>
                            <th style="background:#ffedd5; color:#9a3412;">总合计</th>
                        </tr>
                        <tr>
                            <th style="width:36px;">序号</th>
                            <th>工号</th>
                            <th>姓名</th>
                            <th>证件号码</th>
                            <th>本期所属期</th>
                            <th>员工类型</th>
                            <th>社保_基数</th>
                            <th>单位养老</th>
                            <th>单位失业</th>
                            <th>单位医疗</th>
                            <th>单位其他医疗</th>
                            <th>单位工伤</th>
                            <th style="background:#eff6ff;">单位缴纳合计</th>
                            <th>个人养老</th>
                            <th>个人失业</th>
                            <th>个人医疗</th>
                            <th>个人大额医疗</th>
                            <th style="background:#f0fdf4;">个人缴纳合计</th>
                            <th style="background:#fff7ed;">总合计</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-tab3-ss-sheet"></tbody>
                    <tfoot id="tfoot-tab3-ss-sheet" style="background:#f8fafc; font-weight:700;"></tfoot>
                </table>
            </div>
        </div>

        <!-- ========================================== -->
        <!-- Tab 4: 🏛️ 4. 祺富住房公积金台账与配置 (12列) -->
        <!-- ========================================== -->
        <div id="qifu-tab-housing_fund" class="qifu-tab-content" style="display:none;">
            <!-- 比例卡片 -->
            <div class="qifu-kpi-grid">
                <div class="qifu-kpi-card" style="border-left: 4px solid #0f766e;">
                    <div style="font-size:13px; font-weight:700; color:#0f766e;">🏢 单位公积金缴存比例</div>
                    <div style="font-size:22px; font-weight:800; color:#0f766e; margin-top:4px;" id="ins-tab4-hf-comp">5.00 %</div>
                    <div style="font-size:12px; color:#64748b;">单位统筹缴存比例</div>
                </div>
                <div class="qifu-kpi-card" style="border-left: 4px solid #10b981;">
                    <div style="font-size:13px; font-weight:700; color:#065f46;">👤 个人公积金缴存比例</div>
                    <div style="font-size:22px; font-weight:800; color:#059669; margin-top:4px;" id="ins-tab4-hf-pers">5.00 %</div>
                    <div style="font-size:12px; color:#64748b;">个人工资代扣缴存比例</div>
                </div>
                <div class="qifu-kpi-card" style="border-left: 4px solid #f59e0b;">
                    <div style="font-size:13px; font-weight:700; color:#92400e;">📊 最低公积金基数</div>
                    <div style="font-size:22px; font-weight:800; color:#d97706; margin-top:4px;" id="ins-tab4-hf-base">2,320.00 元</div>
                    <div style="font-size:12px; color:#64748b;">普通员工标准: 116 / 116 元</div>
                </div>
                <div class="qifu-kpi-card" style="border-left: 4px solid #7c3aed;">
                    <div style="font-size:13px; font-weight:700; color:#5b21b6;">🏛️ 当期公积金月缴存总额</div>
                    <div style="font-size:22px; font-weight:800; color:#7c3aed; margin-top:4px;" id="ins-tab4-hf-grand">¥ 6,176.00</div>
                    <div style="font-size:12px; color:#64748b;" id="ins-tab4-hf-sub">单位: ¥ 3,088.00 | 个人: ¥ 3,088.00</div>
                </div>
            </div>

            <!-- 工具栏 -->
            <div class="qifu-toolbar">
                <div class="qifu-toolbar-left">
                    <button class="btn btn-default btn-sm" id="btn-qifu-edit-hf-setting" style="color:#0f766e; border-color:#99f6e4; font-weight:600;">
                        ⚙️ 修改公积金缴存比例
                    </button>
                    <button class="btn btn-default btn-sm" id="btn-tab4-hf-min" style="color:#059669; border-color:#059669; font-weight:600;">
                        ⚡ 一键全员公积金 (最低基数/孟祥山保护)
                    </button>
                    <button class="btn btn-default btn-sm" id="btn-tab4-hf-zero" style="color:#dc2626; border-color:#dc2626; font-weight:600;">
                        🚫 一键取消全员公积金 (设为0)
                    </button>
                </div>
                <div class="qifu-toolbar-right">
                    <button class="btn btn-primary btn-sm" id="btn-tab4-export-hf" style="background:#059669; border-color:#059669; font-weight:600;">
                        📥 导出公积金明细 Excel
                    </button>
                    <button class="btn btn-default btn-sm" id="btn-tab4-print-hf" style="font-weight:600;">
                        🖨️ 打印 / 导出 PDF
                    </button>
                </div>
            </div>

            <!-- 12 列双层表头公积金明细表 -->
            <div class="qifu-table-box">
                <table class="qifu-table table-bordered" id="table-tab4-hf-sheet" style="font-size:11.5px; margin-bottom:0;">
                    <thead>
                        <tr style="background:#f1f5f9; text-align:center; font-weight:700;">
                            <th colspan="6" style="background:#ccfbf1; color:#0f766e;">员工基本信息</th>
                            <th colspan="3" style="background:#e0f2fe; color:#0369a1;">单位缴存 (5%)</th>
                            <th colspan="2" style="background:#dcfce7; color:#15803d;">个人缴存 (5%)</th>
                            <th style="background:#ffedd5; color:#9a3412;">月缴存总额</th>
                        </tr>
                        <tr>
                            <th style="width:36px;">序号</th>
                            <th>工号</th>
                            <th>姓名</th>
                            <th>证件号码</th>
                            <th>本期所属期</th>
                            <th>员工类型</th>
                            <th>公积金_基数</th>
                            <th>单位缴存比例</th>
                            <th style="background:#f0f9ff;">单位缴存金额</th>
                            <th>个人缴存比例</th>
                            <th style="background:#f0fdf4;">个人缴存金额</th>
                            <th style="background:#fff7ed;">月缴存总额</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-tab4-hf-sheet"></tbody>
                    <tfoot id="tfoot-tab4-hf-sheet" style="background:#f8fafc; font-weight:700;"></tfoot>
                </table>
            </div>
        </div>

        <!-- ========================================== -->
        <!-- Tab 5: ⚖️ 5. 个人所得税核定与申报台账 (全新15列标准综合所得预扣预缴表) -->
        <!-- 序号 工号 姓名 证件号码 用工性质 发薪月份 本期税前收入 基本减除费用(5000) 社保个人扣缴 公积金个人扣缴 专项附加扣除 应纳税所得额 适用税率 速算扣除数 本月应预扣税额 -->
        <!-- ========================================== -->
        <div id="qifu-tab-tax" class="qifu-tab-content" style="display:none;">
            <!-- 个税 KPI 统筹看板 -->
            <div class="qifu-kpi-grid">
                <div class="qifu-kpi-card" style="border-left: 4px solid #dc2626;">
                    <div style="font-size:13px; font-weight:700; color:#991b1b;">⚖️ 本月个税代扣总额</div>
                    <div style="font-size:22px; font-weight:800; color:#dc2626; margin-top:4px;" id="tax-kpi-total">¥ 0.00</div>
                    <div style="font-size:12px; color:#64748b;">全员当期个人所得税合计</div>
                </div>
                <div class="qifu-kpi-card" style="border-left: 4px solid #2563eb;">
                    <div style="font-size:13px; font-weight:700; color:#1e40af;">📈 税前应发总额 (倒推总盘)</div>
                    <div style="font-size:22px; font-weight:800; color:#2563eb; margin-top:4px;" id="tax-kpi-gross">¥ 0.00</div>
                    <div style="font-size:12px; color:#64748b;">应发计税收入总额</div>
                </div>
                <div class="qifu-kpi-card" style="border-left: 4px solid #f59e0b;">
                    <div style="font-size:13px; font-weight:700; color:#92400e;">📉 扣除与减除费用总盘</div>
                    <div style="font-size:22px; font-weight:800; color:#d97706; margin-top:4px;" id="tax-kpi-ded">¥ 0.00</div>
                    <div style="font-size:12px; color:#64748b;">5000起征 + 险金 + 专项附加扣除</div>
                </div>
                <div class="qifu-kpi-card" style="border-left: 4px solid #059669;">
                    <div style="font-size:13px; font-weight:700; color:#065f46;">👥 纳税人数与申报期</div>
                    <div style="font-size:22px; font-weight:800; color:#059669; margin-top:4px;" id="tax-kpi-count">26 人</div>
                    <div style="font-size:12px; color:#64748b;" id="tax-kpi-period">所属发薪账期: 2026-07</div>
                </div>
            </div>

            <!-- 工具栏 -->
            <div class="qifu-toolbar">
                <div class="qifu-toolbar-left">
                    <div class="btn-group btn-group-sm" role="group" style="margin-right:6px;">
                        <button type="button" class="btn btn-default btn-tax-view-mode active" data-mode="full_68" style="font-weight:700; font-size:12px; background:#2563eb; color:#fff; border-color:#2563eb;">
                            📑 68列全量法定大宽表
                        </button>
                        <button type="button" class="btn btn-default btn-tax-view-mode" data-mode="simple" style="font-weight:700; font-size:12px; background:#fff; color:#334155; border-color:#cbd5e1;">
                            ✨ 财税精简版 (15列)
                        </button>
                    </div>
                    <button class="btn btn-default btn-sm" id="btn-qifu-edit-tax-setting" style="color:#b45309; border-color:#fde68a; background:#fef3c7; font-weight:600;">
                        ⚙️ 个税起征点、申报周期与 7 级税率表
                    </button>
                    <button class="btn btn-default btn-sm" id="btn-tab5-recalc-tax" style="color:#2563eb; border-color:#93c5fd; font-weight:600;">
                        ⚡ 重新核定当月个税
                    </button>
                </div>
                <div class="qifu-toolbar-right">
                    <button class="btn btn-primary btn-sm" id="btn-tab5-export-tax" style="background:#059669; border-color:#059669; font-weight:600;">
                        📥 导出个税申报明细 Excel
                    </button>
                    <button class="btn btn-default btn-sm" id="btn-tab5-print-tax" style="font-weight:600;">
                        🖨️ 打印 / 导出 PDF
                    </button>
                </div>
            </div>

            <!-- 15 列标准个人所得税明细大表 (顶部同步滑条与自适应超宽视口) -->
            <div class="qifu-table-box" id="tab5-table-box">
                <table class="qifu-table table-bordered" id="table-tab5-tax-sheet" style="font-size:11.5px; margin-bottom:0; min-width:1600px;">
                    <thead>
                        <tr style="background:#f8fafc;">
                            <th style="width:36px;">序号</th>
                            <th>工号</th>
                            <th>姓名</th>
                            <th>证件号码</th>
                            <th>用工性质</th>
                            <th>发薪月份</th>
                            <th style="background:#eff6ff;">本期税前收入</th>
                            <th>基本减除费用</th>
                            <th>社保个人扣缴</th>
                            <th>公积金个人扣缴</th>
                            <th>专项附加扣除</th>
                            <th style="background:#fef3c7; color:#92400e;">应纳税所得额</th>
                            <th style="text-align:center;">适用税率</th>
                            <th>速算扣除数</th>
                            <th style="background:#fee2e2; color:#b91c1c; font-weight:800;">本月应预扣税额</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-tab5-tax-sheet"></tbody>
                    <tfoot id="tfoot-tab5-tax-sheet" style="background:#f8fafc; font-weight:700;"></tfoot>
                </table>
            </div>
        </div>

        <!-- ========================================== -->
        <!-- Tab 6: 📊 6. 月度薪酬综合核定与结算 (母表与老板娘混合总盘) -->
        <!-- ========================================== -->
        <div id="qifu-tab-settlement" class="qifu-tab-content" style="display:none;">
            <!-- 4 大黄金统筹 KPI 看板 -->
            <div class="qifu-kpi-grid">
                <!-- 卡片 1: 在册用工结构 -->
                <div class="qifu-kpi-card" style="border-left: 4px solid #3b82f6;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="font-size:13px; font-weight:700; color:#1e40af;">👥 在册用工结构</span>
                        <span class="qifu-status-badge qifu-status-locked" style="font-size:10.5px;">底册档案</span>
                    </div>
                    <div style="font-size:22px; font-weight:800; color:#0f172a; margin-bottom:8px;">
                        <span id="kpi-emp-total">26</span> <span style="font-size:12px; font-weight:500; color:#64748b;">人 在册总数</span>
                    </div>
                    <div style="font-size:12px; line-height:1.7; color:#475569;">
                        <div style="display:flex; justify-content:space-between;"><span>🛡️ 社保公积金人员 (正式工):</span><strong style="color:#2563eb;" id="kpi-emp-insured">19 人</strong></div>
                        <div style="display:flex; justify-content:space-between;"><span>👴 退休返聘人员:</span><strong style="color:#d97706;" id="kpi-emp-rehire">5 人</strong></div>
                        <div style="display:flex; justify-content:space-between;"><span>🏷️ 其他人员合计 (临时/外籍):</span><strong style="color:#64748b;" id="kpi-emp-other">2 人</strong></div>
                    </div>
                </div>

                <!-- 卡片 2: 社会保险统筹 -->
                <div class="qifu-kpi-card" style="border-left: 4px solid #1e40af;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="font-size:13px; font-weight:700; color:#1e3a8a;">🛡️ 社会保险统筹</span>
                        <span class="qifu-status-badge qifu-status-locked" style="font-size:10.5px;" id="kpi-ss-badge">缴纳 8月 · 所属 202608</span>
                    </div>
                    <div style="font-size:20px; font-weight:800; color:#1e40af; margin-bottom:8px;" id="kpi-ss-grand">
                        ¥ 37,461.92
                    </div>
                    <div style="font-size:12px; line-height:1.7; color:#475569;">
                        <div style="display:flex; justify-content:space-between;"><span>🏢 公司承担社保:</span><strong style="color:#1e3a8a;" id="kpi-ss-comp">¥ 26,821.54</strong></div>
                        <div style="display:flex; justify-content:space-between;"><span>👤 员工个人代扣:</span><strong style="color:#15803d;" id="kpi-ss-pers">¥ 10,640.38</strong></div>
                        <div style="display:flex; justify-content:space-between;"><span>👥 参保人数 / 基数总盘:</span><span style="color:#64748b;"><strong id="kpi-ss-count">19</strong>人 | <span id="kpi-ss-base">¥ 97,356.00</span></span></div>
                    </div>
                </div>

                <!-- 卡片 3: 住房公积金统筹 -->
                <div class="qifu-kpi-card" style="border-left: 4px solid #0f766e;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="font-size:13px; font-weight:700; color:#0f766e;">🏛️ 住房公积金统筹</span>
                        <span class="qifu-status-badge qifu-status-locked" style="font-size:10.5px;" id="kpi-hf-badge">缴纳 8月 · 所属 202608</span>
                    </div>
                    <div style="font-size:20px; font-weight:800; color:#0f766e; margin-bottom:8px;" id="kpi-hf-grand">
                        ¥ 6,176.00
                    </div>
                    <div style="font-size:12px; line-height:1.7; color:#475569;">
                        <div style="display:flex; justify-content:space-between;"><span>🏢 公司缴存公积金 (5%):</span><strong style="color:#0369a1;" id="kpi-hf-comp">¥ 3,088.00</strong></div>
                        <div style="display:flex; justify-content:space-between;"><span>👤 员工个人代扣 (5%):</span><strong style="color:#15803d;" id="kpi-hf-pers">¥ 3,088.00</strong></div>
                        <div style="display:flex; justify-content:space-between;"><span>👥 参保人数 / 基数总盘:</span><span style="color:#64748b;"><strong id="kpi-hf-count">19</strong>人 | <span id="kpi-hf-base">¥ 61,760.00</span></span></div>
                    </div>
                </div>

                <!-- 卡片 4: 薪资发薪总盘与个税 -->
                <div class="qifu-kpi-card" style="border-left: 4px solid #16a34a;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="font-size:13px; font-weight:700; color:#15803d;">💰 薪酬发薪总盘与个税</span>
                        <span class="qifu-status-badge qifu-status-locked" style="font-size:10.5px;" id="kpi-payroll-badge">发薪 2026-07 (在册 26人)</span>
                    </div>
                    <div style="font-size:20px; font-weight:800; color:#16a34a; margin-bottom:8px;" id="kpi-total-net">
                        ¥ 0.00
                    </div>
                    <div style="font-size:12px; line-height:1.7; color:#475569;">
                        <div style="display:flex; justify-content:space-between;"><span>📈 倒推税前应发总额:</span><strong style="color:#2563eb;" id="kpi-total-gross">¥ 0.00</strong></div>
                        <div style="display:flex; justify-content:space-between;"><span>⚖️ 本月个税代扣合计:</span><strong style="color:#dc2626;" id="kpi-total-tax">¥ 0.00</strong></div>
                        <div style="display:flex; justify-content:space-between;"><span>📉 个人代扣总额 (险金+个税):</span><strong style="color:#d97706;" id="kpi-total-person-ded">¥ 0.00</strong></div>
                    </div>
                </div>
            </div>

            <!-- 工具栏 -->
            <div class="qifu-toolbar">
                <div class="qifu-toolbar-left">
                    <button class="btn btn-default btn-sm" id="btn-qifu-calc-payroll" style="font-weight:600; color:#2563eb; border-color:#93c5fd;">
                        ⚡ 重新融合核算 (按最新母表与基数)
                    </button>
                    <button class="btn btn-default btn-sm" id="btn-view-salary-dist" style="color:#1e3a8a; border-color:#93c5fd; font-weight:600;">
                        📋 查看薪资发放表 (24列)
                    </button>
                    <button class="btn btn-default btn-sm" id="btn-view-acc-sheet" style="color:#15803d; border-color:#86efac; font-weight:600;">
                        📑 查看记账工资表 (11列)
                    </button>
                    <button class="btn btn-default btn-sm" id="btn-view-ins-sheet-modal" style="color:#6d28d9; border-color:#c4b5fd; font-weight:600;">
                        🛡️ 查看社会保险 (19列弹窗)
                    </button>
                    <button class="btn btn-default btn-sm" id="btn-view-hf-sheet-modal" style="color:#0f766e; border-color:#99f6e4; font-weight:600;">
                        🏛️ 查看住房公积金 (12列弹窗)
                    </button>
                    <button class="btn btn-default btn-sm" id="btn-view-tax-sheet-modal" style="color:#b45309; border-color:#fde68a; font-weight:600;">
                        ⚖️ 查看个人所得税 (15列弹窗)
                    </button>
                </div>
                <div class="qifu-toolbar-right" style="display:flex; gap:8px;">
                    <button class="btn btn-primary btn-sm" id="btn-export-excel-both" style="background:#2563eb; border-color:#2563eb; font-weight:600;">
                        📥 导出标准全量 Excel (5张Sheet)
                    </button>
                </div>
            </div>

            <!-- 薪酬核定明细表格 (顶部同步滑条与17列大宽表) -->
            <div class="qifu-table-box" id="tab6-table-box">
                <table class="qifu-table" id="table-qifu-payroll">
                    <thead>
                        <tr>
                            <th style="width:45px;">序号</th>
                            <th>工号</th>
                            <th>姓名</th>
                            <th>岗位职务</th>
                            <th>用工性质</th>
                            <th>出勤天/工时</th>
                            <th>车间实发 (税后)</th>
                            <th>职位补贴</th>
                            <th>租房/车补</th>
                            <th>当月总实发 (税后)</th>
                            <th>税前应发工资 (倒推)</th>
                            <th>社保个人代扣</th>
                            <th>公积金个人代扣</th>
                            <th>个税代扣</th>
                            <th>社保单位统筹</th>
                            <th>公积金单位缴纳</th>
                            <th>核算说明</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-qifu-payroll">
                        <tr><td colspan="17" style="text-align:center; padding:30px; color:#94a3b8;">暂无当月核算数据，请点击上方【2. 外部实发导入与智能解析】上传车间实发表</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    `;

    var $container = $(html).appendTo(page.main);

    // ==========================================
    // 基础格式化方法
    // ==========================================
    function fmtMoney(val) {
        if (val === null || val === undefined || isNaN(val)) return '¥ 0.00';
        return '¥ ' + Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    // ==========================================
    // 业务加载函数
    // ==========================================

    // 1. 加载 Tab 1: 员工档案母表 (精简11列标准结构)
    function load_qifu_employees() {
        frappe.call({
            method: 'ashan_cn_procurement.services.employee_salary_service.get_qifu_employees',
            args: { company: COMPANY, period_month: current_month },
            callback: function(r) {
                if (r.message) {
                    render_employees_view(r.message);
                }
            }
        });
    }

    function render_employees_view(list) {
        let total = list.length;
        let resigned = list.filter(e => e.is_resigned_this_month || e.employment_status === '离职').length;
        let insured = list.filter(e => (e.employee_type || '正式工') === '正式工' && !e.is_resigned_this_month && e.employment_status !== '离职').length;
        let rehire = list.filter(e => ((e.employee_type || '') === '退休返聘' || (e.employee_type || '') === '返聘工') && !e.is_resigned_this_month && e.employment_status !== '离职').length;
        let other = total - insured - rehire - resigned;

        $("#tab1-emp-total").text(total + ' 人');
        $("#tab1-emp-insured").text(insured + ' 人');
        $("#tab1-emp-rehire").text(rehire + ' 人');
        $("#tab1-emp-resigned").text(resigned + ' 人');
        $("#tab1-emp-other").text(other + ' 人');

        // 重置表头全选框
        $("#check-all-tab1-employees").prop("checked", false);

        let html = '';
        if (list.length === 0) {
            html = '<tr><td colspan="13" style="text-align:center; padding:30px; color:#94a3b8;">暂无员工档案，请点击上方【➕ 新增祺富员工档案】</td></tr>';
        } else {
            list.forEach((emp, idx) => {
                const isResigned = emp.is_resigned_this_month || emp.employment_status === '离职';
                const isInsured = !isResigned && (emp.is_insured || (emp.social_security_base > 0));
                const isHf = !isResigned && (emp.housing_fund_base > 0);
                html += `
                <tr style="${isResigned ? 'background:#fff1f2;' : ''}">
                    <td style="text-align:center; width:36px; min-width:36px; max-width:36px;"><input type="checkbox" class="tab1-emp-check" data-emp-no="${emp.employee_no}" data-emp-name="${emp.employee_name}"></td>
                    <td style="color:#94a3b8; text-align:center; width:44px; min-width:44px; max-width:44px;">${idx + 1}</td>
                    <td style="text-align:center; width:75px; min-width:75px; max-width:75px;"><strong>${emp.employee_no || '-'}</strong></td>
                    <td style="width:90px; min-width:90px; max-width:90px; text-align:left;">
                        <strong style="color:${isResigned ? '#991b1b' : '#1e3a8a'};">${emp.employee_name}</strong>
                    </td>
                    <td style="font-family:monospace; text-align:center; min-width:170px;">${emp.id_card || '-'}</td>
                    <td style="min-width:90px; text-align:left;">${emp.job_title || '操作工'}</td>
                    <td style="text-align:center; min-width:95px;">
                        ${isResigned ? `<span class="qifu-status-badge" style="background:#fee2e2; color:#b91c1c; font-weight:700; border:1px solid #fca5a5;" title="离职日期: ${emp.relieving_date || '当月'}">🚪 本月离职</span>` : `<span class="qifu-status-badge ${emp.employee_type === '正式工' ? 'qifu-status-locked' : 'qifu-status-draft'}">${emp.employee_type || '正式工'}</span>`}
                    </td>
                    <td style="text-align:center; min-width:100px;">${emp.salary_mode || '固定一口价'}</td>
                    <td class="qifu-money-cell" style="font-weight:600; min-width:110px;">${fmtMoney(emp.fixed_salary)}</td>
                    <td class="qifu-money-cell" style="color:${isInsured ? '#2563eb' : '#94a3b8'}; font-weight:600; min-width:100px;">${fmtMoney(emp.social_security_base)}</td>
                    <td class="qifu-money-cell" style="color:${isHf ? '#059669' : '#94a3b8'}; font-weight:600; min-width:100px;">${fmtMoney(emp.housing_fund_base)}</td>
                    <td class="qifu-money-cell" style="min-width:100px;">${fmtMoney(emp.total_deduction || emp.special_deductions_total)}</td>
                    <td style="text-align:center; white-space:nowrap; width:130px; min-width:130px;">
                        <button class="btn btn-default btn-xs btn-edit-emp" data-id="${emp.name}" style="color:#2563eb; margin-right:4px;">✏️ 修改</button>
                        ${isResigned ? `<button class="btn btn-default btn-xs btn-unresign-emp" data-emp-no="${emp.employee_no}" data-emp-name="${emp.employee_name}" style="color:#059669; border-color:#86efac;" title="撤销离职，恢复在职">🔄 恢复</button>` : `<button class="btn btn-default btn-xs btn-resign-emp" data-emp-no="${emp.employee_no}" data-emp-name="${emp.employee_name}" style="color:#dc2626; border-color:#fca5a5;" title="办理离职，次月社保公积金自动减员">🚪 离职</button>`}
                    </td>
                </tr>
                `;
            });
        }
        $("#tbody-qifu-emp").html(html);
        setTimeout(adjust_active_table_height, 50);
    }

    // 2. 加载 Tab 2: 24 列薪资发放表
    function load_salary_distribution_tab() {
        frappe.call({
            method: 'ashan_cn_procurement.services.payroll_settlement_service.get_salary_distribution_sheet',
            args: { company: COMPANY, period_month: current_month },
            callback: function(r) {
                if (!r.message || !r.message.rows) return;
                const dist_data = r.message;
                const rows = dist_data.rows || [];
                const tot = dist_data.totals || {};

                let trs = '';
                rows.forEach(r => {
                    trs += `
                    <tr>
                        <td style="text-align:center; color:#94a3b8;">${r.seq}</td>
                        <td style="text-align:center;"><strong>${r.employee_no}</strong></td>
                        <td><strong style="color:#1e3a8a;">${r.employee_name}</strong></td>
                        <td class="qifu-money-cell">${r.attendance_days || 0}</td>
                        <td class="qifu-money-cell">${r.work_hours || 0}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.day_salary)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.hour_salary)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.full_attendance)}</td>
                        <td class="qifu-money-cell">${r.overtime_hours || 0}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.overtime_salary)}</td>
                        <td class="qifu-money-cell">${r.national_days || 0}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.national_salary)}</td>
                        <td style="text-align:center;">${r.target_rate || '-'}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.target_salary)}</td>
                        <td class="qifu-money-cell" style="color:#dc2626;">${fmtMoney(r.deduction)}</td>
                        <td class="qifu-money-cell" style="font-weight:600;">${fmtMoney(r.workshop_subtotal)}</td>
                        <td class="qifu-money-cell" style="color:#b45309; font-weight:600;">${fmtMoney(r.post_allowance)}</td>
                        <td class="qifu-money-cell" style="color:#b45309; font-weight:600;">${fmtMoney(r.house_rent_allowance)}</td>
                        <td class="qifu-money-cell" style="color:#b45309; font-weight:700;">${fmtMoney(r.allowance_subtotal)}</td>
                        <td class="qifu-money-cell" style="color:#2563eb; font-weight:700;">${fmtMoney(r.payable_salary)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.salary_adjustment)}</td>
                        <td class="qifu-money-cell" style="color:#16a34a; font-weight:800; font-size:13px;">${fmtMoney(r.net_salary)}</td>
                        <td style="text-align:center; color:#cbd5e1;">${r.sign || ''}</td>
                        <td style="font-size:11px; color:#64748b;">${r.remarks || ''}</td>
                    </tr>
                    `;
                });
                $("#tbody-tab2-dist-sheet").html(trs);
                setTimeout(adjust_active_table_height, 50);

                let tfoot_html = `
                <tr>
                    <td colspan="3" style="text-align:center;">合计</td>
                    <td class="qifu-money-cell">${tot.attendance_days || 0}</td>
                    <td class="qifu-money-cell">${tot.work_hours || 0}</td>
                    <td>-</td><td>-</td>
                    <td class="qifu-money-cell">${fmtMoney(tot.full_attendance)}</td>
                    <td class="qifu-money-cell">${tot.overtime_hours || 0}</td>
                    <td class="qifu-money-cell">${fmtMoney(tot.overtime_salary)}</td>
                    <td class="qifu-money-cell">${tot.national_days || 0}</td>
                    <td class="qifu-money-cell">${fmtMoney(tot.national_salary)}</td>
                    <td>-</td>
                    <td class="qifu-money-cell">${fmtMoney(tot.target_salary)}</td>
                    <td class="qifu-money-cell" style="color:#dc2626;">${fmtMoney(tot.deduction)}</td>
                    <td class="qifu-money-cell">${fmtMoney(tot.workshop_subtotal)}</td>
                    <td class="qifu-money-cell" style="color:#b45309;">${fmtMoney(tot.post_allowance)}</td>
                    <td class="qifu-money-cell" style="color:#b45309;">${fmtMoney(tot.house_rent_allowance)}</td>
                    <td class="qifu-money-cell" style="color:#b45309;">${fmtMoney(tot.allowance_subtotal)}</td>
                    <td class="qifu-money-cell" style="color:#2563eb;">${fmtMoney(tot.payable_salary)}</td>
                    <td class="qifu-money-cell">${fmtMoney(tot.salary_adjustment)}</td>
                    <td class="qifu-money-cell" style="color:#16a34a; font-size:13px;">${fmtMoney(tot.net_salary)}</td>
                    <td>-</td><td>-</td>
                </tr>
                `;
                $("#tfoot-tab2-dist-sheet").html(tfoot_html);
            }
        });
    }

    // 3. 加载 Tab 3: 社保明细台账与配置
    function load_social_insurance_tab() {
        frappe.call({
            method: 'ashan_cn_procurement.services.payroll_settlement_service.get_social_insurance_sheet',
            args: { company: COMPANY, period_month: current_month },
            callback: function(r) {
                if (!r.message) return;
                const ins = r.message;
                const rows = ins.rows || [];
                const tot = ins.totals || {};

                $("#ins-tab3-ss-grand").text(fmtMoney(tot.grand_total));
                $("#ins-tab3-ss-sub").text(`单位: ${fmtMoney(tot.comp_total)} | 个人: ${fmtMoney(tot.pers_total)}`);
                if (rows.length > 0) {
                    $("#ins-tab3-ss-base").text(fmtMoney(rows[0].ss_base));
                }

                let trs = '';
                rows.forEach(r => {
                    const isAdj = !!r.adj_id;
                    trs += `
                    <tr style="${isAdj ? 'background:#fffbeb;' : ''}">
                        <td style="text-align:center; color:#94a3b8;">${r.seq}</td>
                        <td style="text-align:center;"><strong>${r.employee_no}</strong></td>
                        <td>
                            <strong style="color:#2563eb;">${r.employee_name}</strong>
                            ${isAdj ? `<span class="qifu-status-badge qifu-status-draft" style="font-size:10px; margin-left:4px;">${r.biz_type}</span> <a href="javascript:void(0)" class="btn-del-ss-adj" data-id="${r.adj_id}" style="color:#dc2626; font-size:11px; margin-left:4px;" title="删除此补缴/调整项">🗑️</a>` : ''}
                        </td>
                        <td style="text-align:center; font-family:monospace;">${r.id_card || '-'}</td>
                        <td style="text-align:center; font-weight:${isAdj ? '700; color:#b45309;' : 'normal;'}">${r.period_month_str}</td>
                        <td style="text-align:center;">${r.employee_type}</td>
                        <td class="qifu-money-cell" style="font-weight:600;">${fmtMoney(r.ss_base)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.comp_pension)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.comp_unemp)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.comp_med)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.comp_other_med)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.comp_injury)}</td>
                        <td class="qifu-money-cell" style="color:#1e40af; font-weight:700;">${fmtMoney(r.comp_total)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.pers_pension)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.pers_unemp)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.pers_med)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.pers_large_med)}</td>
                        <td class="qifu-money-cell" style="color:#166534; font-weight:700;">${fmtMoney(r.pers_total)}</td>
                        <td class="qifu-money-cell" style="color:#c2410c; font-weight:800; font-size:13px;">
                            ${fmtMoney(r.grand_total)}
                            ${r.late_fee > 0 ? `<div style="font-size:10px; color:#dc2626; font-weight:normal;">(含滞纳金 ${fmtMoney(r.late_fee)})</div>` : ''}
                        </td>
                    </tr>
                    `;
                });
                $("#tbody-tab3-ss-sheet").html(trs);
                setTimeout(adjust_active_table_height, 50);
                setTimeout(function() {
                    sync_dual_scrollbars($("#tab3-top-scrollbar"), $("#tab3-table-box"));
                }, 100);

                let tfoot_html = `
                <tr>
                    <td colspan="5" style="text-align:center; color:#334155; font-weight:700;">合计</td>
                    <td style="text-align:center; font-weight:700; color:#1e40af;">${rows.length}人参保</td>
                    <td class="qifu-money-cell">${fmtMoney(tot.ss_base)}</td>
                    <td class="qifu-money-cell">${fmtMoney(tot.comp_pension)}</td>
                    <td class="qifu-money-cell">${fmtMoney(tot.comp_unemp)}</td>
                    <td class="qifu-money-cell">${fmtMoney(tot.comp_med)}</td>
                    <td class="qifu-money-cell">${fmtMoney(tot.comp_other_med)}</td>
                    <td class="qifu-money-cell">${fmtMoney(tot.comp_injury)}</td>
                    <td class="qifu-money-cell" style="color:#1e40af; font-weight:700;">${fmtMoney(tot.comp_total)}</td>
                    <td class="qifu-money-cell">${fmtMoney(tot.pers_pension)}</td>
                    <td class="qifu-money-cell">${fmtMoney(tot.pers_unemp)}</td>
                    <td class="qifu-money-cell">${fmtMoney(tot.pers_med)}</td>
                    <td class="qifu-money-cell">${fmtMoney(tot.pers_large_med)}</td>
                    <td class="qifu-money-cell" style="color:#166534; font-weight:700;">${fmtMoney(tot.pers_total)}</td>
                    <td class="qifu-money-cell" style="color:#c2410c; font-size:13px; font-weight:800;">${fmtMoney(tot.grand_total)}</td>
                </tr>
                `;
                $("#tfoot-tab3-ss-sheet").html(tfoot_html);
            }
        });
    }

    // 4. 加载 Tab 4: 公积金明细台账与配置
    function load_housing_fund_tab() {
        frappe.call({
            method: 'ashan_cn_procurement.services.payroll_settlement_service.get_housing_fund_sheet',
            args: { company: COMPANY, period_month: current_month },
            callback: function(r) {
                if (!r.message) return;
                const hf = r.message;
                const rows = hf.rows || [];
                const tot = hf.totals || {};

                $("#ins-tab4-hf-grand").text(fmtMoney(tot.total_amount));
                $("#ins-tab4-hf-sub").text(`单位: ${fmtMoney(tot.comp_amount)} | 个人: ${fmtMoney(tot.pers_amount)}`);

                let trs = '';
                rows.forEach(r => {
                    trs += `
                    <tr>
                        <td style="text-align:center; color:#94a3b8;">${r.seq}</td>
                        <td style="text-align:center;"><strong>${r.employee_no}</strong></td>
                        <td><strong style="color:#2563eb;">${r.employee_name}</strong></td>
                        <td style="text-align:center; font-family:monospace;">${r.id_card || '-'}</td>
                        <td style="text-align:center;">${r.period_month_str}</td>
                        <td style="text-align:center;">${r.employee_type}</td>
                        <td class="qifu-money-cell" style="font-weight:600;">${fmtMoney(r.hf_base)}</td>
                        <td style="text-align:center;">${r.comp_rate}%</td>
                        <td class="qifu-money-cell" style="color:#0369a1; font-weight:600;">${fmtMoney(r.comp_amount)}</td>
                        <td style="text-align:center;">${r.pers_rate}%</td>
                        <td class="qifu-money-cell" style="color:#15803d; font-weight:600;">${fmtMoney(r.pers_amount)}</td>
                        <td class="qifu-money-cell" style="color:#c2410c; font-weight:800; font-size:13px;">${fmtMoney(r.total_amount)}</td>
                    </tr>
                    `;
                });
                $("#tbody-tab4-hf-sheet").html(trs);
                setTimeout(adjust_active_table_height, 50);
                setTimeout(function() {
                    sync_dual_scrollbars($("#tab4-top-scrollbar"), $("#tab4-table-box"));
                }, 100);

                let tfoot_html = `
                <tr>
                    <td colspan="5" style="text-align:center; color:#334155; font-weight:700;">合计</td>
                    <td style="text-align:center; font-weight:700; color:#1e40af;">${rows.length}人参缴</td>
                    <td class="qifu-money-cell">${fmtMoney(tot.hf_base)}</td>
                    <td style="text-align:center;">5%</td>
                    <td class="qifu-money-cell" style="color:#0369a1; font-weight:700;">${fmtMoney(tot.comp_amount)}</td>
                    <td style="text-align:center;">5%</td>
                    <td class="qifu-money-cell" style="color:#15803d; font-weight:700;">${fmtMoney(tot.pers_amount)}</td>
                    <td class="qifu-money-cell" style="color:#c2410c; font-size:13px; font-weight:800;">${fmtMoney(tot.total_amount)}</td>
                </tr>
                `;
                $("#tfoot-tab4-hf-sheet").html(tfoot_html);
            }
        });
    }

    // 5. 加载 Tab 5: 个人所得税核定与申报台账 · 支持【✨ 财税精简版 (15列)】与【📑 68列全量法定大宽表】
    function render_tax_simple_table(data, cur_m) {
        const rows = data.rows || [];
        const tot = data.totals || {};

        let thead_html = `
        <tr style="background:#f1f5f9; text-align:center; font-weight:700;">
            <th style="width:36px;">序号</th>
            <th>工号</th>
            <th>姓名 (点击穿透)</th>
            <th>证件号码</th>
            <th>用工性质</th>
            <th>发薪账期</th>
            <th style="background:#dbeafe; color:#1e40af;">本期税前收入</th>
            <th>基本减除(5000×N)</th>
            <th style="background:#fef3c7; color:#b45309;">本期社保扣除</th>
            <th style="background:#fef3c7; color:#b45309;">本期公积金扣除</th>
            <th style="background:#e0f2fe; color:#0369a1;">本期专项附加扣除</th>
            <th style="background:#fff7ed; color:#9a3412;">累计应纳税所得额</th>
            <th>预扣率</th>
            <th>速算扣除数</th>
            <th>往期已缴税额</th>
            <th style="background:#fef2f2; color:#dc2626; font-weight:800;">本月应预扣税额</th>
            <th style="background:#dcfce7; color:#166534; font-weight:800;">税后实发工资</th>
        </tr>
        `;

        let trs = '';
        if (rows.length === 0) {
            trs = `<tr><td colspan="17" style="text-align:center; padding:30px; color:#94a3b8;">当前账期【${cur_m}】暂无薪资个税核定数据。</td></tr>`;
        } else {
            rows.forEach(r => {
                const tax_cur_val = (r.tax_current !== undefined ? r.tax_current : (r.tax_amount || 0));
                const ss_val = (r.ss_person !== undefined ? r.ss_person : (r.ss_person_total || 0));
                const hf_val = (r.hf_person !== undefined ? r.hf_person : (r.hf_person_total || 0));
                const spec_add_val = (r.spec_add_tot_cur !== undefined ? r.spec_add_tot_cur : (r.special_deductions_total || 0));
                const taxable_val = (r.taxable_all !== undefined ? r.taxable_all : (r.taxable_income || 0));
                const thresh_val = (r.thresh_all !== undefined ? r.thresh_all : (r.thresh_cur || 5000));
                const tax_prior_val = (r.tax_paid_prior !== undefined ? r.tax_paid_prior : (r.tax_paid_accumulated || 0));

                trs += `
                <tr>
                    <td style="text-align:center; color:#94a3b8;">${r.seq}</td>
                    <td style="text-align:center;"><strong>${r.employee_no}</strong></td>
                    <td>
                        <a href="javascript:void(0);" class="btn-drill-emp-history" data-emp="${r.employee_no}" style="color:#2563eb; font-weight:700; text-decoration:underline;" title="点击穿透查看 ${r.employee_name} 整个申报周期的月度发薪与个税轨迹">
                            ${r.employee_name} 🔍
                        </a>
                    </td>
                    <td style="text-align:center; font-family:monospace;">${r.id_card || '-'}</td>
                    <td style="text-align:center;"><span class="qifu-status-badge qifu-status-locked" style="background:#e0e7ff; color:#3730a3;">${r.employee_type || '正式工'}</span></td>
                    <td style="text-align:center;">${cur_m}</td>
                    <td class="qifu-money-cell" style="font-weight:700; color:#2563eb;">${fmtMoney(r.gross_salary)}</td>
                    <td class="qifu-money-cell" style="color:#64748b;">${fmtMoney(thresh_val)}</td>
                    <td class="qifu-money-cell" style="color:#d97706;" title="社保个人五险扣除">${fmtMoney(ss_val)}</td>
                    <td class="qifu-money-cell" style="color:#d97706;" title="公积金个人扣除">${fmtMoney(hf_val)}</td>
                    <td class="qifu-money-cell" style="color:#0891b2;" title="7 项专项附加扣除合计">${fmtMoney(spec_add_val)}</td>
                    <td class="qifu-money-cell" style="color:#9a3412; font-weight:700; background:#fff7ed;">${fmtMoney(taxable_val)}</td>
                    <td style="text-align:center; font-weight:700;">${r.tax_rate}%</td>
                    <td class="qifu-money-cell" style="color:#64748b;">${fmtMoney(r.quick_deduct || r.quick_deduction || 0)}</td>
                    <td class="qifu-money-cell" style="color:#64748b;">${fmtMoney(tax_prior_val)}</td>
                    <td class="qifu-money-cell" style="color:${tax_cur_val > 0 ? '#dc2626' : '#166534'}; font-weight:800; font-size:13px; background:${tax_cur_val > 0 ? '#fef2f2' : 'transparent'};">
                        ${fmtMoney(tax_cur_val)}
                    </td>
                    <td class="qifu-money-cell" style="color:#166534; font-weight:700;">${fmtMoney(r.net_salary)}</td>
                </tr>
                `;
            });
        }

        const tot_tax_val = tot.tax_current !== undefined ? tot.tax_current : (tot.tax_amount || 0);
        const tot_ss_val = tot.ss_cur !== undefined ? tot.ss_cur : (tot.ss_person_total || 0);
        const tot_hf_val = tot.hf_cur !== undefined ? tot.hf_cur : (tot.hf_person_total || 0);
        const tot_spec_add_val = tot.spec_add_tot_cur !== undefined ? tot.spec_add_tot_cur : (tot.special_deductions_total || 0);
        const tot_taxable_val = tot.taxable_all !== undefined ? tot.taxable_all : (tot.taxable_income || 0);

        let tfoot_html = `
        <tr>
            <td colspan="6" style="text-align:center; color:#334155; font-weight:700;">合计</td>
            <td class="qifu-money-cell" style="color:#2563eb; font-weight:700;">${fmtMoney(tot.gross_salary)}</td>
            <td class="qifu-money-cell">-</td>
            <td class="qifu-money-cell" style="color:#d97706; font-weight:700;">${fmtMoney(tot_ss_val)}</td>
            <td class="qifu-money-cell" style="color:#d97706; font-weight:700;">${fmtMoney(tot_hf_val)}</td>
            <td class="qifu-money-cell" style="color:#0891b2; font-weight:700;">${fmtMoney(tot_spec_add_val)}</td>
            <td class="qifu-money-cell" style="color:#9a3412; font-weight:700;">${fmtMoney(tot_taxable_val)}</td>
            <td style="text-align:center;">-</td>
            <td class="qifu-money-cell">-</td>
            <td class="qifu-money-cell">-</td>
            <td class="qifu-money-cell" style="color:#dc2626; font-weight:800; font-size:13px;">${fmtMoney(tot_tax_val)}</td>
            <td class="qifu-money-cell" style="color:#166534; font-weight:800; font-size:13px;">${fmtMoney(tot.net_salary)}</td>
        </tr>
        `;

        $("#table-tab5-tax-sheet thead").html(thead_html);
        $("#tbody-tab5-tax-sheet").html(trs);
        $("#tfoot-tab5-tax-sheet").html(tfoot_html);
        adjust_active_table_height();
    }

    function render_tax_full_68_table(data, cur_m) {
        const rows = data.rows || [];
        const tot = data.totals || {};

        let thead_html = `
        <tr style="background:#f1f5f9; text-align:center; font-weight:700; font-size:11px;">
            <th colspan="9" style="background:#e0e7ff; color:#3730a3;">一、员工基本信息</th>
            <th colspan="5" style="background:#fef3c7; color:#92400e;">二、工资扣除 (本月)</th>
            <th colspan="6" style="background:#dcfce7; color:#166534;">三、专项扣除 (本月五险一金)</th>
            <th colspan="8" style="background:#e0f2fe; color:#0369a1;">四、专项附加扣除 (本月7项)</th>
            <th colspan="4" style="background:#fae8ff; color:#86198f;">五、往期累计 (申报周期)</th>
            <th colspan="4" style="background:#ffedd5; color:#9a3412;">六、全部累计 (往期+本月)</th>
            <th colspan="8" style="background:#fee2e2; color:#991b1b;">七、税款核定与实发</th>
        </tr>
        <tr style="background:#f8fafc; font-size:10.5px; text-align:center;">
            <!-- 1. 基本信息 -->
            <th style="width:32px;">序号</th>
            <th>工号</th>
            <th>姓名</th>
            <th>证件号码</th>
            <th>性别</th>
            <th>所属期</th>
            <th>员工类型</th>
            <th>目标工资</th>
            <th>工资类型</th>
            <!-- 2. 工资扣除 (本月) -->
            <th>税前工资</th>
            <th>起征点扣除</th>
            <th>公积金</th>
            <th>社保</th>
            <th>扣除合计</th>
            <!-- 3. 专项扣除 (本月) -->
            <th>基本养老</th>
            <th>基本医疗</th>
            <th>大额医疗</th>
            <th>失业保险</th>
            <th>住房公积金</th>
            <th>专项合计</th>
            <!-- 4. 专项附加扣除 (本月) -->
            <th>子女教育</th>
            <th>继续教育</th>
            <th>大病医疗</th>
            <th>房贷利息</th>
            <th>住房租金</th>
            <th>赡养老人</th>
            <th>婴幼儿照护</th>
            <th>附加合计</th>
            <!-- 5. 往期累计 -->
            <th>税前工资(往)</th>
            <th>起征点(往)</th>
            <th>专项扣除(往)</th>
            <th>专项附加(往)</th>
            <!-- 6. 全部累计 -->
            <th>税前工资(全)</th>
            <th>起征点(全)</th>
            <th>专项扣除(全)</th>
            <th>专项附加(全)</th>
            <!-- 7. 税款计算 -->
            <th style="background:#fff7ed; color:#9a3412; font-weight:700;">累计应税所得额</th>
            <th>预扣率</th>
            <th>速算扣除数</th>
            <th>累计应纳税额</th>
            <th>减免税额</th>
            <th>往期已缴税额</th>
            <th style="background:#fef2f2; color:#dc2626; font-weight:800;">应补/退税额</th>
            <th style="background:#dcfce7; color:#166534; font-weight:800;">税后工资</th>
        </tr>
        `;

        let trs = '';
        if (rows.length === 0) {
            trs = `<tr><td colspan="44" style="text-align:center; padding:30px; color:#94a3b8;">当前账期【${cur_m}】暂无 68 列法定个税数据。</td></tr>`;
        } else {
            rows.forEach(r => {
                trs += `
                <tr style="font-size:11px;">
                    <td style="text-align:center; color:#94a3b8;">${r.seq}</td>
                    <td style="text-align:center;"><strong>${r.employee_no}</strong></td>
                    <td>
                        <a href="javascript:void(0);" class="btn-drill-emp-history" data-emp="${r.employee_no}" style="color:#2563eb; font-weight:700;">
                            ${r.employee_name}
                        </a>
                    </td>
                    <td style="text-align:center; font-family:monospace; font-size:10px;">${r.id_card || '-'}</td>
                    <td style="text-align:center;">${r.gender || '-'}</td>
                    <td style="text-align:center;">${r.period_month_str}</td>
                    <td style="text-align:center;">${r.employee_type}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.target_salary)}</td>
                    <td style="text-align:center;">${r.salary_mode}</td>

                    <!-- 2. 工资扣除 (本月) -->
                    <td class="qifu-money-cell" style="color:#2563eb; font-weight:600;">${fmtMoney(r.gross_salary)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.thresh_cur)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.hf_person)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.ss_person)}</td>
                    <td class="qifu-money-cell" style="color:#b45309; font-weight:600;">${fmtMoney(r.deduct_cur_tot)}</td>

                    <!-- 3. 专项扣除 (本月) -->
                    <td class="qifu-money-cell">${fmtMoney(r.ss_pension)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.ss_med)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.ss_large_med)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.ss_unemp)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.hf_spec)}</td>
                    <td class="qifu-money-cell" style="color:#166534; font-weight:600;">${fmtMoney(r.spec_tot_cur)}</td>

                    <!-- 4. 专项附加扣除 (本月) -->
                    <td class="qifu-money-cell">${fmtMoney(r.spec_add_child)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.spec_add_edu)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.spec_add_med)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.spec_add_loan)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.spec_add_rent)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.spec_add_elder)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.spec_add_baby)}</td>
                    <td class="qifu-money-cell" style="color:#0369a1; font-weight:600;">${fmtMoney(r.spec_add_tot_cur)}</td>

                    <!-- 5. 往期累计 -->
                    <td class="qifu-money-cell">${fmtMoney(r.gross_prior)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.thresh_prior)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.spec_tot_prior)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.spec_add_tot_prior)}</td>

                    <!-- 6. 全部累计 -->
                    <td class="qifu-money-cell" style="font-weight:600;">${fmtMoney(r.gross_all)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.thresh_all)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.spec_tot_all)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.spec_add_tot_all)}</td>

                    <!-- 7. 税款计算 -->
                    <td class="qifu-money-cell" style="color:#9a3412; font-weight:700; background:#fff7ed;">${fmtMoney(r.taxable_all)}</td>
                    <td style="text-align:center; font-weight:700;">${r.tax_rate}%</td>
                    <td class="qifu-money-cell">${fmtMoney(r.quick_deduct)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.tax_calculated)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.tax_relief)}</td>
                    <td class="qifu-money-cell">${fmtMoney(r.tax_paid_prior)}</td>
                    <td class="qifu-money-cell" style="color:${r.tax_current > 0 ? '#dc2626' : '#166534'}; font-weight:800; font-size:12px; background:${r.tax_current > 0 ? '#fef2f2' : 'transparent'};">
                        ${fmtMoney(r.tax_current)}
                    </td>
                    <td class="qifu-money-cell" style="color:#166534; font-weight:800; font-size:12px;">${fmtMoney(r.net_salary)}</td>
                </tr>
                `;
            });
        }

        let tfoot_html = `
        <tr style="font-size:11px; font-weight:700;">
            <td colspan="9" style="text-align:center; color:#334155;">合计</td>
            <td class="qifu-money-cell" style="color:#2563eb;">${fmtMoney(tot.gross_salary)}</td>
            <td class="qifu-money-cell">${fmtMoney(tot.thresh_cur)}</td>
            <td class="qifu-money-cell">${fmtMoney(tot.hf_cur)}</td>
            <td class="qifu-money-cell">${fmtMoney(tot.ss_cur)}</td>
            <td class="qifu-money-cell" style="color:#b45309;">${fmtMoney(tot.deduct_cur)}</td>
            <td colspan="6" class="qifu-money-cell" style="color:#166534;">${fmtMoney(tot.spec_tot_cur)}</td>
            <td colspan="8" class="qifu-money-cell" style="color:#0369a1;">${fmtMoney(tot.spec_add_tot_cur)}</td>
            <td class="qifu-money-cell">${fmtMoney(tot.gross_prior)}</td>
            <td class="qifu-money-cell">${fmtMoney(tot.thresh_prior)}</td>
            <td class="qifu-money-cell">${fmtMoney(tot.spec_tot_prior)}</td>
            <td class="qifu-money-cell">${fmtMoney(tot.spec_add_tot_prior)}</td>
            <td class="qifu-money-cell">${fmtMoney(tot.gross_all)}</td>
            <td class="qifu-money-cell">${fmtMoney(tot.thresh_all)}</td>
            <td class="qifu-money-cell">${fmtMoney(tot.spec_tot_all)}</td>
            <td class="qifu-money-cell">${fmtMoney(tot.spec_add_tot_all)}</td>
            <td class="qifu-money-cell" style="color:#9a3412;">${fmtMoney(tot.taxable_all)}</td>
            <td>-</td><td>-</td>
            <td class="qifu-money-cell">${fmtMoney(tot.tax_calculated)}</td>
            <td>-</td>
            <td class="qifu-money-cell">${fmtMoney(tot.tax_paid_prior)}</td>
            <td class="qifu-money-cell" style="color:#dc2626; font-size:12px;">${fmtMoney(tot.tax_current)}</td>
            <td class="qifu-money-cell" style="color:#166534; font-size:12px;">${fmtMoney(tot.net_salary)}</td>
        </tr>
        `;

        $("#table-tab5-tax-sheet thead").html(thead_html);
        $("#tbody-tab5-tax-sheet").html(trs);
        $("#tfoot-tab5-tax-sheet").html(tfoot_html);
        adjust_active_table_height();
    }

    function load_tax_settlement_tab() {
        const cur_m = $("#qifu-month-select").val() || current_month;
        if (current_tax_view_mode === 'simple') {
            frappe.call({
                method: 'ashan_cn_procurement.services.payroll_settlement_service.get_tax_settlement_sheet',
                args: { company: COMPANY, period_month: cur_m },
                callback: function(r) {
                    if (!r.message) return;
                    const data = r.message;
                    const tot = data.totals || {};
                    $("#tax-kpi-total").text(fmtMoney(tot.tax_amount || tot.current_tax || 0));
                    $("#tax-kpi-gross").text(fmtMoney(tot.gross_salary));
                    $("#tax-kpi-ded").text(fmtMoney((tot.tax_threshold || 5000) + (tot.ss_person_total || 0) + (tot.hf_person_total || 0) + (tot.special_deductions_total || 0)));
                    $("#tax-kpi-count").text(`${data.rows ? data.rows.length : 0} 人`);
                    $("#tax-kpi-period").text(`所属发薪账期: ${cur_m}`);
                    render_tax_simple_table(data, cur_m);
                }
            });
        } else {
            frappe.call({
                method: 'ashan_cn_procurement.services.payroll_settlement_service.get_tax_settlement_full_sheet',
                args: { company: COMPANY, period_month: cur_m },
                callback: function(r) {
                    if (!r.message) return;
                    const data = r.message;
                    const tot = data.totals || {};
                    $("#tax-kpi-total").text(fmtMoney(tot.tax_current));
                    $("#tax-kpi-gross").text(fmtMoney(tot.gross_salary));
                    $("#tax-kpi-ded").text(fmtMoney(tot.deduct_cur));
                    $("#tax-kpi-count").text(`${data.rows ? data.rows.length : 0} 人`);
                    $("#tax-kpi-period").text(`所属发薪账期: ${cur_m} (第 ${data.month_idx || 1} 个月)`);
                    render_tax_full_68_table(data, cur_m);
                }
            });
        }
    }

// 6. 加载 Tab 6: 月度薪酬综合核定结算 (母表与老板娘混合总盘)
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
        const kpi = data.kpi_summary || {};

        // 卡片 1: 人员结构
        $("#kpi-emp-total").text(kpi.total_profile_count || data.total_employees || 0);
        $("#kpi-emp-insured").text((kpi.insured_count || 0) + ' 人');
        $("#kpi-emp-rehire").text((kpi.rehire_count || 0) + ' 人');
        $("#kpi-emp-other").text((kpi.other_count || 0) + ' 人');

        // 卡片 2: 社保统筹
        $("#kpi-ss-badge").text(`缴纳: ${kpi.ss_payment_month_name || ''} · 所属: ${kpi.ss_period_month_str || ''}`);
        $("#kpi-ss-grand").text(fmtMoney(kpi.ss_grand_total));
        $("#kpi-ss-comp").text(fmtMoney(kpi.ss_comp_total));
        $("#kpi-ss-pers").text(fmtMoney(kpi.ss_pers_total));
        $("#kpi-ss-count").text(kpi.ss_count || 0);
        $("#kpi-ss-base").text(fmtMoney(kpi.ss_base_total));

        // 卡片 3: 公积金统筹
        $("#kpi-hf-badge").text(`缴纳: ${kpi.hf_payment_month_name || ''} · 所属: ${kpi.hf_period_month_str || ''}`);
        $("#kpi-hf-grand").text(fmtMoney(kpi.hf_grand_total));
        $("#kpi-hf-comp").text(fmtMoney(kpi.hf_comp_total));
        $("#kpi-hf-pers").text(fmtMoney(kpi.hf_pers_total));
        $("#kpi-hf-count").text(kpi.hf_count || 0);
        $("#kpi-hf-base").text(fmtMoney(kpi.hf_base_total));

        // 卡片 4: 发薪总盘与个税
        $("#kpi-payroll-badge").text(`发薪: ${kpi.payroll_period_month || current_month} (在册 ${kpi.payroll_emp_count || 0}人)`);
        $("#kpi-total-net").text(fmtMoney(data.total_net_salary));
        $("#kpi-total-gross").text(fmtMoney(data.total_gross_salary));
        $("#kpi-total-tax").text(fmtMoney(data.total_tax));
        $("#kpi-total-person-ded").text(fmtMoney(kpi.total_person_deductions));

        const items = data.items || [];
        if (items.length === 0) {
            $("#tbody-qifu-payroll").html('<tr><td colspan="17" style="text-align:center; padding:30px; color:#94a3b8;">暂无当月核算数据，请点击上方【2. 外部实发导入与薪资发放表】上传车间实发表</td></tr>');
            return;
        }

        let html = '';
        items.forEach((it, idx) => {
            const jobTitle = it.job_title || '操作工';
            const empType = it.employee_type || '正式工';
            const attDays = it.attendance_days || 0;
            const workHours = it.work_hours || 0;
            const attStr = `${attDays}天 / ${workHours}h`;
            const workshopNet = (it.net_salary || 0) - (it.post_allowance || 0) - (it.house_rent_allowance || 0);

            html += `
            <tr>
                <td style="color:#94a3b8;">${idx + 1}</td>
                <td><strong>${it.employee_no || '-'}</strong></td>
                <td><strong style="color:#1e3a8a;">${it.employee_name}</strong></td>
                <td>${jobTitle}</td>
                <td><span class="qifu-status-badge ${empType === '正式工' ? 'qifu-status-locked' : 'qifu-status-draft'}">${empType}</span></td>
                <td>${attStr}</td>
                <td class="qifu-money-cell">${fmtMoney(workshopNet)}</td>
                <td class="qifu-money-cell" style="color:#b45309; font-weight:600;">${fmtMoney(it.post_allowance)}</td>
                <td class="qifu-money-cell" style="color:#b45309; font-weight:600;">${fmtMoney(it.house_rent_allowance)}</td>
                <td class="qifu-money-cell" style="color:#16a34a; font-weight:700; font-size:13px;">${fmtMoney(it.net_salary)}</td>
                <td class="qifu-money-cell" style="color:#2563eb; font-weight:700; font-size:13px;">${fmtMoney(it.gross_salary)}</td>
                <td class="qifu-money-cell" style="color:#d97706;">${fmtMoney(it.ss_person_total)}</td>
                <td class="qifu-money-cell" style="color:#d97706;">${fmtMoney(it.hf_person_total)}</td>
                <td class="qifu-money-cell" style="color:#dc2626; font-weight:600;">${fmtMoney(it.tax_amount)}</td>
                <td class="qifu-money-cell" style="color:#64748b;">${fmtMoney(it.ss_company_total)}</td>
                <td class="qifu-money-cell" style="color:#64748b;">${fmtMoney(it.hf_company_total)}</td>
                <td style="font-size:11.5px; color:#64748b; max-width:180px; overflow:hidden; text-overflow:ellipsis;" title="${it.remarks || ''}">${it.remarks || '-'}</td>
            </tr>
            `;
        });
        $("#tbody-qifu-payroll").html(html);
    }

    // ==========================================
    // 模态框与高级功能
    // ==========================================

    // 修改社保/公积金费率与基数配置弹窗
    function open_insurance_edit_dialog() {
        frappe.call({
            method: 'ashan_cn_procurement.services.employee_salary_service.get_insurance_setting',
            args: { company: COMPANY },
            callback: function(r) {
                if (!r.message) return;
                const ins = r.message.setting || {};
                cached_insurance_setting = ins;
                const year = current_month.split("-")[0] || 2026;

                const d = new frappe.ui.Dialog({
                    title: `⚙️ 修改【${COMPANY}】${year} 年度社保公积金与个税配置`,
                    size: 'large',
                    fields: [
                        { fieldtype: 'Section Break', label: '🏢 单位社保缴费比例 (%)' },
                        { fieldname: 'ss_company_pension', fieldtype: 'Percent', label: '单位基本养老 (%)', default: ins.ss_company_pension || 16.0, reqd: 1 },
                        { fieldname: 'ss_company_unemployment', fieldtype: 'Percent', label: '单位失业保险 (%)', default: ins.ss_company_unemployment || 0.5, reqd: 1 },
                        { fieldname: 'ss_company_medical', fieldtype: 'Percent', label: '单位基本医疗 (%)', default: ins.ss_company_medical || 10.0, reqd: 1 },
                        { fieldname: 'ss_company_other_medical', fieldtype: 'Percent', label: '单位其他医疗 (%)', default: ins.ss_company_other_medical || 0.5, reqd: 1 },
                        { fieldname: 'ss_company_injury', fieldtype: 'Percent', label: '单位工伤保险 (%)', default: ins.ss_company_injury || 0.55, reqd: 1 },

                        { fieldtype: 'Section Break', label: '👤 个人社保扣缴比例与救助金' },
                        { fieldname: 'ss_person_pension', fieldtype: 'Percent', label: '个人基本养老 (%)', default: ins.ss_person_pension || 8.0, reqd: 1 },
                        { fieldname: 'ss_person_unemployment', fieldtype: 'Percent', label: '个人失业保险 (%)', default: ins.ss_person_unemployment || 0.5, reqd: 1 },
                        { fieldname: 'ss_person_medical', fieldtype: 'Percent', label: '个人基本医疗 (%)', default: ins.ss_person_medical || 2.0, reqd: 1 },
                        { fieldname: 'big_medical_amount_default', fieldtype: 'Currency', label: '大额医疗基准金额 (元/月)', default: ins.big_medical_amount_default || 22.0, reqd: 1 },
                        { fieldname: 'big_medical_amount_special', fieldtype: 'Currency', label: '大额医疗特殊月份金额 (元/月)', default: ins.big_medical_amount_special || 21.0, reqd: 1 },
                        { fieldname: 'big_medical_special_months', fieldtype: 'Data', label: '特殊金额生效月份 (如: 3,12)', default: ins.big_medical_special_months || '3,12', reqd: 1 },

                        { fieldtype: 'Section Break', label: '🏠 住房公积金与基数起征点' },
                        { fieldname: 'hf_company_rate', fieldtype: 'Percent', label: '单位公积金比例 (%)', default: ins.hf_company_rate || 5.0, reqd: 1 },
                        { fieldname: 'hf_person_rate', fieldtype: 'Percent', label: '个人公积金比例 (%)', default: ins.hf_person_rate || 5.0, reqd: 1 },
                        { fieldname: 'ss_min_base', fieldtype: 'Currency', label: '社保最低缴费基数 (元)', default: ins.ss_min_base || 5013.0, reqd: 1 },
                        { fieldname: 'hf_min_base', fieldtype: 'Currency', label: '公积金最低缴费基数 (元)', default: ins.hf_min_base || 2320.0, reqd: 1 },
                        { fieldname: 'tax_threshold', fieldtype: 'Currency', label: '个税起征点 (元/月)', default: ins.tax_threshold || 5000.0, reqd: 1 }
                    ],
                    primary_action_label: '💾 保存配置并即时生效',
                    primary_action(values) {
                        frappe.call({
                            method: 'ashan_cn_procurement.services.employee_salary_service.save_insurance_setting',
                            args: {
                                company: COMPANY,
                                year: year,
                                data: JSON.stringify(values)
                            },
                            callback: function(res) {
                                if (res.message && res.message.success) {
                                    frappe.show_alert({ message: res.message.message, indicator: 'green' });
                                    d.hide();
                                    load_social_insurance_tab();
                                    load_housing_fund_tab();
                                    load_tax_settlement_tab();
                                    load_payroll_settlement();
                                }
                            }
                        });
                    }
                });
                d.show();
            }
        });
    }

    // 19 列双层表头社保明细弹窗
    function open_social_insurance_modal() {
        frappe.call({
            method: 'ashan_cn_procurement.services.payroll_settlement_service.get_social_insurance_sheet',
            args: { company: COMPANY, period_month: current_month },
            callback: function(r) {
                if (!r.message || !r.message.rows) return;
                const ins_data = r.message;
                const rows = ins_data.rows || [];
                const tot = ins_data.totals || {};

                let trs = '';
                rows.forEach(r => {
                    const isAdj = !!r.adj_id;
                    trs += `
                    <tr style="${isAdj ? 'background:#fffbeb;' : ''}">
                        <td style="text-align:center; color:#94a3b8;">${r.seq}</td>
                        <td style="text-align:center;"><strong>${r.employee_no}</strong></td>
                        <td>
                            <strong style="color:#2563eb;">${r.employee_name}</strong>
                            ${isAdj ? `<span class="qifu-status-badge qifu-status-draft" style="font-size:10px; margin-left:4px;">${r.biz_type}</span> <a href="javascript:void(0)" class="btn-del-ss-adj" data-id="${r.adj_id}" style="color:#dc2626; font-size:11px; margin-left:4px;" title="删除此补缴/调整项">🗑️</a>` : ''}
                        </td>
                        <td style="text-align:center; font-family:monospace;">${r.id_card || '-'}</td>
                        <td style="text-align:center; font-weight:${isAdj ? '700; color:#b45309;' : 'normal;'}">${r.period_month_str}</td>
                        <td style="text-align:center;">${r.employee_type}</td>
                        <td class="qifu-money-cell" style="font-weight:600;">${fmtMoney(r.ss_base)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.comp_pension)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.comp_unemp)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.comp_med)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.comp_other_med)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.comp_injury)}</td>
                        <td class="qifu-money-cell" style="color:#1e40af; font-weight:700;">${fmtMoney(r.comp_total)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.pers_pension)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.pers_unemp)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.pers_med)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.pers_large_med)}</td>
                        <td class="qifu-money-cell" style="color:#166534; font-weight:700;">${fmtMoney(r.pers_total)}</td>
                        <td class="qifu-money-cell" style="color:#c2410c; font-weight:800; font-size:13px;">
                            ${fmtMoney(r.grand_total)}
                            ${r.late_fee > 0 ? `<div style="font-size:10px; color:#dc2626; font-weight:normal;">(含滞纳金 ${fmtMoney(r.late_fee)})</div>` : ''}
                        </td>
                    </tr>
                    `;
                });

                const modal_html = `
                <div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                    <div>
                        <span style="font-size:14px; font-weight:700; color:#4338ca;">【${COMPANY}】${ins_data.report_title || `${current_month} 社会保险缴费明细表`}</span>
                        <span class="qifu-status-badge qifu-status-locked" style="margin-left:8px;">19列双层表头 · 缴纳期: ${ins_data.payment_month_name || ''} · 所属期: ${ins_data.rows[0] ? ins_data.rows[0].period_month_str : ''} · 参保 ${rows.length} 笔</span>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-default btn-xs" id="btn-modal-add-ss-adj" style="color:#b45309; border-color:#fde68a; background:#fef3c7; font-weight:600;">➕ 登记特殊补缴/滞纳金</button>
                        <button class="btn btn-primary btn-xs" id="btn-modal-export-ins" style="background:#059669; border-color:#059669; font-weight:600;">📥 导出此表为 Excel</button>
                        <button class="btn btn-default btn-xs" id="btn-modal-print-ins" style="font-weight:600;">🖨️ 打印/导出 PDF</button>
                    </div>
                </div>
                <div class="qifu-modal-table-scroll">
                    <table class="qifu-table table-bordered" id="table-modal-ins-sheet" style="font-size:11.5px; margin-bottom:0; min-width:1600px;">
                        <thead style="position:sticky; top:0; background:#f8fafc; z-index:1;">
                            <tr style="background:#f1f5f9; text-align:center; font-weight:700;">
                                <th colspan="7" style="background:#e0e7ff; color:#3730a3;">员工基本信息</th>
                                <th colspan="6" style="background:#dbeafe; color:#1e40af;">单位缴纳</th>
                                <th colspan="5" style="background:#dcfce7; color:#166534;">个人缴纳</th>
                                <th style="background:#ffedd5; color:#9a3412;">总合计</th>
                            </tr>
                            <tr>
                                <th style="width:36px;">序号</th>
                                <th>工号</th>
                                <th>姓名</th>
                                <th>证件号码</th>
                                <th>本期所属期</th>
                                <th>员工类型</th>
                                <th>社保_基数</th>
                                <th>单位养老</th>
                                <th>单位失业</th>
                                <th>单位医疗</th>
                                <th>单位其他医疗</th>
                                <th>单位工伤</th>
                                <th style="background:#eff6ff;">单位缴纳合计</th>
                                <th>个人养老</th>
                                <th>个人失业</th>
                                <th>个人医疗</th>
                                <th>个人大额医疗</th>
                                <th style="background:#f0fdf4;">个人缴纳合计</th>
                                <th style="background:#fff7ed;">总合计</th>
                            </tr>
                        </thead>
                        <tbody>${trs}</tbody>
                        <tfoot style="background:#f8fafc; font-weight:700;">
                            <tr>
                                <td colspan="5" style="text-align:center; color:#334155;">合计</td>
                                <td style="text-align:center;">0</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.ss_base)}</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.comp_pension)}</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.comp_unemp)}</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.comp_med)}</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.comp_other_med)}</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.comp_injury)}</td>
                                <td class="qifu-money-cell" style="color:#1e40af;">${fmtMoney(tot.comp_total)}</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.pers_pension)}</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.pers_unemp)}</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.pers_med)}</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.pers_large_med)}</td>
                                <td class="qifu-money-cell" style="color:#166534;">${fmtMoney(tot.pers_total)}</td>
                                <td class="qifu-money-cell" style="color:#c2410c; font-size:13px;">${fmtMoney(tot.grand_total)}</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
                `;

                const ins_dialog = new frappe.ui.Dialog({
                    title: `🛡️ 祺富 · ${ins_data.report_title || '社会保险缴费明细表'}`,
                    size: 'extra-large',
                    fields: [{ fieldtype: 'HTML', fieldname: 'ins_content', options: modal_html }],
                    primary_action_label: '关闭',
                    primary_action() { ins_dialog.hide(); }
                });
                ins_dialog.show();
            }
        });
    }

    // 12 列双层表头公积金明细弹窗
    function open_housing_fund_modal() {
        frappe.call({
            method: 'ashan_cn_procurement.services.payroll_settlement_service.get_housing_fund_sheet',
            args: { company: COMPANY, period_month: current_month },
            callback: function(r) {
                if (!r.message || !r.message.rows) return;
                const hf_data = r.message;
                const rows = hf_data.rows || [];
                const tot = hf_data.totals || {};

                let trs = '';
                rows.forEach(r => {
                    trs += `
                    <tr>
                        <td style="text-align:center; color:#94a3b8;">${r.seq}</td>
                        <td style="text-align:center;"><strong>${r.employee_no}</strong></td>
                        <td><strong style="color:#2563eb;">${r.employee_name}</strong></td>
                        <td style="text-align:center; font-family:monospace;">${r.id_card || '-'}</td>
                        <td style="text-align:center;">${r.period_month_str}</td>
                        <td style="text-align:center;">${r.employee_type}</td>
                        <td class="qifu-money-cell" style="font-weight:600;">${fmtMoney(r.hf_base)}</td>
                        <td style="text-align:center;">${r.comp_rate}%</td>
                        <td class="qifu-money-cell" style="color:#0369a1; font-weight:600;">${fmtMoney(r.comp_amount)}</td>
                        <td style="text-align:center;">${r.pers_rate}%</td>
                        <td class="qifu-money-cell" style="color:#15803d; font-weight:600;">${fmtMoney(r.pers_amount)}</td>
                        <td class="qifu-money-cell" style="color:#c2410c; font-weight:800; font-size:13px;">${fmtMoney(r.total_amount)}</td>
                    </tr>
                    `;
                });

                const modal_html = `
                <div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-size:14px; font-weight:700; color:#0f766e;">【${COMPANY}】${hf_data.report_title || `${current_month} 住房公积金缴存明细表`}</span>
                        <span class="qifu-status-badge qifu-status-locked" style="margin-left:8px;">12列标准版 · 缴纳期: ${hf_data.payment_month_name || ''} · 所属期: ${hf_data.rows[0] ? hf_data.rows[0].period_month_str : ''} · 参保 ${rows.length} 人</span>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-primary btn-xs" id="btn-modal-export-hf" style="background:#059669; border-color:#059669; font-weight:600;">📥 导出此表为 Excel</button>
                        <button class="btn btn-default btn-xs" id="btn-modal-print-hf" style="font-weight:600;">🖨️ 打印/导出 PDF</button>
                    </div>
                </div>
                <div class="qifu-modal-table-scroll">
                    <table class="qifu-table table-bordered" id="table-modal-hf-sheet" style="font-size:11.5px; margin-bottom:0;">
                        <thead style="position:sticky; top:0; background:#f8fafc; z-index:1;">
                            <tr style="background:#f1f5f9; text-align:center; font-weight:700;">
                                <th colspan="6" style="background:#ccfbf1; color:#0f766e;">员工基本信息</th>
                                <th colspan="3" style="background:#e0f2fe; color:#0369a1;">单位缴存 (5%)</th>
                                <th colspan="2" style="background:#dcfce7; color:#15803d;">个人缴存 (5%)</th>
                                <th style="background:#ffedd5; color:#9a3412;">月缴存总额</th>
                            </tr>
                            <tr>
                                <th style="width:36px;">序号</th>
                                <th>工号</th>
                                <th>姓名</th>
                                <th>证件号码</th>
                                <th>本期所属期</th>
                                <th>员工类型</th>
                                <th>公积金_基数</th>
                                <th>单位缴存比例</th>
                                <th style="background:#f0f9ff;">单位缴存金额</th>
                                <th>个人缴存比例</th>
                                <th style="background:#f0fdf4;">个人缴存金额</th>
                                <th style="background:#fff7ed;">月缴存总额</th>
                            </tr>
                        </thead>
                        <tbody>${trs}</tbody>
                        <tfoot style="background:#f8fafc; font-weight:700;">
                            <tr>
                                <td colspan="5" style="text-align:center; color:#334155;">合计</td>
                                <td style="text-align:center;">0</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.hf_base)}</td>
                                <td style="text-align:center;">5%</td>
                                <td class="qifu-money-cell" style="color:#0369a1;">${fmtMoney(tot.comp_amount)}</td>
                                <td style="text-align:center;">5%</td>
                                <td class="qifu-money-cell" style="color:#15803d;">${fmtMoney(tot.pers_amount)}</td>
                                <td class="qifu-money-cell" style="color:#c2410c; font-size:13px;">${fmtMoney(tot.total_amount)}</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
                `;

                const hf_dialog = new frappe.ui.Dialog({
                    title: `🏛️ 祺富 · ${hf_data.report_title || '住房公积金缴存明细表'}`,
                    size: 'extra-large',
                    fields: [{ fieldtype: 'HTML', fieldname: 'hf_content', options: modal_html }],
                    primary_action_label: '关闭',
                    primary_action() { hf_dialog.hide(); }
                });
                hf_dialog.show();
            }
        });
    }

    // 15 列个人所得税明细弹窗
    function open_tax_modal() {
        frappe.call({
            method: 'ashan_cn_procurement.services.payroll_settlement_service.get_tax_settlement_sheet',
            args: { company: COMPANY, period_month: current_month },
            callback: function(r) {
                if (!r.message || !r.message.rows) return;
                const tax_data = r.message;
                const rows = tax_data.rows || [];
                const tot = tax_data.totals || {};

                let trs = '';
                rows.forEach(r => {
                    const hasTax = r.tax_amount > 0;
                    trs += `
                    <tr>
                        <td style="text-align:center; color:#94a3b8;">${r.seq}</td>
                        <td style="text-align:center;"><strong>${r.employee_no}</strong></td>
                        <td><strong style="color:#1e3a8a;">${r.employee_name}</strong></td>
                        <td style="text-align:center; font-family:monospace;">${r.id_card || '-'}</td>
                        <td style="text-align:center;">${r.employee_type}</td>
                        <td style="text-align:center;">${r.period_month_str}</td>
                        <td class="qifu-money-cell" style="color:#2563eb; font-weight:700;">${fmtMoney(r.gross_salary)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.tax_threshold)}</td>
                        <td class="qifu-money-cell" style="color:#d97706;">${fmtMoney(r.ss_person_total)}</td>
                        <td class="qifu-money-cell" style="color:#d97706;">${fmtMoney(r.hf_person_total)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.special_deductions_total)}</td>
                        <td class="qifu-money-cell" style="font-weight:600; color:#b45309;">${fmtMoney(r.taxable_income)}</td>
                        <td style="text-align:center; font-weight:600;">${r.tax_rate}%</td>
                        <td class="qifu-money-cell">${fmtMoney(r.quick_deduction)}</td>
                        <td class="qifu-money-cell" style="color:${hasTax ? '#dc2626' : '#15803d'}; font-weight:800; font-size:13px;">${fmtMoney(r.tax_amount)}</td>
                    </tr>
                    `;
                });

                const modal_html = `
                <div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-size:14px; font-weight:700; color:#b45309;">【${COMPANY}】${tax_data.report_title || `${current_month} 个人所得税核定明细表`}</span>
                        <span class="qifu-status-badge qifu-status-locked" style="margin-left:8px;">15列标准预扣预缴 · 纳税人数: ${rows.length} 人</span>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-primary btn-xs" id="btn-modal-export-tax" style="background:#059669; border-color:#059669; font-weight:600;">📥 导出此表为 Excel</button>
                        <button class="btn btn-default btn-xs" id="btn-modal-print-tax" style="font-weight:600;">🖨️ 打印/导出 PDF</button>
                    </div>
                </div>
                <div class="qifu-modal-table-scroll">
                    <table class="qifu-table table-bordered" id="table-modal-tax-sheet" style="font-size:11.5px; margin-bottom:0; min-width:1600px;">
                        <thead style="position:sticky; top:0; background:#f8fafc; z-index:1;">
                            <tr>
                                <th style="width:36px;">序号</th>
                                <th>工号</th>
                                <th>姓名</th>
                                <th>证件号码</th>
                                <th>用工性质</th>
                                <th>发薪月份</th>
                                <th style="background:#eff6ff;">本期税前收入</th>
                                <th>基本减除费用</th>
                                <th>社保个人扣缴</th>
                                <th>公积金个人扣缴</th>
                                <th>专项附加扣除</th>
                                <th style="background:#fef3c7; color:#92400e;">应纳税所得额</th>
                                <th style="text-align:center;">适用税率</th>
                                <th>速算扣除数</th>
                                <th style="background:#fee2e2; color:#b91c1c; font-weight:800;">本月应预扣税额</th>
                            </tr>
                        </thead>
                        <tbody>${trs}</tbody>
                        <tfoot style="background:#f8fafc; font-weight:700;">
                            <tr>
                                <td colspan="6" style="text-align:center; color:#334155;">合计</td>
                                <td class="qifu-money-cell" style="color:#2563eb;">${fmtMoney(tot.gross_salary)}</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.tax_threshold)}</td>
                                <td class="qifu-money-cell" style="color:#d97706;">${fmtMoney(tot.ss_person_total)}</td>
                                <td class="qifu-money-cell" style="color:#d97706;">${fmtMoney(tot.hf_person_total)}</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.special_deductions_total)}</td>
                                <td class="qifu-money-cell" style="color:#b45309;">${fmtMoney(tot.taxable_income)}</td>
                                <td style="text-align:center;">-</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.quick_deduction)}</td>
                                <td class="qifu-money-cell" style="color:#dc2626; font-size:13px;">${fmtMoney(tot.tax_amount)}</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
                `;

                const tax_dialog = new frappe.ui.Dialog({
                    title: `⚖️ 祺富 · ${tax_data.report_title || '个人所得税核定明细表'}`,
                    size: 'extra-large',
                    fields: [{ fieldtype: 'HTML', fieldname: 'tax_content', options: modal_html }],
                    primary_action_label: '关闭',
                    primary_action() { tax_dialog.hide(); }
                });
                tax_dialog.show();
            }
        });
    }

    // 新增/编辑员工档案弹窗
    function open_emp_dialog(emp_data) {
        const isEdit = !!emp_data;
        const d = new frappe.ui.Dialog({
            title: isEdit ? `✏️ 修改员工薪酬档案 · ${emp_data.employee_name}` : '➕ 新增祺富员工档案',
            size: 'large',
            fields: [
                { fieldtype: 'Section Break', label: '基本身份信息' },
                { fieldtype: 'Data', fieldname: 'employee_no', label: '工号', reqd: 1, default: emp_data ? emp_data.employee_no : '' },
                { fieldtype: 'Data', fieldname: 'employee_name', label: '员工姓名', reqd: 1, default: emp_data ? emp_data.employee_name : '' },
                { fieldtype: 'Column Break' },
                { fieldtype: 'Data', fieldname: 'id_card', label: '身份证号码', default: emp_data ? emp_data.id_card : '' },
                { fieldtype: 'Select', fieldname: 'employee_type', label: '用工性质', options: ['正式工', '退休返聘', '临时工', '外籍工', '劳务派遣'], default: emp_data ? emp_data.employee_type : '正式工' },
                { fieldtype: 'Data', fieldname: 'job_title', label: '岗位职务', default: emp_data ? emp_data.job_title : '操作工' },

                { fieldtype: 'Section Break', label: '薪资与津贴设定' },
                { fieldtype: 'Select', fieldname: 'salary_mode', label: '计薪方式', options: ['固定一口价', '出勤+加班+达标率(车间实发)', '固定月薪+补贴'], default: emp_data ? emp_data.salary_mode : '固定一口价' },
                { fieldtype: 'Currency', fieldname: 'fixed_salary', label: '固定/车间薪资基准 (元)', default: emp_data ? emp_data.fixed_salary : 0 },
                { fieldtype: 'Column Break' },
                { fieldtype: 'Currency', fieldname: 'post_allowance', label: '职位补贴 (元/月)', default: emp_data ? emp_data.post_allowance : 0 },
                { fieldtype: 'Currency', fieldname: 'house_rent_allowance', label: '租房/车补 (元/月)', default: emp_data ? emp_data.house_rent_allowance : 0 },

                { fieldtype: 'Section Break', label: '五险一金与专项扣除' },
                { fieldtype: 'Currency', fieldname: 'social_security_base', label: '社保缴费基数 (元)', default: emp_data ? emp_data.social_security_base : 5124 },
                { fieldtype: 'Currency', fieldname: 'housing_fund_base', label: '公积金基数 (元)', default: emp_data ? emp_data.housing_fund_base : 2320 },
                { fieldtype: 'Column Break' },
                { fieldtype: 'Currency', fieldname: 'special_deductions_total', label: '个税专项附加扣除 (元/月)', default: emp_data ? emp_data.special_deductions_total : 0 },
                { fieldtype: 'Small Text', fieldname: 'remarks', label: '备注说明', default: emp_data ? emp_data.remarks : '' }
            ],
            primary_action_label: isEdit ? '保存修改' : '立即创建',
            primary_action(vals) {
                vals.company = COMPANY;
                if (isEdit) vals.name = emp_data.name;
                frappe.call({
                    method: isEdit ? 'ashan_cn_procurement.services.employee_salary_service.update_employee_salary_profile' : 'ashan_cn_procurement.services.employee_salary_service.create_employee_salary_profile',
                    args: vals,
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.show_alert({ message: r.message.message, indicator: 'green' });
                            d.hide();
                            load_qifu_employees();
                            load_social_insurance_tab();
                            load_housing_fund_tab();
                            load_tax_settlement_tab();
                            load_payroll_settlement();
                        }
                    }
                });
            }
        });
        d.show();
    }

    function get_last_day_of_month(ym) {
        if (!ym || !ym.includes('-')) return '';
        const parts = ym.split('-');
        const y = parseInt(parts[0], 10);
        const m = parseInt(parts[1], 10);
        const d = new Date(y, m, 0).getDate();
        return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    }

    // 办理单人离职弹窗
    function open_resign_dialog(emp_no, emp_name) {
        const default_date = get_last_day_of_month(current_month);
        const d = new frappe.ui.Dialog({
            title: `🚪 办理员工离职 · ${emp_name}`,
            size: 'small',
            fields: [
                { fieldtype: 'Data', fieldname: 'employee_no', label: '工号', default: emp_no, read_only: 1 },
                { fieldtype: 'Data', fieldname: 'employee_name', label: '员工姓名', default: emp_name, read_only: 1 },
                {
                    fieldtype: 'Date',
                    fieldname: 'relieving_date',
                    label: '离职日期',
                    reqd: 1,
                    default: default_date,
                    description: `默认当月最后一天 (${default_date})`
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'resignation_reason',
                    label: '离职原因',
                    options: ['正常离职', '合同到期', '个人原因', '协商解除', '退休', '其他'],
                    default: '正常离职'
                },
                {
                    fieldtype: 'HTML',
                    fieldname: 'rule_tip',
                    options: `
                    <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:6px; padding:8px 10px; font-size:12px; line-height:1.5; color:#1e40af; margin-top:8px;">
                        💡 <strong>财务减员联动规则</strong>：<br>
                        员工在【<strong>${current_month}</strong>】离职后，系统仍会核算其当月在职薪酬与个税；对应次月的社保与公积金将<strong>自动停止缴纳（自动减员）</strong>。
                    </div>
                    `
                }
            ],
            primary_action_label: '确认办理离职',
            primary_action(vals) {
                frappe.call({
                    method: 'ashan_cn_procurement.services.employee_salary_service.set_employee_resignation',
                    args: {
                        employee_no: vals.employee_no,
                        relieving_date: vals.relieving_date,
                        resignation_reason: vals.resignation_reason,
                        company: COMPANY,
                        period_month: current_month
                    },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.show_alert({ message: r.message.message, indicator: 'green' });
                            d.hide();
                            load_monthly_workflow_hub();
                            load_qifu_employees();
                            load_social_insurance_tab();
                            load_housing_fund_tab();
                        }
                    }
                });
            }
        });
        d.show();
    }

    // 批量办理员工离职弹窗
    function open_batch_resign_dialog(selected_emps) {
        if (!selected_emps || selected_emps.length === 0) {
            frappe.msgprint({ title: '提示', indicator: 'orange', message: '请先在员工列表中勾选需要办理离职的人员！' });
            return;
        }
        const default_date = get_last_day_of_month(current_month);
        const emp_names_str = selected_emps.map(e => `${e.name} (${e.no})`).join('、');
        const emp_nos = selected_emps.map(e => e.no);

        const d = new frappe.ui.Dialog({
            title: `🚪 批量办理员工离职 (共 ${selected_emps.length} 人)`,
            size: 'small',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'selected_list',
                    options: `
                    <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:8px 10px; font-size:12px; line-height:1.6; max-height:120px; overflow-y:auto; margin-bottom:10px;">
                        <strong>已选员工 (${selected_emps.length} 人)</strong>：<br>
                        <span style="color:#2563eb;">${emp_names_str}</span>
                    </div>
                    `
                },
                {
                    fieldtype: 'Date',
                    fieldname: 'relieving_date',
                    label: '统一离职日期',
                    reqd: 1,
                    default: default_date,
                    description: `默认当月最后一天 (${default_date})`
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'resignation_reason',
                    label: '离职原因',
                    options: ['正常离职', '合同到期', '个人原因', '协商解除', '退休', '其他'],
                    default: '正常离职'
                },
                {
                    fieldtype: 'HTML',
                    fieldname: 'rule_tip',
                    options: `
                    <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:6px; padding:8px 10px; font-size:12px; line-height:1.5; color:#1e40af; margin-top:8px;">
                        💡 <strong>财务减员联动规则</strong>：<br>
                        批量离职成功后，上述 ${selected_emps.length} 位员工下月对应的社保与公积金将<strong>一键自动减员</strong>！
                    </div>
                    `
                }
            ],
            primary_action_label: `确认批量离职 (${selected_emps.length}人)`,
            primary_action(vals) {
                frappe.call({
                    method: 'ashan_cn_procurement.services.employee_salary_service.batch_set_employee_resignation',
                    args: {
                        employee_nos: JSON.stringify(emp_nos),
                        relieving_date: vals.relieving_date,
                        resignation_reason: vals.resignation_reason,
                        company: COMPANY,
                        period_month: current_month
                    },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint({ title: '✅ 批量离职成功', indicator: 'green', message: r.message.message });
                            d.hide();
                            load_monthly_workflow_hub();
                            load_qifu_employees();
                            load_social_insurance_tab();
                            load_housing_fund_tab();
                        }
                    }
                });
            }
        });
        d.show();
    }

    // 查看薪资发放表 (24列整合版模态框)
    function open_salary_distribution_modal() {
        frappe.call({
            method: 'ashan_cn_procurement.services.payroll_settlement_service.get_salary_distribution_sheet',
            args: { company: COMPANY, period_month: current_month },
            callback: function(r) {
                if (!r.message || !r.message.rows) return;
                const dist_data = r.message;
                const rows = dist_data.rows || [];
                const tot = dist_data.totals || {};

                let trs = '';
                rows.forEach(r => {
                    trs += `
                    <tr>
                        <td style="text-align:center; color:#94a3b8;">${r.seq}</td>
                        <td style="text-align:center;"><strong>${r.employee_no}</strong></td>
                        <td><strong style="color:#1e3a8a;">${r.employee_name}</strong></td>
                        <td class="qifu-money-cell">${r.attendance_days || 0}</td>
                        <td class="qifu-money-cell">${r.work_hours || 0}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.day_salary)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.hour_salary)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.full_attendance)}</td>
                        <td class="qifu-money-cell">${r.overtime_hours || 0}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.overtime_salary)}</td>
                        <td class="qifu-money-cell">${r.national_days || 0}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.national_salary)}</td>
                        <td style="text-align:center;">${r.target_rate || '-'}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.target_salary)}</td>
                        <td class="qifu-money-cell" style="color:#dc2626;">${fmtMoney(r.deduction)}</td>
                        <td class="qifu-money-cell" style="font-weight:600;">${fmtMoney(r.workshop_subtotal)}</td>
                        <td class="qifu-money-cell" style="color:#b45309; font-weight:600;">${fmtMoney(r.post_allowance)}</td>
                        <td class="qifu-money-cell" style="color:#b45309; font-weight:600;">${fmtMoney(r.house_rent_allowance)}</td>
                        <td class="qifu-money-cell" style="color:#b45309; font-weight:700;">${fmtMoney(r.allowance_subtotal)}</td>
                        <td class="qifu-money-cell" style="color:#2563eb; font-weight:700;">${fmtMoney(r.payable_salary)}</td>
                        <td class="qifu-money-cell">${fmtMoney(r.salary_adjustment)}</td>
                        <td class="qifu-money-cell" style="color:#16a34a; font-weight:800; font-size:13px;">${fmtMoney(r.net_salary)}</td>
                        <td style="text-align:center; color:#cbd5e1;">${r.sign || ''}</td>
                        <td style="font-size:11px; color:#64748b;">${r.remarks || ''}</td>
                    </tr>
                    `;
                });

                const modal_html = `
                <div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-size:14px; font-weight:700; color:#1e3a8a;">【${COMPANY}】${current_month} 薪资发放表</span>
                        <span class="qifu-status-badge qifu-status-locked" style="margin-left:8px;">24列标准整合版 · 包含职位/房补行内整合</span>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-primary btn-xs" id="btn-modal-export-dist" style="background:#059669; border-color:#059669; font-weight:600;">📥 导出此表为 Excel</button>
                        <button class="btn btn-default btn-xs" id="btn-modal-print-dist" style="font-weight:600;">🖨️ 打印/导出 PDF</button>
                    </div>
                </div>
                <div class="qifu-modal-table-scroll">
                    <table class="qifu-table table-bordered" id="table-modal-dist-sheet" style="font-size:11.5px; margin-bottom:0; min-width:1800px;">
                        <thead style="position:sticky; top:0; background:#f8fafc; z-index:1;">
                            <tr>
                                <th style="width:36px;">序号</th>
                                <th>工号</th>
                                <th>姓名</th>
                                <th>作业天数</th>
                                <th>作业小时</th>
                                <th>天工资</th>
                                <th>小时工资</th>
                                <th>全勤费</th>
                                <th>加班小时</th>
                                <th>加班费</th>
                                <th>国勤天数</th>
                                <th>国勤工资</th>
                                <th>达标率</th>
                                <th>达标工资</th>
                                <th>扣除</th>
                                <th style="background:#eff6ff;">考勤绩效工资合计</th>
                                <th style="background:#fef3c7;">职位补贴</th>
                                <th style="background:#fef3c7;">房/车补</th>
                                <th style="background:#fef3c7;">补贴工资合计</th>
                                <th style="background:#dbeafe; color:#1e40af;">应发工资合计</th>
                                <th>工资调整</th>
                                <th style="background:#dcfce7; color:#166534;">实发工资合计</th>
                                <th>签字</th>
                                <th>备考</th>
                            </tr>
                        </thead>
                        <tbody>${trs}</tbody>
                        <tfoot style="background:#f8fafc; font-weight:700;">
                            <tr>
                                <td colspan="3" style="text-align:center;">合计</td>
                                <td class="qifu-money-cell">${tot.attendance_days || 0}</td>
                                <td class="qifu-money-cell">${tot.work_hours || 0}</td>
                                <td>-</td><td>-</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.full_attendance)}</td>
                                <td class="qifu-money-cell">${tot.overtime_hours || 0}</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.overtime_salary)}</td>
                                <td class="qifu-money-cell">${tot.national_days || 0}</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.national_salary)}</td>
                                <td>-</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.target_salary)}</td>
                                <td class="qifu-money-cell" style="color:#dc2626;">${fmtMoney(tot.deduction)}</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.workshop_subtotal)}</td>
                                <td class="qifu-money-cell" style="color:#b45309;">${fmtMoney(tot.post_allowance)}</td>
                                <td class="qifu-money-cell" style="color:#b45309;">${fmtMoney(tot.house_rent_allowance)}</td>
                                <td class="qifu-money-cell" style="color:#b45309;">${fmtMoney(tot.allowance_subtotal)}</td>
                                <td class="qifu-money-cell" style="color:#2563eb;">${fmtMoney(tot.payable_salary)}</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.salary_adjustment)}</td>
                                <td class="qifu-money-cell" style="color:#16a34a; font-size:13px;">${fmtMoney(tot.net_salary)}</td>
                                <td>-</td><td>-</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
                `;

                const dist_dialog = new frappe.ui.Dialog({
                    title: `📋 祺富 · ${current_month} 薪资发放表 (24列整合版)`,
                    size: 'extra-large',
                    fields: [{ fieldtype: 'HTML', fieldname: 'dist_content', options: modal_html }],
                    primary_action_label: '关闭',
                    primary_action() { dist_dialog.hide(); }
                });
                dist_dialog.show();
            }
        });
    }

    // 查看记账工资表 (11列财务版模态框)
    function open_accounting_sheet_modal() {
        frappe.call({
            method: 'ashan_cn_procurement.services.payroll_settlement_service.get_accounting_payroll_sheet',
            args: { company: COMPANY, period_month: current_month },
            callback: function(r) {
                if (!r.message || !r.message.rows) return;
                const acc_data = r.message;
                const rows = acc_data.rows || [];
                const tot = acc_data.totals || {};

                let trs = '';
                rows.forEach(r => {
                    trs += `
                    <tr>
                        <td style="text-align:center; color:#94a3b8;">${r.seq}</td>
                        <td style="text-align:center;"><strong>${r.employee_no}</strong></td>
                        <td><strong style="color:#1e3a8a;">${r.employee_name}</strong></td>
                        <td class="qifu-money-cell">${fmtMoney(r.base_performance_salary)}</td>
                        <td class="qifu-money-cell" style="color:#b45309;">${fmtMoney(r.post_allowance)}</td>
                        <td class="qifu-money-cell" style="color:#b45309;">${fmtMoney(r.house_rent_allowance)}</td>
                        <td class="qifu-money-cell" style="color:#2563eb; font-weight:700;">${fmtMoney(r.gross_salary)}</td>
                        <td class="qifu-money-cell" style="color:#d97706;">${fmtMoney(r.hf_person_total)}</td>
                        <td class="qifu-money-cell" style="color:#d97706;">${fmtMoney(r.ss_person_total)}</td>
                        <td class="qifu-money-cell" style="color:#dc2626;">${fmtMoney(r.tax_amount)}</td>
                        <td class="qifu-money-cell" style="color:#d97706; font-weight:600;">${fmtMoney(r.total_deduction)}</td>
                        <td class="qifu-money-cell" style="color:#16a34a; font-weight:800; font-size:13px;">${fmtMoney(r.net_salary)}</td>
                    </tr>
                    `;
                });

                const modal_html = `
                <div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-size:14px; font-weight:700; color:#15803d;">【${COMPANY}】${current_month} 记账工资表</span>
                        <span class="qifu-status-badge qifu-status-locked" style="margin-left:8px;">11列财务标准版 · 基本绩效/补贴/税前/险金/个税/税后</span>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-primary btn-xs" id="btn-modal-export-acc" style="background:#059669; border-color:#059669; font-weight:600;">📥 导出此表为 Excel</button>
                        <button class="btn btn-default btn-xs" id="btn-modal-print-acc" style="font-weight:600;">🖨️ 打印/导出 PDF</button>
                    </div>
                </div>
                <div class="qifu-modal-table-scroll">
                    <table class="qifu-table table-bordered" id="table-modal-acc-sheet" style="font-size:12px; margin-bottom:0; min-width:1200px;">
                        <thead style="position:sticky; top:0; background:#f8fafc; z-index:1;">
                            <tr>
                                <th style="width:36px;">序号</th>
                                <th>工号</th>
                                <th>姓名</th>
                                <th>基本绩效工资</th>
                                <th style="background:#fef3c7;">职位补贴</th>
                                <th style="background:#fef3c7;">房/车补</th>
                                <th style="background:#dbeafe; color:#1e40af;">税前工资</th>
                                <th>公积金</th>
                                <th>社保</th>
                                <th>应补/退税额</th>
                                <th style="background:#fef2f2;">合计扣除</th>
                                <th style="background:#dcfce7; color:#166534;">税后工资合计</th>
                            </tr>
                        </thead>
                        <tbody>${trs}</tbody>
                        <tfoot style="background:#f8fafc; font-weight:700;">
                            <tr>
                                <td colspan="3" style="text-align:center;">合计</td>
                                <td class="qifu-money-cell">${fmtMoney(tot.base_performance_salary)}</td>
                                <td class="qifu-money-cell" style="color:#b45309;">${fmtMoney(tot.post_allowance)}</td>
                                <td class="qifu-money-cell" style="color:#b45309;">${fmtMoney(tot.house_rent_allowance)}</td>
                                <td class="qifu-money-cell" style="color:#2563eb;">${fmtMoney(tot.gross_salary)}</td>
                                <td class="qifu-money-cell" style="color:#d97706;">${fmtMoney(tot.hf_person_total)}</td>
                                <td class="qifu-money-cell" style="color:#d97706;">${fmtMoney(tot.ss_person_total)}</td>
                                <td class="qifu-money-cell" style="color:#dc2626;">${fmtMoney(tot.tax_amount)}</td>
                                <td class="qifu-money-cell" style="color:#d97706;">${fmtMoney(tot.total_deduction)}</td>
                                <td class="qifu-money-cell" style="color:#16a34a; font-size:14px;">${fmtMoney(tot.net_salary)}</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
                `;

                const acc_dialog = new frappe.ui.Dialog({
                    title: `📑 祺富 · ${current_month} 记账工资表 (11列财务版)`,
                    size: 'extra-large',
                    fields: [{ fieldtype: 'HTML', fieldname: 'acc_content', options: modal_html }],
                    primary_action_label: '关闭',
                    primary_action() { acc_dialog.hide(); }
                });
                acc_dialog.show();
            }
        });
    }

    // 登记特殊补缴 / 滞纳金弹窗
    function open_add_insurance_adjustment_dialog() {
        frappe.call({
            method: 'ashan_cn_procurement.services.employee_salary_service.get_qifu_employees',
            callback: function(res) {
                const emp_list = res.message || [];
                const emp_options = emp_list.map(e => ({ label: `${e.employee_no} - ${e.employee_name} (${e.employee_type || '正式工'})`, value: e.employee_no }));

                const d = new frappe.ui.Dialog({
                    title: '➕ 登记社保特殊补缴 / 滞纳金 / 调基差额',
                    fields: [
                        { fieldtype: 'Select', fieldname: 'employee_no', label: '选择员工', options: emp_options, reqd: 1 },
                        { fieldtype: 'Data', fieldname: 'period_month_str', label: '补缴/调整所属期 (如 202605 或 202606)', reqd: 1, default: current_month.replace('-', '') },
                        { fieldtype: 'Select', fieldname: 'biz_type', label: '业务类型', options: ['历史补缴', '滞纳金/利息', '调基差额补退', '特殊补助'], default: '历史补缴', reqd: 1 },
                        { fieldtype: 'Currency', fieldname: 'ss_base', label: '补缴社保基数 (元，录入后自动按费率折算)', default: 5124.0 },
                        { fieldtype: 'Currency', fieldname: 'late_fee', label: '产生滞纳金/利息金额 (元)', default: 0.0 },
                        { fieldtype: 'Small Text', fieldname: 'remarks', label: '备注说明 (如: 补缴5月社保，税局收取滞纳金50元)' }
                    ],
                    primary_action_label: '保存并加入社保台账',
                    primary_action(vals) {
                        frappe.call({
                            method: 'ashan_cn_procurement.services.payroll_settlement_service.save_social_insurance_adjustment',
                            args: {
                                company: COMPANY,
                                period_month: current_month,
                                adjustment_json: JSON.stringify(vals)
                            },
                            callback: function(r) {
                                if (r.message && r.message.success) {
                                    frappe.show_alert({ message: r.message.message, indicator: 'green' });
                                    d.hide();
                                    load_social_insurance_tab();
                                    load_payroll_settlement();
                                }
                            }
                        });
                    }
                });
                d.show();
            }
        });
    }

    // Excel 导出 (支持 all / distribution / accounting / insurance / housing_fund / tax)
    function export_excel_action(sheet_type) {
        frappe.show_alert({ message: '⏳ 正在生成 Excel 报表，请稍候...', indicator: 'blue' });
        frappe.call({
            method: 'ashan_cn_procurement.services.payroll_settlement_service.export_qifu_payroll_excel',
            args: {
                company: COMPANY,
                period_month: current_month,
                sheet_type: sheet_type
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    const b64 = r.message.file_base64;
                    const fname = r.message.filename;
                    const byteChars = atob(b64);
                    const byteNums = new Array(byteChars.length);
                    for (let i = 0; i < byteChars.length; i++) {
                        byteNums[i] = byteChars.charCodeAt(i);
                    }
                    const byteArray = new Uint8Array(byteNums);
                    const blob = new Blob([byteArray], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                    const link = document.createElement('a');
                    link.href = URL.createObjectURL(blob);
                    link.download = fname;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    frappe.show_alert({ message: `📥 成功导出: ${fname}`, indicator: 'green' });
                }
            }
        });
    }

    // 纯净打印
    function print_modal_report(title, subtitle, table_element_id) {
        const table_el = document.getElementById(table_element_id);
        if (!table_el) return;
        const table_html = table_el.outerHTML;

        const iframe = document.createElement('iframe');
        iframe.style.position = 'fixed';
        iframe.style.right = '0';
        iframe.style.bottom = '0';
        iframe.style.width = '0';
        iframe.style.height = '0';
        iframe.style.border = '0';
        document.body.appendChild(iframe);

        const doc = iframe.contentWindow.document;
        doc.open();
        doc.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>${title}</title>
                <style>
                    @page { size: landscape; margin: 6mm; }
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                        color: #0f172a;
                        margin: 0;
                        padding: 4px;
                        background: #fff;
                    }
                    .print-header { text-align: center; margin-bottom: 8px; }
                    .print-title { font-size: 15pt; font-weight: 800; color: #0f172a; margin-bottom: 3px; letter-spacing: 0.5px; }
                    .print-sub { font-size: 8.5pt; color: #475569; font-weight: 500; }
                    .print-table-wrapper { width: 100%; border: 1.5px solid #334155 !important; box-sizing: border-box !important; }
                    table { width: 100%; border-collapse: collapse !important; font-size: 8.2pt; line-height: 1.15; box-sizing: border-box !important; }
                    th, td { border: 1px solid #64748b !important; padding: 3.5px 4px !important; box-sizing: border-box !important; }
                    th { font-weight: 700 !important; text-align: center !important; }
                    .qifu-money-cell { text-align: right !important; font-variant-numeric: tabular-nums; }
                    tfoot tr td { font-weight: 800 !important; }
                </style>
            </head>
            <body>
                <div class="print-header">
                    <div class="print-title">${title}</div>
                    <div class="print-sub">${subtitle}</div>
                </div>
                <div class="print-table-wrapper">
                    ${table_html}
                </div>
            </body>
            </html>
        `);
        doc.close();

        setTimeout(() => {
            iframe.contentWindow.focus();
            iframe.contentWindow.print();
            setTimeout(() => { document.body.removeChild(iframe); }, 3000);
        }, 300);
    }

    // ==========================================
    // 事件监听与委托
    // ==========================================

// ==========================================
    // 月度全流程任务看板与凭证上传核验 (精细化多维数据渲染)
    // ==========================================
    let cached_workflow_status = null;

    function load_monthly_workflow_hub() {
        const cur_m = $("#qifu-month-select").val() || current_month;
        $("#workflow-period-text").text(cur_m);

        frappe.call({
            method: 'ashan_cn_procurement.services.payroll_settlement_service.get_monthly_workflow_status',
            args: { company: COMPANY, period_month: cur_m },
            callback: function(r) {
                if (!r.message) return;
                const wf = r.message;
                cached_workflow_status = wf;

                // 1. 顶部封账状态 Badge 与 Card 5
                if (wf.is_locked) {
                    $("#workflow-lock-status-badge").html(
                        `<span style="color:#b45309; background:#fef3c7; border:1px solid #fde68a; padding:2px 8px; border-radius:10px;">🔒 已核定封账 (纯只读保护)</span>`
                    );
                    $("#btn-wf-lock-action").text("🔒 已封账 (点击反审核解锁)").removeClass("btn-primary").addClass("btn-default").css({"background":"#f8fafc","color":"#475569","border-color":"#cbd5e1"});
                    $("#wf-step5-icon").text("🔒");
                    $("#wf-step5-main").text("月度账期已封账锁定");
                    $("#wf-step5-sub").text("明细纯只读保护 · 下月已开启").css("color", "#b45309");
                    $("#wf-step5-lock-badge").text("已锁定").css({"color":"#b45309","background":"#fef3c7","border-color":"#fde68a"});
                    $("#wf-step-5").css({"background":"#fefce8","border-color":"#fef08a"});
                } else {
                    $("#workflow-lock-status-badge").html(
                        `<span style="color:#059669; background:#dcfce7; border:1px solid #bbf7d0; padding:2px 8px; border-radius:10px;">📝 草稿状态 (待核定)</span>`
                    );
                    const gross_val = wf.task5_settlement ? Number(wf.task5_settlement.total_gross || 0).toLocaleString('zh-CN', {minimumFractionDigits:2}) : '0.00';
                    const net_val = wf.task5_settlement ? Number(wf.task5_settlement.total_net || 0).toLocaleString('zh-CN', {minimumFractionDigits:2}) : '0.00';
                    const cost_val = wf.task5_settlement ? Number(wf.task5_settlement.total_company_cost || 0).toLocaleString('zh-CN', {minimumFractionDigits:2}) : '0.00';

                    if (wf.can_lock) {
                        $("#btn-wf-lock-action").text("🔒 立即执行最终核定").addClass("btn-primary").removeClass("btn-default").css({"background":"#059669","color":"#fff","border-color":"#059669"});
                        $("#wf-step5-icon").text("🟢");
                        $("#wf-step5-main").text(`税前: ¥${gross_val} ｜ 实发: ¥${net_val}`);
                        $("#wf-step5-sub").text(`企业总用工成本: ¥${cost_val}`).css("color", "#15803d");
                        $("#wf-step5-lock-badge").text("可核定").css({"color":"#059669","background":"#dcfce7","border-color":"#bbf7d0"});
                        $("#wf-step-5").css({"background":"#f0fdf4","border-color":"#bbf7d0"});
                    } else {
                        const has_proof_mismatch = wf.task3_ss.status === 'mismatch' || wf.task4_hf.status === 'mismatch';
                        if (has_proof_mismatch) {
                            $("#btn-wf-lock-action").text("⛔ 凭证金额不一致 · 禁止封账").addClass("btn-default").removeClass("btn-primary").css({"background":"#fee2e2","color":"#b91c1c","border-color":"#ef4444","font-weight":"800"});
                            $("#wf-step5-icon").text("⛔");
                            $("#wf-step5-main").text("社保/公积金凭证日期或金额未通过");
                            $("#wf-step5-sub").text("所属期与金额必须全部一致后才允许最终核定封账").css("color", "#b91c1c");
                            $("#wf-step5-lock-badge").text("禁止核定").css({"color":"#b91c1c","background":"#fee2e2","border-color":"#fecaca"});
                            $("#wf-step-5").css({"background":"#fff1f2","border-color":"#ef4444"});
                        } else {
                            $("#btn-wf-lock-action").text("🔒 执行最终核定封账").addClass("btn-default").removeClass("btn-primary").css({"background":"#f8fafc","color":"#64748b","border-color":"#cbd5e1"});
                            $("#wf-step5-icon").text("⚪");
                            $("#wf-step5-main").text(`税前: ¥${gross_val} ｜ 实发: ¥${net_val}`);
                            $("#wf-step5-sub").text("待前置实发与凭证全部核验").css("color", "#64748b");
                            $("#wf-step5-lock-badge").text("待核定").css({"color":"#64748b","background":"#f1f5f9","border-color":"#e2e8f0"});
                            $("#wf-step-5").css({"background":"#ffffff","border-color":"#e2e8f0"});
                        }
                    }
                }

                // 2. Step 1: 档案母表与计薪来源分类 (系统计薪 vs 外部计薪)
                if (wf.task1_profile.status === 'done') {
                    $("#wf-step1-icon").text("🟢");
                    $("#wf-step1-main").text(`在册 ${wf.task1_profile.active_count} 人 · ${wf.task1_profile.change_text || '人员及配置无异动'}`);
                    $("#wf-step1-sub").text(wf.task1_profile.sub_badge || `系统计薪 ${wf.task1_profile.sys_calc_count || 1}人 ｜ 外部计薪 ${wf.task1_profile.ext_calc_count || 25}人`);
                    $("#wf-step-1").css({"background":"#f0fdf4","border-color":"#bbf7d0"});
                } else {
                    $("#wf-step1-icon").text("⚪");
                    $("#wf-step1-main").text("在册人员档案为空");
                    $("#wf-step1-sub").text("请先在档案库录入员工信息");
                    $("#wf-step-1").css({"background":"#ffffff","border-color":"#e2e8f0"});
                }

                // 3. Step 2: 车间实发导入 (精准 25 人，排除非车间人员)
                const is_task2_done = (wf.task2_import.status === 'done' || !!wf.task2_import.file_url);
                if (is_task2_done) {
                    $("#wf-step2-icon").text("🟢");
                    $("#wf-step2-main").text(`已导入 ${wf.task2_import.employee_count} 人 · ¥ ${Number(wf.task2_import.total_net).toLocaleString('zh-CN', {minimumFractionDigits:2})}`);
                    $("#wf-step2-sub").text(`车间实发 ${wf.task2_import.employee_count}人 ｜ 非车间(母表) 1人`);
                    $("#wf-step-2").css({"background":"#f0fdf4","border-color":"#bbf7d0"});
                    $("#btn-wf-upload-salary").html("🗑️ 删除已上传实发表")
                        .attr("data-state", "uploaded")
                        .css({"background":"#fef2f2", "color":"#dc2626", "border-color":"#fecaca", "font-weight":"700"});
                } else {
                    $("#wf-step2-icon").text("⚪");
                    $("#wf-step2-main").text("待上传车间实发表");
                    $("#wf-step2-sub").text("外部计薪 25人 待导入实发表");
                    $("#wf-step-2").css({"background":"#ffffff","border-color":"#e2e8f0"});
                    $("#btn-wf-upload-salary").html("📤 上传车间实发表")
                        .attr("data-state", "empty")
                        .css({"background":"#eff6ff", "color":"#1d4ed8", "border-color":"#bfdbfe", "font-weight":"700"});
                }
                if (wf.task2_import.file_url) {
                    $("#wf-step2-file-badge").show().attr("data-url", wf.task2_import.file_url);
                } else {
                    $("#wf-step2-file-badge").hide().removeAttr("data-url");
                }

                // 4. Step 3: 社保申报表核验 (显示参保人数与公司/个人拆分)
                const ss_insured_cnt = wf.task3_ss.insured_count || 19;
                const ss_comp_str = Number(wf.task3_ss.company_amount || 0).toLocaleString('zh-CN', {minimumFractionDigits:2});
                const ss_pers_str = Number(wf.task3_ss.person_amount || 0).toLocaleString('zh-CN', {minimumFractionDigits:2});
                const ss_tot_str = Number(wf.task3_ss.parsed_amount || wf.task3_ss.sys_amount || 0).toLocaleString('zh-CN', {minimumFractionDigits:2});
                const is_task3_uploaded = (wf.task3_ss.status === 'verified' || !!wf.task3_ss.file_url);

                if (wf.task3_ss.status === 'verified') {
                    $("#wf-step3-icon").text("🟢");
                    $("#wf-step3-main").text(`${ss_insured_cnt} 人参保 · ${wf.task3_ss.file_count || 1}份凭证合计 ¥ ${ss_tot_str}`);
                    $("#wf-step3-sub").text(`所属期 ${wf.task3_ss.expected_period || '—'} 已通过 ｜ 公司 ¥${ss_comp_str} ｜ 个人 ¥${ss_pers_str}`).css("color", "#15803d");
                    $("#wf-step-3").css({"background":"#f0fdf4","border-color":"#bbf7d0"});
                } else if (wf.task3_ss.status === 'mismatch') {
                    const ss_diff_str = Number(wf.task3_ss.difference_amount != null ? wf.task3_ss.difference_amount : Math.abs(wf.task3_ss.parsed_amount - wf.task3_ss.sys_amount)).toLocaleString('zh-CN', {minimumFractionDigits:2});
                    $("#wf-step3-icon").text("⛔");
                    if (wf.task3_ss.period_valid === false && wf.task3_ss.file_url) {
                        $("#wf-step3-main").text(`社保凭证所属期错误 · 应为 ${wf.task3_ss.expected_period || '—'}`);
                        $("#wf-step3-sub").text(`检测到 ${(wf.task3_ss.detected_periods || []).join('、') || '无法识别'} ｜ 禁止最终核定封账`).css("color", "#b91c1c");
                    } else {
                        $("#wf-step3-main").text(`${ss_insured_cnt} 人参保 · 日期通过但金额不符 · 差额 ¥${ss_diff_str}`);
                        $("#wf-step3-sub").text(`所属期 ${wf.task3_ss.expected_period || '—'} ｜ 凭证 ¥${ss_tot_str} ｜ 系统 ¥${Number(wf.task3_ss.sys_amount).toLocaleString('zh-CN', {minimumFractionDigits:2})}`).css("color", "#b91c1c");
                    }
                    $("#wf-step-3").css({"background":"#fff1f2","border-color":"#ef4444","box-shadow":"0 0 0 1px rgba(239,68,68,0.08)"});
                } else {
                    $("#wf-step3-icon").text("🟡");
                    $("#wf-step3-main").text(`${ss_insured_cnt} 人参保 · 待上传申报表 (应缴 ¥${Number(wf.task3_ss.sys_amount).toLocaleString('zh-CN', {minimumFractionDigits:2})})`);
                    $("#wf-step3-sub").text(`公司 ¥${ss_comp_str} ｜ 个人 ¥${ss_pers_str}`);
                    $("#wf-step-3").css({"background":"#ffffff","border-color":"#e2e8f0"});
                }

                if (is_task3_uploaded) {
                    $("#btn-wf-upload-ss").html("🗑️ 删除已上传社保凭证")
                        .attr("data-state", "uploaded")
                        .css({"background":"#fef2f2", "color":"#dc2626", "border-color":"#fecaca", "font-weight":"700"});
                } else {
                    $("#btn-wf-upload-ss").html("📤 上传社保凭证")
                        .attr("data-state", "empty")
                        .css({"background":"#eff6ff", "color":"#1d4ed8", "border-color":"#bfdbfe", "font-weight":"700"});
                }

                if (wf.task3_ss.file_url) {
                    $("#wf-step3-file-badge").show().attr("data-url", wf.task3_ss.file_url);
                } else {
                    $("#wf-step3-file-badge").hide().removeAttr("data-url");
                }

                // 5. Step 4: 公积金凭证核验 (显示参缴人数与公司/个人拆分)
                const hf_insured_cnt = wf.task4_hf.insured_count || 19;
                const hf_comp_str = Number(wf.task4_hf.company_amount || 0).toLocaleString('zh-CN', {minimumFractionDigits:2});
                const hf_pers_str = Number(wf.task4_hf.person_amount || 0).toLocaleString('zh-CN', {minimumFractionDigits:2});
                const hf_tot_str = Number(wf.task4_hf.parsed_amount || wf.task4_hf.sys_amount || 0).toLocaleString('zh-CN', {minimumFractionDigits:2});
                const is_task4_uploaded = (wf.task4_hf.status === 'verified' || !!wf.task4_hf.file_url);

                if (wf.task4_hf.status === 'verified') {
                    $("#wf-step4-icon").text("🟢");
                    $("#wf-step4-main").text(`${hf_insured_cnt} 人参缴 · ${wf.task4_hf.file_count || 1}份凭证合计 ¥ ${hf_tot_str}`);
                    $("#wf-step4-sub").text(`所属期 ${wf.task4_hf.expected_period || '—'} 已通过 ｜ 公司 ¥${hf_comp_str} ｜ 个人 ¥${hf_pers_str}`).css("color", "#15803d");
                    $("#wf-step-4").css({"background":"#f0fdf4","border-color":"#bbf7d0"});
                } else if (wf.task4_hf.status === 'mismatch') {
                    const hf_diff_str = Number(wf.task4_hf.difference_amount != null ? wf.task4_hf.difference_amount : Math.abs(wf.task4_hf.parsed_amount - wf.task4_hf.sys_amount)).toLocaleString('zh-CN', {minimumFractionDigits:2});
                    $("#wf-step4-icon").text("⛔");
                    if (wf.task4_hf.period_valid === false && wf.task4_hf.file_url) {
                        $("#wf-step4-main").text(`公积金凭证所属期错误 · 应为 ${wf.task4_hf.expected_period || '—'}`);
                        $("#wf-step4-sub").text(`检测到 ${(wf.task4_hf.detected_periods || []).join('、') || '无法识别'} ｜ 禁止最终核定封账`).css("color", "#b91c1c");
                    } else {
                        $("#wf-step4-main").text(`${hf_insured_cnt} 人参缴 · 日期通过但金额不符 · 差额 ¥${hf_diff_str}`);
                        $("#wf-step4-sub").text(`所属期 ${wf.task4_hf.expected_period || '—'} ｜ 凭证 ¥${hf_tot_str} ｜ 系统 ¥${Number(wf.task4_hf.sys_amount).toLocaleString('zh-CN', {minimumFractionDigits:2})}`).css("color", "#b91c1c");
                    }
                    $("#wf-step-4").css({"background":"#fff1f2","border-color":"#ef4444","box-shadow":"0 0 0 1px rgba(239,68,68,0.08)"});
                } else {
                    $("#wf-step4-icon").text("🟡");
                    $("#wf-step4-main").text(`${hf_insured_cnt} 人参缴 · 待上传凭证 (应缴 ¥${Number(wf.task4_hf.sys_amount).toLocaleString('zh-CN', {minimumFractionDigits:2})})`);
                    $("#wf-step4-sub").text(`公司 ¥${hf_comp_str} ｜ 个人 ¥${hf_pers_str}`);
                    $("#wf-step-4").css({"background":"#ffffff","border-color":"#e2e8f0"});
                }

                if (is_task4_uploaded) {
                    $("#btn-wf-upload-hf").html("🗑️ 删除已上传公积金凭证")
                        .attr("data-state", "uploaded")
                        .css({"background":"#fef2f2", "color":"#dc2626", "border-color":"#fecaca", "font-weight":"700"});
                } else {
                    $("#btn-wf-upload-hf").html("📤 上传公积金凭证")
                        .attr("data-state", "empty")
                        .css({"background":"#eff6ff", "color":"#1d4ed8", "border-color":"#bfdbfe", "font-weight":"700"});
                }

                if (wf.task4_hf.file_url) {
                    $("#wf-step4-file-badge").show().attr("data-url", wf.task4_hf.file_url);
                } else {
                    $("#wf-step4-file-badge").hide().removeAttr("data-url");
                }

                adjust_active_table_height();
            }
        });
    }

    // 弹窗：上传车间外部实发工资表 Excel (第 2 步)
    function open_upload_workshop_salary_dialog() {
        const cur_m = $("#qifu-month-select").val() || current_month;
        const d = new frappe.ui.Dialog({
            title: `📤 上传【${cur_m}】车间外部实发工资表 (Excel)`,
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'salary_help',
                    options: `
                        <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:6px; padding:10px 12px; margin-bottom:12px; font-size:12px; color:#1e40af; line-height:1.5;">
                            <strong>💡 智能解析与核算说明：</strong><br>
                            • 支持直接上传车间/老板娘本地 <strong>.xlsx / .xlsm / .xls</strong> 实发工资表；<br>
                            • 系统将自动提取作业工时、加班考勤、达标率与车间实发金额，并生成 24 列标准薪资发放台账；<br>
                            • 后台自动执行<strong>【税后实发倒推税前应发与个人所得税】</strong>，并永久归档 Excel 原件供随时下载。
                        </div>
                    `
                },
                {
                    fieldtype: 'Attach',
                    fieldname: 'salary_file',
                    label: '选择车间实发工资表 Excel 文件 (.xlsx, .xlsm, .xls)',
                    reqd: 1
                }
            ],
            primary_action_label: '🚀 立即导入并解析核算',
            primary_action: function(vals) {
                if (!vals || !vals.salary_file) {
                    frappe.msgprint("请先选择车间实发工资表 Excel 文件！");
                    return;
                }
                const file_url = vals.salary_file;
                frappe.show_alert({ message: '🔍 正在智能解析外部实发工资表并倒推税前应发...', indicator: 'blue' });

                frappe.call({
                    method: 'ashan_cn_procurement.services.payroll_settlement_service.upload_and_import_qifu_salary',
                    args: {
                        file_url: file_url,
                        period_month: cur_m
                    },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            d.hide();
                            frappe.msgprint({
                                title: '🎉 车间实发表导入成功',
                                indicator: 'green',
                                message: `
                                    <div style="font-size:13px; line-height:1.6;">
                                        ${r.message.message}<br><br>
                                        <strong>导入实发人数：</strong> ${r.message.count || 26} 人<br>
                                        <strong>实发总额（税后）：</strong> ¥ ${Number(r.message.total_net || 0).toLocaleString('zh-CN', {minimumFractionDigits:2})}<br>
                                        <strong>倒推应发总额（税前）：</strong> ¥ ${Number(r.message.total_gross || 0).toLocaleString('zh-CN', {minimumFractionDigits:2})}<br>
                                        <strong>归档原件路径：</strong> <a href="${file_url}" target="_blank" style="color:#2563eb; font-weight:700;">📥 在线下载原始 Excel</a>
                                    </div>
                                `
                            });
                            load_monthly_workflow_hub();
                            if (current_tab === 'import') load_salary_distribution_tab();
                            if (current_tab === 'tax') load_tax_settlement_tab();
                            if (current_tab === 'settlement') load_payroll_settlement();
                        }
                    }
                });
            }
        });
        d.show();
    }


    // ==========================================
    // 弹窗：上传社保申报表 PDF / ZIP
    // ==========================================
    function open_upload_social_security_dialog() {
        const cur_m = $("#qifu-month-select").val() || current_month;
        const d = new frappe.ui.Dialog({
            title: `🛡️ 上传【${cur_m}】社会保险费缴费申报表 (PDF / ZIP)`,
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'ss_help',
                    options: `
                        <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:6px; padding:10px 12px; margin-bottom:12px; font-size:12px; color:#166534; line-height:1.5;">
                            <strong>💡 智能核验说明：</strong><br>
                            • 支持直接上传税务局/社保局下载的 <strong>.pdf</strong> 缴费申报表，或包含 PDF 的 <strong>.zip</strong> 压缩包；<br>
                            • 系统将自动解析 PDF 内纳税人识别号、所属期与缴费总额，并与系统核算总额实时比对；<br>
                            • 上传成功后将自动规范命名归档，并可随时点击【📥 凭证】下载原件。
                        </div>
                    `
                },
                {
                    fieldtype: 'Attach',
                    fieldname: 'ss_file',
                    label: '选择社保申报表 PDF 或 ZIP 文件',
                    reqd: 1
                }
            ],
            primary_action_label: '🚀 提交并智能解析核验',
            primary_action: function(vals) {
                if (!vals || !vals.ss_file) {
                    frappe.msgprint("请先选择社保 PDF 或 ZIP 文件！");
                    return;
                }
                const file_url = vals.ss_file;
                frappe.show_alert({ message: '🔍 正在智能解析社保凭证并比对金额...', indicator: 'blue' });

                frappe.call({
                    method: 'ashan_cn_procurement.services.payroll_settlement_service.upload_and_verify_social_security_file',
                    args: {
                        company: COMPANY,
                        period_month: cur_m,
                        file_url: file_url
                    },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            d.hide();
                            frappe.msgprint({
                                title: '✅ 社保凭证解析完成',
                                indicator: r.message.is_matched ? 'green' : 'orange',
                                message: `
                                    <div style="font-size:13px; line-height:1.6;">
                                        ${r.message.message}<br><br>
                                        <strong>PDF 提取总额：</strong> ¥ ${Number(r.message.parsed_amount).toLocaleString('zh-CN', {minimumFractionDigits:2})}<br>
                                        <strong>系统核算总额：</strong> ¥ ${Number(r.message.sys_amount).toLocaleString('zh-CN', {minimumFractionDigits:2})}<br>
                                        <strong>归档文件路径：</strong> <a href="${r.message.file_url}" target="_blank" style="color:#2563eb; font-weight:700;">📥 在线查看 / 下载 PDF 原件</a>
                                    </div>
                                `
                            });
                            load_monthly_workflow_hub();
                        }
                    }
                });
            }
        });
        d.show();
    }

    // ==========================================
    // 弹窗：上传公积金缴存凭证 ZIP / PDF
    // ==========================================
    function open_upload_housing_fund_dialog() {
        const cur_m = $("#qifu-month-select").val() || current_month;
        const d = new frappe.ui.Dialog({
            title: `🏛️ 上传【${cur_m}】住房公积金缴存凭证 (ZIP / PDF)`,
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'hf_help',
                    options: `
                        <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:6px; padding:10px 12px; margin-bottom:12px; font-size:12px; color:#1e40af; line-height:1.5;">
                            <strong>💡 智能解压与核验说明：</strong><br>
                            • 支持上传公积金中心下载的 <strong>.zip 压缩包</strong> 或 <strong>.pdf 受理凭证</strong>；<br>
                            • 若为 ZIP 压缩包，系统将在后台<strong>自动解压并仅保留内部 PDF 凭证</strong>，自动清除冗余文件；<br>
                            • 自动识别缴存年月、人数与缴存总额，并与系统公积金核算总盘实时比对；<br>
                            • 下载时始终保证为您提供解压后的清晰原件 PDF。
                        </div>
                    `
                },
                {
                    fieldtype: 'Attach',
                    fieldname: 'hf_file',
                    label: '选择公积金 ZIP 压缩包或 PDF 凭证',
                    reqd: 1
                }
            ],
            primary_action_label: '🚀 提交后台解压与智能核验',
            primary_action: function(vals) {
                if (!vals || !vals.hf_file) {
                    frappe.msgprint("请先选择公积金 ZIP 或 PDF 文件！");
                    return;
                }
                const file_url = vals.hf_file;
                frappe.show_alert({ message: '🔍 正在后台解压公积金凭证并比对金额...', indicator: 'blue' });

                frappe.call({
                    method: 'ashan_cn_procurement.services.payroll_settlement_service.upload_and_verify_housing_fund_file',
                    args: {
                        company: COMPANY,
                        period_month: cur_m,
                        file_url: file_url
                    },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            d.hide();
                            frappe.msgprint({
                                title: '✅ 公积金凭证解析完成',
                                indicator: r.message.is_matched ? 'green' : 'orange',
                                message: `
                                    <div style="font-size:13px; line-height:1.6;">
                                        ${r.message.message}<br><br>
                                        <strong>PDF 提取总额：</strong> ¥ ${Number(r.message.parsed_amount).toLocaleString('zh-CN', {minimumFractionDigits:2})}<br>
                                        <strong>系统核算总额：</strong> ¥ ${Number(r.message.sys_amount).toLocaleString('zh-CN', {minimumFractionDigits:2})}<br>
                                        <strong>归档文件路径：</strong> <a href="${r.message.file_url}" target="_blank" style="color:#2563eb; font-weight:700;">📥 在线查看 / 下载 PDF 原件</a>
                                    </div>
                                `
                            });
                            load_monthly_workflow_hub();
                        }
                    }
                });
            }
        });
        d.show();
    }


// ==========================================
    // 事件监听与委托：任务看板 5 步全流程与凭证操作
    // ==========================================
    $container.on("click", ".wf-goto-tab", function(e) {
        e.preventDefault();
        e.stopPropagation();
        const tab = $(this).attr("data-tab");
        if (tab) $(`.qifu-tab-btn[data-tab='${tab}']`).trigger("click");
    });

    // 凭证文件删除与重置统一执行引擎
    function execute_delete_proof(proof_type, type_label) {
        const cur_m = $("#qifu-month-select").val() || current_month;
        frappe.call({
            method: 'ashan_cn_procurement.services.payroll_settlement_service.delete_payroll_proof_file',
            args: {
                company: COMPANY,
                period_month: cur_m,
                proof_type: proof_type
            },
            freeze: true,
            freeze_message: `正在安全移除【${cur_m}】${type_label}...`,
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: r.message.message,
                        indicator: 'green'
                    }, 4);
                    load_monthly_workflow_hub();
                    if (proof_type === 'salary') {
                        load_salary_distribution_tab();
                        load_qifu_payroll_data();
                    } else if (proof_type === 'social_security') {
                        load_social_insurance_tab();
                    } else if (proof_type === 'housing_fund') {
                        load_housing_fund_tab();
                    }
                } else if (r.message && r.message.message) {
                    frappe.msgprint({
                        title: '删除失败',
                        indicator: 'red',
                        message: r.message.message
                    });
                }
            }
        });
    }

    // ⭐️ 核心统一：车间实发 Excel 上传与解析核算统一执行引擎 (Single Unified Salary Upload Engine)
    function execute_qifu_salary_upload(base64_str, filename, cur_m, on_complete) {
        if (!base64_str) {
            frappe.msgprint({
                title: '❌ 未选择文件',
                indicator: 'orange',
                message: '未检测到文件内容，请重新选择车间实发 Excel 文件！'
            });
            if (on_complete) on_complete(false);
            return;
        }

        const target_month = cur_m || $("#qifu-month-select").val() || current_month;

        frappe.call({
            method: 'ashan_cn_procurement.services.payroll_settlement_service.upload_and_import_qifu_salary',
            type: 'POST',
            freeze: true,
            freeze_message: `🔍 正在智能解析【${filename}】并执行税后实发倒推税前与个税核算...`,
            args: {
                file_data: base64_str,
                filename: filename,
                period_month: target_month
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.msgprint({
                        title: '🎉 车间实发表导入成功',
                        indicator: 'green',
                        message: `
                            <div style="font-size:13px; line-height:1.6;">
                                ${r.message.message}<br><br>
                                <strong>导入实发人数：</strong> ${r.message.total_imported || '—'} 人<br>
                                <strong>实发总额（税后）：</strong> ¥ ${Number(r.message.total_net_salary || 0).toLocaleString('zh-CN', {minimumFractionDigits:2})}<br>
                                <strong>倒推应发总额（税前）：</strong> ¥ ${Number(r.message.total_gross_salary || 0).toLocaleString('zh-CN', {minimumFractionDigits:2})}<br>
                                <strong>归档原件：</strong> <span style="color:#2563eb; font-weight:700;">${filename}</span>
                            </div>
                        `
                    });
                    load_monthly_workflow_hub();
                    load_salary_distribution_tab();
                    if (typeof load_qifu_payroll_data === 'function') load_qifu_payroll_data();
                    if (current_tab === 'tax') load_tax_settlement_tab();
                    if (current_tab === 'settlement') load_payroll_settlement();
                    if (on_complete) on_complete(true);
                } else {
                    const msg = (r.message && r.message.message) || '处理 Excel 文件时发生错误，请检查文件格式！';
                    frappe.msgprint({
                        title: '❌ 导入失败',
                        indicator: 'red',
                        message: msg
                    });
                    if (on_complete) on_complete(false);
                }
            },
            error: function(r) {
                let error_msg = '服务器处理车间实发表时发生异常！';
                if (r && r._server_messages) {
                    try {
                        const msgs = JSON.parse(r._server_messages);
                        error_msg = msgs.map(m => {
                            try { return JSON.parse(m).message; } catch(e) { return m; }
                        }).join('<br>');
                    } catch(e) {}
                } else if (r && r.exc) {
                    error_msg = r.exc.split('\n').filter(Boolean).pop() || r.exc;
                }
                frappe.msgprint({
                    title: '❌ 上传与解析失败',
                    indicator: 'red',
                    message: `<div style="line-height:1.6; font-size:13px;">${error_msg}</div>`
                });
                if (on_complete) on_complete(false);
            }
        });
    }

    // 🚀 零中转极速上传引擎：基于 FileReader 直接转换 Base64 并提交后端解析核算
    function direct_file_upload(accept_exts, on_file_read) {
        const file_input = document.createElement('input');
        file_input.type = 'file';
        file_input.accept = accept_exts;
        file_input.style.display = 'none';
        document.body.appendChild(file_input);

        file_input.onchange = function(e) {
            const file = e.target.files[0];
            document.body.removeChild(file_input);
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(evt) {
                const base64_str = evt.target.result;
                on_file_read(base64_str, file.name, file);
            };
            reader.onerror = function() {
                frappe.msgprint({
                    title: '❌ 读取文件失败',
                    indicator: 'red',
                    message: `无法读取本地文件【${file.name}】，请检查文件是否被占用或损坏！`
                });
            };
            reader.readAsDataURL(file);
        };

        file_input.click();
    }

    function direct_multi_file_upload(accept_exts, on_files_read) {
        const file_input = document.createElement('input');
        file_input.type = 'file';
        file_input.accept = accept_exts;
        file_input.multiple = true;
        file_input.style.display = 'none';
        document.body.appendChild(file_input);
        file_input.onchange = async function(e) {
            const files = Array.from(e.target.files || []);
            document.body.removeChild(file_input);
            if (!files.length) return;
            if (files.length > 20) {
                frappe.msgprint({title:'⛔ 文件过多', indicator:'red', message:'单次最多选择 20 个 PDF/ZIP 凭证文件。'});
                return;
            }
            try {
                const payload = await Promise.all(files.map(file => new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onload = evt => resolve({file_name: file.name, file_base64: evt.target.result});
                    reader.onerror = () => reject(new Error(`无法读取 ${file.name}`));
                    reader.readAsDataURL(file);
                })));
                on_files_read(payload, files);
            } catch (err) {
                frappe.msgprint({title:'❌ 读取文件失败', indicator:'red', message: err.message || String(err)});
            }
        };
        file_input.click();
    }

    $container.on("click", "#btn-wf-upload-salary", function(e) {
        e.preventDefault();
        e.stopPropagation();
        const state = $(this).attr("data-state");
        const cur_m = $("#qifu-month-select").val() || current_month;
        if (state === "uploaded") {
            frappe.confirm(
                `⚠️ 确定要删除【${cur_m}】已上传的车间外部实发工资表吗？<br><br><span style="color:#dc2626; font-size:12px;">删除后该月份车间发放台账与核算明细将被清空重置，需重新上传 Excel 文件。</span>`,
                function() {
                    execute_delete_proof('salary', '车间实发工资表');
                }
            );
        } else {
            direct_file_upload('.xlsx,.xlsm,.xls', function(base64_str, filename) {
                execute_qifu_salary_upload(base64_str, filename, cur_m);
            });
        }
    });

    $container.on("click", "#btn-wf-upload-ss", function(e) {
        e.preventDefault();
        e.stopPropagation();
        const state = $(this).attr("data-state");
        const cur_m = $("#qifu-month-select").val() || current_month;
        if (state === "uploaded") {
            frappe.confirm(`⚠️ 确定要删除【${cur_m}】已上传的全部社保缴费申报表凭证吗？`, function() { execute_delete_proof('social_security', '社保申报表凭证'); });
            return;
        }
        direct_multi_file_upload('.pdf,.zip', function(file_payload, raw_files) {
            const names = raw_files.map(f => f.name).join('、');
            frappe.call({
                method: 'ashan_cn_procurement.services.payroll_settlement_service.upload_and_verify_social_security_file',
                type: 'POST', freeze: true,
                freeze_message: `🔍 正在解析 ${raw_files.length} 个社保文件：先校验所属期，再汇总金额...`,
                args: {company: COMPANY, period_month: cur_m, files_json: JSON.stringify(file_payload)},
                callback: function(r) {
                    if (r.message && r.message.success) {
                        const diff = Number(r.message.difference_amount || 0);
                        frappe.msgprint({title: r.message.is_matched ? '✅ 社保日期与金额均核验一致' : '⛔ 社保日期正确但金额不一致', indicator: r.message.is_matched ? 'green' : 'red', message: `<div style="font-size:13px;line-height:1.7;">${r.message.message}<br><br><strong>核定期：</strong>${cur_m}<br><strong>凭证应属实际缴费期：</strong>${r.message.expected_period || '—'}<br><strong>本批 PDF：</strong>${r.message.proof_count || 0} 份<br><strong>凭证合计：</strong>¥ ${Number(r.message.parsed_amount || 0).toLocaleString('zh-CN',{minimumFractionDigits:2})}<br><strong>系统核算：</strong>¥ ${Number(r.message.sys_amount || 0).toLocaleString('zh-CN',{minimumFractionDigits:2})}<br><strong>差额：</strong>¥ ${diff.toLocaleString('zh-CN',{minimumFractionDigits:2})}<br><strong>选择文件：</strong>${names}${r.message.is_matched ? '' : '<div style="margin-top:9px;padding:8px;border:1px solid #ef4444;background:#fff1f2;color:#b91c1c;border-radius:6px;font-weight:700;">⛔ 金额未通过，凭证已归档但禁止最终核定封账。</div>'}</div>`});
                        load_monthly_workflow_hub();
                        if (typeof load_social_insurance_tab === 'function') load_social_insurance_tab();
                    } else {
                        frappe.msgprint({title: (r.message && r.message.validation_type === 'period_mismatch') ? '⛔ 社保凭证所属期错误 · 已拒绝上传' : '❌ 社保凭证核验失败', indicator: 'red', message: (r.message && r.message.message) || '社保凭证处理失败。'});
                    }
                },
                error: function(r) { let msg='服务器处理社保凭证时发生错误！'; if (r && r._server_messages) { try { msg=JSON.parse(r._server_messages).map(m=>{try{return JSON.parse(m).message}catch(e){return m}}).join('<br>'); } catch(e){} } frappe.msgprint({title:'❌ 请求异常',indicator:'red',message:msg}); }
            });
        });
    });

    $container.on("click", "#btn-wf-upload-hf", function(e) {
        e.preventDefault();
        e.stopPropagation();
        const state = $(this).attr("data-state");
        const cur_m = $("#qifu-month-select").val() || current_month;
        if (state === "uploaded") {
            frappe.confirm(`⚠️ 确定要删除【${cur_m}】已上传的全部住房公积金缴存凭证吗？`, function() { execute_delete_proof('housing_fund', '公积金缴存凭证'); });
            return;
        }
        direct_multi_file_upload('.pdf,.zip', function(file_payload, raw_files) {
            const names = raw_files.map(f => f.name).join('、');
            frappe.call({
                method: 'ashan_cn_procurement.services.payroll_settlement_service.upload_and_verify_housing_fund_file',
                type: 'POST', freeze: true,
                freeze_message: `🔍 正在解析 ${raw_files.length} 个公积金文件：先校验缴存年月，再汇总金额...`,
                args: {company: COMPANY, period_month: cur_m, files_json: JSON.stringify(file_payload)},
                callback: function(r) {
                    if (r.message && r.message.success) {
                        const diff = Number(r.message.difference_amount || 0);
                        frappe.msgprint({title: r.message.is_matched ? '✅ 公积金日期与金额均核验一致' : '⛔ 公积金日期正确但金额不一致', indicator: r.message.is_matched ? 'green' : 'red', message: `<div style="font-size:13px;line-height:1.7;">${r.message.message}<br><br><strong>核定期：</strong>${cur_m}<br><strong>凭证应属实际缴费期：</strong>${r.message.expected_period || '—'}<br><strong>本批 PDF：</strong>${r.message.proof_count || 0} 份<br><strong>凭证合计：</strong>¥ ${Number(r.message.parsed_amount || 0).toLocaleString('zh-CN',{minimumFractionDigits:2})}<br><strong>系统核算：</strong>¥ ${Number(r.message.sys_amount || 0).toLocaleString('zh-CN',{minimumFractionDigits:2})}<br><strong>差额：</strong>¥ ${diff.toLocaleString('zh-CN',{minimumFractionDigits:2})}<br><strong>选择文件：</strong>${names}${r.message.is_matched ? '' : '<div style="margin-top:9px;padding:8px;border:1px solid #ef4444;background:#fff1f2;color:#b91c1c;border-radius:6px;font-weight:700;">⛔ 金额未通过，凭证已归档但禁止最终核定封账。</div>'}</div>`});
                        load_monthly_workflow_hub();
                        if (typeof load_housing_fund_tab === 'function') load_housing_fund_tab();
                    } else {
                        frappe.msgprint({title: (r.message && r.message.validation_type === 'period_mismatch') ? '⛔ 公积金凭证所属期错误 · 已拒绝上传' : '❌ 公积金凭证核验失败', indicator: 'red', message: (r.message && r.message.message) || '公积金凭证处理失败。'});
                    }
                },
                error: function(r) { let msg='服务器处理公积金凭证时发生错误！'; if (r && r._server_messages) { try { msg=JSON.parse(r._server_messages).map(m=>{try{return JSON.parse(m).message}catch(e){return m}}).join('<br>'); } catch(e){} } frappe.msgprint({title:'❌ 请求异常',indicator:'red',message:msg}); }
            });
        });
    });

    // 右上角胶囊文件【🔒 权限受控安全下载】
    $container.on("click", ".btn-wf-download-file", function(e) {
        e.preventDefault();
        e.stopPropagation();
        const ptype = $(this).attr("data-type"); // 'excel', 'ss', 'hf'
        const cur_m = $("#qifu-month-select").val() || current_month;
        const file_url = $(this).attr("data-url");

        if (!file_url) {
            frappe.show_alert({ message: '该账期尚未上传该类型的原始凭证文件', indicator: 'orange' });
            return;
        }

        // 调用专用受控鉴权下载接口，杜绝越权与私自下载
        const download_url = `/api/method/ashan_cn_procurement.services.payroll_settlement_service.download_payroll_proof_file?company=${encodeURIComponent(COMPANY)}&period_month=${encodeURIComponent(cur_m)}&proof_type=${encodeURIComponent(ptype)}`;
        window.open(download_url, "_blank");
    });

    // 阶段 5 综合核定与封账操作 (100% 强拦截保障与实时状态校验)
    $container.on("click", "#btn-wf-lock-action", function(e) {
        e.preventDefault();
        e.stopPropagation();
        const cur_m = $("#qifu-month-select").val() || current_month;

        frappe.show_alert({ message: '🔍 正在实时校验月度核算任务状态...', indicator: 'blue' });

        frappe.call({
            method: 'ashan_cn_procurement.services.payroll_settlement_service.get_monthly_workflow_status',
            args: { company: COMPANY, period_month: cur_m },
            callback: function(r) {
                if (!r.message) {
                    frappe.msgprint("获取月度核定状态失败，请刷新页面重试！");
                    return;
                }
                const wf = r.message;
                cached_workflow_status = wf;

                // 1. 如果当前账期已经封账 -> 弹出反审核解锁登记
                if (wf.is_locked) {
                    frappe.confirm(
                        `<strong>【🔒 当前发薪账期已封账锁定】</strong><br><br>
                        核算公司：<strong>${COMPANY}</strong><br>
                        核算月份：<span style="color:#2563eb; font-weight:800;">${cur_m}</span><br><br>
                        当前月份所有明细已处于纯只读保护状态。<br>
                        是否需要执行【反审核/解锁】以恢复数据修改与重新计算权限？`,
                        function() {
                            frappe.prompt(
                                [{ fieldname: 'reason', fieldtype: 'Small Text', label: '解锁/反审核原因 (必填)', reqd: 1 }],
                                function(values) {
                                    frappe.call({
                                        method: 'ashan_cn_procurement.services.payroll_settlement_service.unlock_monthly_settlement',
                                        args: { company: COMPANY, period_month: cur_m, reason: values.reason },
                                        callback: function(res) {
                                            if (res.message && res.message.success) {
                                                frappe.msgprint({ title: '🔓 账期已反审核解锁', indicator: 'green', message: res.message.message });
                                                load_monthly_workflow_hub();
                                            }
                                        }
                                    });
                                },
                                '反审核解锁原因登记'
                            );
                        }
                    );
                    return;
                }

                // 2. 前置任务校验与强拦截 (严格检查：实发表、社保申报表、公积金凭证)
                let missing_steps = [];
                if (wf.task1_profile.status !== 'done') missing_steps.push("• <strong>第 1 步 · 员工底册</strong>：在册员工人数为 0，请先在档案库录入员工。");
                if (wf.task2_import.status !== 'done') missing_steps.push("• <strong>第 2 步 · 车间实发</strong>：尚未上传并导入【车间外部实发工资表 Excel】。");
                if (wf.task3_ss.status === 'mismatch') {
                    if (wf.task3_ss.period_valid === false && wf.task3_ss.file_url) {
                        missing_steps.push(`• <strong>第 3 步 · 社保申报</strong>：<span style="color:#b91c1c;font-weight:700;">凭证所属期 ${(wf.task3_ss.detected_periods || []).join('、') || '无法识别'} 与核定期 ${cur_m} 对应的实际缴费期 ${wf.task3_ss.expected_period || '—'} 不一致。禁止最终核定封账。</span>`);
                    } else {
                        const ss_diff = Number(wf.task3_ss.difference_amount != null ? wf.task3_ss.difference_amount : Math.abs(wf.task3_ss.parsed_amount - wf.task3_ss.sys_amount)).toLocaleString('zh-CN', {minimumFractionDigits:2});
                        missing_steps.push(`• <strong>第 3 步 · 社保申报</strong>：<span style="color:#b91c1c;font-weight:700;">所属期已通过，但凭证合计 ¥${Number(wf.task3_ss.parsed_amount || 0).toLocaleString('zh-CN', {minimumFractionDigits:2})} 与系统核算 ¥${Number(wf.task3_ss.sys_amount || 0).toLocaleString('zh-CN', {minimumFractionDigits:2})} 不一致，差额 ¥${ss_diff}。</span>`);
                    }
                } else if (wf.task3_ss.status !== 'verified') {
                    missing_steps.push(`• <strong>第 3 步 · 社保申报</strong>：请上传属于 <strong>${wf.task3_ss.expected_period || '次月'}</strong> 的社保 PDF/ZIP，并完成日期+金额双重核验。`);
                }
                if (wf.task4_hf.status === 'mismatch') {
                    if (wf.task4_hf.period_valid === false && wf.task4_hf.file_url) {
                        missing_steps.push(`• <strong>第 4 步 · 公积金凭证</strong>：<span style="color:#b91c1c;font-weight:700;">凭证所属期 ${(wf.task4_hf.detected_periods || []).join('、') || '无法识别'} 与核定期 ${cur_m} 对应的实际缴费期 ${wf.task4_hf.expected_period || '—'} 不一致。禁止最终核定封账。</span>`);
                    } else {
                        const hf_diff = Number(wf.task4_hf.difference_amount != null ? wf.task4_hf.difference_amount : Math.abs(wf.task4_hf.parsed_amount - wf.task4_hf.sys_amount)).toLocaleString('zh-CN', {minimumFractionDigits:2});
                        missing_steps.push(`• <strong>第 4 步 · 公积金凭证</strong>：<span style="color:#b91c1c;font-weight:700;">所属期已通过，但凭证合计 ¥${Number(wf.task4_hf.parsed_amount || 0).toLocaleString('zh-CN', {minimumFractionDigits:2})} 与系统核算 ¥${Number(wf.task4_hf.sys_amount || 0).toLocaleString('zh-CN', {minimumFractionDigits:2})} 不一致，差额 ¥${hf_diff}。</span>`);
                    }
                } else if (wf.task4_hf.status !== 'verified') {
                    missing_steps.push(`• <strong>第 4 步 · 公积金凭证</strong>：请上传属于 <strong>${wf.task4_hf.expected_period || '次月'}</strong> 的公积金 PDF/ZIP，并完成日期+金额双重核验。`);
                }

                if (missing_steps.length > 0) {
                    frappe.msgprint({
                        title: '⚠️ 无法执行最终核定：前置任务尚未全部完成',
                        indicator: 'orange',
                        message: `
                            <div style="font-size:12.5px; line-height:1.7;">
                                <div style="margin-bottom:8px; color:#991b1b; font-weight:700;">
                                    为保证财务核算、税前倒推与纳税申报数据的严肃性与一致性，必须在完成以下前置任务后方可最终封账：
                                </div>
                                <div style="background:#fff1f2; border:1px solid #fecdd3; border-radius:6px; padding:8px 12px; margin-bottom:10px; color:#881337;">
                                    ${missing_steps.join("<br>")}
                                </div>
                                <div style="color:#475569; font-size:12px;">
                                    💡 提示：您可以直接点击上方对应的 <strong>[📤 上传]</strong> 按钮快速完成各步骤。
                                </div>
                            </div>
                        `
                    });
                    return;
                }

                // 3. 前置任务全部就绪，弹出最终综合核定封账确认大弹窗
                frappe.confirm(
                    `<strong>【🎉 前置任务全部就绪 · 执行最终薪酬核定并封账】</strong><br><br>
                    核算公司：<strong>${COMPANY}</strong><br>
                    核算月份：<span style="color:#2563eb; font-weight:800;">${cur_m}</span><br>
                    核定在册：<span style="color:#059669; font-weight:700;">26 人</span><br><br>
                    <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:8px 10px; font-size:12px; line-height:1.6;">
                        • 车间实发总盘：<strong>¥ ${Number(wf.task2_import.total_net || 0).toLocaleString('zh-CN', {minimumFractionDigits:2})}</strong><br>
                        • 社保申报总额：<strong>¥ ${Number(wf.task3_ss.parsed_amount || 0).toLocaleString('zh-CN', {minimumFractionDigits:2})}</strong><br>
                        • 公积金缴存总额：<strong>¥ ${Number(wf.task4_hf.parsed_amount || 0).toLocaleString('zh-CN', {minimumFractionDigits:2})}</strong>
                    </div><br>
                    <span style="color:#15803d; font-weight:600;">🛡️ 封账后效应：</span><br>
                    1. 本月 26 名员工档案、车间实发表、社保/公积金台账与个税申报表将<strong>全部进入纯只读保护，禁止随意篡改</strong>；<br>
                    2. 系统将<strong>自动为您开启下月发薪账期【${wf.next_period_month}】的创建与写入权限</strong>，确保财务核算连续性。<br><br>
                    确认立即执行最终核定封账吗？`,
                    function() {
                        frappe.call({
                            method: 'ashan_cn_procurement.services.payroll_settlement_service.execute_monthly_settlement_lock',
                            args: { company: COMPANY, period_month: cur_m },
                            callback: function(lock_res) {
                                if (lock_res.message && lock_res.message.success) {
                                    frappe.msgprint({
                                        title: '🎉 最终核定封账成功',
                                        indicator: 'green',
                                        message: `
                                            <div style="font-size:13px; line-height:1.6;">
                                                ${lock_res.message.message}<br><br>
                                                <button class="btn btn-primary btn-sm" onclick="$('#qifu-month-select').val('${lock_res.message.next_period_month}').trigger('change'); cur_dialog.hide();">
                                                    ⏩ 立即前往下月【${lock_res.message.next_period_month}】建账与录入
                                                </button>
                                            </div>
                                        `
                                    });
                                    load_monthly_workflow_hub();
                                }
                            }
                        });
                    }
                );
            }
        });
    });

    // 1. 6 大 Tab 切换监听
    $container.on("click", ".qifu-tab-btn", function() {
        $(".qifu-tab-btn").removeClass("active");
        $(this).addClass("active");
        const tab = $(this).attr("data-tab");
        $(".qifu-tab-content").hide();
        $(`#qifu-tab-${tab}`).show();
        current_tab = tab;
        setTimeout(adjust_active_table_height, 50);

        if (tab === 'employees') load_qifu_employees();
        if (tab === 'import') load_salary_distribution_tab();
        if (tab === 'social_insurance') load_social_insurance_tab();
        if (tab === 'housing_fund') load_housing_fund_tab();
        if (tab === 'tax') load_tax_settlement_tab();
        if (tab === 'settlement') load_payroll_settlement();
    });

    // 2. 月份切换
    $container.on("change", "#qifu-month-select", function() {
        current_month = $(this).val();
        load_monthly_workflow_hub();
        if (current_tab === 'employees') load_qifu_employees();
        if (current_tab === 'import') load_salary_distribution_tab();
        if (current_tab === 'social_insurance') load_social_insurance_tab();
        if (current_tab === 'housing_fund') load_housing_fund_tab();
        if (current_tab === 'tax') load_tax_settlement_tab();
        if (current_tab === 'settlement') load_payroll_settlement();
    });

    // 3. 刷新按钮
    $container.on("click", "#btn-qifu-refresh-all", function() {
        load_monthly_workflow_hub();
        if (current_tab === 'employees') load_qifu_employees();
        if (current_tab === 'import') load_salary_distribution_tab();
        if (current_tab === 'social_insurance') load_social_insurance_tab();
        if (current_tab === 'housing_fund') load_housing_fund_tab();
        if (current_tab === 'tax') load_tax_settlement_tab();
        if (current_tab === 'settlement') load_payroll_settlement();
    });

    // 4. Tab 1 员工母表操作
    $container.on("click", "#btn-qifu-new-emp", function() {
        open_emp_dialog(null);
    });
    $container.on("click", ".btn-edit-emp", function() {
        const emp_id = $(this).attr("data-id");
        frappe.call({
            method: 'frappe.client.get',
            args: { doctype: 'Ashan Employee Salary Profile', name: emp_id },
            callback: function(r) {
                if (r.message) open_emp_dialog(r.message);
            }
        });
    });

    // 单人离职
    $container.on("click", ".btn-resign-emp", function() {
        const emp_no = $(this).attr("data-emp-no");
        const emp_name = $(this).attr("data-emp-name");
        open_resign_dialog(emp_no, emp_name);
    });

    // 撤销离职，恢复在职
    $container.on("click", ".btn-unresign-emp", function() {
        const emp_no = $(this).attr("data-emp-no");
        const emp_name = $(this).attr("data-emp-name");
        frappe.confirm(
            `<strong>【🔄 恢复员工在职状态】</strong><br><br>
            员工：<strong>${emp_name} (${emp_no})</strong><br><br>
            确认撤销离职记录，恢复为正常在职员工吗？`,
            function() {
                frappe.call({
                    method: 'ashan_cn_procurement.services.employee_salary_service.cancel_employee_resignation',
                    args: { employee_no: emp_no, company: COMPANY },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.show_alert({ message: r.message.message, indicator: 'green' });
                            load_monthly_workflow_hub();
                            load_qifu_employees();
                            load_social_insurance_tab();
                            load_housing_fund_tab();
                        }
                    }
                });
            }
        );
    });

    // 全选/反选员工
    $container.on("change", "#check-all-tab1-employees", function() {
        const isChecked = $(this).prop("checked");
        $(".tab1-emp-check").prop("checked", isChecked);
    });

    // 批量办理离职
    $container.on("click", "#btn-batch-resign", function() {
        let selected = [];
        $(".tab1-emp-check:checked").each(function() {
            selected.push({
                no: $(this).attr("data-emp-no"),
                name: $(this).attr("data-emp-name")
            });
        });
        open_batch_resign_dialog(selected);
    });

    $container.on("input", "#qifu-emp-search", function() {
        const q = $(this).val().toLowerCase().trim();
        $("#tbody-qifu-emp tr").each(function() {
            const text = $(this).text().toLowerCase();
            $(this).toggle(text.includes(q));
        });
    });

    // 5. 批处理：社保与公积金最低基数/清零
    $container.on("click", "#btn-qifu-ss-batch-min", function() {
        frappe.confirm(
            `<strong>【⚡ 一键全员社保 (最低基数 5124元)】</strong><br><br>
            规则说明：<br>
            1. 将所有用工性质为【正式工】的员工社保基数一键设为最低基数 5,124.00 元；<br>
            2. 退休返聘人员与临时工保持 0 元。<br><br>
            确认执行吗？`,
            function() {
                frappe.call({
                    method: 'ashan_cn_procurement.services.employee_salary_service.set_qifu_social_security_batch',
                    args: { mode: 'min' },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint({ title: '✅ 批处理完成', indicator: 'green', message: r.message.message });
                            load_qifu_employees();
                            load_social_insurance_tab();
                        }
                    }
                });
            }
        );
    });

    $container.on("click", "#btn-qifu-hf-min, #btn-tab4-hf-min", function() {
        frappe.confirm(
            `<strong>【⚡ 一键全员公积金 (最低基数)】</strong><br><br>
            规则说明：<br>
            1. <strong>资格条件</strong>：仅对【社保基数 > 0】的在保员工生效，一键设为最低基数 (2320 元)；<br>
            2. <strong>未参保跳过</strong>：社保基数为 0 的人员将自动跳过并保持 0 元；<br>
            3. <span style="color: #15803d; font-weight: 600;">🛡️ 核心豁免：员工【孟祥山】受最高保护，绝不被修改并保留原有基数！</span><br><br>
            确认执行吗？`,
            function() {
                frappe.call({
                    method: 'ashan_cn_procurement.services.employee_salary_service.set_qifu_housing_fund_batch',
                    args: { mode: 'min' },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint({ title: '✅ 批处理完成', indicator: 'green', message: r.message.message });
                            load_qifu_employees();
                            load_housing_fund_tab();
                        }
                    }
                });
            }
        );
    });

    $container.on("click", "#btn-qifu-hf-zero, #btn-tab4-hf-zero", function() {
        frappe.confirm(
            `<strong>【🚫 一键取消全员公积金 (设为0)】</strong><br><br>将一键把在保员工公积金基数清零 (0 元)。<br><br><span style="color: #15803d; font-weight: 600;">🛡️ 核心保护：员工【孟祥山】将自动豁免，不受任何影响并保留其原有基数！</span><br><br>确认执行吗？`,
            function() {
                frappe.call({
                    method: 'ashan_cn_procurement.services.employee_salary_service.set_qifu_housing_fund_batch',
                    args: { mode: 'zero' },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint({ title: '✅ 批处理完成', indicator: 'green', message: r.message.message });
                            load_qifu_employees();
                            load_housing_fund_tab();
                        }
                    }
                });
            }
        );
    });

    // 6. Tab 2 外部文件上传与 24 列发放表交互 (统一使用 execute_qifu_salary_upload 核心引擎)
    let current_selected_file_b64 = null;
    let current_selected_file_name = null;

    $container.on("change", "#qifu-file-input-tab2", function(e) {
        const file = e.target.files[0];
        if (!file) return;
        current_selected_file_name = file.name;
        $("#qifu-filename-display-tab2").text(`📄 已选择: ${file.name}`);

        const reader = new FileReader();
        reader.onload = function(evt) {
            const raw_b64 = evt.target.result;
            current_selected_file_b64 = raw_b64;
            $("#qifu-import-preview-tab2").show();
            $("#qifu-import-badge-tab2").html(
                `<div style="display:flex; align-items:center; justify-content:space-between;">
                    <span>🔍 正在智能预检【<strong>${file.name}</strong>】...</span>
                 </div>`
            );

            frappe.call({
                method: 'ashan_cn_procurement.services.payroll_settlement_service.preview_import_excel_data',
                type: 'POST',
                args: {
                    file_name: current_selected_file_name,
                    file_base64: current_selected_file_b64
                },
                callback: function(res) {
                    if (res.message && res.message.success) {
                        const m = res.message;
                        $("#qifu-import-badge-tab2").html(
                            `<strong>✅ 预检通过！</strong> 探测发薪账期：<span style="color:#15803d; font-weight:800;">${m.detected_period_month || m.detected_month || current_month}</span> · 识别在册员工：<strong>${m.employee_count}</strong> 人 · 外部实发总盘：<strong>¥ ${Number(m.net_salary_total || 0).toLocaleString('zh-CN', {minimumFractionDigits:2})}</strong>`
                        );
                        if (m.detected_period_month) {
                            current_month = m.detected_period_month;
                            $("#qifu-month-select").val(current_month);
                        }
                    } else {
                        const err = (res.message && res.message.message) || '预检 Excel 文件失败，请检查文件格式！';
                        $("#qifu-import-badge-tab2").html(
                            `<span style="color:#dc2626; font-weight:700;">❌ 预检失败：${err}</span>`
                        );
                    }
                },
                error: function(res) {
                    let error_msg = '预检 Excel 文件时发生异常！';
                    if (res && res._server_messages) {
                        try {
                            const msgs = JSON.parse(res._server_messages);
                            error_msg = msgs.map(m => {
                                try { return JSON.parse(m).message; } catch(e) { return m; }
                            }).join('<br>');
                        } catch(e) {}
                    } else if (res && res.exc) {
                        error_msg = res.exc.split('\n').filter(Boolean).pop() || res.exc;
                    }
                    $("#qifu-import-badge-tab2").html(
                        `<span style="color:#dc2626; font-weight:700;">❌ 预检失败：${error_msg}</span>`
                    );
                }
            });
        };
        reader.onerror = function() {
            frappe.msgprint({
                title: '❌ 读取文件失败',
                indicator: 'red',
                message: `无法读取本地文件【${file.name}】，请检查文件是否被占用或损坏！`
            });
        };
        reader.readAsDataURL(file);
    });

    $container.on("click", "#btn-import-confirm-tab2", function() {
        if (!current_selected_file_b64) {
            frappe.msgprint({
                title: '❌ 未选择文件',
                indicator: 'orange',
                message: '文件尚未读取完成或未选择有效文件，请点击上方区域重新选择！'
            });
            return;
        }

        const $btn = $(this);
        $btn.prop('disabled', true).text('⏳ 正在导入并核算...');
        const cur_m = $("#qifu-month-select").val() || current_month;

        execute_qifu_salary_upload(current_selected_file_b64, current_selected_file_name, cur_m, function(success) {
            $btn.prop('disabled', false).text('⚡ 立即导入并融合核算 (生成24列薪资发放表)');
            if (success) {
                $("#qifu-import-preview-tab2").hide();
                current_selected_file_b64 = null;
                current_selected_file_name = null;
                $("#qifu-filename-display-tab2").text("点击或将车间实发 Excel 文件拖拽至此处上传");
                $("#qifu-file-input-tab2").val('');
            }
        });
    });

    $container.on("click", "#btn-import-cancel-tab2", function() {
        current_selected_file_b64 = null;
        current_selected_file_name = null;
        $("#qifu-filename-display-tab2").text("点击或将车间实发 Excel 文件拖拽至此处上传");
        $("#qifu-import-preview-tab2").hide();
        $("#qifu-file-input-tab2").val('');
    });

    $container.on("click", "#btn-tab2-export-dist", function() { export_excel_action("distribution"); });
    $container.on("click", "#btn-tab2-print-dist", function() {
        print_modal_report(`【${COMPANY}】${current_month} 薪资发放表`, `发薪所属账期: ${current_month}`, "table-tab2-dist-sheet");
    });

    // 7. 社保/公积金 Tab 导出、打印与配置修改
    $container.on("click", "#btn-qifu-edit-ss-setting, #btn-qifu-edit-hf-setting, #btn-qifu-edit-tax-setting", function() {
        open_insurance_edit_dialog();
    });
    $container.on("click", "#btn-tab3-export-ss", function() { export_excel_action("insurance"); });
    $container.on("click", "#btn-tab3-print-ss", function() {
        print_modal_report(`【${COMPANY}】社会保险缴费明细表`, `核定发薪账期: ${current_month}`, "table-tab3-ss-sheet");
    });
    $container.on("click", "#btn-tab3-add-ss-adj", function() { open_add_insurance_adjustment_dialog(); });

    $container.on("click", "#btn-tab4-export-hf", function() { export_excel_action("housing_fund"); });
    $container.on("click", "#btn-tab4-print-hf", function() {
        print_modal_report(`【${COMPANY}】住房公积金缴存明细表`, `核定发薪账期: ${current_month}`, "table-tab4-hf-sheet");
    });

    // 8. Tab 5 个税操作
    
    // 动态视口自适应高度计算引擎 (固定上部，动态下部，彻底锁定滚动条在屏幕可见区)
    function adjust_active_table_height() {
        $(".qifu-tab-content:visible").each(function() {
            const $box = $(this).find(".qifu-table-box");
            if (!$box.length || !$box.is(':visible')) return;
            const topOffset = $box[0].getBoundingClientRect().top;
            const winH = window.innerHeight;
            const bottomMargin = 16;
            const availableH = winH - topOffset - bottomMargin;
            const finalH = Math.max(300, Math.floor(availableH));

            $box.css({
                "height": finalH + "px",
                "max-height": finalH + "px",
                "overflow-y": "auto",
                "overflow-x": "auto",
                "margin-bottom": "0px"
            });
        });
    }

    // 窗口尺寸变化与防抖自适应
    let resizeTimer = null;
    $(window).off("resize.qifu").on("resize.qifu", function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(adjust_active_table_height, 100);
    });

    // 双向滚动条同步引擎 (顶部滑条 <-> 底部表格)
    function sync_dual_scrollbars($topWrapper, $tableBox) {
        adjust_active_table_height();
        if (!$topWrapper.length || !$tableBox.length) return;
        const $table = $tableBox.find("table");
        const scrollW = $table.length ? $table[0].scrollWidth : $tableBox[0].scrollWidth;
        $topWrapper.find(".qifu-top-scrollbar-dummy").css("width", scrollW + "px");

        let isSyncingTop = false;
        let isSyncingBottom = false;

        $topWrapper.off("scroll.sync").on("scroll.sync", function() {
            if (!isSyncingTop) {
                isSyncingBottom = true;
                $tableBox.scrollLeft($(this).scrollLeft());
            }
            isSyncingTop = false;
        });

        $tableBox.off("scroll.sync").on("scroll.sync", function() {
            if (!isSyncingBottom) {
                isSyncingTop = true;
                $topWrapper.scrollLeft($(this).scrollLeft());
            }
            isSyncingBottom = false;
        });
    }

    // 快捷横向滑动按钮
    $container.on("click", ".btn-qifu-scroll-left", function() {
        const targetSel = $(this).attr("data-target") || "#tab5-table-box";
        $(targetSel).stop().animate({ scrollLeft: 0 }, 300);
        $("#tab5-top-scrollbar").stop().animate({ scrollLeft: 0 }, 300);
    });

    $container.on("click", ".btn-qifu-scroll-right", function() {
        const targetSel = $(this).attr("data-target") || "#tab5-table-box";
        const $target = $(targetSel);
        const maxScroll = $target[0].scrollWidth || 3000;
        $target.stop().animate({ scrollLeft: maxScroll }, 400);
        $("#tab5-top-scrollbar").stop().animate({ scrollLeft: maxScroll }, 400);
    });

    // 表头横向滚轮穿透支持
    $container.on("wheel", ".qifu-table thead, .qifu-top-scrollbar-wrapper", function(e) {
        if (e.originalEvent.deltaY !== 0 && e.originalEvent.deltaX === 0) {
            e.preventDefault();
            const $box = $(this).closest(".qifu-tab-content").find(".qifu-table-box");
            $box.scrollLeft($box.scrollLeft() + e.originalEvent.deltaY);
        }
    });

    $container.on("click", ".btn-tax-view-mode", function() {
        $(".btn-tax-view-mode").removeClass("active").css({"background": "#fff", "color": "#334155", "border-color": "#cbd5e1"});
        $(this).addClass("active").css({"background": "#2563eb", "color": "#fff", "border-color": "#2563eb"});
        current_tax_view_mode = $(this).attr("data-mode");
        load_tax_settlement_tab();
    });

    $container.on("click", "#btn-tab5-recalc-tax", function() {
        load_tax_settlement_tab();
        frappe.show_alert({ message: '✅ 个税台账已依据最新社保公积金与专项附加扣除重新核定完成！', indicator: 'green' });
    });
    $container.on("click", "#btn-tab5-export-tax", function() { export_excel_action("tax"); });
    $container.on("click", "#btn-tab5-print-tax", function() {
        print_modal_report(`【${COMPANY}】个人所得税核定与申报明细表`, `核定发薪账期: ${current_month}`, "table-tab5-tax-sheet");
    });

    // 9. Tab 6 综合核定操作
    $container.on("click", "#btn-qifu-calc-payroll", function() {
        frappe.call({
            method: 'ashan_cn_procurement.services.payroll_settlement_service.calculate_and_generate_payroll',
            args: { company: COMPANY, period_month: current_month },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({ message: r.message.message, indicator: 'green' });
                    render_payroll_view(r.message.doc);
                }
            }
        });
    });
    $container.on("click", "#btn-view-salary-dist", function() { open_salary_distribution_modal(); });
    $container.on("click", "#btn-view-acc-sheet", function() { open_accounting_sheet_modal(); });
    $container.on("click", "#btn-view-ins-sheet-modal", function() { open_social_insurance_modal(); });
    $container.on("click", "#btn-view-hf-sheet-modal", function() { open_housing_fund_modal(); });
    $container.on("click", "#btn-view-tax-sheet-modal", function() { open_tax_modal(); });
    $container.on("click", "#btn-export-excel-both", function() { export_excel_action("all"); });

    // 全局委派模态框事件
    $(document).off("click", "#btn-modal-export-dist").on("click", "#btn-modal-export-dist", function() { export_excel_action("distribution"); });
    $(document).off("click", "#btn-modal-print-dist").on("click", "#btn-modal-print-dist", function() {
        print_modal_report(`【${COMPANY}】${current_month} 薪资发放表`, `所属发薪账期: ${current_month}`, "table-modal-dist-sheet");
    });
    $(document).off("click", "#btn-modal-export-acc").on("click", "#btn-modal-export-acc", function() { export_excel_action("accounting"); });
    $(document).off("click", "#btn-modal-print-acc").on("click", "#btn-modal-print-acc", function() {
        print_modal_report(`【${COMPANY}】${current_month} 记账工资表`, `所属发薪账期: ${current_month}`, "table-modal-acc-sheet");
    });
    $(document).off("click", "#btn-modal-export-ins").on("click", "#btn-modal-export-ins", function() { export_excel_action("insurance"); });
    $(document).off("click", "#btn-modal-print-ins").on("click", "#btn-modal-print-ins", function() {
        print_modal_report(`【${COMPANY}】社会保险缴费明细表`, `核定发薪账期: ${current_month}`, "table-modal-ins-sheet");
    });
    $(document).off("click", "#btn-modal-export-hf").on("click", "#btn-modal-export-hf", function() { export_excel_action("housing_fund"); });
    $(document).off("click", "#btn-modal-print-hf").on("click", "#btn-modal-print-hf", function() {
        print_modal_report(`【${COMPANY}】住房公积金缴存明细表`, `核定发薪账期: ${current_month}`, "table-modal-hf-sheet");
    });
    $(document).off("click", "#btn-modal-export-tax").on("click", "#btn-modal-export-tax", function() { export_excel_action("tax"); });
    $(document).off("click", "#btn-modal-print-tax").on("click", "#btn-modal-print-tax", function() {
        print_modal_report(`【${COMPANY}】个人所得税核定明细表`, `核定发薪账期: ${current_month}`, "table-modal-tax-sheet");
    });
    $(document).off("click", "#btn-modal-add-ss-adj").on("click", "#btn-modal-add-ss-adj", function() {
        open_add_insurance_adjustment_dialog();
    });

    // 删除特殊补缴
    $(document).off("click", ".btn-del-ss-adj").on("click", ".btn-del-ss-adj", function() {
        const adj_id = $(this).attr("data-id");
        if (!adj_id) return;
        frappe.confirm("确认要删除这笔社保特殊补缴/滞纳金记录吗？", function() {
            frappe.call({
                method: 'ashan_cn_procurement.services.payroll_settlement_service.delete_social_insurance_adjustment',
                args: { company: COMPANY, period_month: current_month, adj_id: adj_id },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({ message: r.message.message, indicator: 'green' });
                        load_social_insurance_tab();
                        load_tax_settlement_tab();
                        load_payroll_settlement();
                    }
                }
            });
        });
    });

    // 初始化默认加载 Tab 1 (母表底册) 与月度任务看板
    load_qifu_employees();
    load_monthly_workflow_hub();
};