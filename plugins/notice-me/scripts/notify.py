import ctypes
import json
import os
import platform
import subprocess
import sys
import time
from ctypes import wintypes

DEFAULT_CONFIG = {
    "flashEnabled": True,
    "ignoreTypes": ["idle_prompt", "agent_completed"],
    "debounceMs": 2000,
    "customCommands": [],
    "debug": False,
}

CONFIG_PATH = os.path.expanduser("~/.claude/notice-me.json")

TH32CS_SNAPPROCESS = 0x00000002
GW_OWNER = 4
FLASHW_TRAY = 0x00000002
FLASHW_TIMERNOFG = 0x0000000C  # flash until the window comes to the foreground (MSDN FLASHWINFO)


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_char * 260),
    ]


class FLASHWINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("hwnd", wintypes.HWND),
        ("dwFlags", wintypes.DWORD),
        ("uCount", wintypes.UINT),
        ("dwTimeout", wintypes.DWORD),
    ]


def load_config():
    config = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config.update(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return config


def get_status_dir():
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.expanduser("~/.claude/notice-me-data")
    status_dir = os.path.join(base, "status")
    os.makedirs(status_dir, exist_ok=True)
    return status_dir


def cleanup_old_status_files(status_dir):
    cutoff = time.time() - 24 * 3600
    try:
        for name in os.listdir(status_dir):
            path = os.path.join(status_dir, name)
            try:
                if os.path.getmtime(path) < cutoff:
                    os.remove(path)
            except OSError:
                pass
    except OSError:
        pass


def read_last_notified_ms(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("lastNotifiedAtMs")
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def claim_notification_slot(path, debounce_ms):
    """Atomically claim the right to fire, re-checking the debounce window against concurrent hook invocations."""
    now_ms = int(time.time() * 1000)
    payload = json.dumps({"lastNotifiedAtMs": now_ms}).encode("utf-8")

    def try_create():
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return False
        with os.fdopen(fd, "wb") as f:
            f.write(payload)
        return True

    if try_create():
        return True, None

    last_ms = read_last_notified_ms(path)
    ms_since_last = now_ms - last_ms if last_ms is not None else None
    if ms_since_last is not None and ms_since_last < debounce_ms:
        return False, ms_since_last

    try:
        os.remove(path)
    except OSError:
        pass
    return try_create(), ms_since_last


def build_pid_to_ppid():
    kernel32 = ctypes.windll.kernel32
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    entry = PROCESSENTRY32()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
    pid_to_ppid = {}
    if kernel32.Process32First(snapshot, ctypes.byref(entry)):
        while True:
            pid_to_ppid[entry.th32ProcessID] = entry.th32ParentProcessID
            if not kernel32.Process32Next(snapshot, ctypes.byref(entry)):
                break
    kernel32.CloseHandle(snapshot)
    return pid_to_ppid


def build_ancestor_chain(pid):
    pid_to_ppid = build_pid_to_ppid()
    chain = [pid]
    seen = {pid}
    cur = pid
    while cur in pid_to_ppid:
        parent = pid_to_ppid[cur]
        if parent in seen:
            break
        chain.append(parent)
        seen.add(parent)
        cur = parent
    return chain


def find_target_hwnd(ancestors, foreground_hwnd):
    user32 = ctypes.windll.user32

    if foreground_hwnd:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(foreground_hwnd, ctypes.byref(pid))
        if pid.value in ancestors:
            return foreground_hwnd

    windows_by_pid = {}

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, _lparam):
        if (
            user32.IsWindowVisible(hwnd)
            and user32.GetWindowTextLengthW(hwnd) > 0
            and not user32.GetWindow(hwnd, GW_OWNER)
        ):
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            windows_by_pid.setdefault(pid.value, hwnd)
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)

    for pid in ancestors:
        if pid in windows_by_pid:
            return windows_by_pid[pid]
    return None


def get_foreground_window():
    return ctypes.windll.user32.GetForegroundWindow()


def flash(hwnd):
    info = FLASHWINFO()
    info.cbSize = ctypes.sizeof(FLASHWINFO)
    info.hwnd = hwnd
    info.dwFlags = FLASHW_TRAY | FLASHW_TIMERNOFG
    info.uCount = 0
    info.dwTimeout = 0
    ctypes.windll.user32.FlashWindowEx(ctypes.byref(info))


def get_debug_log_path():
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.expanduser("~/.claude/notice-me-data")
    return os.path.join(base, "debug.log")


def log_debug(record):
    path = get_debug_log_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    line = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), **record}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


def resolve_notification_type(payload):
    event = payload.get("hook_event_name", "")
    if event == "Stop":
        return "stop"
    if event == "SubagentStop":
        return "subagent_stop"
    if event == "Notification":
        return payload.get("notification_type", "unknown")
    return None


def process(payload, config):
    """Process a single hook payload and return a record of what was done (for debug logging)."""
    record = {
        "hook_event_name": payload.get("hook_event_name"),
        "session_id": payload.get("session_id", "unknown"),
    }

    notif_type = resolve_notification_type(payload)
    record["notification_type"] = notif_type
    if "message" in payload:
        record["message"] = payload["message"]
    if notif_type is None:
        record["result"] = "unrecognized_event"
        return record

    if notif_type in config["ignoreTypes"]:
        record["result"] = "ignored_type"
        return record

    session_id = record["session_id"]
    cwd = payload.get("cwd") or os.getcwd()

    status_dir = get_status_dir()
    cleanup_old_status_files(status_dir)
    status_path = os.path.join(status_dir, f"{session_id}.json")

    now_ms = int(time.time() * 1000)
    last_ms = read_last_notified_ms(status_path)
    if last_ms is not None and (now_ms - last_ms) < config["debounceMs"]:
        record["result"] = "debounced"
        record["ms_since_last"] = now_ms - last_ms
        return record

    ancestors = build_ancestor_chain(os.getpid())
    foreground_hwnd = get_foreground_window()
    target_hwnd = find_target_hwnd(ancestors, foreground_hwnd)
    is_focused = target_hwnd is not None and foreground_hwnd == target_hwnd
    record["target_hwnd"] = target_hwnd
    record["is_focused"] = is_focused
    if is_focused:
        record["result"] = "focused_skip"
        return record

    claimed, ms_since_last = claim_notification_slot(status_path, config["debounceMs"])
    if not claimed:
        record["result"] = "debounced"
        if ms_since_last is not None:
            record["ms_since_last"] = ms_since_last
        return record

    flashed = bool(config["flashEnabled"] and target_hwnd)
    if flashed:
        flash(target_hwnd)
    record["flashed"] = flashed

    record["custom_commands_run"] = len(config["customCommands"])
    for command in config["customCommands"]:
        subprocess.Popen(command, shell=True, cwd=cwd)

    record["result"] = "fired"
    return record


def main():
    if platform.system() != "Windows":
        return

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return

    config = load_config()
    record = process(payload, config)
    if config.get("debug"):
        log_debug(record)


if __name__ == "__main__":
    main()
