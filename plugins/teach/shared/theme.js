/* 테마 전환 — textbook-html 과 explain-html 이 함께 쓰는 정본. 의존성 없음
   - 반드시 <head> 안, 스타일 뒤에서 동기로 불러온다(첫 화면이 다른 테마로 깜빡이지 않게)
   - 설정은 자동·라이트·다크 셋이다. 자동은 OS 설정(prefers-color-scheme)을 따른다
   - 버튼은 자동 → OS 와 반대 → OS 와 같은 쪽 → 자동 순으로 돈다(첫 클릭에 화면이 반드시 바뀌게)
   - 고른 값은 localStorage 'teach:theme' 에 남는다. file:// 에서는 로컬 페이지가 저장소를
     공유하므로 모든 teach 산출물이 같은 설정을 쓴다(의도된 동작)
   - <html data-theme="light|dark"> 를 붙이고, 색은 base.css 가 이 속성으로 고른다
   - 버튼(#theme-toggle)은 body 가 생기면 우측 상단에 붙인다. 스타일은 base.css
   - textbook-html: docs/assets/theme.js 로 복사해 <script src> 로 불러온다
   - explain-html: shared/inline-shared.js 가 원고의 teach:theme-script 마커 주석 자리에 인라인한다 */
(function () {
  'use strict';
  var KEY = 'teach:theme';
  var LABEL = { auto: '자동', light: '라이트', dark: '다크' };
  var ICON = {
    auto: '<circle cx="12" cy="12" r="8"/><path d="M12 4a8 8 0 0 1 0 16z" fill="currentColor"/>',
    light: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    dark: '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>'
  };
  var root = document.documentElement;
  var mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  var btn = null;

  function load() {
    try { var v = localStorage.getItem(KEY); return v === 'light' || v === 'dark' ? v : 'auto'; }
    catch (e) { return 'auto'; }
  }
  function save(v) {
    try { if (v === 'auto') localStorage.removeItem(KEY); else localStorage.setItem(KEY, v); }
    catch (e) { /* 저장 못해도 이번 화면에는 적용된다 */ }
  }

  function system() { return mq && mq.matches ? 'dark' : 'light'; }
  function nextOf(pref) {
    var sys = system(), other = sys === 'dark' ? 'light' : 'dark';
    return pref === 'auto' ? other : pref === other ? sys : 'auto';
  }

  function apply() {
    var pref = load();
    root.setAttribute('data-theme', pref === 'auto' ? system() : pref);
    if (!btn) return;
    var next = nextOf(pref);
    btn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" ' +
      'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + ICON[pref] + '</svg>';
    btn.title = '테마: ' + LABEL[pref] + ' (누르면 ' + LABEL[next] + ')';
    btn.setAttribute('aria-label', btn.title);
  }

  function mount() {
    if (btn || !document.body) return;
    btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'theme-toggle';
    btn.addEventListener('click', function () {
      save(nextOf(load()));
      apply();
    });
    document.body.appendChild(btn);
    apply();
  }

  apply();
  if (mq) {
    if (mq.addEventListener) mq.addEventListener('change', apply);
    else if (mq.addListener) mq.addListener(apply);
  }
  /* 다른 탭에서 바꾼 설정도 따라간다 */
  window.addEventListener('storage', function (e) { if (e.key === KEY || e.key === null) apply(); });
  if (document.body) mount();
  else document.addEventListener('DOMContentLoaded', mount);
})();
