import os

search_paths = [
    r"d:\SynologyDrive团队\antigravity\erpnext16",
    r"C:\Users\ashan\.gemini\antigravity"
]

clean_js = """// Copyright (c) 2026, Ashan CN Procurement
// Pure SPA Navigation Click Interceptor & Legacy DOM Purge

(function() {
    // 1. Immediately hide and destroy legacy DOM containers
    function purge_legacy() {
        window.init_ashan_cn_sidebar = function() { return false; };
        if (typeof $ !== 'undefined') {
            $('#ashan-cn-sidebar-container, .ashan-sidebar-wrapper').remove();
        }
    }
    purge_legacy();
    if (typeof $ !== 'undefined') {
        $(document).ready(purge_legacy);
        $(document).on('app_ready page-change route-change toolbar_setup', purge_legacy);
    }
    setInterval(purge_legacy, 100);

    // 2. Intercept clicks on sidebar workspace links to prevent full page reloads
    if (typeof $ !== 'undefined') {
        $(document).on('click', '.body-sidebar a, .desk-sidebar a, .layout-side-section a', function(e) {
            var href = $(this).attr('href');
            if (!href) return;
            if ($(this).attr('target') === '_blank' || href.includes('/api/') || href.includes('/files/')) return;
            
            if (href.startsWith('/desk/') || href.startsWith('/app/')) {
                var route = href.replace(/^\\/(desk|app)\\//, '');
                if (route && window.frappe && frappe.set_route) {
                    e.preventDefault();
                    e.stopPropagation();
                    frappe.set_route(route);
                }
            }
        });
    }
})();
"""

overwritten_count = 0
for sp in search_paths:
    for root, dirs, files in os.walk(sp):
        for f in files:
            if f == 'ashan_cn_sidebar.js':
                full_path = os.path.join(root, f)
                print("Overwriting ashan_cn_sidebar.js at:", full_path)
                with open(full_path, "w", encoding="utf-8") as file:
                    file.write(clean_js)
                overwritten_count += 1

print(f"Done! Overwrote {overwritten_count} copies of ashan_cn_sidebar.js.")

