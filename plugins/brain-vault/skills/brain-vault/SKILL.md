---
name: brain-vault
description: >-
  Access, search, or edit the user's "Brain" Obsidian vault (their personal
  notes / knowledge base) from any project. Resolves the vault path
  cross-platform (Windows + Linux) via the BRAIN_VAULT_PATH environment
  variable, falling back to auto-detection. Use whenever the user references
  their Brain vault, personal notes, memos, inbox, or wants to read/write vault
  content while working outside the vault directory.
---

# brain-vault

Locate and work with the user's **Brain** Obsidian vault from anywhere on the
machine. The vault is a structured personal knowledge base; its content is
synced across machines by Obsidian Sync, so its absolute path differs per
machine. This skill resolves that path, then hands off to the vault's own rules.

The skill is intentionally thin: once the path is resolved, **read the vault's
`CLAUDE.md`** for all conventions (Korean, frontmatter, folder layout, commit
style). Do not duplicate those rules here.

## Step 1 — Resolve the vault path

Run this in the Bash tool (works on both Windows Git Bash and Linux). It checks
the env var first, then a default location:

```bash
if [ -n "$BRAIN_VAULT_PATH" ] && [ -d "$BRAIN_VAULT_PATH" ]; then
  echo "FOUND_ENV:$BRAIN_VAULT_PATH"
elif [ -d "$HOME/Documents/Brain" ]; then
  echo "FOUND_DEFAULT:$HOME/Documents/Brain"
else
  echo "NOT_FOUND"
fi
```

Interpret the result:

- **`FOUND_ENV:<path>`** → use `<path>` as the vault root. Proceed to Step 3.
- **`FOUND_DEFAULT:<path>`** → the env var isn't set but the vault is at the
  standard location. Use `<path>`, then go to Step 2 to offer registering it.
- **`NOT_FOUND`** → neither worked. Go to Step 2 and ask the user for the path.

## Step 2 — Register `BRAIN_VAULT_PATH` (only when needed)

Skip this entirely if Step 1 returned `FOUND_ENV`.

**If `FOUND_DEFAULT`:** tell the user you found the vault at the default path,
and ask: *"이 경로를 `BRAIN_VAULT_PATH` 환경변수로 영구 등록해둘까요? (다음
기기/세션부터 자동 인식됩니다)"* — register only if they agree.

**If `NOT_FOUND`:** ask the user for the vault's absolute path. Do not guess.

To register (use the command matching the user's OS), substituting `<PATH>`:

- **Windows** (PowerShell tool):
  ```powershell
  [Environment]::SetEnvironmentVariable("BRAIN_VAULT_PATH", "<PATH>", "User")
  ```
- **Linux** (Bash tool) — append to the user's shell rc and current session:
  ```bash
  echo 'export BRAIN_VAULT_PATH="<PATH>"' >> ~/.bashrc
  ```
  (use `~/.zshrc` instead if the user's shell is zsh)

**Always tell the user after registering:** the new value only reaches *new*
processes — they must **restart the terminal / IDE / Claude Code** for it to be
picked up automatically next time. The current session already has the resolved
path in hand, so continue working now without restarting.

## Step 3 — Work with the vault

With the resolved root (call it `$VAULT`):

1. **Read `$VAULT/CLAUDE.md` first.** It defines how to operate in this vault —
   follow it. Notably: communicate with the user in Korean (존댓말); commit
   messages in Korean without `Co-Authored-by`.
2. Use **absolute paths** under `$VAULT` for all reads/edits (don't rely on `cd`
   persisting). Key folders include `00. Inbox/` (incoming notes) and
   `05. Meta/Templates/`.
3. The vault is a git repo used for change tracking. Commit only when the user
   asks, following the vault's commit conventions.

## Notes

- Resolution order is **env var → default path → ask**. The env var only matters
  on machines where the vault lives somewhere non-standard, or when you want
  zero-touch detection across machines.
- This skill never assumes a path. If detection fails, it asks rather than
  writing to a guessed location.
