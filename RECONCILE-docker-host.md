# docker-host canonicalisation — standards-control-plane (scp)

Phase-1 estate hardening. Captures the docker-host **running** config into version
control and adds an idempotent, health-gated deploy script. **No live redeploy was
performed** — the running `scp` container is untouched and still serving.

## What this branch adds / changes
- **`docker-compose.docker-host.yml`** (NEW — was UNTRACKED on the host): the tailnet-bind
  overlay. It `!override`s the base `3787:3787` (which binds `0.0.0.0`) down to
  `100.84.218.122:3787`, and pins `CT_BASE_URL` / `CT_JWKS_URL` to the DEV Control Tower.
  This overlay is the **only** thing keeping scp off `0.0.0.0:3787` on a firewall-less box,
  and it was living on disk unversioned — capturing it is the core of this change. Verified
  live: `scp` binds `100.84.218.122:3787` and `127.0.0.1:3787` returns nothing (HTTP 000).
- **`scripts/deploy-dev.sh`** (NEW): idempotent, hostname-guarded (`docker-host`), explicit
  two-file compose set (`docker-compose.yml` + `docker-compose.docker-host.yml`),
  `up -d --build`, then health-gated by observed effect — `/health` must return HTTP 200
  **and** body `status=="healthy"`. It polls the tailnet bind (`100.84.218.122:3787`), NOT
  `127.0.0.1` (nothing binds localhost under the tailnet-only overlay — the failure mode that
  makes the dashboard's deploy script poll a dead port).
- **`.env`** un-tracked + git-ignored. It was tracked in this **PUBLIC** repo. It is
  config-only today (PORT/ENV/AUTH_ENABLED/CT_* /CT_APP_ID/PUBLIC_BASE_URL — no secrets, so
  no history scrub is needed), but tracking an env file in a public repo is a latent leak
  risk. `.env.example` remains the template; the live `.env` is backed up off-repo.

## Drift vs origin (host was BEHIND live GitHub)
- Host live-dir HEAD was `1703bb05` (#122); GitHub `main` is `3093449a` (#260). The host is
  strictly behind, and the GitHub tip was never fetched locally — because the live dir's
  `origin` remote is broken (see SSOT follow-up). This branch is cut from GitHub `main`, so it
  does **not** regress those commits.
- The live base `docker-compose.yml` is **byte-identical** to `main`, so the only genuinely
  new artifacts are the untracked overlay and the new deploy script.
- The running image `standards-control-plane-scp` was built **2026-05-17** — ~3 months stale
  (lags both HEAD and origin). Rebuild is deferred to the maintenance window (needs a recreate).

## Follow-ups (intentionally NOT done here)
- **SSOT / host remote fix (blocks the live dir from pulling):** the live dir's `origin` is
  `git@github.com-scp:...`, but `github.com-scp` has no `Host` block in docker-host's
  `~/.ssh/config` — `ssh -G github.com-scp` echoes the literal string as the hostname, so it
  never resolves and the live dir cannot `git fetch`/`pull`/verify. Fix: add
  `Host github.com-scp` → `HostName github.com` (the existing key already auths as `jrnb2024`),
  or repoint the remote to plain `git@github.com:jrnb2024/standards-control-plane.git`.
- **`services.yml` `runtime_contract`** describes a bare-metal venv start
  (`python -m ... serve`, `interpreter: python-venv`, `venv_path: .venv`,
  `start_command: -m standards_control_plane.cli serve …`) that does not match the Docker /
  `restart: unless-stopped` reality. Correct it to the container runtime contract.
  (Not edited here — SSOT/manifest edits are batched centrally.)
- **SVC-002 health gap:** `/health` returns `checks:{}` (empty), so the deploy gate can only
  assert top-level `status==healthy`, not any dependency check. Add real checks (e.g. CT JWKS
  reachability) so the gate asserts `checks.*==ok`.
- **`bearer_legacy` waiver** (`scp-bearer-legacy-migration`, in `services.yml`) expired
  `2026-06-30` — resolve or renew.
- Rebuild the 3-month-stale image once the above land.

Off-repo backups (docker-host): `~/backups/estate-2026-08-22/secrets/scp/`
(`.env`, `docker-compose.docker-host.yml`, and the `.bak-20260808-ct` variant).
