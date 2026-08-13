#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ERPNext 16 & ashan_cn_procurement App 管理与调试 CLI 工具
用法示例:
    python manage_app.py status                # 查看站点连接与 App 状态
    python manage_app.py pull                  # 从远程站点拉取/同步最新 DocType 与 Report 架构
    python manage_app.py test-api              # 执行 REST API 接口健康度与权限测试
    python manage_app.py push-js "Oil Card"    # 将本地 oil_card.js 推送至远程站点为 Client Script
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import shutil

sys.stdout.reconfigure(encoding='utf-8')

# 内置纯 Python 手动解析 .env 文件
def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
TOKEN = os.getenv('ERPNEXT_TOKEN', 'token 781e6538a0816f3:ebfe8d61c03e289')
APP_NAME = os.getenv('ERPNEXT_APP_NAME', 'ashan_cn_procurement')

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_PACKAGE_DIR = os.path.join(ROOT_DIR, 'ashan_cn_procurement', 'ashan_cn_procurement')
DOCTYPE_DIR = os.path.join(APP_PACKAGE_DIR, 'doctype')
REPORT_DIR = os.path.join(APP_PACKAGE_DIR, 'report')


def call_api(endpoint, method='GET', data=None):
    headers = {
        'Authorization': TOKEN,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    req_url = f"{SITE_URL.rstrip('/')}{endpoint}"
    encoded_data = json.dumps(data).encode('utf-8') if data else None
    
    req = urllib.request.Request(req_url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8')
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"[API Error] HTTP {e.code} on {method} {endpoint}")
        try:
            err_json = json.loads(err_body)
            if 'exception' in err_json:
                print(f"  Exception: {err_json['exception']}")
        except Exception:
            print(f"  Raw response: {err_body[:200]}")
        return None
    except Exception as e:
        print(f"[Network Error] {e}")
        return None


def cmd_status():
    print("=" * 60)
    print(" ERPNext 16 站点与 App 状态查看")
    print("=" * 60)
    print(f"站点 URL: {SITE_URL}")
    print(f"当前 App 名: {APP_NAME}")
    
    # 1. 测试连接与获取当前用户
    user_res = call_api('/api/method/frappe.auth.get_logged_user')
    if user_res and 'message' in user_res:
        print(f"当前认证用户: {user_res['message']}")
    else:
        print("警告: 无法验证当前用户，请检查 .env 中的 ERPNEXT_TOKEN 配置")
        return

    # 2. 获取已安装 App 列表与版本
    versions_res = call_api('/api/method/frappe.utils.change_log.get_versions')
    if versions_res and 'message' in versions_res:
        print("\n已安装应用列表:")
        for app, info in versions_res['message'].items():
            print(f"  - {app:<22} v{info.get('version'):<10} {info.get('title')}")
            
    # 3. 本地 DocType 统计
    if os.path.exists(DOCTYPE_DIR):
        doctypes = [d for d in os.listdir(DOCTYPE_DIR) if os.path.isdir(os.path.join(DOCTYPE_DIR, d))]
        print(f"\n本地 DocType 数量: {len(doctypes)} 个")
        for dt in doctypes:
            print(f"  * {dt}")
    else:
        print("\n本地尚未生成 DocType 目录 Structure")


WORKSPACE_DIR = os.path.join(APP_PACKAGE_DIR, 'workspace')
CUSTOM_DIR = os.path.join(APP_PACKAGE_DIR, 'custom')

def cmd_pull():
    print("=" * 60)
    print(" 从 ERPNext 站点同步/拉取 ashan_cn_procurement 最新架构与配置")
    print("=" * 60)
    
    # 查找 Ashan CN Procurement 模块下所有 Module Def
    modules_data = call_api('/api/resource/Module%20Def?fields=["name","app_name"]&limit_page_length=500')
    if not modules_data or 'data' not in modules_data:
        print("错误: 无法读取 Module Def 列表")
        return
        
    ashan_modules = [m['name'] for m in modules_data['data'] if m.get('app_name') == 'ashan_cn_procurement']
    if not ashan_modules:
        ashan_modules = ['Ashan CN Procurement']
    print(f"识别到的 App 模块名: {ashan_modules}")
    
    # 1. 读取并拉取 DocType 列表
    doctypes_data = call_api('/api/resource/DocType?fields=["name","module"]&limit_page_length=1000')
    if doctypes_data and 'data' in doctypes_data:
        app_doctypes = [d['name'] for d in doctypes_data['data'] if d.get('module') in ashan_modules]
        print(f"\n[DocType] 找到 {len(app_doctypes)} 个 App 所属 DocType")
        os.makedirs(DOCTYPE_DIR, exist_ok=True)
        
        for dt_name in app_doctypes:
            encoded = urllib.parse.quote(dt_name)
            dt_res = call_api(f'/api/resource/DocType/{encoded}')
            if dt_res and 'data' in dt_res:
                folder = dt_name.lower().replace(' ', '_')
                dt_folder_path = os.path.join(DOCTYPE_DIR, folder)
                os.makedirs(dt_folder_path, exist_ok=True)
                
                # 写入 json
                with open(os.path.join(dt_folder_path, f"{folder}.json"), 'w', encoding='utf-8') as f:
                    json.dump(dt_res['data'], f, ensure_ascii=False, indent=2)
                    
                # Python 模板
                py_file = os.path.join(dt_folder_path, f"{folder}.py")
                if not os.path.exists(py_file):
                    cls_name = dt_name.replace(' ', '')
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(f"# Copyright (c) 2026, Ashan CN Procurement and contributors\nimport frappe\nfrom frappe.model.document import Document\n\nclass {cls_name}(Document):\n\tpass\n")
                        
                # JS 模板
                js_file = os.path.join(dt_folder_path, f"{folder}.js")
                if not os.path.exists(js_file):
                    with open(js_file, 'w', encoding='utf-8') as f:
                        f.write(f"// Copyright (c) 2026, Ashan CN Procurement and contributors\n// frappe.ui.form.on('{dt_name}', {{\n// \trefresh(frm) {{\n// \t}}\n// }});\n")
                        
                print(f"  [OK] Synced DocType: {dt_name}")

    # 2. 读取并拉取 Report 列表
    reports_data = call_api('/api/resource/Report?fields=["name","module"]&limit_page_length=1000')
    if reports_data and 'data' in reports_data:
        app_reports = [r['name'] for r in reports_data['data'] if r.get('module') in ashan_modules]
        print(f"\n[Report] 找到 {len(app_reports)} 个 App 所属 Report")
        os.makedirs(REPORT_DIR, exist_ok=True)
        
        for r_name in app_reports:
            encoded = urllib.parse.quote(r_name)
            r_res = call_api(f'/api/resource/Report/{encoded}')
            if r_res and 'data' in r_res:
                folder = r_name.lower().replace(' ', '_')
                r_folder_path = os.path.join(REPORT_DIR, folder)
                os.makedirs(r_folder_path, exist_ok=True)
                
                with open(os.path.join(r_folder_path, f"{folder}.json"), 'w', encoding='utf-8') as f:
                    json.dump(r_res['data'], f, ensure_ascii=False, indent=2)
                print(f"  [OK] Synced Report: {r_name}")

    # 3. 读取并拉取 Workspace 列表
    workspaces_data = call_api('/api/resource/Workspace?fields=["name","module","public"]&limit_page_length=1000')
    if workspaces_data and 'data' in workspaces_data:
        app_workspaces = [w['name'] for w in workspaces_data['data'] if w.get('module') in ashan_modules and w.get('public')]
        print(f"\n[Workspace] 找到 {len(app_workspaces)} 个 App 公共 Workspace")
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        
        for ws_name in app_workspaces:
            encoded = urllib.parse.quote(ws_name)
            ws_res = call_api(f'/api/resource/Workspace/{encoded}')
            if ws_res and 'data' in ws_res:
                folder = ws_name.lower().replace(' ', '_')
                ws_folder_path = os.path.join(WORKSPACE_DIR, folder)
                os.makedirs(ws_folder_path, exist_ok=True)
                
                with open(os.path.join(ws_folder_path, f"{folder}.json"), 'w', encoding='utf-8') as f:
                    json.dump(ws_res['data'], f, ensure_ascii=False, indent=2)
                print(f"  [OK] Synced Workspace: {ws_name}")

    # 4. 读取并拉取 Client Scripts & Server Scripts
    client_scripts = call_api('/api/resource/Client%20Script?fields=["name","dt","enabled"]&limit_page_length=100')
    if client_scripts and 'data' in client_scripts:
        cs_dir = os.path.join(CUSTOM_DIR, 'client_script')
        os.makedirs(cs_dir, exist_ok=True)
        ashan_cs = [c['name'] for c in client_scripts['data'] if 'Ashan' in c['name'] or 'Global Desk' in c['name']]
        print(f"\n[Client Script] 找到 {len(ashan_cs)} 个相关 Client Script")
        for cs_name in ashan_cs:
            encoded = urllib.parse.quote(cs_name)
            cs_res = call_api(f'/api/resource/Client%20Script/{encoded}')
            if cs_res and 'data' in cs_res:
                fname = cs_name.lower().replace(' ', '_') + '.json'
                with open(os.path.join(cs_dir, fname), 'w', encoding='utf-8') as f:
                    json.dump(cs_res['data'], f, ensure_ascii=False, indent=2)
                print(f"  [OK] Synced Client Script: {cs_name}")

    server_scripts = call_api('/api/resource/Server%20Script?fields=["name","script_type","disabled"]&limit_page_length=100')
    if server_scripts and 'data' in server_scripts:
        ss_dir = os.path.join(CUSTOM_DIR, 'server_script')
        os.makedirs(ss_dir, exist_ok=True)
        ashan_ss = [s['name'] for s in server_scripts['data'] if 'sidebar' in s['name'].lower() or 'ashan' in s['name'].lower()]
        print(f"\n[Server Script] 找到 {len(ashan_ss)} 个相关 Server Script")
        for ss_name in ashan_ss:
            encoded = urllib.parse.quote(ss_name)
            ss_res = call_api(f'/api/resource/Server%20Script/{encoded}')
            if ss_res and 'data' in ss_res:
                fname = ss_name.lower().replace(' ', '_') + '.json'
                with open(os.path.join(ss_dir, fname), 'w', encoding='utf-8') as f:
                    json.dump(ss_res['data'], f, ensure_ascii=False, indent=2)
                print(f"  [OK] Synced Server Script: {ss_name}")

    print("\n全量架构与配置拉取完成！")


def cmd_test_api():
    print("=" * 60)
    print(" 执行 REST API 健康度与读写测试")
    print("=" * 60)
    
    # 1. 认证测试
    user_res = call_api('/api/method/frappe.auth.get_logged_user')
    if user_res and 'message' in user_res:
        print(f"[PASS] 1. Token 身份鉴权通过 -> 账号: {user_res['message']}")
    else:
        print("[FAIL] 1. Token 身份鉴权失败")

    # 2. 油卡 DocType 读取测试
    oil_cards = call_api('/api/resource/Oil%20Card?limit_page_length=5')
    if oil_cards and 'data' in oil_cards:
        print(f"[PASS] 2. 读取 Oil Card 数据集成功 -> 记录数: {len(oil_cards['data'])}")
    else:
        print("[FAIL] 2. 读取 Oil Card 数据集失败")

    # 3. 报销单据 DocType 读取测试
    reimbursements = call_api('/api/resource/Reimbursement%20Request?limit_page_length=5')
    if reimbursements and 'data' in reimbursements:
        print(f"[PASS] 3. 读取 Reimbursement Request 数据集成功 -> 记录数: {len(reimbursements['data'])}")
    else:
        print("[FAIL] 3. 读取 Reimbursement Request 数据集失败")


def cmd_push_js(dt_name):
    print("=" * 60)
    print(f" 推送本地 JS 到远程 Client Script 调试 -> {dt_name}")
    print("=" * 60)
    
    folder = dt_name.lower().replace(' ', '_')
    js_path = os.path.join(DOCTYPE_DIR, folder, f"{folder}.js")
    
    if not os.path.exists(js_path):
        print(f"错误: 本地找不到文件 {js_path}")
        return

    with open(js_path, 'r', encoding='utf-8') as f:
        js_code = f.read()

    script_name = f"Client Script for {dt_name}"
    
    # 检查远程是否存在该 Client Script
    encoded = urllib.parse.quote(script_name)
    existing = call_api(f'/api/resource/Client%20Script/{encoded}')
    
    payload = {
        "dt": dt_name,
        "script": js_code,
        "enabled": 1
    }
    
    if existing and 'data' in existing:
        res = call_api(f'/api/resource/Client%20Script/{encoded}', method='PUT', data=payload)
        action = "更新"
    else:
        payload["name"] = script_name
        res = call_api('/api/resource/Client%20Script', method='POST', data=payload)
        action = "新建"
        
    if res and 'data' in res:
        print(f"[SUCCESS] 已成功{action} Client Script: '{script_name}'")
    else:
        print(f"[FAILED] 推送 Client Script 失败")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    subcmd = sys.argv[1].lower()
    if subcmd == 'status':
        cmd_status()
    elif subcmd == 'pull':
        cmd_pull()
    elif subcmd == 'test-api':
        cmd_test_api()
    elif subcmd == 'push-js':
        if len(sys.argv) < 3:
            print("错误: 请提供 DocType 名称，例如: python manage_app.py push-js 'Oil Card'")
        else:
            cmd_push_js(sys.argv[2])
    else:
        print(f"未知指令: '{subcmd}'")
        print(__doc__)


if __name__ == '__main__':
    main()
