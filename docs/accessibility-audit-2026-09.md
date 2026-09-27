# Accessibility audit — September 2026

Target standard: **WCAG 2.1 Level AA** (the ADA Title II technical standard), with WCAG 2.2 AA
and WAI-ARIA Authoring Practices checked where relevant.

## Method

1. **Static review** of all 113 Django templates, the Tailwind/daisyUI stylesheet, the navigation
   script, and the form classes, checking for semantic HTML, ARIA usage, labels, alt text,
   headings, landmarks, and focus handling.
2. **Automated testing** with [axe-core](https://github.com/dequelabs/axe-core) 4.10 (rule tags
   `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa`, `best-practice`) against 45 rendered
   pages. These include every index page, sample detail pages of each content type, the account
   forms, cart, and checkout. Each page was run in the **light theme, the dark theme, and at a
   320 px viewport**, which is equivalent to 400% zoom for WCAG 1.4.10 Reflow.
3. **Manual keyboard testing** of the skip link, mobile menu, dropdown menus, Escape handling,
   focus return, and visible focus, at mobile and desktop widths.
4. **Form error testing**: failed login, mismatched registration passwords, and an empty checkout
   submission, checking what is announced and how errors are associated with fields.
5. **Contrast measurement** of daisyUI theme colors in both themes.

Result after fixes: **0 axe violations on all 45 pages** in light, dark, and 320 px modes.

## Findings and fixes

| # | Issue | WCAG SC | Severity | Status |
|---|-------|---------|----------|--------|
| 1 | 56 templates nested a second `<main>` inside `base.html`'s `<main>`, and 3 repeated `id="main-content"`, the skip-link target | 1.3.1, 4.1.1 (best practice) | Serious | Fixed |
| 2 | Site navigation used ARIA `menubar`/`menu`/`menuitem` roles without the arrow-key behavior they promise. This also hid invalid list markup: StreamField wrapper `<div>`s inside the `<ul>` | 4.1.2, 1.3.1 | Serious | Fixed; nav is now a plain link list with native `<details>` disclosure |
| 3 | Login, registration, and password-reset pages had an empty `<title>` | 2.4.2 | Serious | Fixed |
| 4 | Account forms never rendered `form.non_field_errors`, so a failed login showed **no message** | 3.3.1 | Critical | Fixed; error summary with `role="alert"` |
| 5 | Django's `aria-describedby`/`aria-invalid` pointed at help and error ids that the templates never rendered | 1.3.1, 3.3.1 | Serious | Fixed with the shared `form_field.html` include |
| 6 | Checkout rendered `required="false"`. `required` is a boolean attribute, so **every optional field became mandatory** | 3.3.2, 4.1.2 | Serious | Fixed; optional fields are also labeled "(optional)" |
| 7 | Checkout and registration personal-data fields had no `autocomplete` tokens | 1.3.5 | Moderate | Fixed |
| 8 | `{% image … alt="Cover of {{ page.title }}" %}` is not interpolated, so screen readers heard the literal text "{{ page.title }}" (book, product, and magazine covers) | 1.1.1 | Serious | Fixed with the `add` filter; regression test added |
| 9 | Image and card blocks used the image *title* (often a filename) or duplicated the caption as alt text, ignoring Wagtail's alt-text `description` field | 1.1.1 | Moderate | Fixed with `default_alt_text` |
| 10 | Dark theme: primary-colored text (breadcrumbs, `link-primary`, outline buttons) was 3.4:1 and `text-blue-600` links were 3.0:1 | 1.4.3 | Serious | Fixed; dark `--color-primary` lightened |
| 11 | daisyUI's `text-error` is 2.9:1 on white; prose figure captions were 3.4:1 | 1.4.3 | Serious | Fixed with dedicated error color and prose caption color |
| 12 | The focus ring (`#aa3f2e`) was 2.6:1 on the dark background | 1.4.11, 2.4.7 | Moderate | Fixed with a dark-theme focus color |
| 13 | Breadcrumb links had `focus:outline-none`, which removed the global focus ring | 2.4.7 | Moderate | Fixed |
| 14 | Escape closed a desktop dropdown while focus stayed on a now-hidden link | 2.4.3 | Moderate | Fixed; focus returns to the `<summary>` |
| 15 | Cart: `role="table"` on the scroll wrapper, a checkout link with `role="button"`, generic "quantity" labels, a duplicate image link, and totals rows without row headers | 1.3.1, 4.1.2, 2.4.4 | Serious | Fixed |
| 16 | Cart and checkout: the button group and a non-wrapping label (`.label` has `nowrap`) caused horizontal scrolling at 320 px; the scrollable tables were not keyboard focusable | 1.4.10, 2.1.1 | Serious | Fixed |
| 17 | Broken `aria-labelledby`/`aria-describedby` references (home page sections, deep archive, magazine issue, book quantity) | 1.3.1, 4.1.2 | Serious | Fixed |
| 18 | Duplicate breadcrumb `<nav>`s on 6 page types, and pagination `<nav>` nested inside another `<nav>` | 1.3.1, 2.4.1 | Moderate | Fixed |
| 19 | Heading level skips (h1 → h3) on deep archive and search | 1.3.1 | Moderate | Fixed |
| 20 | Decorative icons exposed to screen readers (11 templates) | 1.1.1 | Minor | Fixed with `aria-hidden` |
| 21 | Vague link text ("here") on registration | 2.4.4 | Minor | Fixed |
| 22 | Theme toggle outside any landmark, named "Toggle between light and dark modes" with a redundant live region | 1.3.1, 4.1.2 | Minor | Fixed; now a "Dark mode" `switch` in a labeled `<aside>` |
| 23 | Flash messages nested `role="alert"` inside `role="status"` | 4.1.3 | Minor | Fixed |
| 24 | Root font size fixed at `16px`, which overrides the user's browser font-size setting | 1.4.4 (best practice) | Minor | Fixed; now `100%` |

Already in good shape: skip link, `lang` attribute, `:focus-visible` styling, labeled search
forms, the footer's `<address>` markup, and paginator `aria-current`.

## Remaining recommendations (not fixed in code)

These need a content-model decision, editorial process, or design input.

1. **Captions and transcripts (1.2.1, 1.2.2, 1.2.3, 1.2.5).** `blocks.MediaBlock` renders
   `<video>`/`<audio>` with no way to attach a caption track or transcript. Podcasts and
   uploaded media need transcripts. Consider adding a transcript rich-text field and a
   WebVTT `<track>` upload. For oEmbed videos, captions depend on the provider (enable them on
   YouTube and Vimeo).
2. **Editor-chosen heading colors (1.4.3).** `HeadingBlock.color` accepts any color, so editors
   can pick low-contrast text. Restrict it to a vetted palette or remove it.
3. **Alt text workflow (1.1.1).** Templates now use Wagtail's image **Description** field as alt
   text, falling back to the title. Editors should fill in Description for every meaningful
   image. Consider making it required in the image form.
4. **Fixed theme toggle (WCAG 2.2 2.4.11, 2.5.8).** The toggle floats over the top-right of the
   header and sticky navigation, and on small screens it can cover content or focused elements.
   Consider moving it into the navigation bar.
5. **External links.** Links that open a new window announce it inconsistently. Some use
   `aria-label`, others say nothing. Pick one pattern, such as a visible or screen-reader-only
   "(opens in new window)".
6. **Third-party embeds.** The Internet Archive viewer iframe and the PayPal buttons are outside
   our control. Test them with a screen reader and provide alternatives, such as a direct PDF
   link.
7. **Assistive-technology testing.** This audit used automated tools and keyboard testing. Do
   a manual pass with NVDA + Firefox and VoiceOver + Safari (desktop and iOS) before claiming
   conformance, especially on checkout and the magazine reader.
8. **Accessibility statement.** Publish an accessibility statement page with a contact method
   for reporting barriers.

## Preventing regressions

- Render form fields through `common/templates/form_field.html` and add `form_errors.html` to
  every server-rendered form.
- Don't wrap page content in `<main>`, because `base.html` provides it.
- Don't put `{{ }}` inside template-tag arguments; use filters such as `"Cover of "|add:page.title`.
- Check both themes when adding color utilities; prefer the daisyUI semantic colors.
- Regression tests live in `accounts/tests.py` (`AccountPageAccessibilityTest`),
  `orders/tests.py` (`OrderCreateFormAccessibilityTest`), and `store/tests.py`
  (`TestBookPageRenders`). Consider adding axe-core to CI (for example with Playwright and
  `@axe-core/playwright`).
