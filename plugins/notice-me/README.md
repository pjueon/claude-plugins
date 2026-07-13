# notice-me

Claude Code 창에 포커스가 없을 때(다른 창을 보고 있을 때) 작업표시줄을 깜빡이거나, 사용자가 지정한 명령어를 실행해 알려주는 플러그인이다.

**Windows 전용이다.** Windows가 아닌 OS에서는 훅이 아무것도 하지 않고 즉시 종료한다 — 설치해도 안전하지만 아무 효과가 없다.

## 동작 방식

Claude Code가 알림(`Notification`)을 보내거나 응답을 마칠 때(`Stop`, `SubagentStop`) 훅이 발화한다. 이때:

1. 지금 보고 있는 창이 Claude Code를 실행 중인 창이면(포커스 있음) 아무것도 하지 않는다.
2. 포커스가 없으면 작업표시줄 아이콘을 깜빡이고(`flashEnabled`가 켜져 있으면), 등록해 둔 커스텀 명령어를 실행한다.

깜빡임은 사용자가 그 창을 다시 보면 자동으로 멈춘다.

## 설정

설정 파일은 `~/.claude/notice-me.json`에 둔다. 파일이 없으면 아래 기본값으로 동작한다.

```json
{
  "flashEnabled": true,
  "ignoreTypes": ["idle_prompt", "agent_completed"],
  "debounceMs": 2000,
  "customCommands": [
    "python ./my_script.py"
  ],
  "debug": false
}
```

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `flashEnabled` | boolean | `true` | 작업표시줄 깜빡임 on/off. 꺼도 `customCommands`는 그대로 실행된다. |
| `ignoreTypes` | string[] | `["idle_prompt", "agent_completed"]` | 무시할 알림 타입 목록. 아래 "알림 타입" 참고. |
| `debounceMs` | number | `2000` | 같은 세션에서 알림을 다시 발화하기까지의 최소 간격(밀리초). 짧은 간격으로 알림이 겹쳐 발화하는 걸 막는다. |
| `customCommands` | string[] | `[]` | 무시되지 않은 모든 알림에 대해 실행할 명령어 목록. 순서대로 실행하고 완료를 기다리지 않는다(fire-and-forget). 작업 디렉터리는 현재 Claude Code 세션의 작업 폴더다. |
| `debug` | boolean | `false` | `true`면 매 실행마다 무엇을 판단하고 무엇을 했는지 한 줄씩 로그를 남긴다. 알림이 예상과 다르게 동작할 때 켜서 확인한다. |

### 알림 타입 (`ignoreTypes`에 넣을 수 있는 값)

- `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog`, `elicitation_complete`, `elicitation_response`, `agent_needs_input`, `agent_completed` — Claude Code의 `Notification` 이벤트가 구분하는 세부 타입
- `stop` — 응답을 마쳤을 때(`Stop`)
- `subagent_stop` — 서브에이전트가 끝났을 때(`SubagentStop`)

`idle_prompt`(유휴 알림)와 `agent_completed`(작업 완료 — `stop`과 의미가 겹쳐 중복 발화를 막기 위해)는 기본으로 무시된다. 원하면 `ignoreTypes`에서 빼서 켤 수 있다.

### `customCommands` 안전 수칙

- 이 목록에 적은 명령어는 그대로 셸에서 실행된다. 로컬 설정 파일에 자기 자신이 적어 둔 값이므로 위험하지 않지만, **믿을 수 없는 값을 이 파일에 채우는 스크립트나 도구를 연결하지 않는다.**

## 커스텀 명령어 예시

```json
{
  "customCommands": [
    "python ./my_script.py"
  ]
}
```

## 디버깅

`debug: true`로 설정하면 매 실행 결과가 `${CLAUDE_PLUGIN_DATA}/debug.log`에 한 줄씩 쌓인다. 알림이 안 오거나 계속 오는 등 예상과 다르게 동작할 때 이 로그를 확인한다.
