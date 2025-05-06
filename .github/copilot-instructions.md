# Copilot Instructions

## Package Management

We use `uv` for package management, not `pip`. E.g. `uv add <package-name>` or `uv sync`.

We use the Django framework for tests, not `unittest` or `pytest`. To run tests, use the Django management command `manage.py test <path-to-specific-test>`.

## CSS Styles

We're moving towards using Tailwind CSS with daisyUI components. There may be some residual Bootstrap CSS in the codebase, but we are gradually removing it. Please use Tailwind CSS and daisyUI components for new styles.

Make sure to use the Context7 tool to fetch the latest Tailwind CSS 4.x and daisyUI 5.x style rules so our styles are up to date.
