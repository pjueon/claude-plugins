# 퀴즈 마크업 계약

textbook-html(`book.js` 의 `initQuiz`)과 explain-html(`templates/explain.html`)이 같은 퀴즈 마크업을 쓴다.
한쪽에서 쓴 퀴즈를 다른 쪽에 그대로 옮길 수 있어야 한다.

## 계약

- 문제 하나는 `.quiz[data-answer="N"]` 이다. `N` 은 정답 `li` 의 1-기반 번호다.
- 선택지는 `ol.options > li` 이고 **모든 `li` 에 `data-why`**(왜 맞고 왜 틀리는지)를 단다.
- `.qn`(문제 번호)은 비워 두면 런타임이 "퀴즈 N" 을 넣는다. 질문은 `p.q`, 보충은 `.explain`(선택).
- 채점 결과 클래스는 `pick-good` / `pick-bad` / `done` 이다.

## 사본과 동일성

두 런타임은 각자 인라인되어야 하므로 `initQuiz` 와 퀴즈 CSS 는 **사본**이다. 원본은 textbook-html 쪽이고,
explain-html 템플릿이 그것을 그대로 복사한다. 한쪽을 고치면 다른 쪽도 맞추고 아래를 돌린다.

저장소 루트에서 실행한다.

```bash
B=plugins/teach/skills/textbook-html/templates/assets; E=plugins/teach/skills/explain-html/templates/explain.html
diff <(sed -n '/^  function initQuiz/,/^  }$/p' $B/book.js) <(sed -n '/^  function initQuiz/,/^  }$/p' $E) && echo JS-SAME
diff <(sed -n '/^\/\* 퀴즈 \*\//,/^\.quiz \.explain b\.lbl/p' $B/book.css) <(sed -n '/^\/\* 퀴즈 \*\//,/^\.quiz \.explain b\.lbl/p' $E) && echo CSS-SAME
```

동작 확인은 `../skills/textbook-html/templates/_smoke.html` 의 퀴즈 단정(128~138행)을 템플릿 사본에 붙여 돌린다.
