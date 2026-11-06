"""훅 진입점. stdin 이벤트 JSON → 필요할 때만 additionalContext 출력. 항상 exit 0."""
import json
import sys
import time
from datetime import datetime

import core
import state


def main():
    try:
        event = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        name = event.get("hook_event_name")
        sid = event.get("session_id")
        now = time.time()
        if name == "SessionEnd":
            state.delete_session(sid)
            return 0
        if name == "SessionStart":
            state.prune_sessions(now)
        snapshot, session = state.load(sid)
        tz = datetime.now().astimezone().tzinfo
        text, patch = core.decide(name, event.get("source"), "agent_id" in event, snapshot, session, now, tz)
        state.update_session(sid, patch, now)
        if text:
            out = {"hookSpecificOutput": {"hookEventName": name, "additionalContext": text}}
            sys.stdout.write(json.dumps(out, ensure_ascii=True))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
