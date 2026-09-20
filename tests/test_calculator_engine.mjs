import test from 'node:test';
import assert from 'node:assert/strict';
import { evaluate, resultParts, decimalText, pack, unpack, statistics, numberTable, value } from '../src/munchboka_edutools/static/calculator/engine.mjs';
import { Editor } from '../src/munchboka_edutools/static/calculator/editor.mjs';
const close = (source, expected, context) => assert.ok(Math.abs(evaluate(source, context).d.toNumber() - expected) < 1e-12, source);
test('CW precedence, implicit multiplication and omitted closing parentheses', () => {
  for (const [source, expected] of [['2+3*4', 14], ['-2^2', -4], ['(-2)^2', 4], ['2^-3', .125], ['6/2(1+2)', 1], ['1/2pi', 1/(2*Math.PI)], ['sin(30', .5], ['sqrt(9)+2(3+4)', 17], ['5nCr2', 10], ['5nPr2', 20], ['5!', 120], ['200*10%', 20], ['log(2,8)', 3], ['ln(e)', 1], ['root(3,-8)', -2], ['(-8)^(1/3)', -2], ['dms(30,30,0)', 30.5]]) close(source, expected);
});
test('exact fractions, radicals, pi and formatting survive persistence', () => {
  assert.deepEqual(resultParts(evaluate('1/3+1/6')), { numerator: '1', denominator: '2', whole: '' });
  assert.deepEqual(resultParts(evaluate('sqrt(8)')), { text: '2√2' });
  assert.deepEqual(resultParts(evaluate('sqrt(2)*sqrt(8)')), { text: '4' });
  assert.deepEqual(resultParts(evaluate('1/sqrt(2)')), { numerator: '√2', denominator: '2', whole: '' });
  assert.deepEqual(resultParts(evaluate('pi/3')), { numerator: 'π', denominator: '3', whole: '' });
  assert.deepEqual(resultParts(evaluate('-7/3'), {}, 'Mixed Fraction'), { numerator: '1', denominator: '3', whole: '-2' });
  assert.deepEqual(resultParts(evaluate('sin(45)')), { numerator: '√2', denominator: '2', whole: '' });
  const restored = unpack(JSON.parse(JSON.stringify(pack(evaluate('sqrt(8)/3')))));
  assert.deepEqual(resultParts(restored), { numerator: '2√2', denominator: '3', whole: '' });
  assert.equal(decimalText(evaluate('1/6'), { number: 'Fix', digits: 3 }), '0.167');
  assert.equal(decimalText(evaluate('1/200')), '5×10^-3');
  assert.equal(decimalText(evaluate('1/200'), { norm: 2 }), '0.005');
  assert.equal(decimalText(evaluate('1/2'), { decimal: 'Comma' }), '0,5');
  assert.deepEqual(resultParts(evaluate('360'), {}, 'Prime Factor'), { text: '2^3×3^2×5' });
  assert.deepEqual(resultParts(evaluate('30.5'), {}, 'Sexagesimal'), { text: '30°30′0″' });
});
test('angle settings and inverse functions', () => {
  close('sin(pi/6)', .5, { angle: 'Radian' }); close('sin(100)', 1, { angle: 'Gradian' });
  close('asin(0.5)', 30); close('atan(1)', Math.PI/4, { angle: 'Radian' });
  assert.deepEqual(resultParts(evaluate('asin(0.5)', { angle: 'Radian' })), { numerator: 'π', denominator: '6', whole: '' });
});
test('no JS execution, silent NaN, wrong arity, or unbounded input', () => {
  for (const source of ['globalThis', 'constructor.constructor(1)', 'alert(1)', '1;2', '1/0', 'sqrt(-1)', 'tan(90)', 'log(1,2)', 'asin(2)', '(-1)!', '1.5!', '70!', '5nCr6', '0^0', '1e100', 'sin(1,2)', 'root(2)', '1+*2', '2 3', '1e999999999', '('.repeat(60)+'1']) assert.throws(() => evaluate(source), undefined, source);
  assert.throws(() => evaluate('1'.repeat(3000)));
  assert.equal(evaluate('1e-100').d.toString(), '0');
});
test('variables, Ans and functions', () => {
  close('Ans+A', 7, { ans: pack(evaluate('1+2')), variables: { A: '4' } });
  close('f(3)', 10, { functions: { f: 'x^2+1' } });
  close('g(2)', 10, { functions: { f: 'x^2+1', g: '2f(x)' } });
  assert.throws(() => evaluate('f(1)', { functions: { f: 'f(x)' } }), /Circular/);
});
test('statistics and regression', () => {
  const one = statistics([['1','0'], ['2','0'], ['3','0']]);
  assert.equal(one['x̄'], '2'); assert.equal(one.sx, '1'); assert.equal(one['Σx²'], '14');
  const two = statistics([['1','3'], ['2','5'], ['3','7']], true);
  assert.equal(two.a, '1'); assert.equal(two.b, '2'); assert.equal(two.r, '1');
  assert.throws(() => statistics([]), /No Data/);
  assert.equal(statistics([['1','0']]).sx, undefined);
});
test('table bounds, decimal stepping, independent row errors', () => {
  const table = numberTable('x^2', '1/x', '-1', '1', '.5');
  assert.equal(table.length, 5); assert.equal(table[2].g, null); assert.equal(table[4].f.d, '1');
  assert.equal(numberTable('x', '', '0', '.3', '.1').length, 4);
  for (const args of [['x','','0','50','1'], ['x','x','0','30','1'], ['x','','0','10','0'], ['x','','1','0','1']]) assert.throws(() => numberTable(...args), /Range/);
});
test('natural editor evaluates nested fraction/root/power and moves between slots', () => {
  const e = new Editor(); e.template('frac'); e.insert('1'); e.move('down'); e.insert('3'); e.move('right'); e.insert('+'); e.template('frac'); e.insert('1'); e.move('down'); e.insert('6');
  close(e.source(), .5); assert.match(e.html(), /class="fraction"/);
  const copy = e.snapshot(); e.clear(); e.restore(copy); close(e.source(), .5);
  e.clear(); e.template('root'); e.insert('8'); e.move('right'); e.template('power', '', '2'); close(e.source(), 8);
  e.clear(); e.template('frac'); e.backspace(); assert.equal(e.source(), '');
  e.setText('<script>'); assert.ok(!e.html().includes('<script>'));
});
