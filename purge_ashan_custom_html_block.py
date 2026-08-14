import os
import json
import urllib.request
from http.cookiejar import CookieJar

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()
SITE_URL = 'http://192.168.8.11:6888'
USER = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
PWD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')

cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

login_req = urllib.request.Request(
    f"{SITE_URL}/api/method/login",
    data=json.dumps({'usr': USER, 'pwd': PWD}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
opener.open(login_req)

def call_api(endpoint, method='GET', data=None):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    req_url = f"{SITE_URL.rstrip('/')}{endpoint}"
    encoded_data = json.dumps(data).encode('utf-8') if data else None
    
    req = urllib.request.Request(req_url, data=encoded_data, headers=headers, method=method)
    try:
        with opener.open(req) as resp:
            content = resp.read().decode('utf-8')
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        print(f"API Error {e.code}: {e.read().decode('utf-8')}")
        return None

print("=== 1. Deleting Custom HTML Block 'Ashan Left Sidebar Block' ===")
del_res = call_api('/api/resource/Custom%20HTML%20Block/Ashan%20Left%20Sidebar%20Block', method='DELETE')
print("Delete result:", del_res)

print("\n=== 2. Inspecting all Workspaces for custom blocks ===")
ws_list = call_api('/api/resource/Workspace?limit_page_length=100&fields=["name"]')
if ws_list and 'data' in ws_list:
    for ws_info in ws_list['data']:
        ws_name = ws_info['name']
        ws_doc = call_api(f"/api/resource/Workspace/{urllib.parse.quote(ws_name)}")
        if ws_doc and 'data' in ws_doc:
            doc_data = ws_doc['data']
            custom_blocks = doc_data.get('custom_blocks', [])
            dirty = False
            new_custom_blocks = []
            for cb in custom_blocks:
                if 'ashan' in str(cb).lower() or cb.get('custom_block_name') == 'Ashan Left Sidebar Block':
                    print(f"Removing custom block from workspace '{ws_name}'")
                    dirty = True
                else:
                    new_custom_blocks.append(cb)
            
            # Check content JSON
            content_str = doc_data.get('content', '[]')
            if 'Ashan Left Sidebar Block' in content_str or 'ashan-sidebar-injector' in content_str:
                print(f"Cleaning content field in workspace '{ws_name}'")
                try:
                    cards = json.loads(content_str)
                    filtered_cards = [c for c in cards if 'Ashan Left Sidebar Block' not in str(c)]
                    doc_data['content'] = json.dumps(filtered_cards)
                    dirty = True
                except Exception:
                    pass
            
            if dirty:
                doc_data['custom_blocks'] = new_custom_blocks
                update_res = call_api(f"/api/resource/Workspace/{urllib.parse.quote(ws_name)}", method='PUT', data=doc_data)
                print(f"Updated Workspace '{ws_name}':", update_res is not None)

print("\n=== 3. Clean up Client Scripts in DB ===")
cs_list = call_api('/api/resource/Client%20Script?fields=["name"]')
if cs_list and 'data' in cs_list:
    for cs in cs_list['data']:
        print("Found Client Script:", cs['name'])
        # Disable or remove non-standard client scripts that might alter sidebar
        if 'Sidebar' in cs['name'] or 'Purge' in cs['name']:
            call_api(f"/api/resource/Client%20Script/{urllib.parse.quote(cs['name'])}", method='DELETE')
            print(f"Deleted Client Script: {cs['name']}")

print("\n=== 4. Reset Website Script to clean state ===")
clean_web_script = """
// Ashan Procurement Clean Website Script
console.log('[Ashan] Desk loaded in pure official state.');
"""
call_api('/api/resource/Website%20Script/Website%20Script', method='PUT', data={"javascript": clean_web_script})
print("Website Script reset to clean state.")

print("\nDone!")
