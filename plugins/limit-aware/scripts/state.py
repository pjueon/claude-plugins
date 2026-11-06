"""limit-aware 상태 파일 I/O. 모든 쓰기는 원자적이고, 읽기는 실패해도 None을 돌려준다."""
import json
import os
import re
import tempfile
import time
from pathlib import Path

SID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


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


def session_path(sid):
    if not isinstance(sid, str) or not SID_RE.match(sid):
        return None
    return home() / "sessions" / f"{sid}.json"


def update_session(sid, patch, now):
    """쓰기 직전에 다시 읽어 병합한다(statusline과 hook이 각자 자기 키만 쓴다)."""
    path = session_path(sid)
    if path is None or not patch:
        return
    data = read_json(path) or {"version": 1}
    if all(data.get(k) == v for k, v in patch.items()) and data.get("version"):
        return
    data.update(patch)
    data["updated_at"] = now
    write_json_atomic(path, data)


def load(sid):
    path = session_path(sid)
    return read_json(home() / "snapshot.json"), (read_json(path) if path else None) or {}


def delete_session(sid):
    path = session_path(sid)
    if path:
        try:
            path.unlink()
        except OSError:
            pass


def prune_sessions(now, max_age_sec=3 * 86400):
    removed = 0
    for p in (home() / "sessions").glob("*.json"):
        try:
            if now - p.stat().st_mtime > max_age_sec:
                p.unlink()
                removed += 1
        except OSError:
            pass
    return removed
