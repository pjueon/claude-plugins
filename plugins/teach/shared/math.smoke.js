/* 수식 점검 함수 — 정본. textbook-html 의 references/authoring.md probe 와
   explain-html 의 references/checklist.md probe 가 이 함수의 사본을 쓴다(고치면 양쪽).
   root 는 수식을 그린 본문 루트(<main id="book"> 또는 <main id="doc">)다.
   katexError: LaTeX 오류(문법 오류는 .katex-error, 정의되지 않은 명령은 빨간 글자)가 난 곳의 수
   rawMath: 렌더되지 않고 \( \[ 가 그대로 남은 곳이 있으면 1 */
function mathCheck(root) {
  var katexError = document.querySelectorAll('.katex-error, .katex-html [style*="rgb(204, 0, 0)"]').length;
  var c = root.cloneNode(true);
  Array.prototype.forEach.call(c.querySelectorAll('pre, code, .katex, svg, script'), function (e) { e.remove(); });
  return { katexError: katexError, rawMath: /\\\(|\\\[/.test(c.textContent) ? 1 : 0 };
}
