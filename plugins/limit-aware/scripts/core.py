"""limit-aware 순수 로직 (I/O 없음). 시각(now)과 시간대(tz)는 인자로 받는다."""
from datetime import datetime

LIMIT_THRESHOLDS = (50, 75, 90, 95, 98)
CONTEXT_THRESHOLDS = (50, 70, 85, 95)
WARN_AT = 95
STALE_SEC = 600
WINDOW_SEC = {"five_hour": 5 * 3600, "seven_day": 7 * 86400}
LABEL = {"five_hour": "5h", "seven_day": "주간", "context": "컨텍스트"}
WEEKDAYS = "월화수목금토일"
KEYS = ("five_hour", "seven_day", "context")
NO_SNAPSHOT = "[한도] 한도 정보 없음(statusLine 미설정 — /limit-aware:setup)"


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def bucket_of(used, thresholds):
    """넘은 최대 임계값. 미만이면 0, 값이 없으면 None."""
    if not _num(used):
        return None
    return max((t for t in thresholds if used >= t), default=0)


def active_windows(snapshot, now):
    """resets_at이 지나지 않은 5h/주간 창만 반환."""
    rl = (snapshot or {}).get("rate_limits")
    if not isinstance(rl, dict):
        return {}
    out = {}
    for key in WINDOW_SEC:
        w = rl.get(key)
        if isinstance(w, dict) and _num(w.get("used_percentage")) and _num(w.get("resets_at")) and w["resets_at"] > now:
            out[key] = w
    return out


def context_view(ctx):
    """used_percentage가 있는 컨텍스트만 유효."""
    if isinstance(ctx, dict) and _num(ctx.get("used_percentage")):
        return ctx
    return None


def current_levels(windows, ctx):
    levels = {k: bucket_of(w["used_percentage"], LIMIT_THRESHOLDS) for k, w in windows.items()}
    levels["context"] = bucket_of(ctx["used_percentage"], CONTEXT_THRESHOLDS) if ctx else None
    return levels


def pace(used, resets_at, window_sec, now):
    """창 끝 투영 사용률로 판정: <85 여유, <=110 보통, 그 위 빠름."""
    elapsed = min(max(1 - (resets_at - now) / window_sec, 0.0), 1.0)
    proj = used / max(elapsed, 0.10)
    if proj < 85:
        return "여유"
    return "보통" if proj <= 110 else "빠름"


def format_duration(sec):
    minutes = max(int(sec // 60), 1)
    days, rem = divmod(minutes, 1440)
    hours, mins = divmod(rem, 60)
    if days:
        return f"{days}일 {hours}시간" if hours else f"{days}일"
    if hours:
        return f"{hours}시간 {mins}분" if mins else f"{hours}시간"
    return f"{mins}분"


def format_reset_at(resets_at, now, tz):
    t = datetime.fromtimestamp(resets_at, tz)
    if t.date() == datetime.fromtimestamp(now, tz).date():
        return t.strftime("%H:%M")
    return f"{WEEKDAYS[t.weekday()]} {t:%H:%M}"


def format_tokens(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    return f"{round(n / 1000)}k"


def _remain(used):
    return round(min(max(100 - used, 0), 100))


def _window_text(key, w, now, tz):
    left = w["resets_at"] - now
    at = format_reset_at(w["resets_at"], now, tz)
    when = f"{format_duration(left)} 후 {at} 리셋" if left < 86400 else f"{at} 리셋"
    p = pace(w["used_percentage"], w["resets_at"], WINDOW_SEC[key], now)
    return f"{LABEL[key]} {_remain(w['used_percentage'])}% 남음·{p} ({when})"


def _context_text(ctx):
    text = f"컨텍스트 {_remain(ctx['used_percentage'])}% 남음"
    t, size = ctx.get("used_tokens"), ctx.get("window_size")
    if _num(t) and _num(size):
        text += f" ({format_tokens(t)}/{format_tokens(size)})"
    return text


def staleness_note(windows, ctx, now):
    times = [w["observed_at"] for w in windows.values() if _num(w.get("observed_at"))]
    if ctx and _num(ctx.get("observed_at")):
        times.append(ctx["observed_at"])
    if times and now - min(times) >= STALE_SEC:
        return f"({int((now - min(times)) // 60)}분 전 수치)"
    return ""


def _warning(windows, ctx):
    hot = [LABEL[k] for k, w in windows.items() if w["used_percentage"] >= WARN_AT]
    if ctx and ctx["used_percentage"] >= WARN_AT:
        hot.append(LABEL["context"])
    if hot:
        return f"⚠ {'·'.join(hot)} {WARN_AT}% 이상 사용: 큰 작업은 보류하고 사용자에게 알릴 것"
    return ""


def format_line(snapshot, ctx, now, tz, include_context=True):
    windows = active_windows(snapshot, now)
    ctx = context_view(ctx) if include_context else None
    if not windows and not ctx:
        return None
    parts = [_window_text(k, w, now, tz) for k, w in windows.items()]
    if ctx:
        parts.append(_context_text(ctx))
    line = "[한도] " + " · ".join(parts)
    tail = " ".join(s for s in (staleness_note(windows, ctx, now), _warning(windows, ctx)) if s)
    return f"{line} {tail}" if tail else line


def format_detail(snapshot, ctx, now, tz):
    windows = active_windows(snapshot, now)
    ctx = context_view(ctx)
    if snapshot is None:
        return NO_SNAPSHOT
    if not windows and not ctx:
        return "[한도] 표시할 수치가 없음(구독 한도 정보 없음 또는 첫 응답 전)"
    lines = [f"[한도 상세] 기준 {datetime.fromtimestamp(now, tz):%Y-%m-%d %H:%M %z}"]
    for key, w in windows.items():
        used = w["used_percentage"]
        elapsed = min(max(1 - (w["resets_at"] - now) / WINDOW_SEC[key], 0.0), 1.0)
        lines.append(
            f"- {LABEL[key]}: {used:g}% 사용 · {_window_text(key, w, now, tz).split(' ', 1)[1]} · 창 경과 {elapsed * 100:.0f}%"
        )
    if ctx:
        lines.append(f"- {_context_text(ctx)} · {ctx['used_percentage']:g}% 사용")
    for s in (staleness_note(windows, ctx, now), _warning(windows, ctx)):
        if s:
            lines.append(s)
    return "\n".join(lines)


def decide(event, source, is_subagent, snapshot, session, now, tz):
    """(주입할 문자열 또는 None, 갱신할 세션 상태의 hook 소유 키)를 반환."""
    reported = dict((session.get("reported") or {}))
    notified = bool(session.get("notified_no_snapshot"))

    if event == "SubagentStart":
        # 부모 컨텍스트는 서브에이전트에게 의미가 없고, 세션 상태도 건드리지 않는다.
        return format_line(snapshot, None, now, tz, include_context=False), {}

    if event != "SessionStart" and is_subagent:
        return None, {}

    windows = active_windows(snapshot, now)
    ctx = None if (event == "SessionStart" and source == "compact") else context_view(session.get("context"))
    levels = current_levels(windows, ctx)

    new_reported = dict(reported)
    for k in KEYS:
        if levels.get(k) is not None:
            new_reported[k] = levels[k]
        elif event == "SessionStart" and k == "context":
            new_reported[k] = 0
    text = None
    if snapshot is None:
        if event == "SessionStart" or not notified:
            text, notified = NO_SNAPSHOT, True
    elif event == "SessionStart":
        text = format_line(snapshot, ctx, now, tz)
    elif any(levels.get(k) is not None and levels[k] > reported.get(k, 0) for k in KEYS):
        text = format_line(snapshot, ctx, now, tz)
    patch = {"reported": new_reported, "notified_no_snapshot": notified}
    if event == "SessionStart" and source == "compact":
        patch["context"] = None  # compact 이전 값이 다음 이벤트에서 재사용되지 않게 비운다
    return text, patch
