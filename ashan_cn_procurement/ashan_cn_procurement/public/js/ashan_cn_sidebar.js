// Copyright (c) 2026, Ashan CN Procurement
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
                var route = href.replace(/^\/(desk|app)\//, '');
                if (route && window.frappe && frappe.set_route) {
                    e.preventDefault();
                    e.stopPropagation();
                    frappe.set_route(route);
                }
            }
        });
    }
})();
