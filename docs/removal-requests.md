# Requests to change or remove a page

ADR 0005 lets the Internet Archive preserve every public page. That ADR notes
the cost: archived copies outlive our own edits, and the likeliest case is a
memorial or directory entry about a real person, changed at a family's or
member's request.

This page is what to do when that request arrives. We can always act on our
own site. We can only ask the Internet Archive.

## Who decides

The editor decides, the same as for any other editorial change. Nothing here
needs a developer.

Talk to the maintainer before asking the Internet Archive to exclude anything,
since an exclusion can cover a whole domain rather than one page.

## Handling the request

1. **Reply early**, before anything is decided. Say the request has been
   received and that you'll come back with what can and can't be done.
2. **Find the pages.** A person may appear in more than one place: a memorial
   minute, a directory entry, a magazine article, a news item.
3. **Decide what the right change is.** Often it's an edit rather than a
   removal: a correction, a name change, or taking out a detail such as an
   address.
4. **Make the change on our site** (below).
5. **Ask the Internet Archive** only if the archived copy is itself the
   problem (below).
6. **Record it** (below).

### What to tell the requester

Be plain about the split. On westernfriend.org we control what is published
and can change or withdraw it. The Internet Archive is a separate
organisation, and its copies are not ours to delete — we can ask, and it
decides. Don't promise that an archived copy will come down.

## On our site

In the Wagtail admin, open the page and choose one of:

- **Edit and publish.** The page stays public with the change made. Right for
  corrections, and for removing a single detail.
- **Unpublish.** Under **More**, choose **Unpublish**. The page stops being
  public and visitors get "page not found". The content stays in the admin, so
  it can be restored.
- **Make it private.** Under **More**, choose **Privacy**, and restrict to a
  password, to logged-in users, or to a group. The page keeps its address but
  readers can't see it.

Deleting the page outright is rarely the right answer: it is hard to reverse
and leaves nothing to point to if the request is later withdrawn or disputed.

There is no per-page setting to hide a page from search engines. The
**Crawlers and AI** setting applies to the whole site, so it isn't the tool
for a single request. Unpublishing or making the page private is what stops a
page being reached and re-indexed.

## Asking the Internet Archive

The Archive has no removal form for this. Send a request to
**info@archive.org** and include
([Internet Archive help](https://help.archive.org/help/how-do-i-request-to-remove-something-from-archive-org/)):

- the URL or URLs of the material;
- the time period you'd like excluded;
- the time period during which you controlled the site;
- anything else that helps explain the request.

Say explicitly if you're also asking that the pages not be captured again, as
the Archive's wording is about material already collected.

Western Friend controls westernfriend.org, so the request should come from the
publication rather than from the family, and should say so.

### What this can't promise

The Archive's own wording is that a request "will initiate a review by our
team" and that "we do not make any guarantees beforehand about the outcome of
a request". Take that at face value when setting expectations:

- **No promised outcome.** The Archive decides, at its discretion. It
  publishes no criteria and no appeal.
- **No promised timeframe.** The Archive doesn't publish one for removal
  requests.
- **Excluded usually means hidden, not erased.** An excluded page returns
  "This URL has been excluded from the Wayback Machine". Whether the
  underlying copy is destroyed is not something the Archive states.
- **It covers the Wayback Machine only.** Other services that keep copies,
  such as archive.today, are separate organisations with their own processes.
- **Copies already taken are beyond reach.** Screenshots, PDFs, citations and
  republished text aren't affected by anything the Archive does.

Adding a `robots.txt` rule is not a way to do this. Since 2017 the Archive has
moved away from treating `robots.txt` as an instruction to hide what it has
already collected, and existing snapshots of sites that block its crawler
today remain publicly viewable. Asking directly is the route that works.

Note also that some guides still describe an exclusion form at
`archive.org/about/exclude.php`. That page no longer exists.

### Requests about someone who has died

The Archive publishes no policy for memorials, obituaries, or requests from
family members, and no special standing for next of kin. Such a request goes
through the same general route, at the same discretion.

This is worth saying gently to a grieving family rather than discovering it
late: what we can do on our own site is certain, and what the Archive does
is not.

## Recording the request

Keep a short note, so a later question can be answered without relying on
memory:

- who asked, and when;
- what they asked for;
- what was decided, and by whom;
- what changed on our site, and when;
- whether the Internet Archive was asked, when, and what it said.

Keep it where editorial records are kept, not in this repository, since it
concerns a named person.
