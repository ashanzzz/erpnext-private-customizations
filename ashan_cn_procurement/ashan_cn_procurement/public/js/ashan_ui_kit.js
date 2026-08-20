// Copyright (c) 2026, Ashan CN Procurement and contributors
// AshanUI Kit - 全局企业级标准交互与样式模块库

(function () {
    "use strict";

    if (window.AshanUI) return;

    window.AshanUI = {
        version: "1.0.0",

        /**
         * 1. 统一标准金额格式化
         * @param {number|string} amount 金额数值
         * @param {boolean} withSymbol 是否带人民币符号 ¥ (默认 true)
         * @param {string} suffix 后缀单位 (例如 "元" 或 "")
         * @returns {string} 格式化后的金额字符串
         */
        formatMoney: function (amount, withSymbol = true, suffix = "") {
            const val = parseFloat(amount);
            if (isNaN(val)) return withSymbol ? "¥ 0.00" : "0.00";
            const formatted = val.toLocaleString("zh-CN", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            });
            const prefix = withSymbol ? "¥ " : "";
            const sfx = suffix ? (suffix.startsWith(" ") ? suffix : ` ${suffix}`) : "";
            return `${prefix}${formatted}${sfx}`;
        },

        /**
         * 2. 稳态防抖自动保存指示胶囊 (彻底消除文字抖动与布局位移)
         * @param {jQuery|HTMLElement|string} container 容器元素
         * @param {Object} options 配置项
         * @returns {Object} 控制器对象 { setSaving, setSaved, setDraft, setLocked, setError }
         */
        createSaveIndicator: function (container, options = {}) {
            const $el = $(container);
            $el.empty();

            const defaultText = options.initialText || "草稿就绪";
            const $capsule = $(`
                <div class="ashan-save-indicator state-draft" title="自动保存状态">
                    <span class="indicator-dot"></span>
                    <span class="indicator-text">${defaultText}</span>
                    <span class="indicator-time"></span>
                </div>
            `);
            $el.append($capsule);

            const $text = $capsule.find(".indicator-text");
            const $time = $capsule.find(".indicator-time");

            return {
                setSaving: function (msg = "正在保存...") {
                    $capsule.attr("class", "ashan-save-indicator state-saving");
                    $text.text(msg);
                    $time.text("");
                },
                setSaved: function (timeStr) {
                    $capsule.attr("class", "ashan-save-indicator state-saved");
                    $text.text("已自动保存");
                    if (!timeStr) {
                        const now = new Date();
                        timeStr = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}:${String(now.getSeconds()).padStart(2, "0")}`;
                    }
                    $time.text(timeStr);
                },
                setDraft: function (msg = "草稿录入中") {
                    $capsule.attr("class", "ashan-save-indicator state-draft");
                    $text.text(msg);
                    $time.text("");
                },
                setLocked: function (msg = "已核定锁定") {
                    $capsule.attr("class", "ashan-save-indicator state-locked");
                    $text.text(msg);
                    $time.text("");
                },
                setError: function (msg = "保存异常") {
                    $capsule.attr("class", "ashan-save-indicator state-error");
                    $text.text(msg);
                    $time.text("");
                },
            };
        },

        /**
         * 3. 统一标准年月/账期选择器组件 (Year-Month Navigator)
         * @param {jQuery|HTMLElement|string} container 容器元素
         * @param {Object} options 配置项 { currentYear, currentMonth, minYear, maxYear, onChange }
         * @returns {Object} 控制器对象
         */
        renderPeriodSelector: function (container, options = {}) {
            const $el = $(container);
            $el.empty();

            const now = new Date();
            let year = parseInt(options.currentYear || now.getFullYear(), 10);
            let month = parseInt(options.currentMonth || now.getMonth() + 1, 10);
            const minYear = options.minYear || 2024;
            const maxYear = options.maxYear || 2030;

            let yearOptions = "";
            for (let y = minYear; y <= maxYear; y++) {
                yearOptions += `<option value="${y}" ${y === year ? "selected" : ""}>${y}年</option>`;
            }

            let monthOptions = "";
            for (let m = 1; m <= 12; m++) {
                monthOptions += `<option value="${m}" ${m === month ? "selected" : ""}>${String(m).padStart(2, "0")}月</option>`;
            }

            const $picker = $(`
                <div class="ashan-period-navigator">
                    <button class="ashan-nav-btn btn-prev" title="上一月 (快捷键: Alt+←)">‹</button>
                    <div class="ashan-period-select-wrap">
                        <select class="ashan-period-select sel-year">${yearOptions}</select>
                        <select class="ashan-period-select sel-month">${monthOptions}</select>
                    </div>
                    <button class="ashan-nav-btn btn-next" title="下一月 (快捷键: Alt+→)">›</button>
                    <button class="ashan-nav-today-btn btn-today" title="回到当月">本月</button>
                </div>
            `);
            $el.append($picker);

            function emitChange() {
                if (typeof options.onChange === "function") {
                    options.onChange(year, month);
                }
            }

            $picker.find(".btn-prev").on("click", function () {
                month -= 1;
                if (month < 1) {
                    month = 12;
                    year -= 1;
                }
                $picker.find(".sel-year").val(year);
                $picker.find(".sel-month").val(month);
                emitChange();
            });

            $picker.find(".btn-next").on("click", function () {
                month += 1;
                if (month > 12) {
                    month = 1;
                    year += 1;
                }
                $picker.find(".sel-year").val(year);
                $picker.find(".sel-month").val(month);
                emitChange();
            });

            $picker.find(".btn-today").on("click", function () {
                const cur = new Date();
                year = cur.getFullYear();
                month = cur.getMonth() + 1;
                $picker.find(".sel-year").val(year);
                $picker.find(".sel-month").val(month);
                emitChange();
            });

            $picker.find(".sel-year, .sel-month").on("change", function () {
                year = parseInt($picker.find(".sel-year").val(), 10);
                month = parseInt($picker.find(".sel-month").val(), 10);
                emitChange();
            });

            return {
                getYear: () => year,
                getMonth: () => month,
                getYearMonthString: () => `${year}-${String(month).padStart(2, "0")}`,
                setPeriod: function (newYear, newMonth, triggerChange = false) {
                    year = parseInt(newYear, 10);
                    month = parseInt(newMonth, 10);
                    $picker.find(".sel-year").val(year);
                    $picker.find(".sel-month").val(month);
                    if (triggerChange) emitChange();
                },
            };
        },

        /**
         * 4. 统一公司/实体切换胶囊栏
         * @param {jQuery|HTMLElement|string} container 容器元素
         * @param {Object} options 配置项 { tabs: [{ id, label, badge, color }], activeTab, onChange }
         */
        renderEntityTabs: function (container, options = {}) {
            const $el = $(container);
            $el.empty();

            const tabs = options.tabs || [];
            let activeTab = options.activeTab || (tabs[0] ? tabs[0].id : "");

            const $tabsWrap = $('<div class="ashan-entity-tabs"></div>');
            tabs.forEach((tab) => {
                const isActive = tab.id === activeTab;
                const badgeHtml = tab.badge ? `<span class="tab-badge">${tab.badge}</span>` : "";
                const $btn = $(`
                    <button class="ashan-entity-tab-btn ${isActive ? "active" : ""}" data-id="${tab.id}">
                        <span class="tab-label">${tab.label}</span>
                        ${badgeHtml}
                    </button>
                `);
                $tabsWrap.append($btn);
            });

            $el.append($tabsWrap);

            $tabsWrap.on("click", ".ashan-entity-tab-btn", function () {
                const id = $(this).data("id");
                $tabsWrap.find(".ashan-entity-tab-btn").removeClass("active");
                $(this).addClass("active");
                activeTab = id;
                if (typeof options.onChange === "function") {
                    options.onChange(id);
                }
            });

            return {
                getActiveTab: () => activeTab,
                setActiveTab: function (id, triggerChange = false) {
                    activeTab = id;
                    $tabsWrap.find(".ashan-entity-tab-btn").removeClass("active");
                    $tabsWrap.find(`.ashan-entity-tab-btn[data-id="${id}"]`).addClass("active");
                    if (triggerChange && typeof options.onChange === "function") {
                        options.onChange(id);
                    }
                },
            };
        },

        /**
         * 5. 统一页面级快捷键绑定支持 (Ctrl+S / Cmd+S 保存, Esc 关闭等)
         * @param {Object} handlers { onSave, onEsc, onPrevMonth, onNextMonth }
         */
        bindGlobalHotkeys: function (handlers = {}) {
            $(document).off("keydown.ashanHotkeys").on("keydown.ashanHotkeys", function (e) {
                // Ctrl+S / Cmd+S 保存草稿
                if ((e.ctrlKey || e.metaKey) && (e.key === "s" || e.key === "S")) {
                    e.preventDefault();
                    if (typeof handlers.onSave === "function") {
                        handlers.onSave();
                    }
                }
                // ESC 取消
                if (e.key === "Escape") {
                    if (typeof handlers.onEsc === "function") {
                        handlers.onEsc();
                    }
                }
            });
        },
    };
})();
