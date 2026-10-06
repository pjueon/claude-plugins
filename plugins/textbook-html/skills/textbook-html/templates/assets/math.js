/* 수식 렌더링 — 본문의 \( … \) (인라인), \[ … \] (별행) 를 KaTeX 로 그린다.
   book.js 가 페이지를 나누기 전에 실행되어야 하므로 book.js 바로 앞에서 불러온다. */
(function () {
  if (typeof renderMathInElement !== 'function') return;
  renderMathInElement(document.getElementById('book'), {
    delimiters: [
      { left: '\\[', right: '\\]', display: true },
      { left: '\\(', right: '\\)', display: false }
    ],
    throwOnError: false,
    strict: false
  });
})();
