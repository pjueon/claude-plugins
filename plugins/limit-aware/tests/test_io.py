import json
import multiprocessing
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import setup as setup_mod  # noqa: E402
import state  # noqa: E402
import statusline  # noqa: E402


def _writer(path, n):
    for i in range(n):
        state.write_json_atomic(path, {"i": i, "pad": "x" * 2000})


def _run(script, *args, stdin=b"", env=None, timeout=30):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args], input=stdin, capture_output=True,
        env={**os.environ, **(env or {})}, timeout=timeout,
    )


class Env(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="la 한글 ")
        self.home = Path(self.tmp.name) / "limit-aware"
        os.environ["LIMIT_AWARE_HOME"] = str(self.home)

    def tearDown(self):
        os.environ.pop("LIMIT_AWARE_HOME", None)
        self.tmp.cleanup()


class StateTests(Env):
    def test_atomic_concurrent_reads_never_partial(self):
        path = self.home / "x.json"
        state.write_json_atomic(path, {"i": -1})
        procs = [multiprocessing.Process(target=_writer, args=(path, 100)) for _ in range(3)]
        for p in procs:
            p.start()
        while any(p.is_alive() for p in procs):
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (FileNotFoundError, PermissionError):
                pass
        for p in procs:
            p.join()
        self.assertIsInstance(state.read_json(path), dict)

    def test_read_json_broken_or_missing(self):
        self.home.mkdir(parents=True)
        (self.home / "bad.json").write_text("{", encoding="utf-8")
        self.assertIsNone(state.read_json(self.home / "bad.json"))
        self.assertIsNone(state.read_json(self.home / "none.json"))

    def test_session_id_validation(self):
        for bad in ("../x", "a\\b", "", None):
            self.assertIsNone(state.session_path(bad))

    def test_update_session_merges_owners(self):
        state.update_session("s1", {"context": {"used_percentage": 5}}, 1)
        state.update_session("s1", {"reported": {"five_hour": 50}}, 2)
        data = state.read_json(state.session_path("s1"))
        self.assertEqual(data["context"]["used_percentage"], 5)
        self.assertEqual(data["reported"]["five_hour"], 50)

    def test_prune(self):
        state.update_session("old", {"a": 1}, 1)
        state.update_session("new", {"a": 1}, 1)
        old = state.session_path("old")
        t = time.time() - 4 * 86400
        os.utime(old, (t, t))
        self.assertEqual(state.prune_sessions(time.time()), 1)
        self.assertFalse(old.exists())
        self.assertTrue(state.session_path("new").exists())


class HookTests(Env):
    def event(self, name, **kw):
        return json.dumps({"hook_event_name": name, "session_id": "sess1", **kw}).encode()

    def test_session_start_outputs_valid_json_ascii(self):
        state.write_json_atomic(self.home / "snapshot.json", {"rate_limits": {"five_hour": {
            "used_percentage": 80, "resets_at": time.time() + 3600, "observed_at": time.time()}}})
        r = _run("hook.py", stdin=self.event("SessionStart", source="startup"))
        self.assertEqual(r.returncode, 0)
        out = json.loads(r.stdout.decode("ascii"))
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("5h", out["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(state.read_json(state.session_path("sess1"))["reported"]["five_hour"], 75)

    def test_session_end_deletes_and_is_silent(self):
        state.update_session("sess1", {"a": 1}, 1)
        r = _run("hook.py", stdin=self.event("SessionEnd"))
        self.assertEqual(r.stdout, b"")
        self.assertFalse(state.session_path("sess1").exists())

    def test_garbage_stdin_exit_zero(self):
        for data in (b"", b"not json", b"\xff\xfe"):
            r = _run("hook.py", stdin=data)
            self.assertEqual((r.returncode, r.stdout), (0, b""))


class StatuslineTests(Env):
    PAYLOAD = {
        "session_id": "sess1",
        "rate_limits": {"five_hour": {"used_percentage": 20, "resets_at": 9999999999}},
        "context_window": {
            "context_window_size": 200000, "used_percentage": None,
            "current_usage": {"input_tokens": 1000, "cache_creation_input_tokens": 2000, "cache_read_input_tokens": 37000},
        },
    }

    def wrapped_cfg(self, script_text, **extra):
        bash = setup_mod.find_bash()
        if not bash:
            self.skipTest("bash 없음")
        child = Path(self.tmp.name) / "child.py"
        child.write_text(script_text, encoding="utf-8")
        cmd = f'"{Path(sys.executable).as_posix()}" "{child.as_posix()}"'
        state.write_json_atomic(self.home / "config.json", {"wrapped": {"command": cmd, "shell": "bash", "bash_path": bash}, **extra})

    def test_extract_computes_context_from_usage(self):
        sid, patch, ctx = statusline.extract(self.PAYLOAD, 5)
        self.assertEqual(sid, "sess1")
        self.assertEqual(patch["five_hour"]["observed_at"], 5)
        self.assertEqual((ctx["used_tokens"], ctx["used_percentage"]), (40000, 20.0))

    def test_extract_null_context_and_no_rate_limits(self):
        _, patch, ctx = statusline.extract({"session_id": "s", "context_window": {"current_usage": None}}, 1)
        self.assertEqual((patch, ctx), ({}, None))

    def test_merge_keeps_other_window(self):
        old = {"rate_limits": {"seven_day": {"used_percentage": 1, "resets_at": 2, "observed_at": 1}}}
        new = statusline.merge_snapshot(old, {"five_hour": {"used_percentage": 3}}, 9)
        self.assertEqual(set(new["rate_limits"]), {"seven_day", "five_hour"})
        self.assertEqual(new["statusline_seen_at"], 9)

    def test_records_and_relays_bytes_exactly(self):
        self.wrapped_cfg("import sys; sys.stdout.buffer.write('한글 상태줄'.encode('utf-8')); sys.exit(3)")
        r = _run("statusline.py", stdin=json.dumps(self.PAYLOAD).encode())
        self.assertEqual((r.stdout.decode("utf-8"), r.returncode), ("한글 상태줄", 3))
        self.assertEqual(state.read_json(self.home / "snapshot.json")["rate_limits"]["five_hour"]["used_percentage"], 20)
        self.assertEqual(state.read_json(state.session_path("sess1"))["context"]["used_tokens"], 40000)

    def test_relay_timeout_still_records(self):
        self.wrapped_cfg("import time; time.sleep(10)", relay_timeout_sec=1)
        r = _run("statusline.py", stdin=json.dumps(self.PAYLOAD).encode())
        self.assertEqual((r.returncode, r.stdout), (0, b""))
        self.assertIsNotNone(state.read_json(self.home / "snapshot.json"))

    def test_no_recursion_and_no_config(self):
        self.assertEqual(statusline.relay(b"{}", None), (b"", 0))
        ours = {"wrapped": {"command": '"py" "C:/x/limit-aware/statusline.py"'}}
        self.assertEqual(statusline.relay(b"{}", ours), (b"", 0))


class SetupTests(Env):
    SCRIPT = Path("C:/Users/x y/.claude/limit-aware/statusline.py")

    def test_build_command_quotes_and_slashes(self):
        cmd = setup_mod.build_command("C:\\Python 312\\python.exe", "C:\\Users\\한 글\\statusline.py")
        self.assertEqual(cmd, '"C:/Python 312/python.exe" "C:/Users/한 글/statusline.py"')

    def test_install_preserves_original_and_other_keys(self):
        settings = {"model": "sonnet", "statusLine": {"type": "command", "command": "orca.cmd", "padding": 1}, "z": 1}
        new, cfg = setup_mod.plan_install(settings, None, "py.exe", self.SCRIPT)
        self.assertEqual(cfg["original_statusLine"], settings["statusLine"])
        self.assertEqual(cfg["wrapped"]["command"], "orca.cmd")
        self.assertEqual(new["statusLine"]["padding"], 1)
        self.assertEqual(list(new), ["model", "statusLine", "z"])
        self.assertTrue(setup_mod.is_ours(new["statusLine"]))

    def test_reinstall_keeps_wrapped(self):
        new, cfg = setup_mod.plan_install({"statusLine": {"command": "orca.cmd"}}, None, "py.exe", self.SCRIPT)
        _, cfg2 = setup_mod.plan_install(new, cfg, "py.exe", self.SCRIPT)
        self.assertEqual(cfg2["wrapped"], cfg["wrapped"])

    def test_uninstall_restores_or_removes(self):
        orig = {"type": "command", "command": "orca.cmd"}
        new, cfg = setup_mod.plan_install({"statusLine": orig}, None, "py.exe", self.SCRIPT)
        self.assertEqual(setup_mod.plan_uninstall(new, cfg)["statusLine"], orig)
        new, cfg = setup_mod.plan_install({"a": 1}, None, "py.exe", self.SCRIPT)
        self.assertNotIn("statusLine", setup_mod.plan_uninstall(new, cfg))

    def test_cli_roundtrip_and_bad_json(self):
        settings = Path(self.tmp.name) / "settings.json"
        orig = {"model": "x", "statusLine": {"type": "command", "command": "orca.cmd"}}
        settings.write_text(json.dumps(orig), encoding="utf-8")
        for cmd in ("install", "install", "uninstall"):
            r = _run("setup.py", cmd, "--settings", str(settings))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(settings.read_text(encoding="utf-8")), orig)
        settings.write_text("{bad", encoding="utf-8")
        r = _run("setup.py", "install", "--settings", str(settings))
        self.assertEqual(r.returncode, 1)
        self.assertEqual(settings.read_text(encoding="utf-8"), "{bad")

    def test_uninstall_refuses_when_statusline_changed(self):
        settings = Path(self.tmp.name) / "settings.json"
        settings.write_text(json.dumps({"statusLine": {"command": "orca.cmd"}}), encoding="utf-8")
        _run("setup.py", "install", "--settings", str(settings))
        changed = {"statusLine": {"command": "other.cmd"}}
        settings.write_text(json.dumps(changed), encoding="utf-8")
        r = _run("setup.py", "uninstall", "--settings", str(settings))
        self.assertEqual(r.returncode, 1)
        self.assertEqual(json.loads(settings.read_text(encoding="utf-8")), changed)


if __name__ == "__main__":
    unittest.main()
