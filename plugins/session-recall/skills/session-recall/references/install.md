# Installing cass

Only needed when `cass --version` fails (command not found). In most sessions
cass is already installed and you can skip this entirely.

Installing downloads and runs software, so confirm with the user before running
the command. Pick the one for their OS.

- **Windows (PowerShell):** the scriptblock form is required so the
  `-EasyMode -Verify` flags reach the installer (a plain `irm … | iex` pipe
  can't pass arguments):
  ```powershell
  & ([scriptblock]::Create((irm "https://raw.githubusercontent.com/Dicklesworthstone/coding_agent_session_search/main/install.ps1"))) -EasyMode -Verify
  ```
  This downloads the latest `cass-windows-amd64.zip` from GitHub Releases,
  verifies its checksum, installs `cass.exe` to `~/.local/bin`, and (easy mode)
  adds that directory to PATH. If the release has no prebuilt Windows asset, the
  script falls back to building from source (needs Rust).
- **macOS / Linux:**
  ```bash
  curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/coding_agent_session_search/main/install.sh?$(date +%s)" | bash -s -- --easy-mode --verify
  ```
- **Package managers (alternative):** `scoop install dicklesworthstone/cass`
  (Windows) or `brew install dicklesworthstone/tap/cass` (macOS/Linux).
- Pin a version by appending `-Version <tag>` (Windows) or `--version <tag>`
  (macOS/Linux).

After installing, if `cass` still isn't on PATH, it's at `~/.local/bin/cass` —
either call it by that full path or start a fresh shell. Manual download from
the releases page:
<https://github.com/Dicklesworthstone/coding_agent_session_search/releases/latest>.

To update an existing install later: `cass upgrade --check --json` (reports if
outdated), then `cass upgrade --yes`.
