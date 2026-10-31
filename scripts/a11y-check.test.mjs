/**
 * Tests for scripts/a11y-check.mjs: a page whose stylesheet doesn't load must
 * fail the check, not be scanned as if it were styled.
 *
 * Run with: node --test scripts/a11y-check.test.mjs
 * Like the check itself, it needs `npm ci --prefix scripts` and a Chrome.
 */

import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { createServer } from "node:http";
import process from "node:process";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const run = promisify(execFile);
const CHECK = fileURLToPath(new URL("./a11y-check.mjs", import.meta.url));

const CSS = "body { color: #111; background: #fff; }";

const page = (stylesheet, extra = "") => `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Fixture</title>
<link rel="stylesheet" href="${stylesheet}">
${extra}
</head>
<body><main><h1>Fixture</h1><p>Some text.</p></main></body>
</html>`;

// Adds a stylesheet once the page has loaded, so it is still in flight when
// the check runs.
const ADD_STYLESHEET_AFTER_LOAD = `<script>
window.addEventListener("load", () => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "/never.css";
    document.head.append(link);
});
</script>`;

const html = (body) => (request, response) => {
    response.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    response.end(body);
};
const css = (type) => (request, response) => {
    response.writeHead(200, type ? { "Content-Type": type } : {});
    response.end(CSS);
};
const redirect = (location) => (request, response) => {
    response.writeHead(302, location ? { Location: location } : {});
    response.end();
};

let revalidations = 0;

// Anything not listed here is a 404.
const ROUTES = {
    "/styled/": html(page("/present.css")),
    "/present.css": css("text/css"),
    "/missing-stylesheet/": html(page("/missing.css")),
    "/not-css/": html(page("/html-instead.css")),
    "/html-instead.css": html("<!doctype html><title>Oops</title>"),
    "/css-subtype/": html(page("/css-foo.css")),
    "/css-foo.css": css("text/css-foo"),
    // Chrome applies a stylesheet that has no Content-Type at all.
    "/untyped-stylesheet/": html(page("/untyped.css")),
    "/untyped.css": css(null),
    "/unknown-type/": html(page("/unknown.css")),
    "/unknown.css": css("application/x-unknown-content-type"),
    // A repeated Content-Type: Chrome goes by the last one.
    "/repeated-type/": html(page("/css-last.css")),
    "/css-last.css": (request, response) => {
        response.writeHead(200, ["Content-Type", "text/html", "Content-Type", "text/css"]);
        response.end(CSS);
    },
    "/repeated-type-not-css/": html(page("/html-last.css")),
    "/html-last.css": (request, response) => {
        response.writeHead(200, ["Content-Type", "text/css", "Content-Type", "text/html"]);
        response.end(CSS);
    },
    // With nosniff, Chrome won't apply a stylesheet that has no Content-Type.
    "/nosniff-untyped/": html(page("/nosniff.css")),
    "/nosniff.css": (request, response) => {
        response.writeHead(200, { "X-Content-Type-Options": "nosniff" });
        response.end(CSS);
    },
    "/cut-short/": html(page("/cut.css")),
    "/cut.css": (request, response) => {
        response.writeHead(200, { "Content-Type": "text/css", "Content-Length": "5000" });
        response.write(CSS);
        setTimeout(() => request.socket.destroy(), 100);
    },
    // A 304 when Chrome had nothing cached to revalidate.
    "/unasked-304/": html(page("/stale.css")),
    "/stale.css": (request, response) => {
        response.writeHead(304);
        response.end();
    },
    "/redirected-stylesheet/": html(page("/moved.css")),
    "/moved.css": redirect("/present.css"),
    "/redirected-to-missing/": html(page("/moved-away.css")),
    "/moved-away.css": redirect("/missing.css"),
    // A 3xx with no Location is a final response, not a redirect.
    "/unfollowed-redirect/": html(page("/nowhere.css")),
    "/nowhere.css": redirect(null),
    "/dropped-connection/": html(page("/dropped.css")),
    "/dropped.css": (request) => request.socket.destroy(),
    "/late-stylesheet/": html(page("/present.css", ADD_STYLESHEET_AFTER_LOAD)),
    "/never.css": () => {}, // never answers
    // Two pages sharing a stylesheet Chrome revalidates on the second visit.
    "/cached-first/": html(page("/cached.css")),
    "/cached-second/": html(page("/cached.css")),
    "/cached.css": (request, response) => {
        if (request.headers["if-modified-since"]) {
            revalidations += 1;
            response.writeHead(304);
            response.end();
            return;
        }
        response.writeHead(200, {
            "Content-Type": "text/css",
            "Last-Modified": "Sat, 31 Oct 2026 00:00:00 GMT",
            "Cache-Control": "no-cache",
        });
        response.end(CSS);
    },
};

let server;
let base;

before(async () => {
    server = createServer((request, response) => {
        const route = ROUTES[request.url];
        if (route) {
            route(request, response);
            return;
        }
        response.writeHead(404, { "Content-Type": "text/plain" });
        response.end("Not found");
    });
    await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
    base = `http://127.0.0.1:${server.address().port}`;
});

after(() => {
    server.closeAllConnections();
    return new Promise((resolve) => server.close(resolve));
});

// Runs the checker on the given paths. `output` has stderr too, so a setup
// failure (no Chrome, packages not installed) shows in the assertion message.
async function check(...paths) {
    const urls = paths.map((path) => base + path);
    try {
        const { stdout, stderr } = await run(process.execPath, [CHECK, ...urls], {
            timeout: 120000,
        });
        return { code: 0, stdout, output: stdout + stderr };
    } catch (error) {
        const stdout = error.stdout ?? "";
        return {
            code: error.code,
            stdout,
            output: `${stdout}${error.stderr ?? ""}${error.message}`,
        };
    }
}

function assertPasses({ code, stdout, output }, pages = 1) {
    assert.equal(code, 0, output);
    assert.match(
        stdout,
        new RegExp(`^${pages}/${pages} page\\(s\\) scanned`, "m"),
        output,
    );
}

const escapeRegExp = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

// `reason` is the exact text, or a RegExp for one that varies.
function assertFailsOn({ code, stdout, output }, stylesheet, reason) {
    assert.equal(code, 1, output);
    const why = reason instanceof RegExp ? reason.source : escapeRegExp(reason);
    const url = escapeRegExp(base + stylesheet);
    assert.match(
        stdout,
        new RegExp(`stylesheet did not load: ${url} \\(${why}\\)`),
        output,
    );
    assert.match(stdout, /^0\/1 page\(s\) scanned/m, output);
}

test("a page whose stylesheet loads is scanned", async () => {
    assertPasses(await check("/styled/"));
});

test("a stylesheet that returns 404 fails the check", async () => {
    assertFailsOn(await check("/missing-stylesheet/"), "/missing.css", "HTTP 404");
});

test("a stylesheet served as HTML fails the check", async () => {
    assertFailsOn(
        await check("/not-css/"),
        "/html-instead.css",
        "served as text/html; charset=utf-8, not CSS",
    );
});

test("a stylesheet served as a type that only starts with text/css fails", async () => {
    assertFailsOn(
        await check("/css-subtype/"),
        "/css-foo.css",
        "served as text/css-foo, not CSS",
    );
});

test("a stylesheet with no Content-Type counts as loaded, as Chrome applies it", async () => {
    assertPasses(await check("/untyped-stylesheet/"));
});

test("a stylesheet that redirects to CSS counts as loaded", async () => {
    assertPasses(await check("/redirected-stylesheet/"));
});

test("a stylesheet that redirects to a 404 fails the check", async () => {
    assertFailsOn(await check("/redirected-to-missing/"), "/missing.css", "HTTP 404");
});

test("a 3xx that Chrome doesn't follow fails the check", async () => {
    assertFailsOn(await check("/unfollowed-redirect/"), "/nowhere.css", "HTTP 302");
});

test("a stylesheet whose connection drops fails the check", async () => {
    assertFailsOn(await check("/dropped-connection/"), "/dropped.css", /net::ERR_\w+/);
});

test("a stylesheet whose body is cut short fails the check", async () => {
    assertFailsOn(await check("/cut-short/"), "/cut.css", /net::ERR_\w+/);
});

test("a stylesheet with no Content-Type fails when nosniff is set", async () => {
    assertFailsOn(await check("/nosniff-untyped/"), "/nosniff.css", /net::ERR_\w+/);
});

test("a stylesheet with the unknown-type placeholder counts as loaded", async () => {
    assertPasses(await check("/unknown-type/"));
});

test("a repeated Content-Type header is read as its last value", async () => {
    assertPasses(await check("/repeated-type/"));
    assertFailsOn(
        await check("/repeated-type-not-css/"),
        "/html-last.css",
        "served as text/html, not CSS",
    );
});

test("a 304 when Chrome had no cached copy fails the check", async () => {
    assertFailsOn(
        await check("/unasked-304/"),
        "/stale.css",
        "HTTP 304 to a request with no cached copy",
    );
});

test("a stylesheet still loading when the check runs fails it", async () => {
    assertFailsOn(await check("/late-stylesheet/"), "/never.css", "still loading");
});

test("a stylesheet Chrome revalidates with a 304 counts as loaded", async () => {
    revalidations = 0;

    assertPasses(await check("/cached-first/", "/cached-second/"), 2);
    // Otherwise the second page never exercised the 304.
    assert.ok(revalidations > 0, "the second page never revalidated cached.css");
});
