/**
 * Automated accessibility check: axe-core against a running server.
 *
 * Usage, after `npm ci --prefix scripts` installs the versions locked in
 * scripts/package-lock.json:
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
 * or the places Chrome normally lives). scripts/package.json pins them to
 * exact versions, separately from the site's own packages, and
 * scripts/package-lock.json locks everything they depend on. pa11y-ci and
 * @axe-core/cli were considered and rejected; docs/accessibility-checks.md
 * has the reasons.
 */

import { readFileSync, existsSync } from "node:fs";
import { createRequire } from "node:module";
import process from "node:process";

// Say how to install the packages, rather than failing with a
// module-resolution stack trace.
let puppeteer;
let AXE_SOURCE;
try {
    ({ default: puppeteer } = await import("puppeteer-core"));
    // axe runs inside the page, so its built file is read as source text and
    // injected rather than imported.
    const require = createRequire(import.meta.url);
    AXE_SOURCE = readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");
} catch (error) {
    if (error.code !== "ERR_MODULE_NOT_FOUND" && error.code !== "MODULE_NOT_FOUND") {
        throw error;
    }
    console.error(
        "The checker's packages aren't installed. Run: npm ci --prefix scripts",
    );
    process.exit(2);
}

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

// The Content-Types Chrome applies a stylesheet under in a standards-mode
// page, by their type and subtype: text/css, and also none at all or this
// placeholder, which Chrome accepts for compatibility (as measured in Chrome;
// with X-Content-Type-Options: nosniff it aborts those instead, and that
// abort fails the stylesheet below).
const APPLIED_AS_CSS = new Set([
    "text/css",
    "",
    "application/x-unknown-content-type",
]);

// The type a Content-Type header names, read the way Chrome reads it (checked
// against Chrome on 32 headers): a repeated header arrives as one
// comma-separated list, and commas inside quotes don't split it. A value that
// is just "*/*" names no type. Otherwise its type runs to its first space,
// tab, ";" or "(", and counts only if it has a "/". The last one that counts
// wins; with none, it's "", as if there were no header.
function contentTypeEssence(header) {
    const values = [];
    let value = "";
    let quoted = false;
    for (let i = 0; i < header.length; i += 1) {
        const char = header[i];
        if (quoted && char === "\\" && i + 1 < header.length) {
            value += char + header[i + 1];
            i += 1;
            continue;
        }
        if (char === '"') quoted = !quoted;
        if (char === "," && !quoted) {
            values.push(value);
            value = "";
        } else {
            value += char;
        }
    }
    values.push(value);
    let essence = "";
    for (const candidate of values) {
        const trimmed = candidate.replace(/^[ \t]+|[ \t]+$/g, "");
        if (trimmed === "*/*") continue;
        const type = trimmed.split(/[ \t;(]/)[0];
        if (type.includes("/")) essence = type.toLowerCase();
    }
    return essence;
}

// Why a finished stylesheet request didn't load as CSS, or null if it did.
function stylesheetProblem(request) {
    const response = request.response();
    const status = response?.status();
    // An error status says the most, even when Chrome also aborts the request.
    if (status !== undefined && status !== 304 && (status < 200 || status >= 300)) {
        return `HTTP ${status}`;
    }
    // Checked before the response, because a request can fail after its
    // headers arrived, as when the body is cut short.
    const failure = request.failure();
    if (failure) return failure.errorText;
    if (!response) return "no response";
    if (status === 304) {
        // Only a request revalidating a copy Chrome already has can be
        // answered with a 304; that copy is what Chrome applies.
        const headers = request.headers();
        const revalidating = "if-none-match" in headers || "if-modified-since" in headers;
        return revalidating ? null : "HTTP 304 to a request with no cached copy";
    }
    const header = response.headers()["content-type"] ?? "";
    const essence = contentTypeEssence(header);
    if (APPLIED_AS_CSS.has(essence)) return null;
    // Show the header itself too when the type was read out of a longer one.
    return header.trim().toLowerCase() === essence
        ? `served as ${essence}, not CSS`
        : `served as ${essence} (Content-Type: ${header}), not CSS`;
}

// Records every stylesheet the page requests, by URL, with why it didn't
// load, or null once it has. The network is the measure: Chrome gives a
// stylesheet that 404s or isn't CSS an empty `sheet`, not a missing one, so
// the page itself can't tell a failed stylesheet from an empty one.
function watchStylesheets(page) {
    const stylesheets = new Map();
    page.on("request", (request) => {
        if (request.resourceType() !== "stylesheet") return;
        // A request that follows a redirect carries the URLs it came through;
        // only where the chain ends is checked. A 3xx that Chrome doesn't
        // follow has no such request, so it stays recorded as a failure.
        for (const earlier of request.redirectChain()) {
            stylesheets.delete(earlier.url());
        }
        stylesheets.set(request.url(), "still loading");
    });
    const settle = (request) => {
        if (request.resourceType() === "stylesheet") {
            stylesheets.set(request.url(), stylesheetProblem(request));
        }
    };
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
