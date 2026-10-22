# Livequiz proof of concept

A teacher-controlled classroom quiz at `https://quiz.munchboka.no/`.
Uses PHP 8.4 and the **existing Jeopardy MySQL database**. No second database,
WebSocket subscription, Node server or build step is required on the host.
Deployment status is recorded at the end of this file.

## Included

- Separate quiz email-code sign-in using the existing Osloskolen account records.
  Open `/?login=1`; students can join a session without accounts.
- Quiz library, creation, editing, explicit online saves and revision conflict
  checks. One to fifty questions, two to six choices, 5–600 second answer windows.
- One correct choice, multiple correct choices (exact set), or typed accepted
  answers (case/whitespace normalization; no algebraic equivalence or tolerance).
- Text, safe LaTeX via existing local KaTeX assets, literal code blocks, uploaded
  images via existing private Jeopardy media storage, and click-to-load YouTube
  embeds. Code is displayed, not executed. YouTube is an external service; school
  network and video permissions determine actual playback. Projector/player video
  playback is independent, not synchronized. The timer continues during videos.
- Separate six-digit PIN for each session, locally generated QR code, lobby,
  teacher-controlled questions, deadline, reveal, final scoreboard and recovery
  after refreshing the same student tab. Student tokens stay in sessionStorage;
  opening a different tab/device does not recover that player automatically.
- 1000 points for a correct answer, zero otherwise; no speed bonus or partial credit.
- Snapshot isolation: editing a quiz does not change already-created sessions.
- One poll per second per device, non-overlapping requests, retry backoff and
  visible connection status. Server deadlines and first-answer-wins semantics.
- Maximum 60 participants per room and six-hour room access. These are application
  limits, **not a measured hosting capacity guarantee**. New players join only in
  the lobby; existing players may reconnect after the game starts.

## cPanel deployment for quiz.munchboka.no

The quiz is a separate website with a host-only `__Host-livequiz` session cookie.
Jeopardy keeps its own cookie and login challenges. Both sites use `jp_users` and
exactly the same MySQL database and private database credentials.

1. Create `quiz.munchboka.no` with document root `/home/zebfxvix/public_html/quiz`
   and confirm AutoSSL covers it. No extra database is created.
2. In phpMyAdmin select the existing Jeopardy database. Import
   `private/livequiz/schema.sql`: additive `CREATE TABLE IF NOT EXISTS` for
   `lq_quizzes`, `lq_rooms`, `lq_players`, `lq_answers`, and `lq_login`.
3. Build `quiz-subdomain.zip` with `python3 package.py`. Upload it to the account
   home directory, **outside public_html**, and extract to `/home/zebfxvix`.
   It contains `public_html/quiz/*` and `jeopardy-private/livequiz/*` only.
4. Existing `jeopardy-private/database.php`, `app.php`, and `schema.sql` are not
   included or overwritten. The new private app requires the existing `app.php`.
5. Open `https://quiz.munchboka.no/?login=1`. Sign in with an Osloskolen email.
   Quiz emails use the existing verified `noreply@jeopardy.munchboka.no` sender,
   but the subject, body and login link identify Munchboka Livequiz. Quiz challenges
   use `lq_login`; accounts and the global email budget are shared with Jeopardy.
6. Test a small class before expanding. MySQL concurrency and hosting capacity
   must be checked on the real server. A class of 30 polls about 30 times/second.

The public code expects `/home/zebfxvix/jeopardy-private/livequiz/app.php`.
For a different hosting account update that path before packaging. No credentials,
tests or test login are included. KaTeX and math rendering are bundled locally.

Rollback: remove the two new quiz directories. The original Jeopardy files remain
unchanged. New tables may remain pending a retention decision; no destructive
rollback script is provided.

## Automated deployment

`deployment/deploy.sh` pulls `main` from the public GitHub repository and copies
Livequiz and Jeopardy into `~/public_html/quiz`, `~/jeopardy-private/livequiz`,
`~/public_html/jeopardy` and `~/jeopardy-private`. It never deletes files and
does nothing when the commit is unchanged. No terminal is needed; the only
setup is one cPanel → Cron Jobs entry, every 5 minutes, that always runs the
latest script from `main`:

```sh
curl -fsSL https://raw.githubusercontent.com/reneaas/munchboka-edutools/main/deployment/deploy.sh | /bin/bash >> $HOME/deploy.log 2>&1
```

The first run deploys immediately. Check `~/deploy.log` in File Manager for
`deployed <commit>` or an error. Anyone who can push to `main` controls what the
server runs, as with any deployment. `package.py` remains a manual fallback.

## Data, access and limits

Owner checks and CSRF protect teacher actions. Student tokens are 256-bit random
secrets; the database stores only their SHA-256 hashes. A room PIN permits joining,
not hosting or fetching the answer key. Only the current question is exposed;
answers/grades are withheld until the teacher reveals or finishes the game.
Room-scoped image access checks the current question and original ownership.
Answers and room transitions share a room row lock. Duplicate answer retries
acknowledge the first answer without changing its score. Timer expiry closes
submissions server-side. The server reveals the answer automatically when the
timer runs out or every participant has answered (whichever poll sees it first, so
it works even if the teacher's tab is in the background); the teacher can also
reveal early with "Vis fasit nå".

Host screen: options are shown as a 2 x 2 card grid. On reveal, a focused popup
shows the correct option highlighted with a bar chart of how many chose each option
(typed questions show right/wrong/unanswered), then "Vis leaderboard" shows the
top five, and "Neste spørsmål" starts a centred 3-2-1 countdown before the next
question. The chart data is only sent to the host, and only after reveal.

The current auth system treats every verified Osloskolen account alike, so both
teachers and students with those accounts can author/host. There is no staff-role
directory. Participants see nicknames and scores at reveal/end. Encourage aliases.

This is a classroom proof of concept, not a production-scale launch. Join attempts
are throttled per PHP session (two seconds), not globally or per IP; hostile clients
can evade this. There is no moderation, player removal, result export, session
resume across devices, deletion UI, automatic cleanup, or offline draft recovery.
Expiry blocks access but **does not delete** quizzes, participants, answers or
images. Removed images remain under Jeopardy's existing retention behavior and
50 MiB account quota. Agree retention/deletion and privacy arrangements before
wider use. Quizzes retain only their latest saved version; running rooms retain
snapshots. Quiz sign-in uses the existing PHP mail transport and verified sender; joining a game does not collect student email addresses.

## Verification (2026-10-22)

- 71 backend checks passed under PHP 8.4 with an isolated SQLite database, including
  auto reveal on timeout and on all-answered, and host-only answer distribution.
- Separate teacher and mobile student browser contexts passed quiz creation,
  image upload/display, math rendering, code display, PIN/QR generation, all
  three answer types, refresh recovery, answer reveal and the 3000-point final
  score. Missing CSRF and unauthenticated teacher mutations were rejected.
- Desktop lobby and mobile question screenshots were visually inspected.
- JavaScript/Python syntax checks passed. PHP source syntax checks passed.
- Local tests do not verify MySQL
  concurrency, real-school network behavior, QR scanning on a physical phone,
  real YouTube playback and classroom load remain deployment checks.

## Tests and local fixture

`php tests/core.php` runs backend integration checks against SQLite, removing
MySQL's `FOR UPDATE` clause in a test-only PDO subclass. It covers validation,
ownership, revisions, snapshots, hidden answers/scores, participant credentials,
join/answer retries, deadlines, full-game scoring and media scoping. It does not
prove MySQL locking under concurrent load.

For an isolated browser fixture (requires PHP 8.4 with PDO SQLite, Fileinfo and
image metadata support, Python 3, Node and Playwright):

```sh
python3 tests/prepare-local.py /private/tmp/livequiz-browser
php /private/tmp/livequiz-browser/setup.php
LIVEQUIZ_LOCAL=1 LIVEQUIZ_PRIVATE=/private/tmp/livequiz-browser/private/livequiz/app.php php -S 127.0.0.1:8765 -t /private/tmp/livequiz-browser/public
```

In another terminal run `node tests/browser.cjs` with Playwright resolvable, or set
`PLAYWRIGHT_MODULE` to its installed module path. `CHROMIUM_PATH` optionally selects
an existing browser executable. The fixture uses an isolated database and a
**test-only login page**. Never upload the fixture or tests to hosting.

The browser test creates a quiz, uploads an image, checks math/code display,
generates PIN/QR, joins through a separate mobile-sized browser context, answers,
refreshes, reveals and verifies the final score. YouTube embedding is checked
with a locally intercepted frame; it does not verify external video playback.

## Third-party assets

`public/vendor/qrcode.js`: qrcode-generator 1.4.4 by Kazuhiko Arase,
MIT license bundled in `vendor/LICENSE`, obtained from the version-pinned npm
package via jsDelivr. Upstream: https://github.com/kazuhikoarase/qrcode-generator.
No external QR service receives the join URL. KaTeX and math rendering are loaded
from the quiz domain's own bundled local files.

`public/vendor/codemirror/`: CodeMirror 5.65.2 core and Python mode, MIT license
bundled in `vendor/codemirror/LICENSE`, same version already used by the
`interactive-code` directive elsewhere in this project. `code.js` wires it into
the question editor's code field (syntax highlighting, auto-indent) and question
display (read-only, same highlighting). Code is never executed, only displayed.
