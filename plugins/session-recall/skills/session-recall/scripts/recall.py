#!/usr/bin/env python3
"""Claude Code 로컬 세션(~/.claude/projects/*/*.jsonl) 조회 도구. 표준 라이브러리만 사용.

    recall.py list   [--project 부분문자열] [--days N] [--limit N]
    recall.py search 검색어... [--project ...] [--days N] [--limit N] [--role user|assistant]
    recall.py show   세션ID(앞 8자 이상) [--grep 검색어] [--context N] [--max-chars N]
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

NOISE = re.compile(r"<(system-reminder|local-command-caveat|local-command-stdout|command-name|command-message|command-args)\b.*?(</\1>|$)", re.S)


def root():
    base = os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude"
    return Path(base) / "projects"


def text_of(msg):
    """메시지에서 사람이 읽을 텍스트만 추출(도구 호출·결과·thinking 제외)."""
    c = msg.get("content")
    if isinstance(c, list):
        c = "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    return NOISE.sub("", c or "").strip()


def parse(path):
    """세션 파일 → (메타, 메시지 목록). 메시지: (timestamp, role, text)"""
    meta = {"id": path.stem, "path": path, "cwd": "", "title": "", "start": "", "end": ""}
    msgs = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            t = d.get("type")
            if t == "ai-title":
                meta["title"] = d.get("aiTitle") or meta["title"]
            ts = d.get("timestamp", "")
            if ts:
                meta["start"] = meta["start"] or ts
                meta["end"] = ts
            if d.get("cwd"):
                meta["cwd"] = meta["cwd"] or d["cwd"]
            if t in ("user", "assistant") and not d.get("isMeta") and not d.get("isSidechain"):
                txt = text_of(d.get("message", {}))
                if txt:
                    msgs.append((ts, t, txt))
    return meta, msgs


def sessions(project=None, days=None):
    cutoff = datetime.now().timestamp() - days * 86400 if days else 0
    files = [p for p in root().glob("*/*.jsonl") if p.stat().st_mtime >= cutoff
             and (not project or project.lower() in p.parent.name.lower())]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def local(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts[:16]


def one_line(s, n):
    s = " ".join(s.split())
    return s if len(s) <= n else s[:n] + "…"


def cmd_list(a):
    for p in sessions(a.project, a.days)[: a.limit]:
        m, msgs = parse(p)
        first = next((t for _, r, t in msgs if r == "user"), "")
        print(f"{m['id'][:8]}  {local(m['start'])}  {m['cwd']}  ({len(msgs)}msg)")
        print(f"    {m['title'] or one_line(first, 60)}")
        if m["title"] and first:
            print(f"    첫 요청: {one_line(first, 100)}")


def cmd_search(a):
    terms = [t.lower() for t in a.query]
    hits = 0
    for p in sessions(a.project, a.days):
        m, msgs = parse(p)
        for i, (ts, role, txt) in enumerate(msgs):
            low = txt.lower()
            if a.role and role != a.role or not all(t in low for t in terms):
                continue
            pos = low.find(terms[0])
            snip = txt[max(0, pos - 80): pos + 160]
            print(f"{m['id'][:8]} #{i} {local(ts)} [{role}] {m['cwd']} — {m['title']}")
            print(f"    …{one_line(snip, 240)}…")
            hits += 1
            if hits >= a.limit:
                return
    if not hits:
        print("일치하는 결과 없음")


def cmd_show(a):
    found = [p for p in root().glob("*/*.jsonl") if p.stem.startswith(a.id)]
    if len(found) != 1:
        sys.exit(f"세션 '{a.id}' 일치 {len(found)}건 — ID를 더 길게 지정하세요")
    m, msgs = parse(found[0])
    print(f"# {m['title']} ({m['id']})\n# {m['cwd']}  {local(m['start'])} ~ {local(m['end'])}\n")
    keep = range(len(msgs))
    if a.grep:
        g = a.grep.lower()
        idx = {j for i, (_, _, t) in enumerate(msgs) if g in t.lower()
               for j in range(i - a.context, i + a.context + 1)}
        keep = sorted(j for j in idx if 0 <= j < len(msgs))
    for i in keep:
        ts, role, txt = msgs[i]
        if len(txt) > a.max_chars:
            txt = txt[: a.max_chars] + f"\n…(이하 {len(txt) - a.max_chars}자 생략)"
        print(f"--- #{i} {local(ts)} [{role}]\n{txt}\n")


def main():
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, limit):
        p.add_argument("--project", help="프로젝트 폴더명 부분 일치(예: claude-workspace)")
        p.add_argument("--days", type=int, help="최근 N일 이내 수정된 세션만")
        p.add_argument("--limit", type=int, default=limit)

    l = sub.add_parser("list"); common(l, 15); l.set_defaults(f=cmd_list)
    s = sub.add_parser("search"); s.add_argument("query", nargs="+", help="모든 단어를 포함한 메시지(대소문자 무시)")
    common(s, 10); s.add_argument("--role", choices=["user", "assistant"]); s.set_defaults(f=cmd_search)
    w = sub.add_parser("show"); w.add_argument("id"); w.add_argument("--grep"); w.add_argument("--context", type=int, default=2)
    w.add_argument("--max-chars", type=int, default=1500); w.set_defaults(f=cmd_show)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
