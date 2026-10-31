/**
 * Automated accessibility check: axe-core against a running server.
 *
 * Usage, after `npm ci --include=dev` installs the versions locked in
 * package-lock.json:
 *   node scripts/a11y-check.mjs <url> [<url> ...]
 *
 * The URL list normally comes from `./manage.py a11y_urls` so the scan covers
 * whatever the seeded database actually contains (see docs/accessibility-checks.md).
 *
 * Targets WCAG 2.2 AA. Exits 1 if any page has a violation axe rates
 * `serious` or `critical`; `moderate` and `minor` issues are reported but do
 * not fail the run, so the check cannot be ignored for crying wolf.
 *
 * Every stylesheet a page requests has to load as CSS before axe runs: a
 * page missing its styles can pass contrast and layout rules the real page
 * fails. A page whose stylesheet doesn't load fails the run, naming the
 * stylesheet and why. scripts/a11y-check.test.mjs proves it.
 *
 * Tool choice (issue #1282): axe-core driven by puppeteer-core. Both are
 * pure-JavaScript npm packages - no browser download, no native binaries -
 * and the browser is whatever Chrome the environment already has (CHROME_PATH,
 * or the places Chrome normally lives). They are devDependencies pinned to
 * exact versions, and package-lock.json locks everything they depend on.
 * pa11y-ci and @axe-core/cli were considered and rejected;
 * docs/accessibility-checks.md has the reasons.
 */

import { readFileSync, existsSync } from "node:fs";
import { createRequire } from "node:module";
import process from "node:process";

import puppeteer from "puppeteer-core";

// axe runs inside the page, so its built file is read as source text and
// injected rather than imported.
const require = createRequire(import.meta.url);
const AXE_SOURCE = readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");

// WCAG 2.2 AA and everything it inherits. No best-practice rules, so every
// failure maps to a WCAG success criterion the project has committed to.
// axe-core 4.10 tags no rule wcag22a (the 2.2 A criteria have no automated
// rules yet), but the tag is listed so such rules are picked up the release
// they appear instead of being silently skipped.
const AXE_TAGS = [
    "wcag2a",
    "wcag2aa",
    "wcag21a",
    "wcag21aa",
    "wcag22a",
    "wcag22aa",
];

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

// Records every stylesheet the page requests, by URL, with why it didn't
// load, or null once it has. The network is the measure: Chrome gives a
// stylesheet that 404s or isn't CSS an empty `sheet`, not a missing one, so
// the page itself can't tell a failed stylesheet from an empty one.
function watchStylesheets(page) {
    const stylesheets = new Map();
    const settle = (request) => {
        if (request.resourceType() !== "stylesheet") return;
        const status = request.response()?.status();
        if (status >= 300 && status < 400) {
            // A redirect: the request it leads to is checked instead.
            stylesheets.delete(request.url());
        } else if (status === undefined) {
            stylesheets.set(
                request.url(),
                request.failure()?.errorText ?? "no response",
            );
        } else if (status < 200 || status >= 300) {
            stylesheets.set(request.url(), `HTTP ${status}`);
        } else {
            // Chrome won't apply a stylesheet served as anything but CSS.
            const type = request.response().headers()["content-type"] ?? "";
            stylesheets.set(
                request.url(),
                /^text\/css\b/i.test(type)
                    ? null
                    : `served as ${type || "no content type"}, not text/css`,
            );
        }
    };
    page.on("request", (request) => {
        if (request.resourceType() === "stylesheet") {
            stylesheets.set(request.url(), "still loading");
        }
    });
    page.on("requestfinished", settle);
    page.on("requestfailed", settle);
    return stylesheets;
}

async function scanPage(browser, url) {
    const page = await browser.newPage();
    const stylesheets = watchStylesheets(page);
    try {
        const response = await page.goto(url, {
            // The load event waits for the stylesheets the page links to load
            // or fail, so the check below sees how each one ended.
            waitUntil: ["load", "networkidle2"],
            timeout: 60000,
        });
        if (!response || response.status() >= 400) {
            throw new Error(
                `HTTP ${response ? response.status() : "no response"}`,
            );
        }
        const failed = [...stylesheets]
            .filter(([, problem]) => problem !== null)
            .map(([href, problem]) => `${href} (${problem})`);
        if (failed.length > 0) {
            throw new Error(`stylesheet did not load: ${failed.join(", ")}`);
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
