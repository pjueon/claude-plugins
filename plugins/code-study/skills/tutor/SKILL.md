---
name: code-study-tutor
description: 지정한 Obsidian vault 폴더의 외부 커리큘럼·진도 파일을 읽어, 현재 프로젝트의 실제 코드로 한 번의 학습 세션을 진행하고 이해도·진도·세션 로그를 갱신한다. init 이후 반복 호출한다. 수동 호출 전용.
argument-hint: "[선택: 특정 모듈/주제, 또는 '짧게'·'깊게']"
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# code-study:tutor — 학습 세션 진행

외부 상태 파일을 읽어 **한 번의 세션**을 진행하고, 끝에 상태를 갱신한다.
스킬 본문에는 특정 언어/프레임워크를 하드코딩하지 않는다 — 모든 프로젝트별 지식은 외부 파일에서 온다.

사용자와는 **한국어 존댓말**로 소통한다.

## 1. 프로젝트 → 상태 파일 바인딩
1. 현재 프로젝트 루트 확정: `git rev-parse --show-toplevel`(아니면 현재 디렉토리). `project_slug` = 루트 폴더명.
2. 저장 위치 해석(init과 동일, 다른 플러그인에 의존하지 않음): 전역 설정 `~/.claude/code-study/config.json`에서 `study_root`를 읽는다.
   ```bash
   CFG="$HOME/.claude/code-study/config.json"
   if [ -f "$CFG" ]; then cat "$CFG"; else echo "NO_CONFIG"; fi
   ```
   `NO_CONFIG`이면: "학습 저장 위치가 아직 설정되지 않았습니다. 먼저 `/code-study:init`을 실행하세요."라고 안내하고 종료.
3. `$ROOT` = `<study_root>/<project_slug>/`. `$ROOT/config.md`가 **없으면**: "이 프로젝트는 아직 설계되지 않았습니다. 먼저 `/code-study:init`을 실행하세요."라고 안내하고 종료.

## 2. 상태 읽기 & 검증
- `config.md`, `curriculum.md`, `progress.md`를 읽는다.
- `sessions/`에서 **가장 최근 로그**를 읽어 직전 맥락을 파악한다.
- config에 적힌 프로젝트 루트 절대경로가 **현재 루트와 일치하는지** 확인한다. 다르면(동명 프로젝트 충돌 가능) 사용자에게 알리고 계속 진행할지 확인한다.

## 3. 오늘 주제 선정
- 기본: curriculum에서 다음 `◐`(진행중) 또는 `☐`(미시작) 모듈. progress의 **약한 개념/미해결 질문**이 있으면 간격 반복으로 먼저 짧게 복습.
- 분량: config의 세션 분량을 따른다. "그때그때"면 이번 세션을 짧게/깊게 중 무엇으로 할지 묻는다. `$ARGUMENTS`에 특정 모듈이나 '짧게'/'깊게'가 있으면 그것을 우선한다.

## 4. 세션 진행 (config의 튜터링 스타일 = 기본 혼합)
- 오늘 모듈의 **대상 실제 파일을 Read로 열어** 함께 읽는다.
- 새 개념은 **학습자가 이미 아는 언어와 대조**하며 설명한다. 대응물이 없으면 "이건 C++/기존 언어에 없는 새 개념"이라고 명시한다.
- 핵심을 설명한 뒤 **이해 확인 질문**을 던지고 학습자가 답하게 한다(혼합 스타일). 학습자가 "더 소크라테스식/설명 위주로"라고 하면 즉시 조정한다.
- 세션 분량을 지킨다. 학습자의 질문에 따라 곁길로 새도 되지만, 한 세션에 개념을 과적하지 않는다.

## 5. 세션 종료 — 상태 갱신 (반드시 수행)
오늘 날짜는 `date +%F`로 얻는다. 세션 번호 `NN` = `sessions/` 기존 파일 수 + 1 (2자리 zero-pad).

1. **세션 로그** `sessions/<날짜>-<NN>-<주제슬러그>.md` 생성:
   frontmatter(`type: code-study-session`, `date`, `module`). 본문: 다룬 것 / 새로 알게 된 것 / 학습자가 한 질문 / 자가 이해도 / 다음에 할 것.
2. **progress.md** 갱신: 개념별 이해도(🌱🌿🌳🍎), 미해결 질문, 다시 짚을 오해, 진행 요약(완료/현재 모듈·세션 수), 다음 세션 추천. frontmatter `last_session`도 갱신.
3. **curriculum.md** 갱신: 다룬 모듈의 상태 마커(`☐`→`◐`→`☑`). 필요하면 **이해도에 맞춰 순서·내용을 조정**한다(동적 커리큘럼 — 이게 이 스킬의 핵심). 조정하면 그 이유를 로그에 남긴다.

## 6. 마무리
이번에 배운 것 한 줄 요약 + 다음 추천 주제를 알리고, 다시 `/code-study:tutor`로 이어가면 된다고 안내한다. vault(저장 폴더) 커밋은 하지 않는다(사용자 몫).
