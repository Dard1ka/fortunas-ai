import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const html = readFileSync(resolve(__dirname, '../../index.html'), 'utf-8');
const manifest = JSON.parse(
  readFileSync(resolve(__dirname, '../../public/manifest.webmanifest'), 'utf-8'),
);

test('theme-color meta = manifest theme_color = violet kanonik', () => {
  expect(html).toMatch(/<meta name="theme-color" content="#6D5EF7"/);
  expect(manifest.theme_color).toBe('#6D5EF7');
});

test('copy Qwen3 sudah tidak ada (LLM = Gemini)', () => {
  expect(html).not.toMatch(/Qwen3/i);
  expect(JSON.stringify(manifest)).not.toMatch(/Qwen3/i);
});

test('noscript Bahasa Indonesia ada', () => {
  expect(html).toMatch(/<noscript>[\s\S]*JavaScript[\s\S]*<\/noscript>/);
});
