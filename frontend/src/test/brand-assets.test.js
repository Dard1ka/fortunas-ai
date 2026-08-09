// Menjaga aset merek setelah rebrand logo (Spec 5):
//   (a) tidak ada aset emas lama yang tersisa dirujuk,
//   (b) tiap ikon yang ditulis manifest benar-benar ada berkasnya,
//   (c) atribut `sizes` COCOK dengan dimensi asli PNG-nya — bug lama:
//       manifest menulis "256x256" untuk berkas yang aslinya 1254px,
//   (d) tepat satu ikon maskable (syarat Android adaptive icon).
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

const PUBLIC = resolve(__dirname, '../../public');
const html = readFileSync(resolve(__dirname, '../../index.html'), 'utf-8');
const manifest = JSON.parse(
  readFileSync(resolve(PUBLIC, 'manifest.webmanifest'), 'utf-8'),
);

/** Baca lebar/tinggi dari header IHDR PNG — tanpa dependency baru. */
function pngSize(file) {
  const buf = readFileSync(file);
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
}

test('aset emas lama tidak dirujuk lagi di index.html', () => {
  expect(html).not.toMatch(/favicon\.svg|logo-mark\.svg|logo-mark-256\.png/);
});

test('index.html menunjuk favicon PNG + apple-touch baru', () => {
  expect(html).toMatch(/href="\/favicon-32\.png"/);
  expect(html).toMatch(/href="\/favicon-16\.png"/);
  expect(html).toMatch(/rel="apple-touch-icon" href="\/apple-touch-icon\.png"/);
});

test('setiap ikon manifest ada berkasnya dan sizes-nya cocok dengan PNG', () => {
  expect(manifest.icons.length).toBeGreaterThan(0);
  for (const icon of manifest.icons) {
    const file = resolve(PUBLIC, icon.src.replace(/^\//, ''));
    expect(existsSync(file), `${icon.src} tidak ada`).toBe(true);
    const { width, height } = pngSize(file);
    expect(icon.sizes, `sizes ${icon.src}`).toBe(`${width}x${height}`);
  }
});

test('tepat satu ikon maskable (syarat Android adaptive icon)', () => {
  const maskable = manifest.icons.filter((i) => i.purpose === 'maskable');
  expect(maskable).toHaveLength(1);
});

test('logo yang dipakai di dalam app ada', () => {
  expect(existsSync(resolve(PUBLIC, 'logo-mark.png'))).toBe(true);
});
