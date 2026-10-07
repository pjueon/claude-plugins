# 저장 전 점검

통과 못 한 항목이 있으면 통과했다고 쓰지 않는다. 점검용 사본과 스크린샷은 scratchpad 에만 둔다.

## 1. 기계 점검 (probe)

산출 HTML 의 **사본**을 scratchpad 에 만들어 아래 두 조각을 붙인다.

`<head>` 바로 뒤:

```html
<script>window.__errs=[];addEventListener('error',function(e){__errs.push(e.message)});</script>
```

`</body>` 앞:

```html
<script>
window.addEventListener('load', function () {
  var r = [], d = document.documentElement, bad = 0, ans = [];
  r.push('scheme=' + (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  r.push('pageOverflow=' + (d.scrollWidth - d.clientWidth));
  var pres = document.querySelectorAll('pre'), po = 0;
  pres.forEach(function (p) { if (p.scrollWidth - p.clientWidth > 1) po++; });
  r.push('preOverflow=' + po + '/' + pres.length);
  r.push('sections=' + [].map.call(document.querySelectorAll('#doc > section[id]'), function (s) { return s.id; }).join(','));
  r.push('tocLinks=' + document.querySelectorAll('#toc a').length);
  var qs = document.querySelectorAll('.quiz'); r.push('quiz=' + qs.length);
  qs.forEach(function (q, i) {
    var a = +q.dataset.answer, li = q.querySelectorAll('ol.options > li'); ans.push(a);
    if (!(a >= 1 && a <= li.length)) { bad++; return; }
    li.forEach(function (x) { if (!x.dataset.why || !x.querySelector('.why')) bad++; });
    var pick = (i % 2) ? a - 1 : a % li.length;   // 짝수 번째 문제는 오답, 홀수 번째는 정답을 누른다
    li[pick].click();
    if (!(q.classList.contains('done') && li[a - 1].classList.contains('pick-good')
          && (pick === a - 1 || li[pick].classList.contains('pick-bad')))) bad++;
  });
  r.push('quizBad=' + bad, 'answers=' + ans.join(''));
  r.push('placeholders=' + (document.body.innerHTML.match(/▣/g) || []).length);
  r.push('chars=' + document.getElementById('doc').innerText.length);
  r.push('errors=' + __errs.length + (__errs.length ? ' ' + __errs.join(' | ') : ''));
  var o = document.createElement('pre'); o.id = 'probe-out'; o.textContent = r.join(' '); document.body.appendChild(o);
});
</script>
```

실행 (Windows Git Bash 기준. 다른 OS 는 Chrome 경로만 바꾼다):

```bash
C="/c/Program Files/Google/Chrome/Application/chrome.exe"
"$C" --headless=new --disable-gpu --no-sandbox --virtual-time-budget=3000 \
  --window-size=1280,1000 --dump-dom "file:///C:/…/probe.html" | grep -o '<pre id="probe-out">[^<]*'
```

| 조합 | 추가 플래그 | 기대 |
|---|---|---|
| 데스크톱·라이트 | `--window-size=1280,1000` | `pageOverflow=0 quizBad=0 errors=0 placeholders=0` |
| 데스크톱·다크 | `--force-dark-mode` | 위와 같음. `scheme=dark` 가 나와야 실제로 다크로 본 것이다 |
| 모바일 | `--window-size=390,844` | `pageOverflow=0` (`pre` 는 상자 안 스크롤이라 넘침 허용) |

그 밖의 기대값: `sections=background,intuition,detail,quiz`, `quiz=5`, `answers` 에 한 번호가
몰려 있지 않음(예: `21342`), `chars` 가 대략 12,000자 이하(넘으면 줄이거나 textbook-html 을 제안).
스크린샷(`--screenshot=<scratchpad>/shot-….png`)을 찍어 Read 로 보고 목차·퀴즈·콜아웃·diff 색·
위젯이 두 테마와 모바일 폭에서 읽히는지 눈으로 확인한다.

정적 점검:

```bash
grep -nE '<script[^>]+src=|<link[^>]+href=|@import|url\(|type="module"|fetch\(' file.html   # 0건
grep -nP '[\x{2500}-\x{257F}]|\+-{3,}\+' file.html                                        # 0건 (ASCII 도식)
```

## 2. 내용 점검

- 본문의 수치·출력·트레이스가 **근거 메모와 일치**하는가. 위젯 `STEPS` 도 실행 출력에서 왔는가.
- 변경 계열이면 본문의 파일 수·증감 줄 수가 `git show --stat` 과 일치하는가.
- 퀴즈 5문이 본문만으로 풀리는가. 함정 문제가 없는가. 정답 위치가 고른가. `data-why` 가 "왜 맞고
  왜 틀리는지"를 말하는가.
- 배경 접기 앞뒤에 연결 문장이 있는가. 절과 절 사이의 전환이 매끄러운가.
- h2·h3·`summary`·`.box-t` 를 전부 훑어 `authoring.md` "한국어 문체"의 섹션명 규칙(명사구)을 지켰는가.
- 근거를 얻지 못한 부분이 머리 메타나 본문에 "확인하지 못함"으로 적혀 있는가.

## 3. 퀴즈 마크업 계약 비교 (템플릿 또는 textbook-html 런타임을 고쳤을 때)

템플릿의 `initQuiz` 와 퀴즈 CSS 는 `textbook-html` 의 사본이다. 한쪽을 고치면 다른 쪽도 맞춘다.

```bash
B=plugins/teach/skills/textbook-html/templates/assets; E=plugins/teach/skills/explain-html/templates/explain.html
diff <(sed -n '/^  function initQuiz/,/^  }$/p' $B/book.js) <(sed -n '/^  function initQuiz/,/^  }$/p' $E) && echo JS-SAME
diff <(sed -n '/^\/\* 퀴즈 \*\//,/^\.quiz \.explain b\.lbl/p' $B/book.css) <(sed -n '/^\/\* 퀴즈 \*\//,/^\.quiz \.explain b\.lbl/p' $E) && echo CSS-SAME
```

동작 확인은 `textbook-html/templates/_smoke.html` 의 퀴즈 단정(128~138행)을 템플릿 사본에 붙여 돌린다.
