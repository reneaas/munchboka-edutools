# Jeopardy hosting connection test

This checks a PHP-to-MySQL connection only. It does not create tables, accounts,
or games, and is not yet the saving service.

## Upload with cPanel File Manager

1. Find the document root for `jeopardy.munchboka.no` under **Domains**.
2. In your hosting account's home directory, create `jeopardy-private` **outside
   public_html and outside all domain document roots**. Note its absolute path;
   do not assume that the example `/home/...` path matches your account.
3. Upload `database.example.php` into that private folder and rename it
   `database.php`. Edit it in cPanel: enter the full database username and
   password. Confirm the MySQL hostname with the hosting settings or provider;
   `localhost` is an initial default, not a verified account setting.
   Keep PHP strings quoted. In a single-quoted PHP string, write a literal
   apostrophe as `\'` and a literal backslash as `\\`.
4. Edit `$configPath` in `check-database.php` to the absolute path of that
   private `database.php` file. Upload `check-database.php` into the subdomain's
   document root. No password belongs in this public file.
5. Visit `https://jeopardy.munchboka.no/check-database.php`.
6. After success, delete `check-database.php` from the server. Leave the private
   configuration in place for the future application. If it fails, double-check
   the settings listed in the response; do not share the configuration file or
   credentials when asking for help.

Do not upload this entire folder to the public website. Only the test script
goes in the document root. The completed configuration must remain private and
must not be committed to Git.

Success verifies connectivity and a read-only query, not write privileges,
email delivery, authentication, backups, or the future save/reopen workflow.

## Automated deployment via GitHub Actions

`.github/workflows/deploy-jeopardy.yml` deploys `pilot/public/` and
`pilot/private/` via FTPS on every push to `main` that touches those paths, or
manually from the Actions tab (`workflow_dispatch`). `dangerous-clean-slate` is
left off, so existing server-only files (`jeopardy-private/database.php`) are
never removed; only files present in the repo are uploaded/overwritten.

Required repository secrets (Settings → Secrets and variables → Actions),
shared with the `deploy-livequiz` workflow since both sites live on the same
cPanel account:

- `CPANEL_FTP_SERVER` — the FTP hostname (cPanel → FTP Accounts, or your
  provider's documented FTP host).
- `CPANEL_FTP_USERNAME` — the FTP account username.
- `CPANEL_FTP_PASSWORD` — the FTP account password. Prefer a dedicated FTP
  account over the main cPanel password if your host supports creating one.

Because `jeopardy-private/` lives outside `public_html`, the FTP account must
land at (or have access up to) the cPanel account home directory rather than
being chrooted into a single subdomain's document root. The workflow assumes
FTPS (explicit TLS); if your host only supports plaintext FTP, change
`protocol: ftps` to `protocol: ftp` in both workflow files.
