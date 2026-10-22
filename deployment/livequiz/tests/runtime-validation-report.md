# Synchronized Lifecycle Validation

Date: 2026-10-22. Target: standalone Livequiz. All tests use disposable local data,
not the deployed service.

## Environment

- PHP 8.5.12 with PDO SQLite; Node v25.8.0.
- Playwright with installed Chromium headless shell revision 1243.
- `command -v docker` and `command -v mysql` returned no executable. No local
  MySQL/Docker concurrency test was possible; SQLite is the existing fallback.
- Existing PHP fixture served at `http://127.0.0.1:8766`.
- Production targets PHP 8.4 and MySQL, which were not exercised here.

## Results

| Tier | Result | Exit code | Scope |
| --- | --- | --- | --- |
| Backend | PASS | 0 | `php tests/core.php`: 96 checks |
| Browser | PASS | 0 | `node tests/browser.cjs`: two complete multiplayer flows |

The existing tests were extended in place. The backend suite now tests server
leaderboard/countdown transitions and deadline compatibility. The browser suite
retains authoring, images, math, code, video URL, all answer types and authorization
coverage, and adds shared-state assertions and a second timeout/concurrency flow.

| Requested case | Evidence |
| --- | --- |
| All players answer early | Last submission enters results; one version increment |
| Timer expires first | Five-second question closes with one unanswered player |
| Zero-response alternatives | Four counts include zeroes; all four chart rows render |
| Player disconnects | Offline browser does not prevent server deadline closure |
| Results/leaderboard refresh | Reopened host/participant views retain authoritative state |
| Duplicate host progression | Same-version requests produce one success and one rejection |
| Final question | All clients enter finished with expected accumulated scores |
| Shared countdown/next question | Matching versions, indices and deadlines across clients; refresh during countdown; next deadline anchored to countdown end |

Additional checks: late joining an open leaderboard updates existing clients;
concurrent answer requests and duplicate retries preserve one answer per player;
participants cannot call host controls; late answers are rejected; submitted cards
stay locked after refresh. Desktop and mobile checks cover modal bounds, horizontal
overflow, two grid columns and computed backdrop blur. Screenshots of question,
results and leaderboard dialogs were inspected.

## Reproduction

Use the fixture commands and environment overrides in `../README.md`. Run:

```sh
php tests/core.php
node tests/browser.cjs
```

For the browser command, set `LIVEQUIZ_BASE` to the fixture URL and, when needed,
`PLAYWRIGHT_MODULE` and `CHROMIUM_PATH` to installed local tooling. Never point
this suite at production: it requires a test-only login and creates quizzes/rooms.

## Limits

Local behavior verification passes. Production concurrency remains unverified:
SQLite strips `FOR UPDATE`, and the PHP built-in server processes requests in one
worker. Simultaneous browser requests test retry/outcome behavior, not InnoDB lock
contention. Production classroom load, actual mail/YouTube, physical devices and
real network delays remain deployment checks. Polling provides synchronized
server deadlines but does not guarantee identical display frames on every client.