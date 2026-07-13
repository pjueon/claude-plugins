# notice-me — Claude Code 알림 플러그인 설계

## 1. 목표

Claude Code가 사용자 입력을 기다리거나 작업을 마쳤을 때, **지금 그 창을 보고 있지 않다면** 로컬에서 눈에 띄게 알려준다.

- 화면을 보고 있음(포커스 상태) → 아무것도 하지 않음
- 다른 창에 포커스가 가 있음 → 작업표시줄 깜빡임 + 사용자가 등록한 커스텀 명령어 실행

VS Code 통합 터미널, 독립 터미널(Windows Terminal, cmd 등) 등 Claude Code를 어디서 띄웠든 동일한 로직으로 동작해야 한다. 특정 앱(예: VS Code)을 전제하지 않는다.

## 2. 대상 환경

- **Windows 전용.** Windows가 아닌 OS에서는 훅 스크립트가 아무것도 하지 않고 즉시 종료한다(`platform.system() != "Windows"` 시 no-op).
- 외부 서비스로 알림을 보내지 않는다 — 전부 로컬에서 끝난다. 네트워크 호출 없음.
- 구현은 Python 표준 라이브러리(`ctypes`)만으로 한다. 서드파티 패키지, PowerShell 실행 모두 불필요.

## 3. 설정 (JSON)

사용자 설정 파일 `~/.claude/notice-me.json`으로 동작을 조정한다. 사용자가 직접 열어 편집하는 파일이라 **고정되고 찾기 쉬운 경로**에 둔다. 플러그인 디렉터리(`${CLAUDE_PLUGIN_ROOT}`) 안에 두지 않는 이유는 업데이트마다 그 경로 자체가 바뀌기 때문이다 — 7절 참고. (디바운스용 상태 파일처럼 사람이 직접 편집할 일이 없는 데이터는 `${CLAUDE_PLUGIN_DATA}`에 둔다. 두 파일의 성격이 달라 위치도 다르다 — 5.4 참고.)

```json
{
  "flashEnabled": true,
  "ignoreTypes": ["idle_prompt", "agent_completed"],
  "debounceMs": 2000,
  "customCommands": [
    "python ./my_script.py"
  ]
}
```

- **`flashEnabled`**: 작업표시줄 깜빡임 on/off. **기본값 `true`.** `false`면 깜빡임만 끄고 `customCommands`는 그대로 실행한다(둘은 독립된 채널).
- **`ignoreTypes`**: 무시할 알림 타입 목록. **기본값은 `["idle_prompt", "agent_completed"]`** — 유휴 알림은 기본적으로 무시하고, `agent_completed`는 같은 의미의 `Stop`과 중복 발화하므로 기본으로 같이 무시한다(4절 참고). 값은 아래 4절의 타입 이름 중에서 고른다.
- **`debounceMs`**: 같은 세션에서 알림을 다시 발화하기까지의 최소 간격(밀리초). **기본값 `2000`.** 5.4 참고.
- **`customCommands`**: 무시되지 않은 모든 알림에 대해 동일하게 실행할 명령어 목록. 순서대로 실행하며, 각 명령어는 대기하지 않고(fire-and-forget) 실행한다. 작업 디렉터리는 훅이 전달받은 `cwd`. 안전성은 5.5 참고.
- 설정 파일이 없으면 기본값(`flashEnabled: true`, `ignoreTypes: ["idle_prompt", "agent_completed"]`, `debounceMs: 2000`, `customCommands: []`)으로 동작한다.

## 4. 알림 타입

Claude Code의 `Notification` 이벤트는 `matcher`로 아래 8가지 타입을 구분한다(공식 문서 기준):

`permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog`, `elicitation_complete`, `elicitation_response`, `agent_needs_input`, `agent_completed`

여기에 `Stop`, `SubagentStop` 이벤트를 각각 합성 타입 `stop`, `subagent_stop`으로 매핑해 `ignoreTypes` 설정 하나로 전부 다룰 수 있게 한다.

**`agent_completed`는 "작업 완료"를 알리는 `Stop`과 의미가 겹친다.** 같이 켜 두면 완료 시점에 알림이 두 번(깜빡임 두 번, `customCommands`도 두 번) 발화하므로, 훅 등록 단계에서 아예 빼는 대신 **3절의 `ignoreTypes` 기본값에 넣어 두는 것으로 처리한다** — 원한다면 사용자가 `ignoreTypes`에서 빼서 켤 수도 있다. "이 타입은 무시한다"는 판단을 전부 같은 자리(`ignoreTypes`)에서 하기 위한 선택이다(5.1 참고).

> **중요(구현 시 최우선 검증)**: 이 설계는 `Notification` 이벤트의 stdin JSON 안에 세부 타입을 나타내는 필드가 실제로 존재한다고 가정한다. 공식 문서는 훅 등록 시 쓰는 `matcher` 값(위 8가지)만 나열할 뿐, 그 값이 stdin JSON의 어느 필드에 그대로 들어오는지는 명시하지 않는다. 5.1에서 이 필드를 직접 읽어 `ignoreTypes`와 비교하는 방식을 쓰므로, **구현 착수 시 실제 payload를 한 번 덤프해서 필드가 존재하는지, 어떤 키인지 먼저 확인한다.** 필드가 없다면 이전 방식(타입마다 `matcher`를 나눠 등록하고 커맨드 인자로 타입을 넘기는 방식)으로 되돌려야 한다.

## 5. 구현 방식

### 5.1 훅 등록 — 이벤트당 엔트리 하나

`hooks/hooks.json`에 `matcher` 없이 이벤트당 엔트리 하나씩(`Notification`, `Stop`, `SubagentStop` 총 3개)만 등록한다. 세 이벤트 모두 같은 커맨드를 가리키고, 인자도 넘기지 않는다.

```json
{
  "hooks": {
    "Notification": [
      { "hooks": [{ "type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}\"/scripts/notify.py" }] }
    ],
    "Stop": [
      { "hooks": [{ "type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}\"/scripts/notify.py" }] }
    ],
    "SubagentStop": [
      { "hooks": [{ "type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}\"/scripts/notify.py" }] }
    ]
  }
}
```

`matcher`를 생략하면 그 이벤트의 모든 발생(= `Notification`의 8가지 타입 전부)에 대해 훅이 호출된다. 어느 이벤트·어느 타입인지는 훅 등록 단계가 아니라 **스크립트 안에서 stdin JSON을 읽어** 판단한다:

- 어느 이벤트인지는 공통 필드 `hook_event_name`(`"Notification"` / `"Stop"` / `"SubagentStop"`)으로 안다 — 이 필드는 공식 문서에 명시되어 있다.
- `Notification`의 세부 타입(`idle_prompt` 등)은 stdin JSON의 타입 필드를 읽어서 안다 — 4절의 검증 항목 참고.

이전에는 타입별로 매처를 나누고 커맨드에 타입을 인자로 박아 넣는 방식을 썼지만, `hook_event_name`이 문서화된 필드라는 걸 감안하면 그럴 필요가 없다. `hooks.json`이 8~9개 엔트리에서 3개로 줄고, "이 타입을 무시한다"는 판단도 등록 시점(matcher 유무)과 실행 시점(`ignoreTypes`)으로 나뉘어 있던 게 `ignoreTypes` 하나로 합쳐진다.

### 5.2 포커스 판별 — 조상 PID 체인

특정 앱을 전제하지 않기 위해, "지금 활성 창을 가진 프로세스가 나(=Claude Code를 실행 중인 프로세스)의 조상 중 하나인가"만 확인한다. 조상 체인만 구하고, 실제 포커스 판정은 5.3에서 창을 찾은 뒤 한 번에 처리한다(정의를 두 곳에 나눠 두지 않는다).

```python
def build_ancestor_chain(pid):
    # 자기 자신 → 부모 → 조부모 → ... → 더 이상 부모를 찾을 수 없는 최상위 조상
    ...
```

- `build_ancestor_chain`은 `kernel32`의 `CreateToolhelp32Snapshot` + `Process32First/Next`로 전체 프로세스의 PID→PPID 맵을 만든 뒤, 자기 PID에서부터 부모를 계속 따라 올라가 **더 이상 부모를 찾을 수 없는 최상위 조상까지** 리스트로 쌓는다(중간에 끊겨도 그 시점까지 쌓은 체인으로 판단).
- 터미널 안에서 실행하든, VS Code 통합 터미널 안에서 실행하든 조상 체인만 다를 뿐 로직은 동일하다. VS Code 전용 처리, 창 제목 매칭, 여러 창 구분 로직이 전부 불필요해진다.
- 알려진 한계: 조상 프로세스(특히 `conhost.exe`, `cmd.exe` 같은 중간 프로세스)가 자식보다 먼저 종료되어 체인이 끊기는 경우가 있다. 이 경우 그 지점까지의 체인으로만 판단한다.

### 5.3 로컬 알림 — 작업표시줄 깜빡임

깜빡일 대상 창은 조상 체인을 가까운 순서(자기 자신 → 부모 → …)로 훑으며, **눈에 보이는 최상위 창을 가진 첫 조상**을 찾아 그 창을 깜빡인다.

```python
def find_target_hwnd(ancestors):
    windows = enum_visible_top_level_windows()  # EnumWindows + GetWindowThreadProcessId
    for pid in ancestors:  # 가까운 조상부터
        for hwnd, owner_pid in windows:
            if owner_pid == pid:
                return hwnd
    return None

def flash(hwnd):
    ctypes.windll.user32.FlashWindowEx(...)  # FLASHW_TRAY | FLASHW_TIMERNOSTOP
```

포커스 판별과 깜빡임 대상 찾기는 같은 값으로 통일한다: `target_hwnd = find_target_hwnd(ancestors)`를 먼저 구하고, `is_focused = (GetForegroundWindow() == target_hwnd)`로 판단한다. 5.2의 "조상 체인에 `fg_pid`가 있는가"와 별개로 판단하지 않는다 — 조상 여러 개가 각자 창을 가진 경우 두 정의가 어긋날 수 있기 때문이다.

`flashEnabled`가 `false`면 `flash(hwnd)` 호출 자체를 건너뛴다. `is_focused` 판정과 `customCommands` 실행 여부에는 영향을 주지 않는다.

### 5.4 디바운스 — 세션별 상태 파일

같은 세션에서 알림이 짧은 간격으로 여러 번 겹쳐 발화하는 것(예: `Notification`과 `Stop`이 거의 동시에 오는 경우)을 막기 위해, 세션마다 "마지막으로 실제 알림을 발화한 시각"을 파일로 기록한다.

- **위치**: `${CLAUDE_PLUGIN_DATA}/status/<session_id>.json`. 세션마다 파일을 분리하는 이유는 **여러 Claude Code 세션을 동시에 켜 두었을 때 세션 간에 디바운스 상태가 서로 간섭하지 않게** 하기 위함이다. `session_id`는 훅 stdin JSON의 공통 필드(`session_id`)에서 가져온다.
- **판단 로직**:
  1. 타입이 `ignoreTypes`에 없는지 먼저 확인한다(4절).
  2. 상태 파일이 있으면 `lastNotifiedAtMs`를 읽는다. `now_ms - lastNotifiedAtMs < debounceMs`면 이번 알림은 건너뛴다(깜빡임도, `customCommands`도 실행하지 않음).
  3. 건너뛰지 않기로 했으면 포커스 판별(5.2~5.3)을 진행하고, 실제로 깜빡임/`customCommands`를 실행했을 때만 상태 파일에 `now_ms`를 기록한다. 포커스가 있어서 아무것도 안 한 경우엔 상태 파일을 갱신하지 않는다.
- **정리(24시간 이상 된 파일 삭제)**: 상태 파일이 무한히 쌓이지 않도록, 매 실행마다 `${CLAUDE_PLUGIN_DATA}/status/` 안에서 **수정 시각이 24시간보다 오래된 파일을 지운다.** 파일은 "실제로 알림을 발화했을 때"만 갱신되므로, 세션이 살아있어도 24시간 넘게 포커스 상태라 한 번도 발화하지 않았다면 그 세션의 상태 파일이 지워질 수 있다. 문제는 없다 — 지워지면 다음 알림 때 "이전 기록 없음"으로 취급돼 디바운스가 그냥 초기화될 뿐이다.

### 5.5 커스텀 명령어 실행

디바운스를 통과하고 포커스가 없고 타입이 `ignoreTypes`에 없으면, `customCommands` 목록의 각 명령어를 실행한다(완료를 기다리지 않음, fire-and-forget).

**실행 방식**: `subprocess.Popen(command_string, shell=True, cwd=hook_cwd)`처럼 설정 파일에 적힌 명령어 문자열을 그대로 셸(Windows에서는 `cmd.exe`)에 넘긴다. `python ./my_script.py`처럼 사용자가 익숙한 형태로 그대로 적을 수 있게 하기 위해서다. `os.system`이 아니라 `subprocess.Popen`을 쓰는 이유는 셸을 매번 새로 띄우면서도 대기하지 않고 다음 로직으로 넘어갈 수 있어야 하기 때문이다(`os.system`은 완료까지 블로킹한다).

**안전한가**: `shell=True`로 임의 문자열을 실행하는 것 자체는, 그 문자열이 **사용자 자신이 로컬 설정 파일에 적어 둔 값일 때는** 위험하지 않다 — 이미 그 사용자 권한으로 뭐든 실행할 수 있는 로컬 환경이기 때문에 권한 상승이 없다. 다만 지켜야 할 경계가 두 가지 있다:

1. **훅 payload의 값을 명령어 문자열에 절대 끼워 넣지 않는다.** `customCommands`의 문자열은 설정 파일에 있는 그대로만 실행하고, `message`나 `cwd` 같은 훅 JSON 필드 값을 문자열 포매팅으로 명령어에 섞지 않는다(`cwd`는 `Popen`의 `cwd=` 인자로만 넘긴다). 여기서 문자열 조합을 하는 순간 셸 인젝션 통로가 열린다 — 이 필드들의 값은 궁극적으로 Claude Code 세션이 다루는 외부 컨텍스트(대화 내용 등)에서 흘러올 수 있어 신뢰할 수 없다.
2. **설정 파일 자체가 신뢰 경계다.** `~/.claude/notice-me.json`을 다른 주체(다른 사용자, 동기화되는 공유 저장소, 악성 플러그인 업데이트 스크립트 등)가 쓸 수 있다면 임의 코드 실행으로 이어진다. 플러그인은 이 파일을 자동으로 채우거나 원격 값으로 덮어쓰지 않는다 — 오직 사용자가 직접 수정할 때만 내용이 바뀐다.

**더 안전한 대안(고려했으나 채택 보류)**: `"python ./my_script.py"` 같은 문자열 대신 `["python", "./my_script.py"]`처럼 인자를 배열로 받아 `shell=False`로 실행하면, 셸 메타문자(`&`, `|`, `;` 등) 해석 자체가 없어져 인젝션 표면이 원천적으로 사라진다(Claude Code 자체 훅 문서도 `${CLAUDE_PLUGIN_ROOT}` 경로를 다룰 때 이 exec-form을 권장한다). 다만 사용자가 준 예시(`"python ./my_script.py"`)가 문자열 형태였고, 두 형태를 동시에 지원하면 파서가 복잡해진다. **1번 규칙(payload 값 미삽입)만 지키면 문자열 형태도 안전하므로, 지금은 문자열 형태 하나만 지원하는 쪽으로 잠정 결정한다.** 배열 형태 지원 여부는 구현 시 재검토한다.

## 6. 전체 흐름

```
Claude Code 훅 발화 (Notification / Stop / SubagentStop)
        ↓
   notify.py (stdin으로 훅 JSON 수신 → hook_event_name, 타입, session_id 파싱)
        ↓
   Windows 아니면 즉시 종료
        ↓
   type이 ignoreTypes에 있으면 즉시 종료
        ↓
   status/<session_id>.json 확인 → debounceMs 이내면 즉시 종료
        ↓
   조상 PID 체인 계산 → 포커스 창 소유 PID와 비교
        ↓
   ┌────────────────┬─────────────────────────────────────┐
   │ 포커스 있음      │ 포커스 없음                           │
   ↓                ↓                                     ↓
  아무것도 안 함   (flashEnabled면) 깜빡임 + customCommands 실행
                   → status/<session_id>.json에 현재 시각 기록
```

## 7. 플러그인 파일 구조 (구현 예정)

```
plugins/notice-me/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   └── hooks.json
└── scripts/
    └── notify.py
```

- **훅 자동 등록**: `hooks/hooks.json`은 플러그인이 설치되는 순간 Claude Code가 자동으로 읽어 적용한다. 사용자가 `settings.json`을 직접 편집할 필요가 없다 — `/plugin install notice-me@jueon` 한 번이면 끝난다. (단, `hooks.json`을 세션 중간에 수정한 경우엔 `/reload-plugins` 또는 재시작이 필요하다 — 이건 개발 중에만 해당.)
- **설정 파일**: `~/.claude/notice-me.json` — 사용자가 직접 찾아 편집하는 파일이라 플러그인 버전과 무관한 고정 경로에 둔다.
- **상태 파일**: `${CLAUDE_PLUGIN_DATA}/status/*.json` — 사람이 편집할 일이 없는, 플러그인이 스스로 쓰고 지우는 데이터라 `CLAUDE_PLUGIN_DATA`(Claude Code가 플러그인별로 제공하는 영구 데이터 디렉터리, 훅 프로세스에 환경변수로도 전달됨)에 둔다. **플러그인이 업데이트돼도 유지되고**, 플러그인을 완전히 제거하면 같이 삭제된다.
- 두 경우 모두 `${CLAUDE_PLUGIN_ROOT}`(스크립트가 설치된 경로, 업데이트마다 바뀜)에는 두지 않는다.

## 8. 다듬을 지점

- **[구현 착수 전 최우선 검증] VS Code 통합 터미널에서 체인이 실제로 창 소유 프로세스까지 닿는가**: 이 설계 전체가 "조상 PID를 타고 올라가면 결국 창을 가진 프로세스에 닿는다"는 가정에 기대고 있다. VS Code는 다중 프로세스 구조라 통합 터미널의 셸은 `ptyHost`/`conhost` 계열 밑에 떠 있고, 실제 HWND는 메인 `Code.exe`가 가진다. `ptyHost`가 메인 프로세스의 자식으로 fork되는 구조라면 체인이 닿겠지만, ConPTY/conhost가 중간에 재부모화(reparent)하면 체인이 끊겨 **정작 주력 사용 환경(VS Code 통합 터미널)에서 포커스 판별이 항상 "포커스 없음"으로 나오는** 실패가 날 수 있다. 이건 다듬을 지점이 아니라 설계가 성립하는지 여부이므로, 다른 부분을 구현하기 전에 먼저 VS Code 통합 터미널 안에서 `GetForegroundWindow()`의 소유 PID와 `build_ancestor_chain(os.getpid())` 결과를 직접 덤프해 두 값이 만나는지 확인한다.
- **중복 억제**: `agent_completed` vs `Stop` 중복은 3절의 `ignoreTypes` 기본값에 `agent_completed`를 넣는 것으로 1차 해소했고, 5.4의 세션별 디바운스가 2차 안전망 역할을 한다(짧은 간격으로 겹치는 다른 조합의 알림도 함께 걸러짐).
- **상태 파일 동시 쓰기**: 같은 세션에서 두 훅이 거의 동시에 발화하면 `status/<session_id>.json`을 읽고-쓰는 사이에 경쟁이 생길 수 있다. 로컬 알림용 저부하 도구이므로 파일 잠금까지는 우선순위가 낮지만, 실제로 중복 발화가 관찰되면 검토한다.
- **정리 비용**: 매 실행마다 `status/` 디렉터리 전체를 스캔해 24시간 지난 파일을 지우는 방식은 세션이 아주 많이 쌓였을 때만 문제가 될 정도로 가볍다. 문제가 되면 정리를 매 실행이 아니라 확률적으로(예: 5% 확률) 수행하는 것도 방법이다.
- **조상 체인 단절**: 5.2에서 언급한 대로 중간 프로세스가 먼저 종료되면 체인이 끊긴다. 위 첫 번째 항목의 검증과 같이 확인한다.
- **[구현 착수 전 최우선 검증, 4절과 동일] `notification_type` 필드 미문서화**: stdin JSON에 세부 타입을 담은 필드가 실제로 있는지 공식 문서에 없다. 5.1이 이 필드를 직접 읽는 방식으로 바뀌면서 **이 불확실성이 더 이상 사소한 참고사항이 아니라 설계 전체의 전제가 됐다** — 필드가 없으면 `Notification`의 세부 타입을 전혀 구분할 수 없다. 다른 것보다 먼저 실제 payload를 덤프해 확인하고, 없으면 이전 방식(타입별 `matcher` 분리)으로 되돌린다.
- **`python` PATH 의존성**: 5.1의 훅 커맨드는 `python "${CLAUDE_PLUGIN_ROOT}"/scripts/notify.py`처럼 `python`을 그대로 호출한다. 사용자 환경에 `python`이 PATH에 없거나 `py` 런처만 있는 경우 훅이 조용히 실패할 수 있다 — 구현 시 실제 동작을 확인한다.

## 9. 폐기한 접근 (이전 초안 대비)

- **Discord Webhook 원격 알림** — 로컬 알림(작업표시줄 깜빡임)만으로 충분하다고 판단해 제외. 아웃바운드 HTTPS, 시크릿 관리, 암호화 범위 등 관련 고려사항 전부 불필요해짐.
- **VS Code 프로세스명 하드코딩 + 창 제목/`cwd` 매칭으로 여러 창 구분** — 조상 PID 체인 방식으로 대체되며 자동으로 해결된다. 특정 프로세스명(`Code.exe`)에 의존하지 않으므로 터미널, VS Code, 그 외 어떤 앱에서 실행하든 동일하게 동작한다.
- **`Notification`의 8개 타입마다 `matcher`를 나눠 훅 엔트리를 등록하고 커맨드에 타입을 인자로 넘기는 방식** — `hook_event_name`이 공식 문서화된 필드라는 점에 기대어, 이벤트당 엔트리 하나(`matcher` 생략)로 줄이고 세부 타입은 스크립트가 stdin JSON에서 직접 읽는 방식으로 대체했다(5.1). 다만 이 대체는 "stdin JSON에 타입 필드가 실제로 존재한다"는 아직 검증 안 된 가정에 기대므로, 구현 시 그 가정이 깨지면 이 방식으로 되돌아갈 수 있다.
