// Copyright (c) 2026, Ashan CN Procurement
// Direct post-login landing route from /desk to /app/my-business Dashboard Workspace

(function() {
    function redirect_desk_to_dashboard() {
        var path = window.location.pathname.toLowerCase();
        if (path === '/desk' || path === '/desk/' || path === '/desk#') {
            console.log('[Ashan CN Boot] Redirecting /desk landing to /app/my-business...');
            window.location.replace('/app/my-business');
        } else if (window.frappe && frappe.get_route_str) {
            var route = frappe.get_route_str().toLowerCase();
            if (!route || route === '' || route === 'desk' || route === 'app') {
                frappe.set_route('my-business');
            }
        }
    }

    // Execute immediately on script parse
    redirect_desk_to_dashboard();

    // Bind to DOM ready & Frappe events
    if (typeof $ !== 'undefined') {
        $(document).on('app_ready route-change page-change', redirect_desk_to_dashboard);
        $(document).ready(redirect_desk_to_dashboard);
    }
})();
