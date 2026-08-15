# Copyright (c) 2026, Ashan CN Procurement and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from ashan_cn_procurement.reimbursement.service import (
    release_all_reservations,
    release_removed_reservations,
    reserve_request_sources,
)


class ReimbursementRequest(Document):
    def validate(self):
        self._update_totals()
        if not self.is_new():
            release_removed_reservations(self)

    def on_trash(self):
        release_all_reservations(self)

    def after_insert(self):
        reserve_request_sources(self)

    def on_update(self):
        reserve_request_sources(self)

    def _update_totals(self):
        total = sum(frappe.utils.flt(row.amount) for row in self.get("invoice_items"))
        self.total_amount = total
        self.outstanding_amount = total
        self.paid_amount = 0
        if not self.payment_status:
            self.payment_status = "未付款"
