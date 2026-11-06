"""limits 스킬용: 현재 한도·컨텍스트 상세를 출력한다. 사용법: report.py [--session <id>]"""
import argparse
import sys
import time
from datetime import datetime

import core
import state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    snapshot, session = state.load(args.session)
    tz = datetime.now().astimezone().tzinfo
    print(core.format_detail(snapshot, session.get("context"), time.time(), tz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
