// Renders CI check results as Markdown. Used by ci.yml for the run's Summary
// tab and by comment-on-pr.yml for the PR comment.
//
// The result files come from a pull request's own CI run, and a PR can edit
// ci.yml, so their contents are untrusted. Only three things are taken from
// them: which known checks ran, whether each passed, and each check's output.
// Check names and fix commands come from CHECKS below, and output is only ever
// shown inside a code block, so a result file can't add links, headings, or
// @-mentions to a comment posted as github-actions[bot].
const fs = require('fs');
const path = require('path');

// Keys match the `checks` keys written by each job in ci.yml.
const CHECKS = {
  'pre-commit': {
    job: 'lint',
    label: 'pre-commit hooks (ruff, formatting, templates)',
    fix: 'uv run pre-commit run --all-files',
  },
  'django-check': {
    job: 'test',
    label: 'Django system checks',
    fix: 'uv run python manage.py check --fail-level WARNING',
  },
  migrations: {
    job: 'test',
    label: 'Missing migrations',
    fix: 'uv run python manage.py makemigrations',
  },
  tests: {
    job: 'test',
    label: 'Tests',
    fix: 'uv run python manage.py test --exclude-tag seed',
  },
  'seed-tests': {
    job: 'seed',
    label: 'Development content seeding tests',
    fix: 'uv run python manage.py test --tag seed',
  },
};

// Keep both ends of long output: the first error is usually near the start,
// and the summary (e.g. "FAILED (failures=2)") at the end.
const HEAD = 2000;
const TAIL = 3000;

function clip(text) {
  if (text.length <= HEAD + TAIL) return text;
  const omitted = text.length - HEAD - TAIL;
  return `${text.slice(0, HEAD)}\n\n… ${omitted} characters omitted; see the full log in the workflow run …\n\n${text.slice(-TAIL)}`;
}

// Fence with more backticks than the longest run in the text, so output can't
// close the code block early (e.g. a diff of a Markdown file containing ```).
function fenceFor(text) {
  const runs = (text.match(/`+/g) || []).map((run) => run.length + 1);
  return '`'.repeat(Math.max(3, ...runs));
}

// Reads every <dir>/*/result.json and returns every check in CHECKS, in order,
// as { key, passed, missing, output }. A check with no result (its job crashed,
// or the artifact didn't download) counts as failed, so missing results can
// never read as "All checks passed".
function readResults(dir) {
  const found = new Map();
  if (fs.existsSync(dir)) {
    for (const entry of fs.readdirSync(dir)) {
      const file = path.join(dir, entry, 'result.json');
      if (!fs.existsSync(file)) continue;
      let parsed;
      try {
        parsed = JSON.parse(fs.readFileSync(file, 'utf8'));
      } catch {
        continue;
      }
      for (const [key, check] of Object.entries(parsed?.checks ?? {})) {
        if (!Object.hasOwn(CHECKS, key) || found.has(key)) continue;
        found.set(key, {
          key,
          passed: check?.outcome === 'success',
          missing: false,
          output: typeof check?.output === 'string' ? check.output : '',
        });
      }
    }
  }
  return Object.keys(CHECKS).map(
    (key) => found.get(key) ?? { key, passed: false, missing: true, output: '' },
  );
}

// results: from readResults(). problems: short, trusted descriptions of
// failures the checks don't explain (e.g. a job that failed while installing
// dependencies). author: PR author to greet when something failed, or null.
function render({ results, problems = [], runUrl, author = null }) {
  const failures = results.filter((r) => !r.passed && !r.missing);
  const anyFailed = results.some((r) => !r.passed) || problems.length > 0;

  const status = (r) => {
    if (r.missing) return `⚠️ No result reported ([see the workflow run](${runUrl}))`;
    return r.passed ? '✅ Passed' : '❌ Failed';
  };
  const rows = [
    ...results.map((r) => `| ${CHECKS[r.key].label} | ${status(r)} |`),
    ...problems.map((problem) => `| ${problem} | ⚠️ [See the workflow run](${runUrl}) |`),
  ];

  const details = failures.flatMap((r) => {
    const output = clip(r.output || '(no output captured)');
    const fence = fenceFor(output);
    return [
      `<details><summary>❌ ${CHECKS[r.key].label}</summary>`,
      '',
      fence,
      output,
      fence,
      '',
      `Run \`${CHECKS[r.key].fix}\` locally to reproduce and fix.`,
      '</details>',
      '',
    ];
  });

  const greeting =
    author && anyFailed
      ? [`👋 Hi @${author}, thanks for the pull request! Please take a look at the failing checks below before this is merged.`, '']
      : [];
  const tip = failures.some((r) => r.key === 'pre-commit')
    ? ['💡 Run `uv run pre-commit install` once and these hooks will fix most issues automatically each time you commit.', '']
    : [];

  return [
    ...greeting,
    '## CI results',
    '',
    '| Check | Result |',
    '|---|---|',
    ...rows,
    '',
    ...(details.length ? ['## Failures', '', ...details, ...tip] : []),
    ...(anyFailed ? [] : ['All checks passed. 🎉', '']),
    `[Full workflow run](${runUrl})`,
  ].join('\n');
}

module.exports = { CHECKS, readResults, render };
