# 대상 종류별 근거 수집과 상세 절 구성

설명문의 모든 사실은 **이번 세션에서 직접 읽거나 실행한 것**에서 나온다. 수집한 수치와 출처
명령은 scratchpad 의 근거 메모에 짝지어 적는다(점검 때 대조한다).

## 1. 대상 판정과 수집

| 종류 | 판정 단서 | 근거 수집 | 상세 절 이름과 구성 |
|---|---|---|---|
| 커밋 | 7~40자리 hex, `HEAD~n` | `git show --stat <sha>`, `git show <sha>`, 변경 전 상태 `git show <sha>^:<path>`, 호출처는 Grep | **코드 훑기** — 변경을 이해하기 좋은 순서로 묶는다(파일 순서가 아님). 묶음마다 발췌 `pre.diff` 와 `ol.notes` |
| 브랜치·범위 | 브랜치명, `a..b` | `git merge-base`, `git log --oneline base..head`, `git diff base...head --stat` 후 본문 | 같음 |
| PR | `#123`, 숫자, PR URL | `gh pr view <n\|url> --json title,body,url,baseRefName,headRefName,commits,files`, `gh pr diff`, 필요하면 `--comments` | 같음. 머리 메타에 PR URL |
| 작업 중 diff | "지금 변경", "staged" | `git diff`, `git diff --staged` | 같음 |
| 이슈·버그 | 이슈 번호·URL, 증상 서술 | `gh issue view --comments`, 연결 PR·커밋(`git log --grep '#N'`), 안전하면 재현을 직접 실행, 원인 코드 탐색 | **원인 추적과 수정** — 증상 → 재현(실행 결과) → 원인 → 수정 → 교훈 |
| 개념·알고리즘·현상 | 저장소 대상이 아님 | scratchpad 에 toy 스크립트(Python/Node)를 써서 실행하고 출력을 그대로 인용한다. 위젯 데이터도 이 출력에서 가져온다 | **동작 따라가기** — 단계별 상태 변화(같은 도식 계열 재사용), 한계와 반례 |
| 그 밖(설계 문서·로그) | 파일 경로 | Read 로 읽고 원문 줄을 인용(줄 번호 포함) | 문서의 논증 구조나 사건 타임라인 |

변경 계열은 파일이 많아도 **묶음 3~5개**로 줄인다. 묶음당 발췌는 30줄 안팎으로 하고, 생성 파일·
lock 파일은 "다루지 않음"으로 밝힌다. 탐색 범위가 넓으면 Explore 에 맡긴다.

## 2. 실패했을 때

| 상황 | 처리 |
|---|---|
| PR 인데 `gh auth status` 실패 | GitHub 원격이면 `git fetch origin pull/N/head` (로컬 브랜치를 만들지 않고 FETCH_HEAD 만)로 diff 를 얻는다. 본문·토론은 "확인하지 못함"이라고 머리 메타에 밝힌다. 그것도 실패하면 멈추고 `! gh auth login` 을 안내한다 |
| PR·이슈 URL | `gh pr view <url>` 은 저장소 밖에서도 된다. URL 을 우선 쓴다 |
| 저장소 밖인데 SHA·브랜치 대상 | `git rev-parse --show-toplevel` 이 실패하면 저장소 경로를 한 번만 묻는다 |
| 대상이 모호함("그 버그") | 한 번만 묻는다 |
| 재현이 위험하거나 불가능 | 실행하지 않고 이슈 본문의 보고를 인용하며 "직접 재현하지 않음"이라고 쓴다 |
| 실행 환경 없음(Python·Node 모두 없음) | 묻는다. 수치를 손으로 계산해 쓰지 않는다 |
