/**
 * Read-only acceptance test for the role-focused procurement workbenches.
 *
 * The script signs in with credentials from .env, opens each Desk page,
 * verifies that the shared runtime rendered a visible workbench, checks the
 * stage/table structure, captures screenshots, and reports application errors.
 */
import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const root = path.resolve(import.meta.dirname, "..");
const artifactDir = path.join(root, "temp_screenshots", "procurement_workbench_white_screen");

function loadEnv(filePath) {
    const values = {};
    if (!fs.existsSync(filePath)) return values;
    for (const rawLine of fs.readFileSync(filePath, "utf8").split(/\r?\n/)) {
        const line = rawLine.trim();
        if (!line || line.startsWith("#")) continue;
        const separator = line.indexOf("=");
        if (separator < 1) continue;
        values[line.slice(0, separator).trim()] = line
            .slice(separator + 1)
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
    throw new Error("Missing ERPNEXT_USERNAME or ERPNEXT_PASSWORD in .env; no browser check was run.");
}

const workbenches = [
    {
        route: "material-request-workbench",
        title: "物料申请",
        stageCount: 1,
        requiredHeaders: ["物料名称", "规格", "参考单价", "预估金额", "备注"],
    },
    {
        route: "procurement-execution-workbench",
        title: "采购执行",
        stageCount: 4,
        requiredHeaders: ["物料名称", "规格", "数量", "金额", "备注"],
    },
    {
        route: "material-receipt-workbench",
        title: "收货入库",
        stageCount: 1,
        requiredHeaders: ["物料名称", "规格", "订购总数", "已收数", "未收数量", "备注"],
    },
];

const isPlatformSocketOriginWarning = (message) => message.includes("socket.io: Invalid origin");

async function waitForWorkbench(page, expectedTitle) {
    const container = page.locator(".picker-page-container").filter({
        hasText: expectedTitle,
    });
    await container.waitFor({ state: "visible", timeout: 30000 });
    await container.locator("h2").filter({ hasText: expectedTitle }).waitFor({
        state: "visible",
        timeout: 30000,
    });
    await container.locator("#picker-data-table").waitFor({ state: "visible", timeout: 30000 });
    return container;
}

fs.mkdirSync(artifactDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await context.newPage();
const consoleErrors = [];

page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
});
page.on("pageerror", (error) => consoleErrors.push(error.message));

try {
    await page.goto(`${siteUrl}/login`, { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.locator("#login_email").fill(username);
    await page.locator("#login_password").fill(password);
    await page.locator("button.btn-login:not(.btn-login-with-email-link)").click();
    await page.waitForURL(/\/desk/, { timeout: 30000 });

    const results = [];
    for (const workbench of workbenches) {
        const startedAt = Date.now();
        const errorStart = consoleErrors.length;
        await page.goto(`${siteUrl}/desk/${workbench.route}`, {
            waitUntil: "domcontentloaded",
            timeout: 30000,
        });
        const container = await waitForWorkbench(page, workbench.title);
        await page.waitForTimeout(1200);

        const title = (await container.locator("h2").innerText()).trim();
        const stageCount = await page.locator(".picker-kpi-card[data-stage]").count();
        const headers = (await page.locator("#picker-table-thead th").allInnerTexts())
            .map((text) => text.replace(/\s+/g, "").trim());
        const requiredHeadersPresent = workbench.requiredHeaders.every((required) => (
            headers.some((header) => header.includes(required))
        ));
        const dimensions = await container.evaluate((element) => {
            const rect = element.getBoundingClientRect();
            const scroll = element.querySelector("#picker-main-table-scroll");
            return {
                width: Math.round(rect.width),
                height: Math.round(rect.height),
                tableClientWidth: scroll ? Math.round(scroll.clientWidth) : 0,
                tableScrollWidth: scroll ? Math.round(scroll.scrollWidth) : 0,
            };
        });
        const assetUrls = await page.evaluate(() => ({
            js: [...document.scripts]
                .map((element) => element.src)
                .filter((src) => src.includes("procurement_workbench.js")),
            css: [...document.querySelectorAll('link[rel="stylesheet"]')]
                .map((element) => element.href)
                .filter((href) => href.includes("procurement_workbench.css")),
        }));

        await page.screenshot({
            path: path.join(artifactDir, `${workbench.route}.png`),
            fullPage: true,
        });

        const routeErrors = consoleErrors.slice(errorStart);
        const applicationErrors = routeErrors.filter((message) => !isPlatformSocketOriginWarning(message));
        results.push({
            route: workbench.route,
            expectedTitle: workbench.title,
            title,
            expectedStageCount: workbench.stageCount,
            stageCount,
            headerCount: headers.length,
            headers,
            requiredHeadersPresent,
            dimensions,
            assetUrls,
            loadMs: Date.now() - startedAt,
            applicationErrors,
            platformWarnings: routeErrors.filter(isPlatformSocketOriginWarning),
        });
    }

    // Frappe Desk keeps Page wrappers alive.  A cold URL load cannot prove
    // that a cached page is restored on internal SPA navigation, which is the
    // exact regression that previously appeared as a white page.
    const spaErrorStart = consoleErrors.length;
    const spaRoutes = [
        ["procurement-execution-workbench", "采购执行"],
        ["material-receipt-workbench", "收货入库"],
        ["material-request-workbench", "物料申请"],
    ];
    let spaActiveContainer;
    for (const [route, title] of spaRoutes) {
        await page.evaluate((targetRoute) => frappe.set_route(targetRoute), route);
        spaActiveContainer = await waitForWorkbench(page, title);
    }
    const spaRouteErrors = consoleErrors.slice(spaErrorStart);
    const spaApplicationErrors = spaRouteErrors.filter((message) => !isPlatformSocketOriginWarning(message));
    const spaReturnState = {
        title: (await spaActiveContainer.locator("h2").innerText()).trim(),
        tableVisible: await spaActiveContainer.locator("#picker-data-table").isVisible(),
        applicationErrors: spaApplicationErrors,
        platformWarnings: spaRouteErrors.filter(isPlatformSocketOriginWarning),
    };

    console.log(JSON.stringify({ results, spaReturnState }, null, 2));
    const failed = results.filter((result) => (
        result.title !== result.expectedTitle
        || result.stageCount !== result.expectedStageCount
        || result.headerCount === 0
        || !result.requiredHeadersPresent
        || result.dimensions.width < 800
        || result.dimensions.height < 200
        || result.assetUrls.js.length === 0
        || result.assetUrls.css.length === 0
        || result.applicationErrors.length > 0
    ));
    if (
        failed.length
        || spaReturnState.title !== "物料申请"
        || !spaReturnState.tableVisible
        || spaReturnState.applicationErrors.length > 0
    ) {
        const failedRoutes = failed.map((item) => item.route);
        if (spaReturnState.title !== "物料申请" || !spaReturnState.tableVisible || spaReturnState.applicationErrors.length > 0) {
            failedRoutes.push("desk-spa-revisit");
        }
        throw new Error(`Procurement workbench acceptance failed: ${failedRoutes.join(", ")}`);
    }
} finally {
    await browser.close();
}
