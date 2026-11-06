---
name: setup
description: >-
  limit-aware가 한도 수치를 받도록 ~/.claude/settings.json의 statusLine을 설정한다.
  기존 statusLine이 있으면 보존하고 출력을 그대로 중계한다. limit-aware를 처음
  설치했거나 플러그인을 업데이트한 뒤, 또는 "한도 정보 없음"이 나올 때 사용한다.
disable-model-invocation: true
---

# setup

플러그인은 statusLine을 직접 등록할 수 없어서, 사용자 settings에 래퍼를 한 번 설치해야 한다.

1. 현재 상태를 확인하고 사용자에게 설명한다.

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/setup.py" status
   ```

2. 사용자가 동의하면 설치한다. 기존 settings는 `~/.claude/limit-aware/backups/`에 백업되고, 기존 statusLine은 `config.json`에 보존되어 출력이 그대로 중계된다.

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/setup.py" install
   ```

3. 되돌리려면 다음을 실행한다.

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/setup.py" uninstall
   ```

설치 후 첫 응답이 끝나면 수치가 기록된다. 플러그인을 업데이트한 뒤에는 `install`을 다시 실행해 복사본을 갱신한다.
