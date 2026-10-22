# Jeopardy maker

Hosted at https://jeopardy.munchboka.no with PHP 8.4 and MySQL on Domene.no.
The directory name `pilot` is retained for deployment continuity. Registration is open to teachers and students who verify an @osloskolen.no email address.

## Features

- New games start with an empty title and no categories or sample questions.
  Users name each category when adding it and can remove every category, including
  the last. Up to eight categories and one to eight shared point rows (1–10000).
  Named drafts with zero categories can be saved; playback asks the user to add one.
- Question and answer text with inline `$...$` and display `$$...$$` LaTeX.
- Local KaTeX 0.16.22 assets and fonts, MIT license included. No external CDN.
  Rendering uses `trust: false`, bounded expansion/size, escaped plain text,
  and a visible raw expression for invalid math.
- One optional PNG, JPEG or WebP image on each question and answer, including
  image-only content. Editable image descriptions and live previews.
- Explicit online saving, revision checks and retained revision snapshots.
  Network/validation failures leave the editor contents in the current tab.
  Unsaved edits trigger a navigation warning. No autosave or offline draft store.
- Existing single-category pilot games normalize in memory; historical revisions
  are preserved. Gameplay still uses the shared package's Jeopardy runtime.

## Deployment layout

- `private/app.php` and `private/schema.sql` → `/home/zebfxvix/jeopardy-private/`
- `public/*`, including `.htaccess` and `vendor/` → `/home/zebfxvix/public_html/jeopardy/`
- Existing `jeopardy-private/database.php` remains private and is never included
  in a source archive or overwritten during deployment.

The schema is additive (`CREATE TABLE IF NOT EXISTS`); no tables are dropped.
The new `jp_media` table stores image bytes as MEDIUMBLOB, so game content and
images are covered by the same database backup. Original filenames are not stored.
Uploads require login and CSRF, are limited to 2 MiB and 16 megapixels (8000 px
per dimension), and are checked with Fileinfo and image metadata. Only PNG,
JPEG and WebP MIME types are served. SVG and arbitrary HTML are not accepted.
Images are never placed in the executable/public filesystem. The media endpoint
requires ownership and serves a fixed validated Content-Type with nosniff.
A locked per-account check enforces a 50 MiB quota. Removed/replaced images remain
stored to keep old revisions intact; media cleanup/library management is future work.

## Authentication

Email uses PHP `mail()` and `noreply@jeopardy.munchboka.no`. SPF and DKIM were
valid in cPanel; delivery to the pilot account was verified. Domain-wide
registration is enabled; accounts are created only after code verification. Codes expire after ten minutes, are hashed,
single-use, session-bound, limited to five attempts, and throttled to one request
per minute / five per hour per address, plus 500 requests per hour across the service. The global budget uses a locked database row and records no IP addresses. Sessions use Secure, HttpOnly, SameSite=Lax host-only
cookies and an eight-hour application expiry. All mutations require CSRF tokens.

## Verification (2026-10-15)

- PHP 8.4 syntax checks and JavaScript syntax checks passed.
- `tests/core.php`: 76 checks passed, covering login, ownership, revisions,
  legacy normalization, multiple categories, LaTeX preservation, image ownership,
  image-only questions, alt text, escaping, invalid types and upload limits.
  Tests use SQLite with adapted MySQL locking syntax; concurrency requires MySQL.
- Live hosting: uploaded a PNG, edited inline math and display square roots,
  saved and reloaded it, added a second category with fractions/derivatives,
  verified incomplete content is rejected without clearing editor fields,
  and played the saved question/image/answer. Visually checked rendered math.
- Prior release: login email received and successful sign-in/save/reopen verified.

Operational follow-up: privacy notice,
account/deletion and media retention workflows, backup restore, session recovery,
and publishing/sharing requirements. Games and media are private unless the owner explicitly shares a saved snapshot.

## Theme and registration release (2026-10-15)

The `Utseende` selector offers light, dark and system modes. The choice is stored
in localStorage, applied before page paint and shared across tabs. App and player
use the same html data-theme value. Inputs, cards, previews, notices and errors
have theme-specific colors. Browser checks verified the light player modal,
dark editor, navigation persistence and signed-out registration page. The live
server rejected an outside-domain address without sending mail.

The registration tests cover teacher/student addresses, lookalike domains,
case handling, separate verified accounts, repeat login, saving and cross-account
access rejection. No email was sent to an invented teacher/student address.
A second person's real inbox delivery has not been tested.

Category update: live browser verified a blank new game, creation of a user-named
Historie category with empty questions, and removal of that last category. Existing
unsaved user work was left open in its original tab; verification used a new tab.

## Link sharing (2026-10-15)

Owners can use Del spill / Kopier lenke / Oppdater delt versjon / Stopp deling in
the editor. Sharing requires a saved nonempty game without unsaved changes.
`jp_shares` holds one explicitly published content snapshot and revision per game,
with a random 256-bit token. Later saves do not change the snapshot. Updating it
keeps the link; revoking removes access and sharing again generates a new token.
Owner and CSRF checks apply to all sharing mutations, with game-row locks and
revision checks. Public pages contain the selected game and no owner email or
editing controls. Public image requests validate the active token, membership
in the snapshot, and image ownership. A token cannot expose unrelated images.
Shared responses are no-store, noindex and no-referrer; all rendering remains
escaped and uses the same math and image pipeline. Revocation prevents future
requests; content already loaded or copied by recipients cannot be recalled.

76 backend checks passed, including public access, ownership, snapshot isolation,
image scoping, revocation and token rotation. Live browser checks opened the test
game in Incognito without login, played a question, displayed its PNG and LaTeX
answer, revoked the link and confirmed that a fresh anonymous request was denied.
The sample game was returned to private after verification.

## Educational presentation update (2026-10-17, deployed)

Public title/description and visible introduction emphasize subject revision,
classroom collaboration and teacher/student authoring. A public `?about=1` page
explains purpose, user-created content, account restrictions and sharing without
claiming official Osloskolen affiliation. Main navigation uses undervisningsquiz.
Jeopardy remains explicitly described as the activity format. Anonymous public
home/about pages permit indexing; authenticated, shared and other pages retain
noindex. This is truthful presentation, not a guarantee of filter categorization.
See SCHOOL-IT.md for a draft category-review request. No request has been sent.

PHP syntax passed. Browser access was restored and jeopardy-education-v6.zip
was uploaded and extracted through cPanel; the extraction result confirmed
public_html/jeopardy/index.php. Incognito verification confirmed the live public
homepage, educational title and introduction, and navigation to the complete
about page. The homepage layout was visually checked in dark mode. No
credentials, schema or saved content were changed.

### Heading follow-up (2026-10-17, deployed)

Restored Jeopardy as the public heading and brand at the owner’s request.
Page and Open Graph titles retain “for lærere og elever”; the educational
introduction, metadata description and about page remain. Deployed
jeopardy-heading-v7.zip via cPanel and verified the anonymous live homepage.
