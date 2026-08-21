import os
import time
import paramiko
import subprocess
import base64

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()
HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER_SSH = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')
SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
ERPNEXT_USER = os.getenv('ERPNEXT_USER', 'Administrator')
ERPNEXT_PASS = os.getenv('ERPNEXT_PASSWORD', 'admin')

# 用 Node.js Puppeteer (在 Unraid 主机上) 进行截图测试
PUPPETEER_SCRIPT = f"""
const puppeteer = require('puppeteer');

(async () => {{
    const browser = await puppeteer.launch({{
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1400,900']
    }});
    const page = await browser.newPage();
    await page.setViewport({{width: 1400, height: 900}});

    // Login
    await page.goto('{SITE_URL}/login', {{waitUntil: 'networkidle2', timeout: 30000}});
    await page.type('#login_email', '{ERPNEXT_USER}');
    await page.type('#login_password', '{ERPNEXT_PASS}');
    await page.click('.btn-login');
    await page.waitForNavigation({{waitUntil: 'networkidle2', timeout: 30000}});
    await new Promise(r => setTimeout(r, 3000));

    // Go to my-business workspace
    await page.goto('{SITE_URL}/desk/my-business', {{waitUntil: 'networkidle2', timeout: 30000}});
    await new Promise(r => setTimeout(r, 3000));

    // Clear localStorage to start fresh
    await page.evaluate(() => {{
        localStorage.removeItem('ashan-cn-sidebar-state');
        localStorage.removeItem('section-breaks-state');
    }});
    await page.reload({{waitUntil: 'networkidle2'}});
    await new Promise(r => setTimeout(r, 3000));

    // Screenshot 1: fresh state
    await page.screenshot({{path: '/tmp/test_fresh_state.png', fullPage: false}});
    console.log('SCREENSHOT_1: fresh state');

    // List section titles
    const sections = await page.$$eval('.body-sidebar .section-item .standard-sidebar-item', els => els.map(e => e.textContent.trim().substring(0, 40)));
    console.log('SECTIONS:', JSON.stringify(sections));

    // Click 财务与报销 section
    const clicked = await page.evaluate(() => {{
        const items = document.querySelectorAll('.body-sidebar .section-item .standard-sidebar-item');
        for (const item of items) {{
            if (item.textContent.includes('财务') || item.textContent.includes('报销')) {{
                item.click();
                return item.textContent.trim().substring(0, 30);
            }}
        }}
        return null;
    }});
    console.log('CLICKED:', clicked);
    await new Promise(r => setTimeout(r, 1500));

    // Screenshot 2: after clicking 财务
    await page.screenshot({{path: '/tmp/test_after_caiwu.png', fullPage: false}});

    // Count open/closed sections
    const states = await page.evaluate(() => {{
        const children = document.querySelectorAll('.body-sidebar .sidebar-item-children');
        let opened = 0, closed = 0;
        children.forEach(c => {{
            if (c.getAttribute('data-state') === 'opened') opened++;
            else if (c.getAttribute('data-state') === 'closed') closed++;
        }});
        return {{opened, closed}};
    }});
    console.log('STATES_AFTER_CAIWU:', JSON.stringify(states));

    // Read localStorage
    const ashanState = await page.evaluate(() => localStorage.getItem('ashan-cn-sidebar-state'));
    const nativeState = await page.evaluate(() => localStorage.getItem('section-breaks-state'));
    console.log('ASHAN_STATE:', ashanState);
    console.log('NATIVE_STATE:', nativeState);

    // Click 仓库与库存 section
    await page.evaluate(() => {{
        const items = document.querySelectorAll('.body-sidebar .section-item .standard-sidebar-item');
        for (const item of items) {{
            if (item.textContent.includes('库存') || item.textContent.includes('仓库')) {{
                item.click();
                return;
            }}
        }}
    }});
    await new Promise(r => setTimeout(r, 1500));

    // Screenshot 3: after clicking 库存
    await page.screenshot({{path: '/tmp/test_after_kucun.png', fullPage: false}});

    const states2 = await page.evaluate(() => {{
        const children = document.querySelectorAll('.body-sidebar .sidebar-item-children');
        let opened = 0, closed = 0;
        children.forEach(c => {{
            if (c.getAttribute('data-state') === 'opened') opened++;
            else if (c.getAttribute('data-state') === 'closed') closed++;
        }});
        return {{opened, closed}};
    }});
    console.log('STATES_AFTER_KUCUN:', JSON.stringify(states2));

    const ashanState2 = await page.evaluate(() => localStorage.getItem('ashan-cn-sidebar-state'));
    console.log('ASHAN_STATE_2:', ashanState2);

    await browser.close();
    console.log('DONE');
}})().catch(e => {{ console.error('ERROR:', e.message); process.exit(1); }});
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER_SSH, password=PASSWORD, timeout=10)

sftp = ssh.open_sftp()
with sftp.open('/tmp/test_sidebar_state.js', 'w') as f:
    f.write(PUPPETEER_SCRIPT)
sftp.close()

cmd = "cd /tmp && node test_sidebar_state.js 2>&1"
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
stdout.channel.recv_exit_status()
out = stdout.read().decode('utf-8', errors='replace')
print(out)

# Pull screenshots back
for fname in ['test_fresh_state.png', 'test_after_caiwu.png', 'test_after_kucun.png']:
    try:
        sftp = ssh.open_sftp()
        sftp.get(f'/tmp/{fname}', fname)
        sftp.close()
        print(f"[OK] Downloaded {fname}")
    except Exception as ex:
        print(f"[WARN] Could not download {fname}: {ex}")

ssh.close()
