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
  images via existing private Jeopardy media storage, and automatically loaded YouTube
  embeds. Active questions request autoplay with sound; results do not restart playback.
  Video fades in after four uninterrupted seconds in the YouTube PLAYING state.
  Buffering, pause and end hide it immediately and reset the reveal timer. Pointer
  and keyboard interaction with the iframe are disabled; separate Play/Pause controls
  provide a fallback when audible autoplay is blocked. Removed players are destroyed.
  This is a best-effort timing workaround: YouTube offers no title-visibility event,
  and four seconds does not guarantee that titles/captions will be absent. Hiding
  playback is not compliant with YouTube's visible-player requirements.
  Captions are requested off, but YouTube may honor viewer preferences. YouTube no
  longer supports hiding titles, and subtitles burned into the video image cannot be removed. Code is displayed, not executed. YouTube is an external service; school
  network and video permissions determine actual playback. YouTube playback is host-only; participant screens never create a player,
  request YouTube resources or receive the video ID, including on results.
  Students hear the host’s speakers. The timer continues during videos.
- Separate six-digit PIN for each session, locally generated QR code, lobby,
  teacher-controlled questions, deadline, reveal, final scoreboard and recovery
  after refreshing the same student tab. Student tokens stay in sessionStorage;
  opening a different tab/device does not recover that player automatically.
- Quiz-level scoring choice: fixed 1000 points, or speed scoring from 1000 at the
  start to zero at the deadline (500 halfway), rounded to the nearest integer.
  Formula: `round(1000 * (1 - elapsed / time_limit))`, clamped to 0–1000.
  A correct answer that rounds to zero still counts as correct in results.
  Only fully correct answers earn points; incorrect answers earn zero.
  Speed uses server processing time and the question deadline, never client timestamps.
  YouTube questions keep full points for the first four seconds from the server's
  question start. Afterwards the score decreases to zero at the existing deadline:
  `round(1000 * remaining / (time_limit - 4))`, clamped to 0–1000. A 30-second
  video question gives 1000 through second 4, 500 at second 17, and zero at 30.
  This grace period is not synchronized to actual host playback or buffering.
  Network delay and video time beyond the grace period count toward elapsed time.
  Existing quizzes/rooms default to fixed scoring. Each room snapshots its scoring
  choice, so edits affect newly created games only. No database migration needed.
- Snapshot isolation: editing a quiz does not change already-created sessions.
- One poll per second per device (every 200 ms during the transition countdown), non-overlapping requests, retry backoff and
  visible connection status. Server deadlines and first-answer-wins semantics.
- Maximum 60 participants per room and six-hour room access. These are application
  limits, **not a measured hosting capacity guarantee**. New players may join an
  unfinished game and receive its current state; existing players may reconnect.

## Randomized team play

In the host lobby, select **Individuelt spill** (default) or **Tilfeldige lag**,
set **Maks antall spillere per lag** (default 3, integer 2–60), then click
**Lagre spillmodus**. Unsaved settings block starting. Individual rooms follow
exactly the existing question/results/leaderboard/countdown flow.

For team rooms, **Fordel lag og start** locks the room and reads the current lobby
roster. `teams.php` computes `K = ceil(N / M)` and rejects an empty roster or
`floor(N / K) < M - 1`, leaving the lobby and settings intact. It uses an unbiased
Fisher–Yates shuffle (`random_int`) and deals players round-robin into K teams.
For N=13, M=3, the correct sizes are **[3,3,3,2,2]**; [3,2,2,2,2] totals only 11.

Settings and assignments live in the room's existing `content` JSON under `play`.
No schema migration, second database or new service is required. Old rooms without
this key default to individual mode. Assignment and the transition to
`TEAM_OVERVIEW` commit in one transaction, using the same room lock and version
checks as joining, answering and progression. A failed or duplicate start cannot
persist a partial assignment or reshuffle teams. Polling only reads assignments.

The host sees all team cards; participants see their own team. The host continues
from the overview into the synchronized three-second `COUNTDOWN`, then question 0.
Subsequent lifecycle transitions are unchanged. Only the host may configure or
advance a room. Settings lock once assignments are made. Team games reject new
participants after that point; existing browser tokens reconnect to the same team.
Individual games still allow late joins. Disconnected players remain eligible,
but the question deadline always closes the question, so nobody blocks it forever.

Answers and points remain individual, including the optional speed-scoring mode
and video grace period already supported by the app. No new timing-based scoring
is introduced by teams. Charts still count each individual answer. The team
leaderboard sums authoritative stored member scores through `lq_team_total`;
it does not maintain a separate counter that retries could increment twice.
Scores accumulate across questions. Ties use team number ascending for a stable
order. Sum scoring intentionally gives larger teams more potential points than
smaller ones. Team identities, members and personal membership are consistent
across polling and refreshes. Refresh existing tabs after deployment.

Team-specific tests: `php tests/teams.php` (also runs `core.php`) and
`node tests/teams-browser.cjs` against the disposable fixture below. The backend
suite covers all specified examples and every N=1–60/M=2–60 combination. The
browser suite uses one host and five independently authenticated participant tabs,
including a disconnected player. SQLite and the local PHP server do not establish
MySQL/InnoDB concurrency guarantees or classroom load capacity.

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
answers/grades are withheld until the question ends or the teacher finishes the game.
Room-scoped image access checks the current question and original ownership.
Answers and room transitions share a room row lock. Duplicate answer retries
acknowledge the first answer without changing its score. Timer expiry closes
submissions server-side. The server reveals the answer automatically when the
timer runs out or every participant has answered. The last accepted answer checks
this inside the same transaction; any authenticated poller also checks deadlines,
so an inactive host tab does not stop the game. The teacher can still reveal early
with "Vis fasit nå".

### Synchronized lifecycle

The server returns a canonical `state` and a monotonically increasing `version`.
Existing short `phase` values remain in the database and API for stored-room
compatibility:

| State | Stored phase | Transition |
| --- | --- | --- |
| `LOBBY` | `lobby` | Host starts the first question |
| `QUESTION_ACTIVE` | `question` | All participants answered, deadline, or host reveal |
| `QUESTION_RESULTS` | `reveal` | Host selects "Vis leaderboard" |
| `LEADERBOARD` | `leaderboard` | Host selects "Neste spørsmål" or final results |
| `COUNTDOWN` | `countdown` | Server countdown deadline starts the next question |
| `QUIZ_FINISHED` | `finished` | Terminal state |

Every manual transition checks owner, CSRF, current version and allowed source
state. Stale/repeated controls return an error without advancing again. Room locks
serialize controls, answers, joins and state snapshots. Scores still come solely
from the persisted answers using the room’s fixed or speed scoring choice; wrong answers always earn zero.

All clients show centered dialogs with blurred backdrops. Four-choice questions
use a 2 x 2 grid; existing two-to-six-choice, multi-answer and text questions are
preserved. Participants select cards and confirm with "Send svar"; the inputs lock
while submitting and after acknowledgement. Results include the original question,
correct alternatives and server-derived counts, including zero-count alternatives.
Text questions show accepted answers and right/wrong/unanswered counts. Everyone
sees the full ranked leaderboard; only the host sees progression buttons.

`countdown_end`, `deadline` and `now` are Unix seconds (possibly fractional) in the
API. The countdown lasts three seconds; clients display its remaining time, never
advance the game locally. After expiry, the next authorized poll starts the next
question with its deadline anchored to the countdown end. If all clients go away,
reconnecting catches up to that deadline, not a restarted timer. Observed state
changes are subject to network/polling latency, not frame-perfect broadcasts.

All registered room participants are eligible, including late joins during an
active question. Disconnected players stay in the roster and retain scores; they
can delay all-answered completion only until the existing question deadline
(5–600 seconds). There is no heartbeat-based removal or connection-based scoring.

No SQL migration is required. The existing BIGINT deadline column accepts precise
millisecond deadlines for new countdowns/subsequent questions; legacy second-based
deadlines are still recognized. Saved quizzes, answers and room snapshots are not
rewritten. Refresh already-open browser tabs after deploying the PHP and JS update
so they stop using the old host-local leaderboard/countdown controls.

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

- 96 backend checks passed under PHP 8.5.12 with an isolated SQLite database,
  including state sequencing, deadlines, retry safety and unchanged scoring.
- Browser flows passed with a host and up to three simulated participants:
  all-answered, timeout with a disconnected player, zero-count bars, late joins,
  results/leaderboard/countdown refresh, duplicate progression, simultaneous and
  duplicate answers, shared countdown deadlines and final results.
- Existing authoring, media/math/code, all three answer types, CSRF and teacher
  authorization checks passed. Desktop/mobile dialogs were visually inspected.
- MySQL/InnoDB concurrency, PHP 8.4 deployment, classroom load and real network
  behavior remain unverified locally. SQLite and the single-worker PHP fixture
  cannot establish production concurrent-locking behavior.
- Detailed evidence: [tests/runtime-validation-report.md](tests/runtime-validation-report.md).

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

`node tests/youtube.cjs` uses the same fixture and environment options to check
four-second reveal timing, blocked autoplay, buffering, pause/end, errors and
player cleanup. Both browser suites mock the external YouTube API; they do not
verify actual media playback, title timing or YouTube policy compliance.

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
