# -*- coding: utf-8 -*-
ps1_content = '''Start-Process -FilePath "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" -ArgumentList '--remote-debugging-port=9222', '--user-data-dir="C:\\edge_debug_profile"', 'http://192.168.8.11:6888/desk/my-business'
'''

with open(r'd:\SynologyDrive团队\antigravity\erpnext16\启动Edge调试模式.ps1', 'w', encoding='utf-8') as f:
    f.write(ps1_content)

print("[OK] Created 启动Edge调试模式.ps1")
