import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const read = (p) => readFileSync(resolve(__dirname, p), 'utf-8');

test('tokens.css tidak memuat font dari Google', () => {
  expect(read('../theme/tokens.css')).not.toMatch(/fonts\.googleapis|fonts\.gstatic/);
});

test('index.html tanpa preconnect pihak ketiga', () => {
  expect(read('../../index.html')).not.toMatch(/fonts\.googleapis|fonts\.gstatic/);
});
