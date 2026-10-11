# 코드 하이라이팅 — teach 스킬 공통

textbook-html(`book.js`)과 explain-html(`templates/explain.html`)이 같은 하이라이터를 쓴다.
토크나이저는 `highlight.js` 가 정본이고 두 런타임이 사본을 가진다. 토큰 색은 `base.css` 에 있다.

## 계약

- 색칠 대상은 `pre > code` 와 `pre code.python` 이다. `<code class="plain">` 은 건너뛴다.
  명령 출력·로그·트레이스·JSON 처럼 코드가 아닌 블록에 쓴다.
- `code` 안의 **텍스트 노드만** 바꾼다. 저자가 넣은 `<b class="hl">` 같은 강조 표시는 남는다.
  `pre > .cap`(캡션)은 `code` 밖이므로 색칠되지 않는다.
- 이미 칠한 블록에는 `data-hl="done"` 이 붙어 두 번 칠하지 않는다.
- 토큰 클래스는 `tok-kw`(키워드) · `tok-str`(문자열) · `tok-com`(주석) · `tok-num`(숫자) ·
  `tok-fn`(`def`·`class` 뒤 이름) · `tok-dec`(데코레이터) · `tok-self`(`self`·`cls`) 7종이다.
  색은 `base.css` 의 `--c-kw` … `--c-self` 변수(라이트·다크 쌍)이므로 색을 바꾸려면 거기만 고친다.

## 언어

기본은 Python 이다. 다른 언어의 코드를 실으면 사본의 `PY_KW`(키워드 목록)를 그 언어에 맞게 바꾼다.
한 문서에 언어가 둘이면 키워드를 합집합으로 둔다(오탐이 조금 늘지만 충분하다). 주석·문자열 표기 자체가 다른 언어
(슬래시 두 개로 주석을 여는 계열 등)는 `PY_RE` 의 첫 두 그룹도 고친다. 이렇게 문서마다 고쳐 쓰므로 사본이 정본과
다를 수 있고, 아래 비교 명령은 템플릿(수정 전 사본)에만 적용한다.

## diff 블록(explain-html)

explain-html 은 `markDiff` 로 줄을 `.add`·`.del`·`.hunk` 로 나눈 **뒤에** 색칠한다. 줄 단위로 토큰을 나누므로
여러 줄에 걸친 삼중따옴표 문자열은 색이 어긋날 수 있다. `.hunk` 줄은 흐린 색을 유지한다(`pre.diff .hunk span`).

## 정본과 사본

| 사본 | 범위 |
|---|---|
| textbook-html `skills/textbook-html/templates/assets/book.js` | `var PY_KW` 부터 `highlightAll` 끝까지 |
| explain-html `skills/explain-html/templates/explain.html` | 같은 범위 |

정본을 고치면 두 사본에 같은 변경을 적용하고, 사본을 직접 고쳤다면 정본에도 반영한 뒤 아래를 돌린다.
저장소 루트에서 실행한다. `HL-SAME` 이 나와야 한다. 작업 트리의 줄바꿈이 CRLF 일 수 있어 `tr -d '\r'` 로 맞춘다.

```bash
P=plugins/teach; Q=$P/shared; B=$P/skills/textbook-html/templates/assets/book.js; E=$P/skills/explain-html/templates/explain.html
H() { tr -d '\r' < "$1" | awk '/^  var PY_KW/{p=1} p{print} p&&/^  function highlightAll/{h=1} h&&/^  }$/{exit}'; }
[ -n "$(H $Q/highlight.js)" ] && diff <(H $B) <(H $Q/highlight.js) && diff <(H $E) <(H $Q/highlight.js) && echo HL-SAME
```

범위의 끝을 `highlightAll` 뒤의 첫 `  }` 로 잡는다(`esc` 의 `  }` 에서 멈추지 않게 하려는 것). 사본의 들여쓰기(2칸)가 바뀌면 범위가
비어 `[ -n … ]` 가 실패한다.

동작 확인은 textbook-html 은 `_smoke.html`(하이라이터 단정과 토큰 색 적용 단정), explain-html 은 점검 절차의 `hlPending=0` 과
스크린샷으로 한다.
