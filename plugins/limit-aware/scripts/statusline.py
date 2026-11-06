"""statusLine 래퍼 (단독 실행 파일; setup이 ~/.claude/limit-aware/ 로 복사한다).

stdin JSON에서 한도·컨텍스트 수치를 파일로 기록한 뒤, config.json에 보존된 기존
statusLine 명령이 있으면 같은 stdin으로 실행해 출력과 종료 코드를 그대로 중계한다.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

VERSION = "0.1.0"
SID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
RECURSION_ENV = "LIMIT_AWARE_STATUSLINE"


def home():
    if os.environ.get("LIMIT_AWARE_HOME"):
        return Path(os.environ["LIMIT_AWARE_HOME"])
    base = os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
    return Path(base) / "limit-aware"


def read_json(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write_json_atomic(path, data):
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
    except OSError:
        return False
    for _ in range(5):
        try:
            os.replace(tmp, path)
            return True
        except PermissionError:
            time.sleep(0.02)
        except OSError:
            break
    try:
        os.unlink(tmp)
    except OSError:
        pass
    return False


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def extract(payload, now):
    """(session_id, rate_limits 패치, context 또는 None)"""
    sid = payload.get("session_id")
    rl = payload.get("rate_limits") if isinstance(payload.get("rate_limits"), dict) else {}
    patch = {}
    for key in ("five_hour", "seven_day"):
        w = rl.get(key)
        if isinstance(w, dict) and _num(w.get("used_percentage")) and _num(w.get("resets_at")):
            patch[key] = {"used_percentage": w["used_percentage"], "resets_at": w["resets_at"], "observed_at": now}
    cw = payload.get("context_window") if isinstance(payload.get("context_window"), dict) else {}
    size, pct, cu = cw.get("context_window_size"), cw.get("used_percentage"), cw.get("current_usage")
    tokens = None
    if isinstance(cu, dict):
        tokens = sum(cu.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    if not _num(pct) and _num(tokens) and _num(size) and size:
        pct = tokens / size * 100
    ctx = None
    if _num(pct):
        ctx = {"used_percentage": pct, "used_tokens": tokens, "window_size": size, "observed_at": now}
    return sid, patch, ctx


def merge_snapshot(old, patch, now):
    snap = old if isinstance(old, dict) else {}
    rl = snap.get("rate_limits") if isinstance(snap.get("rate_limits"), dict) else {}
    rl = {**rl, **patch}
    return {"version": 1, "statusline_seen_at": now, "rate_limits": rl}


def record(raw, now):
    try:
        payload = json.loads(raw.decode("utf-8"))
        sid, patch, ctx = extract(payload, now)
        base = home()
        write_json_atomic(base / "snapshot.json", merge_snapshot(read_json(base / "snapshot.json"), patch, now))
        if isinstance(sid, str) and SID_RE.match(sid):
            path = base / "sessions" / f"{sid}.json"
            data = read_json(path) or {"version": 1}
            data.update({"context": ctx, "updated_at": now})
            write_json_atomic(path, data)
    except Exception:
        pass


def relay(raw, cfg):
    """기존 statusLine 명령을 실행해 (stdout 바이트, 종료 코드)를 돌려준다. 실패하면 ('', 0)."""
    wrapped = (cfg or {}).get("wrapped")
    if not isinstance(wrapped, dict) or not wrapped.get("command") or os.environ.get(RECURSION_ENV):
        return b"", 0
    command = wrapped["command"]
    if "limit-aware/statusline.py" in command.replace("\\", "/"):
        return b"", 0
    if wrapped.get("shell") == "powershell":
        argv = ["powershell", "-NoProfile", "-Command", command]
    else:
        argv = [wrapped.get("bash_path") or "bash", "-c", command]
    try:
        proc = subprocess.run(
            argv, input=raw, capture_output=True,
            timeout=cfg.get("relay_timeout_sec", 3), env={**os.environ, RECURSION_ENV: "1"},
        )
    except (OSError, subprocess.SubprocessError):
        return b"", 0
    return proc.stdout, proc.returncode


def main():
    raw = sys.stdin.buffer.read()
    record(raw, time.time())
    out, code = relay(raw, read_json(home() / "config.json"))
    sys.stdout.buffer.write(out)
    sys.stdout.buffer.flush()
    return code


if __name__ == "__main__":
    sys.exit(main())
