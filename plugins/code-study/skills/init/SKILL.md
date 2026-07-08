---
name: code-study-init
description: 현재(또는 인자로 지정한) 프로젝트를 분석해, 그 프로젝트의 언어·프레임워크를 배우기 위한 커리큘럼·설정을 사용자가 지정한 Obsidian vault 폴더의 외부 파일로 생성한다. 프로젝트당 한 번 실행하는 설계 단계. 수동 호출 전용.
argument-hint: "[대상 프로젝트 경로 (생략 시 현재 프로젝트)]"
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, Agent
---

# code-study:init — 프로젝트별 학습 설계

대상 프로젝트를 분석해 **외부 상태 파일**(config·curriculum·progress)을 사용자가 지정한 Obsidian vault 폴더에 만든다.
스킬 본문에는 특정 언어/프레임워크를 하드코딩하지 않는다 — 대상 프로젝트가 무엇이든(TS·Rust·Go·C#…) 감지해서 맞춘다.
이 플러그인은 다른 플러그인에 의존하지 않는다(brain-vault 불필요).

사용자와는 **한국어 존댓말**로 소통한다.

## 1. 대상 프로젝트 확정
1. `$ARGUMENTS`에 경로가 있으면 그 경로, 없으면 현재 작업 디렉토리를 대상으로 한다.
2. 프로젝트 루트를 확정한다: `git -C <경로> rev-parse --show-toplevel`. git 저장소가 아니면 해당 경로를 루트로 쓴다.
3. `project_slug` = 루트 폴더명의 kebab-case.

## 2. 학습 기록 저장 위치 결정
**자체 전역 설정 파일** `~/.claude/code-study/config.json`에 저장 위치를 한 번만 기록해 재사용한다(brain-vault 등 다른 플러그인·환경변수에 의존하지 않는다).

```bash
CFG="$HOME/.claude/code-study/config.json"
if [ -f "$CFG" ]; then cat "$CFG"; else echo "NO_CONFIG"; fi
```
- 파일이 있으면 그 안의 `study_root`(모든 프로젝트의 학습 폴더가 놓이는 부모 폴더)를 쓴다.
- `NO_CONFIG`이면: 사용자에게 **학습 기록을 저장할 폴더의 절대경로**를 묻는다(예: Obsidian vault 안의 원하는 위치. 전용 하위 폴더 하나를 권장). 폴더 존재를 확인한 뒤 저장한다(다음부터 재사용, 프로젝트마다 다시 묻지 않음):
  ```bash
  mkdir -p "$HOME/.claude/code-study"
  printf '{\n  "study_root": "%s"\n}\n' "<사용자가_준_절대경로>" > "$HOME/.claude/code-study/config.json"
  ```

**상태 저장 루트** `$ROOT` = `<study_root>/<project_slug>/`.

## 3. 이미 초기화됐는지 확인
`$ROOT/config.md`가 이미 있으면: "이미 초기화돼 있습니다"라고 알리고, 다시 설계할지(덮어쓰기)·아니면 `/code-study:tutor`로 바로 갈지 묻는다. 임의로 덮어쓰지 않는다.

## 4. 스택 감지
루트의 매니페스트/설정으로 언어·프레임워크·테스트러너·빌드도구를 판별한다. 흔한 신호:
`package.json`·`tsconfig.json`(JS/TS), `Cargo.toml`(Rust), `pyproject.toml`/`requirements.txt`(Python), `go.mod`(Go), `pom.xml`/`build.gradle`(JVM), `*.csproj`(C#), `CMakeLists.txt`(C/C++), `Gemfile`(Ruby), `composer.json`(PHP) 등.
주 매니페스트와 디렉토리 구조를 읽어 **주 언어·프레임워크·학습 대상 하위 범위**를 정한다. 규모가 크면 `Agent`(Explore)로 구조 스캔을 위임해 컨텍스트를 아낀다.

## 5. 학습자 프로필 인터뷰 (짧게)
이미 대화에서 드러난 정보는 다시 묻지 않는다. 부족한 것만 `AskUserQuestion`으로 확인한다:
- **이미 아는 언어**(대조 기준). 없으면 묻는다.
- **이 프로젝트에서 배우고 싶은 범위/목표**(전체 저장소 / 특정 하위 폴더).
- **튜터링 스타일**(기본: 혼합=설명 후 이해확인 질문), **세션 분량**(기본: 짧게 자주), **대화 언어**(기본: 한국어).

## 6. 커리큘럼 설계 (친숙 → 낯섦)
학습자가 **이미 아는 언어 기준**으로 배열한다:
- 아는 언어에 대응물이 있는 것(문법·타입·순수 로직)을 앞에, **대응물이 없는 개념 산**(예: 반응성, 소유권, GC, 이벤트 루프 등)을 명시적으로 표시하고 뒤에 배치.
- 각 모듈에 **목표·핵심 개념(아는 언어와의 대조 포함)·대상 실제 파일**을 매핑한다.
- ⚠️ 매핑한 파일은 **실제 존재를 반드시 확인**(Glob/Bash)하고, 초반 모듈은 **작은 앵커 파일**을 고른다. 존재하지 않는 파일을 커리큘럼에 넣지 않는다.

## 7. 외부 상태 파일 생성
`$ROOT/`에 아래 3개를 만든다. Obsidian 친화(frontmatter + 마크다운), 한국어.

**config.md** — 거의 불변인 설정:
frontmatter `type: code-study-config`, `project_slug`, `created:<오늘>`(오늘 날짜는 `date +%F`). 본문: 프로젝트 루트 **절대경로**, 주 언어·프레임워크, 학습 대상 범위, 학습자 프로필(아는 언어/처음 배우는 것/대조 전략), 튜터링 스타일·세션 분량·대화 언어, 상태 파일 저장 루트 `$ROOT`(절대경로).

**curriculum.md** — 진도표:
frontmatter `type: code-study-curriculum`. 모듈 목록(M0..Mn), 각 모듈에 상태 마커 `☐`(미시작)/`◐`(진행)/`☑`(완료) + 목표 + 핵심 개념 + 대상 파일. 맨 위에 "tutor가 이해도에 따라 순서·내용을 갱신할 수 있다"는 안내.

**progress.md** — 이해도/진행:
frontmatter `type: code-study-progress`, `last_session: null`. 본문: 진행 요약, 개념별 이해도 표(척도 🌱🌿🌳🍎), 미해결 질문, 다시 짚을 오해, 다음 세션 추천(첫 모듈).

## 8. 보고
감지한 스택 요약 + 모듈 목록 + 저장 위치를 사용자에게 보고하고, **`/code-study:tutor`로 첫 세션을 시작**하라고 안내한다. 커밋은 하지 않는다(vault 커밋은 사용자 몫).
