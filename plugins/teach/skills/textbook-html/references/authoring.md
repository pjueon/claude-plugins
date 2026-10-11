# 장 집필과 점검

## 장 하나를 쓰는 순서

1. **커리큘럼에서 그 장의 항목 · 페이지 수 · 시간을 확인한다.** 페이지 수는 지키는 것이 좋다.
2. **앞장이 미뤄 둔 것을 확인한다.** 앞장에 `.later` 로 "N장에서 본다"고 적어둔 것,
   커리큘럼의 "앞장에서 받는 것". 아직 다루지 않은 것이 있으면 이 장에서 다룬다.
3. **코드가 누적되는 교재면 `authoring/02-코드-정본.md` 를 먼저 연다.** 본문 코드는 정본을 따른다.
4. **페이지 목록을 먼저 적고**(제목 + 한 줄), 그 다음에 본문을 쓴다.
   페이지 개수가 커리큘럼과 다르면 그 이유를 커리큘럼에 반영한다.
5. `ch-template.html` 을 복사해 쓴다. 없는 마크업은 만들지 않는다.
   수식은 LaTeX `\( \)`·`\[ \]` 로 쓴다(`../../../shared/math.md`). 코드 식별자는 `<code>`.
6. **`book.js` 의 `BOOK` 에 이 장의 `ready: true` 와 실제 페이지 수를 반영한다.**
7. 점검(아래)을 돌린다.

## 점검 — 두 명령

브라우저 경로 예: `/c/Program Files/Google/Chrome/Application/chrome.exe`
(Edge 도 된다. `--headless=new` 를 지원하는 크로미움이면 무엇이든)

### 1) 런타임 점검 — `_smoke.html`

54개 단정(사이드바, 페이지 이동, 카운터·진행률·주소 `#sN`, 하이라이터 토큰, 부등호 보존, 탭, 수식 렌더(KaTeX),
퀴즈 채점·키보드 조작, 용어 툴팁 `#tip`, 페이지 참조 링크·돌아가기).
**`book.css` · `book.js` 를 고칠 때마다 돌린다.**

```bash
chrome --headless=new --disable-gpu --no-sandbox --virtual-time-budget=4000 \
  --dump-dom "file:///<authoring 절대경로>/_smoke.html" > out.html
# out.html 의 <pre id="test-out"> 에서 FAIL 이 0 인지 확인
```

`_smoke.html` 의 단정은 `BOOK` 구조에 묶이지 않게 쓴다(장 수를 하드코딩하지 말 것).
`TERMS` 의 `_smoke` 항목은 이 파일이 참조하므로 지우지 않는다.

### 2) 새 장 점검 — 임시 probe

장 파일 **사본**에 아래를 붙여 모든 페이지를 켜고 검사한다. 확인할 것: 코드 블록 가로 넘침
(1280px 기준 0), 페이지 수, 툴팁 미연결 개수(`TERMS` 에 없는 `data-term`).

```javascript
// chNN.html 사본의 </body> 앞에 붙인다
/* shared/math.smoke.js 의 사본 — 고치면 양쪽 */
function mathCheck(root) {
  var katexError = document.querySelectorAll('.katex-error, .katex-html [style*="rgb(204, 0, 0)"]').length;
  var c = root.cloneNode(true);
  Array.prototype.forEach.call(c.querySelectorAll('pre, code, .katex, svg, script'), function (e) { e.remove(); });
  return { katexError: katexError, rawMath: /\\\(|\\\[/.test(c.textContent) ? 1 : 0 };
}

window.addEventListener('load', function () {
  var res = [], scs = document.querySelectorAll('.screen');
  for (var i = 0; i < scs.length; i++) {
    scs[i].classList.add('is-active');
    var pres = scs[i].querySelectorAll('pre');
    for (var j = 0; j < pres.length; j++) {
      var over = pres[j].scrollWidth - pres[j].clientWidth;
      if (over > 1) res.push('s' + (i + 1) + 'pre' + (j + 1) + '=' + over);
    }
    scs[i].classList.remove('is-active');
  }
  var m = mathCheck(document.getElementById('book'));
  var box = document.createElement('pre'); box.id = 'probe-out';
  box.textContent = (res.length ? 'OVERFLOW ' + res.join(',') : 'NO-OVERFLOW')
    + ' screens=' + scs.length
    + ' termsMissing=' + document.querySelectorAll('.term:not([data-def])').length
    + ' katexError=' + m.katexError + ' rawMath=' + m.rawMath;
  document.body.appendChild(box);
});
```

`--window-size=1280,1250 --dump-dom` 으로 열고 `<pre id="probe-out">` 를 읽는다.
기대값은 `NO-OVERFLOW screens=<커리큘럼의 페이지 수> termsMissing=0 katexError=0 rawMath=0`.
`katexError`·`rawMath` 의 뜻과 오류 해석은 `../../../shared/math.md` 의 "점검" 절을 본다.
가로 넘침이 나오면 **코드 줄을 줄인다**(본문 폭 45rem, 코드 폰트 .82rem → 약 90자).
레이아웃을 넓히는 방향으로 대응하지 않는다.

probe 의 `NO-OVERFLOW` 는 `<pre>` 만 본다. **페이지 자체의 가로 스크롤**은 따로 본다 —
페이지마다 `is-active` 를 돌리면서 그 페이지의 `.term[data-def]` 마다 `mouseover` 를 보내고,
`document.documentElement.scrollWidth > clientWidth` 인지 확인한다. 본문에 넣은 표·그림·위젯이
넓어도 여기서 잡힌다. (툴팁은 `book.js` 가 body 에 붙인 `#tip` 하나를 화면 안에 맞춰 띄운다.
예전 `.term::after` 방식은 숨겨져 있어도 레이아웃에 남아 줄 끝에서 페이지 가로 스크롤을 만들었다.)

### 3) 눈으로 확인

```bash
chrome --headless=new --disable-gpu --no-sandbox --virtual-time-budget=9000 \
  --window-size=1280,1400 --screenshot=shot.png "file:///<...>/chNN.html#s5"
```

`#sN` 으로 특정 페이지를 연다. `--virtual-time-budget` 이 작으면 전환 애니메이션 중간이 찍힌다.
헤드리스는 기본이 다크 모드다. 라이트 모드는 실제 브라우저에서 본다.

## 다른 페이지를 인용할 때

`book.js` 가 본문 텍스트에서 다음을 자동으로 링크로 바꾼다(마크업 불필요).
`<code>`·`<pre>`·이미 링크인 곳·`kicker`·그림(`svg`) 안은 건드리지 않는다.

- **"페이지 N"**(같은 장) — 누르면 그 페이지로 바로 이동하고, 하단에 돌아가기 버튼이 뜬다. "페이지 4·6", "페이지 2~3" 처럼 이어 쓴 번호도 각각 링크가 된다.
- **"N장 페이지 M"** — `chNN.html#sM` 링크. `ready` 인 장만 링크가 된다. 누르면 그 장으로 이동하고
  이동한 쪽에 돌아가기 버튼이 뜬다.
- 링크로 만들면 안 되는 자리(번호가 다른 뜻인 경우)는 `<code>` 로 감싼다.

그래서 집필할 때는:

1. 같은 장의 "페이지 N" 은 그냥 쓴다. 단, **본문 논증이 그 표·그림을 보면서 따라가야 하면** 그 자리에
   작게 다시 보인다(`.box.note` 에 "다시 보기").
2. **다른 장의 내용**을 근거로 쓸 때는 괄호 한 줄 요약을 붙이거나 다시 보인다.
3. **퀴즈·과제가 앞 페이지의 표·코드를 전제하면** 그 표를 문제 옆에 다시 보인다. 정답이 드러나는 재게시는 하지 않는다.

## 한국어 문체

공통 기준 `../../../shared/writing-style.md` 를 따른다(explain-html 과 공유).

## 자주 틀리는 것

1. **코드 해설의 행 번호 어긋남** — 가장 자주 틀린다. `ol.notes` 를 쓸 때마다 실제 코드와
   대조한다. 코드를 한 줄 고치면 그 아래 모든 번호가 밀린다.
2. **페이지를 중간에 끼워 넣기** — `kicker` 번호, 주석 구분선 번호, 본문의 "페이지 N" 상호 참조,
   `BOOK` 의 `screens` 값을 모두 다시 매긴다.
   `grep -n "페이지 [0-9]" docs/chNN.html | grep -v kicker` 로 남은 참조를 확인한다.
   참조가 자동 링크가 되었다고 번호가 맞는 것은 아니다 — 링크가 가리키는 페이지에 인용한 표·수치가 실제로 있는지 본다.
3. **`TERMS` 에 없는 `data-term`** — 툴팁이 조용히 안 나온다. probe 의 `termsMissing` 이 잡는다.
4. **`ready: true` 를 안 켜서** 목차에서 새 장이 회색으로 남는 것.
5. **`.later` 로 표시만 하고 안 다루는 것.** 표시한 장에서 반드시 다룬다.
   `.later` 문구와 본문에는 "갚는다·빚" 같은 비유를 쓰지 않는다(어색한 번역투).
   "N장에서 다룹니다 / N장에서 다룸", "약속을 지킵니다", "미뤄 둔 질문" 처럼 쓴다.
   (장부·기획 같은 작업 문서의 "갚을 장" 은 내부 용어라 그대로 둬도 된다.)
6. **용어를 정의하기 전에 쓰는 것.** 이름이 붙은 페이지보다 뜻을 설명하는 페이지가 앞에 와야 한다.
   집필 후 `grep` 으로 첫 등장 위치를 확인한다.
7. **부등호를 이스케이프하지 않은 것** — `pre` 안에서 `<` `>` 는 `&lt;` `&gt;` 로 쓴다.
8. **일괄 치환으로 수식이 깨지는 것** — 파이썬 등으로 본문을 치환할 때 일반 문자열 안의 `\tfrac`·`\text`·`\theta` 의 `\t` 가
   탭 문자로 바뀌어 수식이 조용히 깨진다. 치환 문자열은 raw 로 쓰고, 끝나면
   `grep -nP "[\x00-\x08\x0b\x0c\x0e-\x1f]" docs/chNN.html` 이 0건인지 확인한다. 코드 블록(`pre`)은 의도한 변경 외에 diff 가 없어야 한다.
9. **후공개 장에서 답을 흘리는 것** — 예시 코드·퀴즈 해설 등 본문 어딘가에 과제의 답이 드러나면 후공개의 의미가 없다.
   자리표시자(`details.fold answer` 의 `fold-body`)에는 아래 두 줄만 그대로 둔다(summary 는 그대로). 문구를 장마다 바꾸지 않는다.

   ```html
   <!-- teach:answer-pending -->
   <p>직접 작성해 본 뒤 공개됩니다. 실습을 커밋하고 피드백을 받으면 이 자리에 모범답안이 들어옵니다.</p>
   ```

   점검은 `grep -c "teach:answer-pending" docs/chNN.html`.

## 진도 저장 주의

`file://` 에서는 로컬로 열린 모든 페이지가 `localStorage` 를 공유한다.
`book.js` 의 `STORE_KEY` 를 교재마다 다른 접두어로 둔다(예: `ddd-book:progress`).
같은 블록의 `NAV_KEY`·`BACK_KEY`(`sessionStorage`)도 같은 접두어로 바꾼다.

완독(✓)은 직전 페이지에서 '다음'으로 마지막 페이지에 왔을 때만 남는다. `#sN` 딥링크나 목차 클릭으로
마지막 페이지를 열어 본 것은 완독이 아니다. '다음 장'으로 넘어가면 그 장은 항상 페이지 1부터 열린다.
