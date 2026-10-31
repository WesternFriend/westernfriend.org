/**
 * Tests for scripts/a11y-check.mjs: a page whose stylesheet doesn't load must
 * fail the check, not be scanned as if it were styled.
 *
 * Run with: node --test scripts/a11y-check.test.mjs
 * Like the check itself, it needs `npm ci --include=dev` and a Chrome.
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

const page = (stylesheet) => `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Fixture</title>
<link rel="stylesheet" href="${stylesheet}">
</head>
<body><main><h1>Fixture</h1><p>Some text.</p></main></body>
</html>`;

// Anything not listed here, or in REDIRECTS, is a 404.
const ROUTES = {
    "/styled/": ["text/html", page("/present.css")],
    "/missing-stylesheet/": ["text/html", page("/missing.css")],
    "/not-css/": ["text/html", page("/html-instead.css")],
    "/redirected-stylesheet/": ["text/html", page("/moved.css")],
    "/present.css": ["text/css", "body { color: #111; background: #fff; }"],
    // A 200 the browser won't apply as CSS, as a misrouted URL might return.
    "/html-instead.css": ["text/html", "<!doctype html><title>Oops</title>"],
};

const REDIRECTS = { "/moved.css": "/present.css" };

let server;
let base;

before(async () => {
    server = createServer((request, response) => {
        if (REDIRECTS[request.url]) {
            response.writeHead(302, { Location: REDIRECTS[request.url] });
            response.end();
            return;
        }
        const route = ROUTES[request.url];
        if (!route) {
            response.writeHead(404, { "Content-Type": "text/plain" });
            response.end("Not found");
            return;
        }
        const [type, body] = route;
        response.writeHead(200, { "Content-Type": `${type}; charset=utf-8` });
        response.end(body);
    });
    await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
    base = `http://127.0.0.1:${server.address().port}`;
});

after(() => new Promise((resolve) => server.close(resolve)));

async function check(path) {
    try {
        const { stdout } = await run(process.execPath, [CHECK, base + path]);
        return { code: 0, stdout };
    } catch (error) {
        return { code: error.code, stdout: error.stdout };
    }
}

test("a page whose stylesheet loads is scanned", async () => {
    const { code, stdout } = await check("/styled/");

    assert.equal(code, 0, stdout);
    assert.match(stdout, /^1\/1 page\(s\) scanned/m);
});

test("a stylesheet that returns 404 fails the check", async () => {
    const { code, stdout } = await check("/missing-stylesheet/");

    assert.equal(code, 1, stdout);
    assert.match(
        stdout,
        /stylesheet did not load: \S+\/missing\.css \(HTTP 404\)/,
    );
    assert.match(stdout, /^0\/1 page\(s\) scanned/m);
});

test("a stylesheet served as something other than CSS fails the check", async () => {
    const { code, stdout } = await check("/not-css/");

    assert.equal(code, 1, stdout);
    assert.match(stdout, /stylesheet did not load: \S+\/html-instead\.css /);
    assert.ok(
        stdout.includes(
            "html-instead.css (served as text/html; charset=utf-8, not text/css)",
        ),
        stdout,
    );
    assert.match(stdout, /^0\/1 page\(s\) scanned/m);
});

test("a stylesheet that redirects to CSS counts as loaded", async () => {
    const { code, stdout } = await check("/redirected-stylesheet/");

    assert.equal(code, 0, stdout);
    assert.match(stdout, /^1\/1 page\(s\) scanned/m);
});
