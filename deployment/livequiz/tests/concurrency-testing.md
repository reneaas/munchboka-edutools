# Class Battle concurrency simulation

## Results — 2026-11-13

Local MySQL 26.10.0 with InnoDB, PHP CLI server configured with eight child workers (plus parent). Independent student sessions and tokens; three teacher sessions. HTTP requests capped at 48 in flight. Worker probes observed nine distinct processes in the 90-student run and seven in the 300-student run.

| Scenario | Result | Answer requests | Answer p95 | State p95 |
| --- | --- | ---: | ---: | ---: |
| 3 classes × 30 students, 2 questions | Passed | 720 | 94 ms | 162 ms |
| 3 classes × 100 students, 2 questions | Passed | 2,400 | 143 ms | 214 ms |

Raw measurements: [90 students](results/class-battle-90.json), [300 students](results/class-battle-300.json).
Latency measures dispatched requests, excluding the client's concurrency queue and simulated outbound delay. These are local measurements, not production capacity estimates.

Verified:
- Concurrent redemption of the same invitation creates exactly one class.
- All concurrent student joins retained, with correct class membership.
- Co-host student lists/results scoped to their class; progression requests rejected.
- Shared question deadlines and identical standings across classrooms.
- Concurrent polling and answer bursts, including three simultaneous identical submissions per student.
- Conflicting retry after an acknowledged submission preserves the original answer/score.
- Late join rejected after roster lock.
- Clients skipping polling can resume the current state.
- Exact totals, averages, answer counts, and final phase for both questions.
- Existing Playwright Class Battle test passed against this MySQL fixture: three teachers, six students, reloads, mobile layout, and final winner.

The successful runs returned no unexpected HTTP errors: each had two intentional 403 permission rejections and one intentional 422 late-join rejection. Database inspection confirmed 180 answers for 90 students and 600 for 300 students. InnoDB recorded 6,041 row-lock waits and a maximum wait of 188 ms across the session, confirming actual overlapping transactions.

An earlier unrestricted connection burst failed with ECONNRESET against PHP's development server and left an unfinished test room. Limiting the harness to 48 simultaneous requests avoided that backlog limit; this does not prove unrestricted production bursts are safe.

Limitations: short two-question simulations, one machine, no real school networks, no server restart/failover, no injected packet loss. The retry test models a lost response by resending after success; it does not physically drop the response. The 250 ms delay is client-side outbound delay. Join-versus-start and kick-versus-start races are not covered by this harness. Test the actual hosting stack separately before declaring a production capacity limit.

## Reproduce

Use an empty disposable directory and dedicated loopback port. Requires MySQL, PHP with PDO MySQL, Python, and Node. Never deploy the generated fixture: it contains a test login endpoint.

In separate terminals (foreground servers):
```sh
mkdir -p /private/tmp/lq-test
mysqld --initialize-insecure --datadir=/private/tmp/lq-test/mysql
mysqld --datadir=/private/tmp/lq-test/mysql --bind-address=127.0.0.1 --port=33079 --socket=/private/tmp/lq-test/mysql.sock --mysqlx=OFF
```

Prepare the fixture once, then start PHP:
```sh
python3 deployment/livequiz/tests/prepare-concurrency.py /private/tmp/lq-test/site 33079
PHP_CLI_SERVER_WORKERS=8 LIVEQUIZ_LOCAL=1 LIVEQUIZ_PRIVATE=/private/tmp/lq-test/site/private/livequiz/app.php php -S 127.0.0.1:8878 -t /private/tmp/lq-test/site/public
```

Run:
```sh
REPORT_PATH=/private/tmp/lq-test/90.json node deployment/livequiz/tests/class-battle-concurrency.cjs
STUDENTS_PER_CLASS=100 REPORT_PATH=/private/tmp/lq-test/300.json node deployment/livequiz/tests/class-battle-concurrency.cjs
```

The harness accepts only 127.0.0.1 and checks a fixture marker before creating data. Each run creates new quizzes/rooms. Stop both foreground servers after testing. No persistent MySQL service is needed.
