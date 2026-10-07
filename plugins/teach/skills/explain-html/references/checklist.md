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
/* shared/quiz.smoke.js 의 사본 — 고치면 양쪽 */
function quizSmoke(ok, quiz) {
  var opts = quiz.querySelectorAll('ol.options > li');
  var answer = parseInt(quiz.dataset.answer, 10);
  var qn = quiz.querySelector('.qn');
  ok('퀴즈 정답 번호가 선택지 범위 안', answer >= 1 && answer <= opts.length, 'answer=' + quiz.dataset.answer + ' / li=' + opts.length);
  ok('퀴즈 번호(.qn) 존재', !!qn && qn.textContent.length > 0);
  var whyOk = true, keyOk = true;
  Array.prototype.forEach.call(opts, function (li) {
    var why = li.querySelector('.why');
    if (!li.dataset.why || !why || why.textContent !== li.dataset.why) whyOk = false;
    if (li.getAttribute('tabindex') !== '0' || li.getAttribute('role') !== 'button') keyOk = false;
  });
  ok('모든 선택지에 해설 주입', whyOk);
  ok('선택지 키보드 조작 가능', keyOk);
  if (!(answer >= 1 && answer <= opts.length)) return;

  var wrong = answer === 1 ? 1 : 0;   // 정답이 아닌 첫 선택지(0-기반)
  opts[wrong].dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
  ok('틀린 선택 표시', opts[wrong].classList.contains('pick-bad'));
  ok('정답도 함께 표시', opts[answer - 1].classList.contains('pick-good'));
  ok('해설 공개', quiz.classList.contains('done'));
  var before = Array.prototype.map.call(opts, function (li) { return li.className; }).join('|');
  Array.prototype.forEach.call(opts, function (li) { li.click(); });
  var after = Array.prototype.map.call(opts, function (li) { return li.className; }).join('|');
  ok('채점 후 재선택 무시', before === after, before + ' → ' + after);
}

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
  function ok(name, cond, extra) { if (!cond) { bad++; r.push('FAIL[' + name + (extra ? ' :: ' + extra : '') + ']'); } }
  qs.forEach(function (q) { ans.push(q.dataset.answer); quizSmoke(ok, q); });
  r.push('quizBad=' + bad, 'answers=' + ans.join(''));
  var c = document.body.cloneNode(true);   // probe 스크립트 자신과 코드 인용은 빼고 센다
  c.querySelectorAll('script, pre').forEach(function (n) { n.remove(); });
  r.push('placeholders=' + ((c.innerHTML.match(/▣/g) || []).length + (document.title.match(/▣/g) || []).length));
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
| 데스크톱·라이트 | `--window-size=1280,1000 --blink-settings=preferredColorScheme=1` (시스템 설정을 따르므로 기본값이 다크일 수 있다. 실제로 적용됐는지는 `scheme=` 출력이 알려 준다) | `pageOverflow=0 quizBad=0 errors=0 placeholders=0` |
| 데스크톱·다크 | `--force-dark-mode` | 위와 같음. `scheme=dark` 가 나와야 실제로 다크로 본 것이다 |
| 모바일 | headless 는 창 폭을 500 이상으로 올릴 수 있으므로, **390px 폭 `iframe` 을 담은 래퍼 페이지**에서 `contentDocument.documentElement.scrollWidth - clientWidth` 를 잰다(`--allow-file-access-from-files` 필요) | `pageOverflow=0` (`pre` 는 상자 안 스크롤이라 넘침 허용) |

`pre` 안의 `▣`(인용한 코드·diff 에 원문으로 들어 있는 경우)는 위 `placeholders` 에 안 잡히므로 `grep -n ▣ file.html` 로 직접 확인한다. 데스크톱에서 `preOverflow` 가 0 이 아닌 것은 긴 줄이 상자 안에서 가로로 스크롤되는 것이라 허용한다.

`chars` 는 `innerText` 라서 접힌 `details` 본문이 빠진다. 읽는 시간은 SKILL.md E7 의 공식으로 어림한다. 스크린샷 경로는 Windows 에서 절대경로(`cygpath -w`)여야 한다.

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
- h2·h3·`summary`·`.box-t` 를 전부 훑어 `../../../shared/writing-style.md` 의 섹션명 규칙(명사구)을 지켰는가. 템플릿이 정한 접는 배경 summary 문구("기초 배경 — 이미 아시면 건너뛰세요")는 예외다.
- 인용한 코드·diff 가 `git show` 등의 **원문 그대로**인가(hunk 헤더 포함. 줄이거나 생략한 곳은 `…` 로 표시한다).
- 근거를 얻지 못한 부분이 머리 메타나 본문에 "확인하지 못함"으로 적혀 있는가.

## 3. 퀴즈 마크업 계약 비교 (템플릿 또는 textbook-html 런타임을 고쳤을 때)

`../../../shared/quiz.md` 의 "정본과 사본" 비교 명령을 돌린다.
