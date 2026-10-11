#!/usr/bin/env node
/* 공유 자산 인라인 — explain-html 의 단일 HTML 을 완성한다. 의존성 없음(Node 만).

   사용법: node inline-shared.js <원고.html> [<출력.html>]   (출력을 생략하면 원고를 덮어쓴다)

   원고 안의 마커 주석을 아래 내용으로 바꾼다.
     <!-- teach:base-style -->   shared/base.css (공통 부품 스타일). 항상 필요하다
     <!-- teach:math-style -->   KaTeX CSS(글꼴은 data URI) + shared/math.css
     <!-- teach:math-script -->  katex.min.js + auto-render.min.js + math.js
   본문에 수식(\( … \), \[ … \])이 없으면 math 마커 둘은 그냥 지운다.
   이미 인라인된 파일에 다시 돌려도 같은 결과가 나온다(멱등). */
'use strict';
var fs = require('fs'), path = require('path');

var DIR = __dirname;
var BANNER = '/*! KaTeX v0.16.11 | MIT License | Copyright (c) 2013-2020 Khan Academy and other contributors | https://katex.org */\n';
var MARK = {
  base: '<!-- teach:base-style -->',
  mstyle: '<!-- teach:math-style -->',
  mscript: '<!-- teach:math-script -->'
};
var BLOCK = {
  base: ['style', 'base'],
  mstyle: ['style', 'math'],
  mscript: ['script', 'math']
};

function die(msg) { console.error('inline-shared: ' + msg); process.exit(1); }
function read(rel) { return fs.readFileSync(path.join(DIR, rel), 'utf8'); }
function count(s, sub) { return s.split(sub).length - 1; }

/* 한 번만 치환한다. 치환 문자열 안의 $&, $1, $$ 가 해석되지 않도록 함수로 넘긴다. */
function replaceOnce(html, marker, text) {
  return html.replace(marker, function () { return text; });
}

function build() {
  var css = read('katex/katex.min.css').replace(/url\(fonts\/([^)]+\.woff2)\)/g, function (_, name) {
    var b64 = fs.readFileSync(path.join(DIR, 'katex', 'fonts', name)).toString('base64');
    return 'url(data:font/woff2;base64,' + b64 + ')';
  });
  if (css.indexOf('url(fonts/') >= 0) die('katex.min.css 에 woff2 가 아닌 글꼴 참조가 남아 있다');
  var js = [read('katex/katex.min.js'), read('katex/auto-render.min.js'), read('math.js')].join(';\n');
  var out = {
    base: read('base.css'),
    mstyle: BANNER + css + '\n' + read('math.css'),
    mscript: BANNER + js
  };
  Object.keys(out).forEach(function (k) {
    var tag = BLOCK[k][0];
    if (out[k].indexOf('</' + tag) >= 0) die('인라인할 ' + k + ' 내용에 </' + tag + ' 가 들어 있다');
    Object.keys(MARK).forEach(function (m) {
      if (out[k].indexOf(MARK[m]) >= 0) die('인라인할 ' + k + ' 내용에 마커 문자열 ' + MARK[m] + ' 가 들어 있다');
    });
  });
  return out;
}

function hasMath(html) {
  var t = html
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/<(pre|code|script|style)\b[\s\S]*?<\/\1>/g, '');
  return /\\\(|\\\[/.test(t);
}

function main() {
  var inp = process.argv[2], outp = process.argv[3] || inp;
  if (!inp) die('사용법: node inline-shared.js <원고.html> [<출력.html>]');
  var html = fs.readFileSync(inp, 'utf8');

  /* 이미 인라인된 블록을 마커로 되돌린다(멱등) */
  Object.keys(BLOCK).forEach(function (k) {
    var tag = BLOCK[k][0], name = BLOCK[k][1];
    var re = new RegExp('<' + tag + ' data-teach="' + name + '">\\n[\\s\\S]*?\\n</' + tag + '>', 'g');
    html = html.replace(re, function () { return MARK[k]; });
  });

  var math = hasMath(html);
  Object.keys(MARK).forEach(function (k) {
    var n = count(html, MARK[k]), need = k === 'base' || math;
    if (need && n !== 1) die('마커 ' + MARK[k] + ' 가 ' + n + '개다(1개여야 한다)');
    if (!need && n > 1) die('마커 ' + MARK[k] + ' 가 ' + n + '개다(0~1개여야 한다)');
  });

  var parts = build();
  Object.keys(MARK).forEach(function (k) {
    if (k !== 'base' && !math) { html = html.split(MARK[k]).join(''); return; }
    var tag = BLOCK[k][0], name = BLOCK[k][1];
    html = replaceOnce(html, MARK[k], '<' + tag + ' data-teach="' + name + '">\n' + parts[k] + '\n</' + tag + '>');
  });

  fs.writeFileSync(outp, html);
  console.log((math ? 'inlined' : 'no-math') + ' ' + outp + ' ' + Buffer.byteLength(html) + ' bytes');
}

main();
