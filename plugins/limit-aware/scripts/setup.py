"""statusLine 설정 도우미. 사용법: setup.py status|install|uninstall [--settings PATH]

install: 기존 statusLine을 config.json에 보존하고, settings.json의 statusLine만 래퍼로 교체한다.
"""
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

import state

SCRIPT = Path(__file__).resolve().parent / "statusline.py"
MARK = "limit-aware/statusline.py"


def settings_path():
    base = os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
    return Path(base) / "settings.json"


def build_command(python_exe, script):
    return f'"{Path(python_exe).as_posix()}" "{Path(script).as_posix()}"'


def is_ours(status_line):
    return isinstance(status_line, dict) and MARK in str(status_line.get("command", "")).replace("\\", "/")


def find_bash():
    for cand in (os.environ.get("CLAUDE_CODE_GIT_BASH_PATH"), shutil.which("bash"),
                 "C:/Program Files/Git/bin/bash.exe", "C:/Program Files/Git/usr/bin/bash.exe"):
        if cand and "system32" not in cand.lower().replace("\\", "/") and Path(cand).exists():
            return Path(cand).as_posix()
    return None


def plan_install(settings, config, python_exe, script):
    """(새 settings, 새 config). 순수 함수."""
    cur = settings.get("statusLine")
    config = dict(config or {"version": 1})
    if not is_ours(cur):
        config["original_statusLine"] = cur
        config["wrapped"] = None
        if isinstance(cur, dict) and cur.get("command"):
            bash = find_bash()
            config["wrapped"] = {"command": cur["command"], "shell": "bash" if bash else "powershell", "bash_path": bash}
        config.setdefault("relay_timeout_sec", 3)
    new = {"type": "command", "command": build_command(python_exe, script)}
    for key in ("padding", "refreshInterval"):
        if isinstance(cur, dict) and key in cur:
            new[key] = cur[key]
    return {**settings, "statusLine": new}, config


def plan_uninstall(settings, config):
    out = dict(settings)
    original = (config or {}).get("original_statusLine")
    if original is None:
        out.pop("statusLine", None)
    else:
        out["statusLine"] = original
    return out


def _write_settings(path, settings):
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _read_settings(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _backup(path):
    if path.exists():
        dest = state.home() / "backups" / f"settings.{time.strftime('%Y%m%d-%H%M%S')}.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        print(f"백업: {dest}")


def cmd_status(path):
    settings = _read_settings(path)
    cfg = state.read_json(state.home() / "config.json") or {}
    snap = state.read_json(state.home() / "snapshot.json")
    print(f"settings: {path}")
    print(f"statusLine: {json.dumps(settings.get('statusLine'), ensure_ascii=False)}")
    print(f"limit-aware 래퍼 적용: {is_ours(settings.get('statusLine'))}")
    print(f"중계 대상: {json.dumps(cfg.get('wrapped'), ensure_ascii=False)}")
    seen = (snap or {}).get("statusline_seen_at")
    print(f"스냅샷: {'없음' if seen is None else f'{int((time.time() - seen) // 60)}분 전 갱신'}")
    installed = state.home() / "statusline.py"
    print(f"복사본: {'있음' if installed.exists() else '없음'} (플러그인 업데이트 후에는 install을 다시 실행)")


def cmd_install(path):
    settings = _read_settings(path)
    cfg = state.read_json(state.home() / "config.json")
    installed = state.home() / "statusline.py"
    new_settings, new_cfg = plan_install(settings, cfg, sys.executable, installed)
    _backup(path)
    installed.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCRIPT, installed)
    state.write_json_atomic(state.home() / "config.json", new_cfg)
    latest = _read_settings(path)  # 쓰기 직전에 다시 읽어 statusLine 키만 교체
    latest["statusLine"] = new_settings["statusLine"]
    _write_settings(path, latest)
    print("statusLine 변경:")
    print(f"  전: {json.dumps(settings.get('statusLine'), ensure_ascii=False)}")
    print(f"  후: {json.dumps(latest['statusLine'], ensure_ascii=False)}")
    print(f"  중계: {json.dumps(new_cfg.get('wrapped'), ensure_ascii=False)}")


def cmd_uninstall(path):
    cfg = state.read_json(state.home() / "config.json")
    if cfg is None:
        print("config.json이 없어 되돌릴 원본 정보가 없습니다.")
        return 1
    _backup(path)
    latest = _read_settings(path)
    _write_settings(path, plan_uninstall(latest, cfg))
    print("원래 statusLine으로 복원했습니다.")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("status", "install", "uninstall"))
    ap.add_argument("--settings", type=Path, default=None)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    path = args.settings or settings_path()
    try:
        if args.command == "status":
            cmd_status(path)
        elif args.command == "install":
            cmd_install(path)
        else:
            return cmd_uninstall(path)
    except ValueError as e:
        print(f"settings.json을 읽지 못해 중단했습니다(파일은 수정하지 않음): {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
