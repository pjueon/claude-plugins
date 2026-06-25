---
name: session-recall
description: >-
  Search and recall the user's past conversations with AI coding agents (Claude
  Code and others) using the local `cass` CLI. Use whenever the user wants to
  find or revisit something from an earlier session — "didn't we talk about X
  before?", "what did I work on last week?", "find that session where we fixed
  the auth bug". Searches conversation history, not the current codebase (use
  Grep/Glob for files).
---

# session-recall

Recall the user's past AI coding-agent conversations via `cass`
(coding-agent-search), a local CLI that indexes session logs from Claude Code
and ~20 other agents into one searchable archive. Runs fully locally.

Use this when the user reaches back to an earlier conversation ("last time",
"before", "last week", "remember when…"). If they instead want to grep the
current repo's files, that's Grep/Glob — not this skill.

## Golden rule: never launch the TUI

`cass` defaults to a full-screen TUI you can't drive. Pass `--robot` (alias
`--json`) to **every** data command so output is JSON on stdout. A bare `cass`
or `cass search "x"` without it opens the TUI and hangs. stdout = data,
stderr = logs, exit 0 = success.

## Workflow

### 0. Ensure cass is installed

Run `cass --version`. If it fails (not found), read
[references/install.md](references/install.md) for the OS-specific install
command and confirm with the user before running it.

### 1. Check readiness and freshness

`cass` searches an **index** and does **not** auto-sync — conversations created
since the last index are invisible until you re-index. Run `cass triage --json`:

- If `not_initialized`: build the archive once with `cass index --full --json
  --no-progress-events` (scans all local logs; can take a while).
- Otherwise, prefer adding `--refresh` to your search/pack in step 2 — it folds
  in new conversations and is a no-op when already current. For an explicit sync
  without searching (e.g. "update my history first"): `cass index --json
  --no-progress-events`.

Exit codes guide retries: `3` = index missing (run `index --full`), `4` =
network, `7` = lock/busy (wait), `0` = success.

### 2. Answer the question

All of these accept time filters (`--today`, `--yesterday`, `--week`,
`--days N`, `--since`, `--until`) and `--agent <slug>` / `--workspace <path>`.

- **Find a past topic** → `cass search "jwt refresh bug" --robot --refresh
  --limit 8`. Default mode is hybrid; force `--mode lexical|semantic` if results
  are off. Each hit has `source_path` + `line_number` (needed for step 3). Trim
  with `--limit`, `--fields summary`, or `--max-content-length`.
- **"What did I do last week?"** → `cass timeline --week --json --group-by day`
  — an activity overview rather than message hits. Then drill in with a search.
- **List recent sessions** → `cass sessions --json --limit 10`, or
  `cass sessions --current --json` for the current directory.
- **Overview / counts** ("which agent did I use most?") → `cass search "*"
  --json --aggregate agent,date --week`.

### 3. Drill into a hit

```bash
cass view <source_path> -n <line> -C 8 --json     # lines around a hit
cass expand <source_path> -n <line> --json        # messages around a hit
cass export <source_path> --format markdown       # full session as markdown
```

`cass resume <source_path> --json` gives a command to reopen the session in its
native agent. `cass pack "question" --robot --max-tokens 4000` builds a bounded,
cited bundle to carry findings into another prompt.

## Keep output lean

Start narrow (small `--limit`, a time filter, `--fields summary`). Prefer
`timeline` / `--aggregate` for overviews, `search` only when the user wants
specific messages. Summarize findings in prose with `source_path:line`
references — don't dump raw JSON at the user.

## When unsure, ask cass — it's self-describing

`cass <cmd> --help` (flags), `cass capabilities --json` (features, agent slugs,
exit codes), `cass robot-docs examples` (cheat sheet), `cass triage --json`
(readiness + next command). Deeper reference:
[references/cass-reference.md](references/cass-reference.md).
