# notice-me

A Claude Code plugin that flashes your taskbar icon or runs a custom command when Claude Code's window loses focus (i.e., you're looking at another window).

**Windows only.** On non-Windows OSes, the hook does nothing and exits immediately — installing it elsewhere is harmless but has no effect.

## How it works

The hook fires when Claude Code sends a notification (`Notification`) or finishes responding (`Stop`, `SubagentStop`). At that point:

1. If the window you're currently looking at is the one running Claude Code (focused), nothing happens.
2. If it's not focused, the taskbar icon flashes (when `flashEnabled` is on) and any registered custom commands run.

The flashing stops automatically once you switch back to that window.

## Configuration

The config file lives at `~/.claude/notice-me.json`. If it doesn't exist, the defaults below apply.

```json
{
  "flashEnabled": true,
  "ignoreTypes": ["idle_prompt", "agent_completed"],
  "debounceMs": 2000,
  "customCommands": [
    "python ./my_script.py"
  ],
  "debug": false
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `flashEnabled` | boolean | `true` | Toggles taskbar flashing on/off. `customCommands` still run even when this is off. |
| `ignoreTypes` | string[] | `["idle_prompt", "agent_completed"]` | Notification types to ignore. See "Notification types" below. |
| `debounceMs` | number | `2000` | Minimum interval (ms) before the same session can fire another notification. Prevents overlapping notifications firing too close together. |
| `customCommands` | string[] | `[]` | Commands to run for every notification that isn't ignored. Run in order, fire-and-forget (no wait for completion). The working directory is the current Claude Code session's working folder. |
| `debug` | boolean | `false` | When `true`, logs one line per run describing what was evaluated and what was done. Turn this on to debug unexpected notification behavior. |

### Notification types (valid values for `ignoreTypes`)

- `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog`, `elicitation_complete`, `elicitation_response`, `agent_needs_input`, `agent_completed` — subtypes of Claude Code's `Notification` event
- `stop` — when a response finishes (`Stop`)
- `subagent_stop` — when a subagent finishes (`SubagentStop`)

`idle_prompt` and `agent_completed` are ignored by default (`agent_completed` overlaps in meaning with `stop`, so it's excluded to avoid duplicate firing). Remove them from `ignoreTypes` to enable them.

### `customCommands` safety notes

- Commands listed here run directly in the shell. Since these are values you wrote yourself into a local config file, this is safe by default — but **don't wire up a script or tool that fills this file with untrusted values.**

## Custom command example

```json
{
  "customCommands": [
    "python ./my_script.py"
  ]
}
```

## Debugging

With `debug: true`, each run's result is appended as a line to `${CLAUDE_PLUGIN_DATA}/debug.log`. Check this log when notifications aren't firing or are firing unexpectedly.
