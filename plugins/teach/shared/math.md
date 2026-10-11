# 수식 — teach 스킬 공통

textbook-html 과 explain-html 이 같은 방식으로 수식을 쓴다. 수식은 **LaTeX** 로 쓰고 **KaTeX** 가 그린다.
KaTeX(0.16.11, MIT 라이선스)는 이 폴더의 `katex/` 에 로컬 사본으로 있고 `katex/LICENSE` 에 라이선스 원문이 있다.
네트워크 없이 `file://` 로 열려야 하므로 CDN 은 쓰지 않는다.

## 공유 파일

| 파일 | 무엇 |
|---|---|
| `katex/` | KaTeX 로컬 사본(`katex.min.js`·`auto-render.min.js`·`katex.min.css`·`fonts/*.woff2`·`LICENSE`) |
| `math.js` | 본문의 `\( … \)`·`\[ … \]` 를 KaTeX 로 그리는 호출. 루트는 `<main id="book">` 또는 `<main id="doc">` |
| `math.css` | 수식 보정 스타일(`.katex` 크기, 별행 수식 넘침, 콜아웃 제목 안의 수식) |
| `math.smoke.js` | 점검 함수 `mathCheck(root)`. 두 스킬의 probe 가 사본을 쓴다 |
| `inline-shared.js` | explain-html 용. `base.css`·KaTeX·`math.js`·`math.css` 를 HTML 하나에 인라인한다 |

두 스킬이 이 파일들을 가져가는 방식이 다르다.

| | textbook-html | explain-html |
|---|---|---|
| 산출물 | 폴더(`docs/`) | 단일 HTML |
| 가져가는 방식 | 골격 세우기에서 `docs/assets/` 로 복사하고 `<link>`·`<script src>` 로 불러온다 | 원고의 마커 주석(`<!-- teach:math-style -->`, `<!-- teach:math-script -->`)을 `inline-shared.js` 가 인라인한다 |

## 쓰는 규칙

수식은 유니코드(`x⁽¹⁾`, `‖a‖`)를 `<code>` 에 넣지 말고 **LaTeX 로 쓴다.** 고정폭 글꼴로 나와
첨자가 어긋나고 분수·제곱근·Σ 한계 표기가 안 되기 때문이다.

- 문장 속은 `\( … \)`, 별행은 `<p style="text-align:center">\[ … \]</p>`.
- 코드 식별자·함수명(`SVC`, `np.dot`)은 수식이 아니라 `<code>` 로 둔다. `<pre>` 안은 렌더하지 않는다.
- HTML 안이므로 부등호는 `&lt;` 로 쓴다(`>` 는 그대로 가능).
- 노름은 `\lVert a\rVert`, 한글은 `\text{모든}` 으로 감싼다.
- **제목과 속성값에는 수식을 쓰지 않는다.** `h2`·`h3` 와 `data-title`·`data-why`·`data-def`·`aria-label` 이 해당한다. 목차는 제목의 텍스트를 복사해 만들어 KaTeX 의 MathML 사본까지 겹쳐 나오고, 속성값은 렌더 대상이 아니거나 렌더 뒤에 텍스트로 주입된다. 콜아웃 제목(`.box-t`)의 수식은 `math.css` 가 대문자 변환을 막아 두었으므로 쓸 수 있다. 퀴즈 선택지 해설(`data-why`)은 일반 텍스트(그리스 문자 허용)로 쓰고, 수식이 필요한 설명은 `.explain` 에 둔다.
- 위젯이 JS 로 만들어 내는 수식은 렌더되지 않는다(위젯 값은 숫자 위주로 쓰거나 `<code>`).
- 연산 기호는 **의미마다 다른 기호를 쓰고, 처음 쓰는 페이지에서 먼저 설명한다.** 같은 기호를 두 가지 뜻으로 쓰지 않는다.
  - 대상: 내적, 스칼라 곱, 숫자 곱, 원소별 곱, 외적, 합성곱 등 문서에 나오는 연산. 필요한 것만 다룬다.
  - 어떤 기호를 쓸지는 문서의 분야와 독자 관례에 맞춘다. 내적만 해도 `w\cdot x`, `w^{T}x`, `\langle x, y\rangle`, `\langle a|b\rangle` 처럼 다양하다. 하나를 골라 문서 전체에서 통일하고, 다른 책의 표기가 있으면 "다른 책의 표기" 상자로 짚는다.
  - 예시(내적을 `\cdot` 로 정한 경우): 스칼라 곱은 기호 생략(`tw`), 숫자 곱은 `\times`(생략하면 34 로 읽힌다), 원소별 곱은 `\odot`, 합성곱은 `*`.
  - 본문 텍스트·표의 `3·4` 도 같은 규칙을 따른다. 집필 후 `grep` 으로 같은 기호가 두 뜻으로 쓰인 곳이 없는지 훑는다.
- 파이썬 등으로 본문을 일괄 치환할 때는 raw 문자열을 쓴다. 일반 문자열 안의 `\t` 가 탭 문자로 바뀌어 `\theta`·`\tfrac`·`\text` 가 조용히 깨진다.

## 점검

`mathCheck(root)` 는 `{ katexError, rawMath }` 를 돌려준다. 기대값은 둘 다 0 이다.

- `katexError`: LaTeX 오류가 난 곳의 수. 오류 메시지는 `.katex-error` 의 `title` 속성에 있고, 빨간 글자는 그 글자가 곧 틀린 명령이다.
- `rawMath`: 렌더되지 않고 `\(` 가 그대로 남은 곳이 있으면 1. 스크립트 순서 오류이거나, 중괄호 `{ }` 짝이 안 맞는 식(이 경우는 오류 표시 없이 원문이 그대로 보인다)이다.

점검은 식의 내용(숫자·부호)이 맞는지는 보지 못한다. 검수에서 직접 계산한다.

사본과 정본이 같은지 확인한다. 저장소 루트에서 실행하고 `MATH-SAME` 이 나와야 한다.

```bash
P=plugins/teach; Q=$P/shared; K='/^function mathCheck/,/^}$/p'
diff <(sed -n "$K" $P/skills/textbook-html/references/authoring.md) <(sed -n "$K" $Q/math.smoke.js) \
  && diff <(sed -n "$K" $P/skills/explain-html/references/checklist.md) <(sed -n "$K" $Q/math.smoke.js) && echo MATH-SAME
```
