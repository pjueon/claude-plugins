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
