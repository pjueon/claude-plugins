---
name: session-recall
description: >-
  사용자의 과거 Claude Code 세션 대화를 로컬 로그에서 찾아 회상한다. "예전에
  X 얘기한 적 있지?", "지난주에 뭐 했지?", "그 인증 버그 고치던 세션 찾아줘"처럼
  이전 대화를 다시 확인하고 싶을 때 사용한다. 대화 기록을 검색하는 스킬이며
  현재 코드베이스 검색(Grep/Glob)과는 다르다.
---

# session-recall

`~/.claude/projects/<프로젝트>/<세션ID>.jsonl`에 저장된 Claude Code 로컬 세션을
`scripts/recall.py`(Python 3, 표준 라이브러리만 사용)로 읽는다. 인덱스나 외부 도구가
없어 항상 최신 상태이고 별도 설치가 필요 없다. 다른 에이전트의 세션은 대상이 아니다.

스크립트 경로는 이 스킬 폴더 기준 `scripts/recall.py`이다. 아래에서 `recall`은
`python <스킬 폴더>/scripts/recall.py`를 뜻한다. 출력이 한글이므로 Windows에서도 UTF-8로 출력된다.

## 사용법

```bash
recall list   --days 7 --limit 15            # 최근 세션: ID, 시각, 작업 폴더, 제목
recall search jwt refresh --days 30          # 모든 단어를 포함한 메시지 검색(user/assistant 텍스트)
recall show 707dc646                         # 세션 전체 대화(ID는 앞 8자면 충분)
recall show 707dc646 --grep jwt --context 3  # 검색어 주변 메시지만
```

공통 필터: `--project <폴더명 일부>`(예: `claude-workspace`), `--days N`, `--limit N`.
`search`는 `--role user|assistant`로 화자를 제한할 수 있다.

## 진행 방식

1. 기간·주제가 모호하면 `list`로 먼저 범위를 잡고, 주제가 있으면 `search`로 후보 세션을 찾는다.
2. 후보가 나오면 `show <ID> --grep <검색어>`로 해당 부분만 확인한다. 전체 출력은 길 수 있으니 꼭 필요할 때만 쓴다.
3. 사용자에게는 원문을 쏟아붓지 말고 요약해 답한다. 근거로 세션 ID(앞 8자)와 시각을 함께 알려 준다.

## 주의

- 사용자 발화와 어시스턴트 텍스트만 검색된다. 도구 호출·결과·thinking, 서브에이전트 대화는 제외된다.
- 검색은 대소문자 무시 단순 부분 일치라서 의미 검색은 안 된다. 결과가 없으면 동의어·영문/한글 표기를 바꿔 다시 시도한다.
- `/clear` 이후에도 이전 세션 파일은 남아 있으므로 그 세션들도 검색된다. 현재 세션도 결과에 포함될 수 있다.
