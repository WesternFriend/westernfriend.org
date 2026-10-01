/**
 * Automated accessibility check: axe-core against a running server.
 *
 * Usage:
 *   node scripts/a11y-check.mjs <url> [<url> ...]
 *
 * The URL list normally comes from `./manage.py a11y_urls` so the scan covers
 * whatever the seeded database actually contains (see docs/accessibility-checks.md).
 *
 * Targets WCAG 2.2 AA. Exits 1 if any page has a violation axe rates
 * `serious` or `critical`; `moderate` and `minor` issues are reported but do
 * not fail the run, so the check cannot be ignored for crying wolf.
 *
 * Tool choice (issue #1282): axe-core driven by puppeteer-core. Both are
 * pure-JavaScript npm packages - no browser download, no native binaries -
 * and the browser is whatever Chrome the environment already has (CHROME_PATH,
 * or the places Chrome normally lives). pa11y-ci was considered and rejected:
 * it pulls a full puppeteer + chromium download into a repo whose only other
 * JavaScript is the Tailwind build.
 */

import { readFileSync, existsSync } from "node:fs";
import { createRequire } from "node:module";
import process from "node:process";

import puppeteer from "puppeteer-core";

const require = createRequire(import.meta.url);
const AXE_SOURCE = readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");

// WCAG 2.2 AA and everything it inherits; no best-practice rules, so every
// failure maps to a WCAG success criterion the project has committed to.
const AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

const FAIL_IMPACTS = new Set(["serious", "critical"]);

function chromePath() {
    if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
    const candidates = [
        "/usr/bin/google-chrome", // GitHub Actions ubuntu runners
        "/usr/bin/chromium-browser",
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ];
    const found = candidates.find((path) => existsSync(path));
    if (!found) {
        console.error(
            "No Chrome found. Set CHROME_PATH to a Chrome/Chromium binary.",
        );
        process.exit(2);
    }
    return found;
}

async function scanPage(browser, url) {
    const page = await browser.newPage();
    try {
        const response = await page.goto(url, {
            waitUntil: "networkidle2",
            timeout: 60000,
        });
        if (!response || response.status() >= 400) {
            throw new Error(
                `HTTP ${response ? response.status() : "no response"}`,
            );
        }
        await page.evaluate(AXE_SOURCE);
        const results = await page.evaluate(
            (tags) =>
                window.axe.run(document, {
                    runOnly: { type: "tag", values: tags },
                }),
            AXE_TAGS,
        );
        return results.violations;
    } finally {
        await page.close();
    }
}

function report(url, violations) {
    const failing = violations.filter((violation) =>
        FAIL_IMPACTS.has(violation.impact),
    );
    const label = failing.length > 0 ? "FAIL" : "ok  ";
    console.log(`${label} ${url} - ${violations.length} violation(s)`);
    for (const violation of violations) {
        const marker = FAIL_IMPACTS.has(violation.impact) ? "✗" : "·";
        console.log(
            `  ${marker} [${violation.impact}] ${violation.id}: ` +
                `${violation.help} (${violation.nodes.length} element(s))`,
        );
        for (const node of violation.nodes.slice(0, 3)) {
            console.log(`      ${node.target.join(" ")}`);
        }
        if (violation.nodes.length > 3) {
            console.log(`      ... and ${violation.nodes.length - 3} more`);
        }
    }
    return failing.length;
}

const urls = process.argv.slice(2).filter(Boolean);
if (urls.length === 0) {
    console.error("Usage: node scripts/a11y-check.mjs <url> [<url> ...]");
    process.exit(2);
}

const browser = await puppeteer.launch({
    executablePath: chromePath(),
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
});

let failures = 0;
let scanned = 0;
try {
    for (const url of urls) {
        try {
            failures += report(url, await scanPage(browser, url));
            scanned += 1;
        } catch (error) {
            // A page that cannot be scanned is a failure, not a skip: silently
            // scanning fewer pages would let a regression through.
            console.log(`FAIL ${url} - could not scan: ${error.message}`);
            failures += 1;
        }
    }
} finally {
    await browser.close();
}

console.log(
    `\n${scanned}/${urls.length} page(s) scanned, ` +
        `${failures} serious-or-critical failure(s)`,
);
process.exit(failures > 0 ? 1 : 0);
