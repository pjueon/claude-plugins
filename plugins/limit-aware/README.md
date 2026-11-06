# limit-aware

Claude Code가 자신의 5시간 한도, 주간 한도, 현재 세션의 컨텍스트 잔량을 스스로 인지하게 한다.

## 동작

- 수치는 statusLine 입력에만 들어 있어서, statusLine 래퍼(`scripts/statusline.py`)가 수치를 `~/.claude/limit-aware/`에 기록한다. 기존 statusLine이 있으면 보존해 출력을 그대로 중계한다.
- 훅이 그 수치를 한 줄로 요약해 모델에게 주입한다.
  - 항상: 세션 시작, 서브에이전트 시작
  - 구간을 처음 돌파할 때만: 프롬프트 제출, 도구 사용 후 (한도 50/75/90/95/98%, 컨텍스트 50/70/85/95%). 95% 이상이면 경고 문구가 붙는다.
- `limits` 스킬로 모델이 현재 상황을 직접 조회할 수 있다.

```
[한도] 5h 22% 남음·보통 (48분 후 14:30 리셋) · 주간 59% 남음·여유 (월 09:00 리셋) · 컨텍스트 38% 남음 (124k/200k)
```

페이스(여유/보통/빠름)는 창 경과 비율 대비 사용률로 창 끝 사용률을 투영해 판정한다.

## 설치 후 최초 1회

플러그인은 statusLine을 등록할 수 없으므로 `/limit-aware:setup`으로 래퍼를 설치한다. 백업과 원복(`uninstall`)을 지원한다. 플러그인을 업데이트한 뒤에는 다시 실행해 복사본을 갱신한다.

## 한계

- Python 3가 `python` 명령으로 실행돼야 한다(macOS·Linux에서 `python3`만 있다면 alias가 필요).
- `rate_limits`는 Pro/Max 구독자에게만, 세션의 첫 응답 이후부터 제공된다. 그 외에는 컨텍스트만 표시된다.
- statusLine은 대화형 TUI에서만 실행되므로 헤드리스(`-p`)에서는 수치가 갱신되지 않는다.
- 상태 파일: 세션별 파일은 SessionEnd에 삭제되고, SessionStart에서 3일 넘은 파일을 정리한다.

## 테스트

```bash
python -m unittest discover -s plugins/limit-aware/tests
```
