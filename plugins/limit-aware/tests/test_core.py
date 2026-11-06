import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import core  # noqa: E402

TZ = timezone(timedelta(hours=9))
NOW = datetime(2026, 11, 6, 13, 42, tzinfo=TZ).timestamp()


def at(h, m, day=6):
    return datetime(2026, 11, day, h, m, tzinfo=TZ).timestamp()


def snap(five=None, seven=None, observed=NOW):
    rl = {}
    if five:
        rl["five_hour"] = {"used_percentage": five[0], "resets_at": five[1], "observed_at": observed}
    if seven:
        rl["seven_day"] = {"used_percentage": seven[0], "resets_at": seven[1], "observed_at": observed}
    return {"rate_limits": rl}


def ctx(pct, tokens=None, size=200000, observed=NOW):
    return {"used_percentage": pct, "used_tokens": tokens, "window_size": size, "observed_at": observed}


class Buckets(unittest.TestCase):
    def test_bucket_of(self):
        t = core.LIMIT_THRESHOLDS
        self.assertEqual([core.bucket_of(v, t) for v in (49.9, 50, 74, 98.5, 120)], [0, 50, 50, 98, 98])
        self.assertIsNone(core.bucket_of(None, t))


class Format(unittest.TestCase):
    def test_golden_line(self):
        s = snap(five=(78, at(14, 30)), seven=(41, at(9, 0, day=9)))
        line = core.format_line(s, ctx(62, 124000), NOW, TZ)
        self.assertEqual(
            line,
            "[한도] 5h 22% 남음·보통 (48분 후 14:30 리셋) · 주간 59% 남음·"
            "여유 (월 09:00 리셋) · 컨텍스트 38% 남음 (124k/200k)",
        )

    def test_pace_boundaries(self):
        w, r = 5 * 3600, NOW + 2.5 * 3600  # 경과 50%
        self.assertEqual(core.pace(42, r, w, NOW), "여유")
        self.assertEqual(core.pace(42.5, r, w, NOW), "보통")
        self.assertEqual(core.pace(55, r, w, NOW), "보통")
        self.assertEqual(core.pace(55.5, r, w, NOW), "빠름")
        early = NOW + 4.95 * 3600  # 경과 1%: 분모 하한 10%
        self.assertEqual(core.pace(2, early, w, NOW), "여유")
        self.assertEqual(core.pace(15, early, w, NOW), "빠름")

    def test_duration_and_reset(self):
        self.assertEqual(core.format_duration(30), "1분")
        self.assertEqual(core.format_duration(3 * 3600 + 12 * 60), "3시간 12분")
        self.assertEqual(core.format_duration(2 * 86400 + 5 * 3600), "2일 5시간")
        self.assertEqual(core.format_reset_at(at(14, 30), NOW, TZ), "14:30")
        self.assertEqual(core.format_reset_at(at(1, 0, day=7), NOW, TZ), "토 01:00")

    def test_tokens(self):
        self.assertEqual(core.format_tokens(124000), "124k")
        self.assertEqual(core.format_tokens(1_000_000), "1M")
        self.assertEqual(core.format_tokens(1_500_000), "1.5M")

    def test_expired_window_hidden(self):
        s = snap(five=(80, NOW - 1), seven=(10, at(9, 0, day=12)))
        self.assertNotIn("5h", core.format_line(s, None, NOW, TZ))
        self.assertIsNone(core.format_line(snap(five=(80, NOW - 1)), None, NOW, TZ))

    def test_context_only(self):
        self.assertEqual(core.format_line({"rate_limits": {}}, ctx(30), NOW, TZ), "[한도] 컨텍스트 70% 남음")

    def test_stale_and_warning(self):
        s = snap(five=(96, at(14, 30)), observed=NOW - 12 * 60)
        line = core.format_line(s, None, NOW, TZ)
        self.assertIn("(12분 전 수치)", line)
        self.assertIn("5h 95% 이상 사용", line)
        self.assertNotIn("이상 사용", core.format_line(snap(five=(90, at(14, 30))), None, NOW, TZ))
        self.assertIn("컨텍스트 95%", core.format_line(snap(five=(10, at(14, 30))), ctx(95), NOW, TZ))

    def test_detail(self):
        out = core.format_detail(snap(five=(78, at(14, 30))), ctx(62, 124000), NOW, TZ)
        self.assertIn("5h: 78% 사용", out)
        self.assertIn("컨텍스트", out)
        self.assertEqual(core.format_detail(None, None, NOW, TZ), core.NO_SNAPSHOT)


class Decide(unittest.TestCase):
    S = snap(five=(76, at(14, 30)), seven=(10, at(9, 0, day=12)))

    def run_ev(self, event, s=None, session=None, source=None, sub=False):
        return core.decide(event, source, sub, s if s is not None else self.S, session or {}, NOW, TZ)

    def test_session_start_always_injects_and_records(self):
        text, patch = self.run_ev("SessionStart")
        self.assertIn("5h", text)
        self.assertEqual(patch["reported"]["five_hour"], 75)

    def test_crossing_injects_once(self):
        session = {"reported": {"five_hour": 50, "seven_day": 0, "context": 0}}
        text, patch = self.run_ev("UserPromptSubmit", session=session)
        self.assertIsNotNone(text)
        self.assertEqual(patch["reported"]["five_hour"], 75)
        text, _ = self.run_ev("PostToolUse", session={"reported": patch["reported"]})
        self.assertIsNone(text)

    def test_skips_multiple_buckets_in_one_report(self):
        s = snap(five=(92, at(14, 30)))
        text, patch = self.run_ev("PostToolUse", s=s, session={"reported": {"five_hour": 0}})
        self.assertIsNotNone(text)
        self.assertEqual(patch["reported"]["five_hour"], 90)

    def test_reset_lowers_then_rereports(self):
        low = snap(five=(10, at(14, 30)))
        text, patch = self.run_ev("PostToolUse", s=low, session={"reported": {"five_hour": 90}})
        self.assertIsNone(text)
        self.assertEqual(patch["reported"]["five_hour"], 0)
        high = snap(five=(55, at(14, 30)))
        text, _ = self.run_ev("PostToolUse", s=high, session={"reported": patch["reported"]})
        self.assertIsNotNone(text)

    def test_context_crossing_and_compact(self):
        s = snap(five=(10, at(14, 30)))
        text, patch = self.run_ev("PostToolUse", s=s, session={"context": ctx(72), "reported": {"context": 50}})
        self.assertIn("컨텍스트", text)
        self.assertEqual(patch["reported"]["context"], 70)
        text, patch = self.run_ev("SessionStart", s=s, source="compact", session={"context": ctx(90), "reported": {"context": 85}})
        self.assertNotIn("컨텍스트", text)
        self.assertEqual(patch["reported"]["context"], 0)

    def test_null_context_keeps_reported(self):
        s = snap(five=(10, at(14, 30)))
        _, patch = self.run_ev("PostToolUse", s=s, session={"context": None, "reported": {"context": 70}})
        self.assertEqual(patch["reported"]["context"], 70)

    def test_no_snapshot_notice_once(self):
        text, patch = core.decide("SessionStart", "startup", False, None, {}, NOW, TZ)
        self.assertEqual(text, core.NO_SNAPSHOT)
        text, _ = core.decide("UserPromptSubmit", None, False, None, patch, NOW, TZ)
        self.assertIsNone(text)

    def test_snapshot_without_rate_limits_is_silent(self):
        text, _ = core.decide("SessionStart", "startup", False, {"rate_limits": {}}, {}, NOW, TZ)
        self.assertIsNone(text)

    def test_subagent_start_no_context_no_state(self):
        text, patch = self.run_ev("SubagentStart", session={"context": ctx(60)})
        self.assertIn("5h", text)
        self.assertNotIn("컨텍스트", text)
        self.assertEqual(patch, {})

    def test_inside_subagent_is_silent(self):
        text, patch = self.run_ev("PostToolUse", session={"reported": {}}, sub=True)
        self.assertIsNone(text)
        self.assertEqual(patch, {})


if __name__ == "__main__":
    unittest.main()
