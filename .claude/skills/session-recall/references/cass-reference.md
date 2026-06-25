# cass reference (for session-recall)

Deeper reference for the `cass` (coding-agent-search) CLI. Read this when
SKILL.md's quick guidance isn't enough — e.g. you need an agent slug, a less
common subcommand, or precise control over output. When in doubt, the live
source of truth is always `cass <cmd> --help`, `cass capabilities --json`, and
`cass robot-docs examples`.

## Table of contents
- [Mental model](#mental-model)
- [Global flags & output formats](#global-flags--output-formats)
- [Agent slugs (for --agent)](#agent-slugs-for---agent)
- [Time filters](#time-filters)
- [Full subcommand map](#full-subcommand-map)
- [Exit codes](#exit-codes)
- [Useful env vars](#useful-env-vars)
- [Chaining searches](#chaining-searches)
- [Copy-paste recipes](#copy-paste-recipes)

## Mental model

- `cass` normalizes session logs from ~20 coding agents into one local SQLite
  archive plus a lexical (BM25) index and an optional semantic (embedding)
  index. SQLite is the source of truth; lexical search is the always-available
  fast path; semantic is opportunistic enrichment.
- Default UX is an interactive TUI. For automation you must use the non-TUI
  subcommands with `--robot`/`--json`. stdout = data, stderr = logs/progress.
- Data lives in a platform data dir (Windows: `%APPDATA%\coding-agent-search\
  coding-agent-search\data`). Override with `--data-dir` or `CASS_DATA_DIR`.

## Global flags & output formats

- `--robot` / `--json` — structured JSON on stdout (the key flag for agents).
- `--robot-format <fmt>` — `json` (default, pretty), `jsonl` (one object per
  line), `compact` (single-line), `sessions` (just `source_path` per line — for
  chaining), `toon` (token-optimized).
- `--robot-meta` — extra metadata (`elapsed_ms`, realized `search_mode`,
  `fallback_reason`, `cache_stats`).
- `--fields <list>` — pick JSON fields; presets `minimal`
  (`source_path,line_number,agent`) and `summary`
  (`+title,score`). Cuts tokens hard.
- `--max-content-length N` — truncate snippet/content fields (UTF-8 safe).
- `--max-tokens N` — soft token budget for the whole robot payload.
- `--display table|lines|markdown` — human-readable output (use only when
  showing a person directly; otherwise prefer JSON).
- `--data-dir <path>` — point at an alternate archive.
- `-q/--quiet` — warnings/errors only.

## Agent slugs (for --agent)

`codex`, `claude_code`, `gemini`, `clawdbot`, `vibe`, `opencode`, `amp`,
`cline`, `aider`, `cursor`, `chatgpt`, `pi_agent`, `factory`, `openclaw`,
`antigravity`, `kimi`, `openhands`, `copilot`, `copilot_cli`, `qwen`, `crush`,
`hermes`. Confirm the current list with `cass capabilities --json` (the
`Connectors` block). `--agent` can be repeated to include several.

## Time filters

Available on `search`, `pack`, `timeline` (and others):
- `--today`, `--yesterday`, `--week` (last 7 days), `--days N` (last N days).
- `--since <when>` / `--until <when>` where `<when>` is an ISO date
  (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`), a keyword (`today`, `yesterday`,
  `now`), or a relative offset (`-7d`, `-24h`, `-30m`, `-1w`). The dash forms
  work without `=` thanks to `allow_hyphen_values`.

## Full subcommand map

Readiness & self-description (read-only, safe):
- `triage` (aliases `ready`, `preflight`) — one-shot readiness + next command.
- `status` / `state` — health, index freshness, recommendation.
- `health` — minimal <50ms check; exit 0 healthy, 1 unhealthy.
- `capabilities` — features, connectors, exit codes, env vars.
- `introspect` — full API/argument/response schemas.
- `robot-docs <topic>` — machine docs (`guide`, `examples`, `commands`,
  `sources`).
- `stats` — archive statistics. `diag` — diagnostics. `storage` — on-disk
  footprint. `analytics` — token/tool/model analytics. `api-version`.

Indexing & maintenance:
- `index [--full] [--watch] [--semantic] [--no-progress-events] --json` — build
  or update the archive. `--full` = rebuild; bare = incremental.
- `upgrade [--check] [--yes] [--json]` — check/install newer cass release.
- `doctor` — diagnose/repair derived assets (start with `cass doctor check
  --json`). `dedup`, `quarantine`, `mirror`, `forget`, `sources` — advanced data
  management; usually leave alone.
- `models` — manage semantic-search models (optional; `cass models --list`).

Querying:
- `search <query>` — one-off search to stdout (the workhorse).
- `pack <query>` — deterministic, citation-rich evidence bundle for handoffs.
- `timeline` — activity timeline over a range (`--group-by hour|day|none`).
- `sessions` — list recent sessions (`--current`, `--workspace`, `--limit`).
- `context <path>` — find sessions related to a source path.

Following up on a result:
- `view <path> -n LINE [-C N]` — show a file/line with context.
- `expand <path> -n LINE [-C N]` — show messages around a line.
- `export <path> [--format markdown|text|json|html] [-o file] [-c]` — export a
  conversation. `--include-tools` / `--include-skills` to add detail.
- `export-html` — self-contained (optionally encrypted) HTML archive.
- `resume <path> [--json|--shell|--exec]` — resolve a session into a
  ready-to-run resume command for its native harness.
- `timeline`, `pages`, `import`, `swarm`, `lessons`, `release-verify` — niche.

## Exit codes

`0` success · `1` health-check failed (retry) · `2` usage/parse error · `3`
index/db missing (run `index --full`) · `4` network (retry) · `5` data
corruption · `6` incompatible version · `7` lock/busy (retry) · `8` partial
result · `9` unknown · `10` config/timeout · `11` config validation · `12`
source/SSH · `13` mapping/not-found · `14` I/O · `15` semantic/embedder
unavailable · `20–24` model acquisition/IO. Confirm via `cass capabilities
--json`.

## Useful env vars

- `CASS_DATA_DIR` / `CASS_DB_PATH` — archive location.
- `CASS_OUTPUT_FORMAT` — default robot format.
- `CASS_SEARCH_LIMIT`, `CASS_SEARCH_TIMEOUT_MS`, `CASS_SEARCH_MODE` — search
  defaults.
- `CODING_AGENT_SEARCH_NO_UPDATE_PROMPT=1` — suppress update prompts.
- `TUI_HEADLESS=1` — guard against accidental TUI launches.
- `NO_COLOR` / `CASS_NO_COLOR` — disable ANSI color (cleaner parsing).

## Chaining searches

`--robot-format sessions` emits one `source_path` per line; `--sessions-from -`
reads such a list from stdin. This lets you narrow in two passes:

```bash
cass search "checkout" --robot-format sessions \
  | cass search "timeout" --sessions-from - --robot --limit 5
```

Or scope a pack to sessions found by a prior search:

```bash
cass search "auth" --robot-format sessions \
  | cass pack "auth bug root cause" --robot --sessions-from -
```

## Copy-paste recipes

```bash
# First-run from zero context
cass triage --json
cass index --full --json --no-progress-events     # only if not initialized

# Topic recall, fresh, scoped to last 2 weeks, compact
cass search "postgres deadlock" --robot --refresh --days 14 --limit 8 --fields summary

# "What did I do last week?" overview, then drill in
cass timeline --week --json --group-by day
cass search "<topic from timeline>" --robot --since 2026-06-15 --limit 6

# Only Claude Code sessions in one project
cass search "rate limiter" --robot --agent claude_code --workspace <project-path> --limit 5

# Show the actual conversation around a hit
cass view "<source_path>" -n 142 -C 8 --json
cass export "<source_path>" --format markdown -o ./recovered-session.md

# Overview counts without pulling messages
cass search "*" --json --aggregate agent,date --week

# Bounded cited bundle to carry into another prompt
cass pack "why did the deploy fail" --robot --max-tokens 4000 --max-evidence 8
```
