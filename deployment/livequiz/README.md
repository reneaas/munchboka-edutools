# Livequiz proof of concept

A teacher-controlled classroom quiz at `https://quiz.munchboka.no/`.
Uses PHP 8.4 and the **existing Jeopardy MySQL database**. No second database,
WebSocket subscription, Node server or build step is required on the host.
Deployment status is recorded at the end of this file.

## Optional Lightning Round (Lynrunde)

In the room lobby, enable **Aktiver lynrunde**, choose **Varighet på lynrunde
(sekunder)**, and save the game settings. It defaults to disabled and 60 seconds;
valid durations are 5–600 integer seconds. This is a session setting, including
sessions created by guest hosts through share links.

Normal gameplay and the last normal results/leaderboard remain unchanged. The
last leaderboard's **Start lynrunde** opens an introduction. The teacher starts
the shared 3–2–1 countdown, after which all clients use one server deadline. The
teacher sees only the Lightning Round heading and timer; participants answer
independently, with no intervening answer reveal, charts or countdowns. Completing
all questions displays a waiting screen. Expiry or completion by every eligible
participant opens the final leaderboard; only the host can finish the game.

Implementation:

- `lightning.php` handles configuration, eligible participant membership, independent
  Fisher–Yates question orders, progress, answering and completion. Orders are
  stored in the existing room JSON at countdown start. Late individual entrants
  receive a fresh order with the same remaining deadline; late team entrants wait
  for the next game. Existing participant tokens can reconnect. Every original question is
  included once per participant, including typed/multiple-answer questions.
- Phases `light_intro`, `light_count`, `lightning`, `light_done` map to explicit
  `LIGHTNING_*` client states and fit the existing phase column. The active
  deadline equals the scheduled countdown end plus duration, even if polling is
  delayed. The server rejects answers at/after the deadline.
- Existing `lq_answers` rows store each Lightning Round answer with question key
  `-1 - original_question_index`, keeping them distinct from normal answers under
  the existing primary key. Progress is derived from these persisted answers.
  The room row lock serializes submissions, retries and completion. Accepted
  submissions return the next participant state in the same transaction; older
  polling responses cannot move the browser back to an earlier question.
- Correct Lightning Round answers earn 1,000 points and incorrect answers zero,
  using the existing correctness grader. There is no speed bonus in this round.
  The normal optional speed-scoring mode remains unchanged. Existing leaderboard
  sums include both sets of answers, and team totals remain sums of individual
  totals with unchanged assignments. No additional Lightning Round table or
  database migration is required.
- Participant images are an explicit exception to normal host-only media during
  this round. Only the participant's current image is authorized; future images,
  correct answers and question order are not sent. LaTeX, code and existing
  question types are preserved. Videos remain absent on participant devices;
  video-based questions therefore rely on recall from the normal round.

Validation: `php tests/lightning.php`, `node tests/lightning-browser.cjs`, plus
existing normal-game and team regressions. The browser suite uses separate host
and participant contexts, overlapping duplicate HTTP requests, refresh, all-done
and timed completion. Tests use the local SQLite fixture; production MySQL row
locking follows the existing design but is not load-tested here. Independent
random orders may occasionally coincide, particularly in short quizzes.

## Folders and subfolders

The teacher library has **Ny mappe**, clickable folders and a breadcrumb path.
Open a folder to create subfolders or save a new quiz directly inside it. Use
**Flytt** on a quiz to choose its folder or return it to the top level. Inside a
folder, use **Gi mappen nytt navn**, **Flytt mappe**, or **Slett mappe**. Deleting a
folder moves its quizzes and direct subfolders to its parent; it never deletes
quiz content. Quiz edits, share links and running games are independent of moves.

Organization is private to each signed-in teacher. One `lq_library` record per
teacher stores the folder tree and quiz assignments. The new table is created
additively on first library access in the **existing database**, without changes
to existing quiz tables or a manual deployment step. The database user needs
CREATE permission for this first use. Folder mutations lock the teacher's record;
quiz creation in a folder is atomic. Invalid parents, cross-owner access and
folder cycles are rejected. Up to 500 folders per teacher; names are limited to
120 UTF-8 bytes. Legacy quizzes start at the library's top level.

`php tests/folders.php` checks migration, ownership, nesting, moves and safe
removal. `tests/folders-browser.cjs` covers the library UI and new quiz saving,
including mobile/dark mode, CSRF and account-free guest restrictions.

## Participant results

After a question, participants see the correct answers and their own points,
including zero when they did not answer. Typed questions list accepted answers.
Only the teacher sees answer-distribution charts and statistics; participant
state responses omit the distribution. The separate leaderboard is unchanged.
`tests/results-browser.cjs` checks these screens for all three question types.

## Question images and videos

During questions and results, the host's image or video scales to the space remaining after
question text, controls and answer alternatives. The full image or 16:9 video stays visible
without cropping, and resizing the window recalculates the fit. Short landscape
screens put the image beside the alternatives and use compact controls. Results
reserve a separate scrollable statistics section so charts do not displace the
image or answers. Other
media can scroll within the media area; exceptionally long question/answer text
retains scrolling rather than being cut off. Participant screens remain image-free.
`tests/video-fit-browser.cjs` checks video fitting and playback controls using a
mock YouTube API. `tests/image-fit-browser.cjs` checks portrait, landscape and square images across
projector, desktop, tablet and phone sizes.

## Light and dark themes

Use **Mørk modus / Lys modus** in the site header or game dialog to switch themes.
The site initially follows the device's color preference. A manual selection is
saved in that browser and survives refresh/navigation, with changes synced across
tabs. Teachers and participants choose independently. If browser storage is
unavailable, switching still works for the current page. Both themes cover the
quiz editor, questions, results, team cards and leaderboards; images, QR codes and
videos keep their original colors. `tests/theme-browser.cjs` checks theme switching,
persistence, game dialogs, editor colors, mobile width and unavailable storage.

## Share a quiz with another teacher

In **Mine quizer**, choose **Del quiz**, then **Kopier lenke**. Anyone with that
link can select **Start spill for min klasse** without signing in. Each start
creates an independent, six-hour game with its own PIN, participants, scores and
individual/team settings. Guests can host but cannot edit, delete or reshare the
source through the owner APIs. They can forward the link they received.

The link uses the latest saved version. Started games keep a snapshot, so later
edits do not change an ongoing class. **Slå av deling** invalidates the link for
new starts; ongoing games continue. Sharing again creates a new key. Deleting
the source quiz also disables its link. The original owner retains access to
rooms created from their quiz in the recent-games list.

Share keys use 256 random bits and are carried in the URL fragment, then a request
header/body, rather than in request URLs. Every guest room has a separate host
credential, stored in that tab's sessionStorage and hashed in its room snapshot.
Keep the hosting tab open; refresh works, but the room URL alone cannot recover
guest control in another browser. Student URLs/PINs do not contain host access.
Host authorization is checked for state, control and room media; CSRF checks
remain mandatory for mutations. Credentials are not returned in game state.
Sharing metadata uses existing JSON columns in the same database: no new table,
account or database migration is required. Deployment includes `sharing.php`.

Validation: `php tests/sharing.php` extends the backend checks; run
`node tests/sharing-browser.cjs` against a disposable `prepare-local.py` fixture
with the same Playwright environment variables as the other browser tests.

## Late arrivals and the teacher game code

The teacher sees **Bli med: quiz.munchboka.no · Spillkode …** in every game
window, including questions, countdowns, race progress, results and the final
screen. Students can enter the code on the quiz homepage.

Late individual players join the current regular question immediately, start a
fresh independent Race attempt, or receive their own Lightning order with only
the existing time remaining. Joining does not extend timers or reset anyone's
progress. Late team players wait on a dedicated lobby screen until the next game;
existing teams and cyclic turn orders never change mid-game. Waiting players
cannot answer and do not count toward completion or current leaderboards.
Joining after a game has ended also places the player in the waiting lobby.

Waiting membership is stored in the existing room JSON. **Spill igjen med samme
spillere** admits everyone back into the lobby; the next start includes waiting
players in the normal team allocation. Reconnection is idempotent, and the existing
60-player room limit includes waiting players. No schema migration is required.

`php tests/late-join.php` and `node tests/late-join-browser.cjs` (fixture port 8792)
cover individual/team behavior across regular quiz, Race and Lightning, completion
counts, unchanged timers/teams, reconnects, visible teacher codes and replay entry.

## Play again with the same lobby

After the final screen (or the completed Race/Lightning results), the host can
choose **Spill igjen med samme spillere**. Everyone returns to the lobby with the
same room, PIN, nicknames and participant/host credentials. The current game mode,
team-size preference and Lightning settings stay selected. Start automatically
saves and applies any changed lobby settings. Randomized teams are allocated afresh at the next start.

Replay clears previous answers, scores, race attempts/winner and Lightning orders.
It reuses the room's original quiz snapshot and extends the room expiry to six
hours from replay. Previous results are replaced, not archived. Only the host can
restart, and only after completion. Restart runs inside the existing room lock;
room versions reject duplicate host requests. A persisted run counter accompanies
all answer requests, preventing old regular, Lightning or Race submissions from
being counted in a later game. Participant polling continues on the final screen
so players return to the lobby automatically, without rejoining or refreshing.

`php tests/replay.php` checks retained players/settings, cleared scores/progress,
mode switches, stale requests, repeated replay and shared-host access.
`node tests/replay-browser.cjs` exercises the same connected browser sessions
across repeated normal games, cooperative Race and Lightning Round (fixture port
8795 by default).

## Quiz Race

In the lobby, select **Spilltype → Quiz Race**, choose individual play or randomized
teams, then start. Start saves changed settings atomically; the separate save
button remains available. Regular quiz remains the default. Race replaces the
normal question lifecycle for that session; Lightning Round and point scoring do
not run in a race. Existing team allocation and maximum team size are unchanged.

The initial shared three-second countdown leads to `RACE_ACTIVE`. There are no
question timers or intermediate results. Each individual or team must answer every
question correctly in one attempt. Correct answers advance; incorrect answers
reset progress and shuffle all questions again. Shuffles are independent and may
coincidentally repeat a previous order. First completion ends the race for everyone,
shows the winner and progress board, and lets the host finish the game.

Cooperative teams have one shared order/progress/attempt, and the existing team
member list defines a fixed cyclic turn order. Only the active member receives the
question and can submit. Teammates see whose turn it is. Active position is
`(start + progress) % teamSize`; failure advances `start` by exactly one, resets
progress, and increments the zero-based attempt. The interface displays attempts
starting at one. Reset messages name the next starter and disappear after six
seconds without delaying answers. No votes or independent team-member scores are
used in this mode.

`private/livequiz/race.php` persists competitors, shuffled orders, progress,
attempts, starting positions, revisions, update/reset timestamps, completion times
and the winner in the existing room JSON snapshot. No new tables or database are
required. `race-answer` validates the participant, active member, attempt, revision
and question while holding the existing room transaction/row lock. Repeated or
stale submissions are rejected without changing progress or rotating twice. The
first final correct answer processed under that lock commits the sole winner;
later submissions are rejected. It reuses answer grading (including typed-answer
normalization), without adding points to ordinary quiz answer records.

Submission responses include immediate updated state and the next question when
it is still that participant's turn. Other teammates and the teacher synchronize
through existing polling. Client rendering uses the competitor's revision, so
other competitors cannot erase a partially entered answer. Refreshing restores the
same attempt and turn. Late individual racers start their own attempt immediately. Late team players
wait for the next game; existing player tokens can reconnect. Shared-link hosts can also run races without accounts.
The teacher sees a progress board; active participants receive code, math and
current-question images. YouTube videos are not replayed in this mode.

There is no automatic skip for a disconnected active teammate: the team waits for
that member to reconnect. The host can end an active race with **Avslutt spillet**.
Ending accepts a slightly stale progress version but checks the run identifier, so
ongoing answers cannot block the host and an old stop request cannot close a replay.
The current progress is retained without inventing a winner; all players stop and
the host can return everyone to the lobby. Rooms retain the existing
six-hour expiry. Winning order is server processing order, not client click time.
MySQL/InnoDB concurrent locking and classroom load require production verification;
local tests use SQLite and a single-worker PHP server.

Verification: `php tests/race.php` covers team sizes 2–5, starter wraparound,
failures by different members, fixed membership, independent competitors, hidden
answers/media access, retries/stale turns, reconnects, one-question/single-member
boundaries, shared hosting and terminal states. `node tests/race-browser.cjs`
checks individual/team flows, immediate responses, images, mobile layouts,
duplicate reset requests and competing winning submissions. Use the same fixture
and Playwright variables as below; its default port is 8796.

## Background music

The server discovers MP3, M4A, OGG and WAV files directly in `public/music/`
on each page load (case-insensitive extensions, arbitrary filenames). Hidden files,
subdirectories and symlinks are ignored. Reload the teacher page after changing
the collection. An empty collection disables music gracefully. Browser support
for the chosen audio format still applies. The host randomly selects a track
for each ordinary question and loops it from the beginning, starting at 25% volume
with a short fade-in. Independent selections can repeat a song on consecutive
questions. Music pauses during countdowns, results,
leaderboards, YouTube questions, expired timers and lost connections. The same
player keeps its selection and position when toggled or reconnected within a question.
Host controls allow
music to be switched off and volume adjusted; participants never create a player
or download the track. Start/Next primes playback; if the browser blocks autoplay,
use “Spill musikk”. Reloading resets the controls to their defaults. The existing
deployment script copies new tracks and removes obsolete supported audio files
from the deployed quiz music folder. Music also plays during the Lightning Round.

## Included

- Separate quiz email-code sign-in using the existing Osloskolen account records.
  Open `/?login=1`; students can join a session without accounts.
- Quiz library, creation, editing, explicit online saves and revision conflict
  checks. One to fifty questions, two to six choices, 5–600 second answer windows.
- One correct choice, multiple correct choices (exact set), or typed accepted
  answers (lowercase, all whitespace removed, and comma/dot decimal separators
  treated equally for numeric answers; no algebraic equivalence or tolerance).
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
  network and video permissions determine actual playback. Images and YouTube playback
  are host-only; participant state omits image metadata and video IDs, and image
  downloads require host authorization. Participant screens never create a player,
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
**Lagre spillmodus**, or start directly to save and apply the selected settings. Individual rooms follow
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
Individual games also start with the same synchronized countdown before question 0.
The answer deadline and scoring timer begin after that countdown.
Subsequent lifecycle transitions are unchanged. Only the host may configure or
advance a room. Settings lock once assignments are made. New team participants wait for the next game after that point; existing browser
tokens reconnect to the same team.
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
| `LOBBY` | `lobby` | Host starts the first countdown (or team overview) |
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

All active room participants are eligible, including late individual joins during
an active question. Team arrivals waiting for the next game are not eligible. Disconnected players stay in the roster and retain scores; they
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

Lobby start regression checks: `php tests/start-settings.php` and
`node tests/start-settings-browser.cjs` (fixture port 8794) cover direct starts
with edited settings, all game/team combinations, invalid fields, replay changes,
and explicit save immediately followed by Start. Control responses return the
current authoritative state so Start does not depend on a later polling update.

`php tests/race-finish.php` and `node tests/race-finish-browser.cjs` (fixture port
8793) verify early termination, host authorization, rejection of subsequent
answers and old-run stop requests, and a deliberately stale host progress view
in individual and cooperative team races.
