import os
import sys

pkg_dir = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement"
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

import ashan_cn_procurement.boot as boot

class DummyLoginManager:
    def __init__(self):
        self.home_page = None

lm = DummyLoginManager()
class DummyLocal:
    response = {}

import frappe
frappe.local = DummyLocal()

boot.set_login_redirect(lm)
print("Dummy LoginManager home_page:", lm.home_page)
print("frappe.local.response home_page:", frappe.local.response.get("home_page"))

