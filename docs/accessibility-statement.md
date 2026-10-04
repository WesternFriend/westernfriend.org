# Accessibility statement

The site links to an accessibility statement from the footer on every page.
The link appears once a live page with the slug `accessibility` is published,
so it is never a dead link while the page is being drafted.

## Publishing it

1. In the Wagtail admin, add a child page under the home page, choosing the
   **Page** content type (the `WfPage` model). The home page offers several
   child types; the generic Wagtail *Page* used in the tests cannot be added
   through the editor and has no body to hold the wording.
2. Title it **Accessibility**, and set the slug to `accessibility`.
3. Paste the wording below into the page body, edit it to suit, and publish.
4. The footer link appears on every page.

Or run `./manage.py create_accessibility_statement` to create the page as an
unpublished **draft**, pre-filled with the wording below, for an editor to
review and publish. The command does not publish it — the text makes a public
claim on Western Friend's behalf and a person has to stand behind it.

The editor owns this text. The draft below is a starting point, not something
to publish unread: it makes a public claim about the site on Western Friend's
behalf, and the contact address has to be one somebody actually reads.

## Keeping it true

A statement that lists problems that have been fixed, or omits ones that
haven't, is worse than none. Review it whenever an item in
`docs/accessibility-audit-2026-09.md` is fixed or added.

---

## Draft wording

**Accessibility**

Western Friend wants everyone to be able to read what we publish, including
people who use screen readers, keyboards, magnification, or speech input.

**What we aim for**

We aim to meet the Web Content Accessibility Guidelines (WCAG) 2.2 at level
AA across westernfriend.org.

**Where we currently fall short**

We had the site reviewed in September 2026. These are the problems we know
about and have not yet fixed:

- **Audio and video have no captions or transcripts.** Podcasts and uploaded
  video are published without them. Where a video is hosted on YouTube or
  Vimeo, any captions are the ones that service provides.
- **Some embedded material is outside our control.** The Internet Archive
  reader and the PayPal payment buttons come from other organisations, and we
  cannot change how they behave with assistive technology. If one of them
  blocks you, write to us and we will get you what you need another way.
- **Our testing has limits.** The review used automated checks and keyboard
  testing. We have not yet done a full pass with a screen reader, so there
  will be problems we have not found. Please tell us about them.

**Telling us about a problem**

If something on this site stops you reading it, please write to
[editor@westernfriend.org](mailto:editor@westernfriend.org) or call
(503) 487-2945. Tell us the page and what happened, and we will reply and say
what we can do.

If you need an article in another form, ask, and we will send it to you.

**This statement**

Last reviewed: *(date the editor publishes it)*.
