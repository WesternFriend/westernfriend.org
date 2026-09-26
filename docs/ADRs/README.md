# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records for the Western Friend website.

An ADR captures a significant technical decision: what was decided, why, and what the trade-offs are. ADRs are written once and rarely changed — if a decision is reversed, a new ADR supersedes the old one rather than editing it.

## When to write an ADR

Write an ADR when you make a decision that:

- Is non-obvious and would surprise a future contributor
- Has meaningful trade-offs that were weighed
- Cannot be reversed cheaply (or reversal requires its own decision)
- Explains *why* the code looks the way it does

Examples: choosing a sanitization strategy, adding a caching layer, selecting a third-party library, deviating from a framework's default behavior.

Skip the ADR for routine implementation choices, bug fixes, or anything that is self-evident from the code.

## Naming convention

```
NNNN-short-hyphenated-title.md
```

Use the next available four-digit number. Titles should be descriptive but concise.

## How to write an ADR

Copy `_template.md` and fill in each section. Keep the language direct — future contributors (and AI agents) should be able to read an ADR in under two minutes.

## Updating ADRs

- **Do not edit** a previously accepted ADR to change its decision.
- If a decision is superseded, set its `Status` to `Superseded by ADR NNNN` and write a new ADR.
- Minor corrections (typos, broken links) are acceptable without a new ADR.
