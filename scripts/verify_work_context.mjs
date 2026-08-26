/**
 * Read-only acceptance test for the user business working context.
 *
 * It temporarily updates only the test user's work-context preference, opens a
 * brand-new Material Request without saving it, verifies the company/date
 * defaults, then restores the user's original preference in a finally block.
 */
import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const root = path.resolve(import.meta.dirname, "..");
const artifactDir = path.join(root, "temp_screenshots", "work_context_acceptance");

function loadEnv(filePath) {
    const values = {};
    if (!fs.existsSync(filePath)) return values;
    for (const rawLine of fs.readFileSync(filePath, "utf8").split(/\r?\n/)) {
        const line = rawLine.trim();
        if (!line || line.startsWith("#")) continue;
        const separator = line.indexOf("=");
        if (separator < 1) continue;
        values[line.slice(0, separator).trim()] = line.slice(separator + 1)
            .trim()
            .replace(/^['"]|['"]$/g, "");
    }
    return values;
}

const env = loadEnv(path.join(root, ".env"));
const siteUrl = (
    process.env.ERPNEXT_SITE_URL_LOCAL
    || process.env.ERPNEXT_SITE_URL
    || env.ERPNEXT_SITE_URL_LOCAL
    || env.ERPNEXT_SITE_URL
    || "http://192.168.8.11:6888"
).replace(/\/$/, "");
const username = process.env.ERPNEXT_USERNAME || env.ERPNEXT_USERNAME;
const password = process.env.ERPNEXT_PASSWORD || env.ERPNEXT_PASSWORD;

if (!username || !password) {
    throw new Error("Missing ERPNEXT_USERNAME or ERPNEXT_PASSWORD in .env.");
}

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await context.newPage();
const consoleErrors = [];
let originalContext = null;
fs.mkdirSync(artifactDir, { recursive: true });

page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
});
page.on("pageerror", (error) => consoleErrors.push(error.message));

async function saveWorkContext(nextContext) {
    return page.evaluate(async (payload) => {
        const response = await frappe.call({
            method: "ashan_cn_procurement.services.work_context_service.save_work_context",
            type: "POST",
            args: payload,
            freeze: false,
        });
        return response.message;
    }, nextContext);
}

try {
    await page.goto(`${siteUrl}/login`, { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.locator("#login_email").fill(username);
    await page.locator("#login_password").fill(password);
    await page.locator("button.btn-login:not(.btn-login-with-email-link)").click();
    await page.waitForURL(/\/desk/, { timeout: 30000 });

    await page.goto(`${siteUrl}/desk/material-request-workbench`, {
        waitUntil: "domcontentloaded",
        timeout: 30000,
    });
    const userMenu = page.locator('a[aria-label="User Menu"]');
    const workContextTrigger = page.locator("#ashan-work-context-trigger");
    await userMenu.waitFor({ state: "visible", timeout: 30000 });
    await page.locator('script[src*="ashan_work_context.js"]').waitFor({ state: "attached", timeout: 30000 });
    await workContextTrigger.waitFor({ state: "visible", timeout: 30000 });
    const loadedAssets = await page.evaluate(() => ({
        workContextScript: [...document.scripts]
            .map((script) => script.src)
            .find((source) => source.includes("ashan_work_context.js")) || "",
        uiKitStylesheet: [...document.querySelectorAll('link[rel="stylesheet"]')]
            .map((link) => link.href)
            .find((source) => source.includes("ashan_ui_kit.css")) || "",
    }));
    if (
        !loadedAssets.workContextScript.includes("v=20260826.62")
        || !loadedAssets.uiKitStylesheet.includes("v=20260826.62")
    ) {
        throw new Error("The deployed work-context assets are not using the current cache version.");
    }

    originalContext = await page.evaluate(() => frappe.boot.ashan_work_context || null);
    if (!originalContext?.companies?.length) {
        throw new Error("No accessible company was returned in the work context.");
    }

    await userMenu.click();
    await page.waitForTimeout(500);
    const profileMenuRestored = {
        workContextDialogCount: await page.locator(".modal:visible").filter({ hasText: "当前工作环境" }).count(),
        route: await page.evaluate(() => frappe.get_route?.() || []),
    };
    if (profileMenuRestored.workContextDialogCount) {
        throw new Error("The native user menu is still being intercepted by work-context settings.");
    }

    await page.goto(`${siteUrl}/desk/material-request-workbench`, {
        waitUntil: "domcontentloaded",
        timeout: 30000,
    });
    await workContextTrigger.waitFor({ state: "visible", timeout: 30000 });
    await workContextTrigger.click();
    const settingsDialog = page.locator(".modal:visible").filter({ hasText: "当前工作环境" });
    await settingsDialog.waitFor({ state: "visible", timeout: 10000 });
    const settingsVisible = {
        company: await settingsDialog.locator("select").count(),
        dateModeOptions: await settingsDialog.locator("[data-date-mode]").count(),
    };
    await settingsDialog.locator('[data-date-mode="system"]').click();
    settingsVisible.fixedDateVisibleInSystemMode = await settingsDialog
        .locator('[data-fieldname="work_date"] input')
        .isVisible();
    await page.screenshot({
        path: path.join(artifactDir, "work-context-system-default.png"),
        fullPage: true,
    });
    await settingsDialog.getByRole("button", { name: "关闭" }).click();

    const targetCompany = originalContext.companies.find((company) => company.includes("祺富"))
        || originalContext.companies[0];
    const targetDate = "2026-08-24";
    await workContextTrigger.click();
    const applyDialog = page.locator(".modal:visible").filter({ hasText: "当前工作环境" });
    await applyDialog.waitFor({ state: "visible", timeout: 10000 });
    await applyDialog.locator("select").selectOption(targetCompany);
    await applyDialog.locator('[data-date-mode="fixed"]').click();
    await applyDialog.locator('[data-fieldname="work_date"] input').waitFor({ state: "visible" });
    await applyDialog.locator('[data-fieldname="work_date"] input').fill(targetDate);
    await applyDialog.getByRole("button", { name: "保存并应用" }).click();
    await applyDialog.waitFor({ state: "hidden", timeout: 15000 });
    const runtimeBeforeNewDocument = await page.evaluate(() => ({
        apiType: typeof window.AshanWorkContext,
        apiKeys: Object.keys(window.AshanWorkContext || {}),
        context: window.AshanWorkContext?.getContext?.() || null,
        factoryPatched: String(frappe.model.get_new_doc).includes("getNewDocumentWithContext"),
    }));
    const fixedTriggerText = await workContextTrigger.innerText();

    await page.evaluate(() => frappe.new_doc("Material Request"));
    await page.waitForFunction(() => (
        window.cur_frm?.doctype === "Material Request" && window.cur_frm?.is_new?.()
    ), null, { timeout: 15000 });
    await page.waitForTimeout(500);
    const newDocument = await page.evaluate(() => ({
        company: window.cur_frm.doc.company,
        transaction_date: window.cur_frm.doc.transaction_date,
    }));

    await workContextTrigger.click();
    const allCompanyDialog = page.locator(".modal:visible").filter({ hasText: "当前工作环境" });
    await allCompanyDialog.waitFor({ state: "visible", timeout: 10000 });
    await allCompanyDialog.locator("select").selectOption("全部公司");
    await allCompanyDialog.locator('[data-date-mode="system"]').click();
    await allCompanyDialog.getByRole("button", { name: "保存并应用" }).click();
    await allCompanyDialog.waitFor({ state: "hidden", timeout: 15000 });
    const systemDate = await page.evaluate(() => frappe.datetime.get_today());
    const systemModeContext = await page.evaluate(() => window.AshanWorkContext?.getContext?.() || null);
    const systemTriggerText = await workContextTrigger.innerText();
    await page.evaluate(() => frappe.new_doc("Material Request"));
    await page.waitForFunction(() => (
        window.cur_frm?.doctype === "Material Request" && window.cur_frm?.is_new?.()
    ), null, { timeout: 15000 });
    await page.waitForTimeout(500);
    const systemDefaultNewDocument = await page.evaluate(() => ({
        company: window.cur_frm.doc.company,
        transaction_date: window.cur_frm.doc.transaction_date,
    }));

    const applicationErrors = consoleErrors.filter((message) => (
        !message.includes("socket.io: Invalid origin")
    ));
    const result = {
        settingsVisible,
        loadedAssets,
        profileMenuRestored,
        runtimeBeforeNewDocument,
        fixedTriggerText,
        targetCompany,
        targetDate,
        newDocument,
        systemDate,
        systemModeContext,
        systemTriggerText,
        systemDefaultNewDocument,
        applicationErrors,
    };
    console.log(JSON.stringify(result, null, 2));

    if (
        settingsVisible.company !== 1
        || settingsVisible.dateModeOptions !== 2
        || settingsVisible.fixedDateVisibleInSystemMode
        || runtimeBeforeNewDocument.context?.date_mode !== "fixed"
        || runtimeBeforeNewDocument.context?.fixed_work_date !== targetDate
        || !fixedTriggerText.includes(targetDate)
        || newDocument.company !== targetCompany
        || newDocument.transaction_date !== targetDate
        || systemModeContext?.date_mode !== "system"
        || !systemTriggerText.includes("系统当天")
        || systemDefaultNewDocument.company !== ""
        || systemDefaultNewDocument.transaction_date !== systemDate
        || applicationErrors.length
    ) {
        throw new Error("Business work-context acceptance failed.");
    }
} finally {
    if (originalContext) {
        await saveWorkContext({
            company: originalContext.company || "",
            date_mode: originalContext.date_mode || "system",
            work_date: originalContext.date_mode === "fixed"
                ? (originalContext.fixed_work_date || originalContext.work_date)
                : "",
        });
    }
    await browser.close();
}
