# 퀴즈 마크업 계약

textbook-html(`book.js`)과 explain-html(`templates/explain.html`)이 같은 퀴즈 마크업과 채점 로직을 쓴다.
한쪽에서 쓴 퀴즈를 다른 쪽에 그대로 옮길 수 있어야 한다.

## 계약

- 문제 하나는 `.quiz[data-answer="N"]` 이다. `N` 은 정답 `li` 의 1-기반 번호다.
- 선택지는 `ol.options > li` 이고 **모든 `li` 에 `data-why`**(왜 맞고 왜 틀리는지)를 단다.
- `.qn`(문제 번호) 요소를 생략하면 런타임이 "퀴즈 N" 을 넣는다. 질문은 `p.q`, 보충은 `.explain`(선택).
- 채점 결과 클래스는 `pick-good` / `pick-bad` / `done` 이다.

## 작성 지침

- **정답 위치는 스크립트로 정한다.** 문제마다 `shuf -i 1-4 -n 1`(4지선다 기준, 선택지 수에 맞춘다)로 `N` 을 뽑아 그 자리에 정답을 둔다. 감으로 고르지 않는다.
- **정답이 오답보다 길거나 구체적이지 않게 한다.** 내용을 몰라도 가장 길고 상세한 선택지를 고르면 맞는 문제가 되지 않도록, 선택지의 길이와 구체성을 비슷하게 맞춘다.

## 정본과 사본

정본은 이 폴더의 `quiz.js`(`initQuiz` 함수)와 `quiz.css`(퀴즈 스타일)다. 두 런타임은 각자 인라인되어야
하므로 아래 둘이 정본을 **그대로 복사한 사본**을 갖는다.

| 사본 | JS | CSS |
|---|---|---|
| textbook-html | `skills/textbook-html/templates/assets/book.js` | `.../assets/book.css` |
| explain-html | `skills/explain-html/templates/explain.html` | 같은 파일 |

정본을 고치면 두 사본에 같은 변경을 적용하고, 사본을 직접 고쳤다면 정본에도 반영한 뒤 아래를 돌린다.
저장소 루트에서 실행한다. `JS-SAME`·`CSS-SAME`·`SMOKE-SAME` 이 모두 나와야 한다.

```bash
P=plugins/teach; Q=$P/shared; B=$P/skills/textbook-html/templates/assets; E=$P/skills/explain-html/templates/explain.html
J='/^  function initQuiz/,/^  }$/p'; C='/^\/\* 퀴즈 \*\//,/^\.quiz \.explain b\.lbl/p'
diff <(sed -n "$J" $B/book.js) $Q/quiz.js && diff <(sed -n "$J" $E) $Q/quiz.js && echo JS-SAME
diff <(sed -n "$C" $B/book.css) $Q/quiz.css && diff <(sed -n "$C" $E) $Q/quiz.css && echo CSS-SAME
K='/^function quizSmoke/,/^}$/p'; S=$B/../_smoke.html; X=$P/skills/explain-html/references/checklist.md
diff <(sed -n "$K" $S) $Q/quiz.smoke.js && diff <(sed -n "$K" $X) $Q/quiz.smoke.js && echo SMOKE-SAME
```

동작 확인은 `quiz.smoke.js`(`quizSmoke(ok, quizElement)`)로 한다. 퀴즈 하나를 틀린 답으로 눌러 채점·해설·재선택 무시를 단정한다.
정본과 같은 사본을 두 곳이 갖는다. `_smoke.html` 은 textbook-html 런타임 점검에서, explain-html 은 `references/checklist.md` 의 probe 에서 호출한다.
