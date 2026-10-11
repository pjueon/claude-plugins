/* 수식 렌더링 — 본문의 \( … \) (인라인), \[ … \] (별행) 를 KaTeX 로 그린다.
   textbook-html(<main id="book">)과 explain-html(<main id="doc">)이 함께 쓰는 정본이다.
   본문을 나누거나 가공하는 런타임 스크립트(book.js 등)보다 먼저 실행되어야 한다. */
(function () {
  if (typeof renderMathInElement !== 'function') return;
  var root = document.getElementById('book') || document.getElementById('doc');
  if (!root) return;
  renderMathInElement(root, {
    delimiters: [
      { left: '\\[', right: '\\]', display: true },
      { left: '\\(', right: '\\)', display: false }
    ],
    throwOnError: false,
    strict: false
  });
})();
