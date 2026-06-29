# claude-plugins

개인적으로 사용하는 Claude Code 플러그인을 한곳에서 관리하려고 만든 플러그인 마켓플레이스다. 여러 프로젝트에서 쓰는 스킬·서브에이전트를 플러그인으로 묶어 두고, `/plugin` 명령어로 필요한 프로젝트에 골라 설치한다.

마켓플레이스 카탈로그는 [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json)에 있고, 각 플러그인은 `plugins/<이름>/` 아래 표준 플러그인 레이아웃(`.claude-plugin/plugin.json` + `skills/`·`agents/` 등)을 따른다. 어떤 플러그인이 있고 무엇을 하는지는 카탈로그와 각 플러그인의 `plugin.json`, `SKILL.md`를 본다.

## 설치

마켓플레이스를 한 번 등록한 뒤, 필요한 프로젝트에서 플러그인을 설치한다. 아래에서 `<플러그인>`은 카탈로그에 적힌 플러그인 이름으로 바꾼다.

```bash
# 1. 이 repo를 마켓플레이스로 등록 (Claude Code가 repo 전체를 클론함)
/plugin marketplace add https://github.com/pjueon/claude-plugins.git

# 2. 플러그인 설치 (<플러그인>@<마켓플레이스 이름>)
/plugin install <플러그인>@jueon
```

설치한 스킬은 `/<스킬>` 또는 `/<플러그인>:<스킬>`로 호출한다. 정확한 이름은 해당 플러그인의 `skills/` 폴더를 본다.

## 업데이트

플러그인이 갱신(이 repo에 새 커밋 push)됐을 때, 설치된 플러그인은 **자동으로 최신화되지 않는다.** 마켓플레이스 카탈로그를 다시 받아온 뒤 플러그인을 업데이트한다.

```bash
# 1. 마켓플레이스 카탈로그 갱신 (repo를 git pull 함)
/plugin marketplace update jueon

# 2. 플러그인을 최신 버전으로 업데이트
/plugin update <플러그인>@jueon
```

`/plugin marketplace update`에서 마켓플레이스 이름을 생략하면 등록된 모든 마켓플레이스를 갱신한다.

매번 수동으로 갱신하기 번거로우면 자동 업데이트를 켠다. `/plugin` → `Marketplaces` 탭 → 마켓플레이스 선택 → `Enable auto-update`로 활성화하면, Claude Code 시작 시 자동으로 최신 버전을 받아온다.

대화형 메뉴로 관리하려면 `/plugin`을 입력한다.

- `Installed` 탭 — 설치된 플러그인 업데이트·제거
- `Marketplaces` 탭 — 마켓플레이스 갱신(`U`)·자동 업데이트 토글·제거

## 라이선스

[MIT](LICENSE)
