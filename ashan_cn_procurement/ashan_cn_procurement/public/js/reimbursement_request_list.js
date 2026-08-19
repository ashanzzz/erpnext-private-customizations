/* ==========================================================================
   报销申请列表页定制 (Reimbursement Request List View)
   ========================================================================== */

frappe.listview_settings['Reimbursement Request'] = {
    add_fields: ["custom_doc_details", "title", "applicant", "posting_date", "total_tax_inclusive_amount", "status"],

    formatters: {
        custom_doc_details: function(value, df, doc) {
            if (typeof ashan !== 'undefined' && ashan.doc_details && ashan.doc_details.render_badges) {
                return ashan.doc_details.render_badges(value);
            }
            return value || "";
        }
    }
};
