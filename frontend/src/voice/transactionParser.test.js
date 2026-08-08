// Parser transaksi suara multi-item (Wave C area E) — port setia
// mobile/lib/voice/transaction_parser.dart (353 baris, NOL test di Dart).
// Fixture blok A/B/C TERVERIFIKASI dengan menjalankan parser Dart asli
// (inventaris area-voice-parser). Blok C = known-quirk baseline; C1/C2/C3
// DIPERBAIKI di commit fix terpisah (test ini lalu di-update).
import { describe, expect, test } from 'vitest';
import { parseTransaction, parseNumberRun } from './transactionParser.js';

const NOW = new Date(2026, 7, 8, 10, 0, 0); // → INV-20260808-000 deterministik

const parse = (t) => parseTransaction(t, { now: NOW });
const items = (t) => parse(t).items;

describe('Blok A — 7 sampel resmi tool/parser_check.dart', () => {
  test('A1 dua item dengan harga digit + Rp glue', () => {
    const r = parse('penghapus 10 dengan harga 100.000 dan pensil 2 dengan harga Rp20.000');
    expect(r.items).toEqual([
      { product: 'Penghapus', qty: 10, unit_price: 100000 },
      { product: 'Pensil', qty: 2, unit_price: 20000 },
    ]);
    expect(r.confidence).toBe(0.92);
  });

  test('A2 preamble panjang, qty-only → confidence 0.6', () => {
    const r = parse('baik saya konfirmasi untuk barangnya ada sabun cuci 10, penghapus 2, pensil 5');
    expect(r.items).toEqual([
      { product: 'Sabun Cuci', qty: 10, unit_price: 0 },
      { product: 'Penghapus', qty: 2, unit_price: 0 },
      { product: 'Pensil', qty: 5, unit_price: 0 },
    ]);
    expect(r.confidence).toBe(0.6);
  });

  test('A3 tiga item, rp glue + kata angka + satuan kilo', () => {
    const r = parse('baik saya konfirmasi pesanannya ada sabun cuci 10 dengan harga rp8.500 minyak goreng 5 dengan harga Rp20.000 lalu ada beras 2 kilo dengan harga Rp60.000');
    expect(r.items).toEqual([
      { product: 'Sabun Cuci', qty: 10, unit_price: 8500 },
      { product: 'Minyak Goreng', qty: 5, unit_price: 20000 },
      { product: 'Beras', qty: 2, unit_price: 60000 },
    ]);
    expect(r.confidence).toBe(0.92);
  });

  test('A4 invoice eksplisit + kata angka', () => {
    const r = parse('Invoice INV-2024, sabun cuci qty 10 harga delapan ribu lima ratus');
    expect(r.invoice).toBe('INV-2024');
    expect(r.items).toEqual([{ product: 'Sabun Cuci', qty: 10, unit_price: 8500 }]);
    expect(r.confidence).toBe(0.92);
  });

  test('A5 pemisah koma + dan + satuan karung', () => {
    const r = parse('sabun cuci qty 10 harga delapan ribu lima ratus, minyak goreng 5 harga dua puluh ribu, dan beras dua karung enam puluh ribu');
    expect(r.items).toEqual([
      { product: 'Sabun Cuci', qty: 10, unit_price: 8500 },
      { product: 'Minyak Goreng', qty: 5, unit_price: 20000 },
      { product: 'Beras', qty: 2, unit_price: 60000 },
    ]);
  });

  test('A6 satuan sachet/kg dibuang', () => {
    const r = parse('beli kopi sachet 12 seharga seribu lima ratus lalu gula 3 kg harga lima belas ribu');
    expect(r.items).toEqual([
      { product: 'Kopi', qty: 12, unit_price: 1500 },
      { product: 'Gula', qty: 3, unit_price: 15000 },
    ]);
  });

  test('A7 invoice digit → prefiks INV- + customer 2 kata', () => {
    const r = parse('invoice 7781 atas nama Bu Siti, teh kotak 24 harga 4500 dan air mineral 12 harga 3000');
    expect(r.invoice).toBe('INV-7781');
    expect(r.customer).toBe('Bu Siti');
    expect(r.items).toEqual([
      { product: 'Teh Kotak', qty: 24, unit_price: 4500 },
      { product: 'Air Mineral', qty: 12, unit_price: 3000 },
    ]);
  });
});

describe('Blok B — kasus yang harus tetap hijau', () => {
  test.each([
    ['nasi goreng 3 porsi harga dua belas ribu', 'Nasi Goreng', 3, 12000],
    ['es teh 2 gelas harga lima ribu', 'Es Teh', 2, 5000],
    ['ayam 1 ekor harga tiga puluh lima ribu', 'Ayam', 1, 35000],
    ['laptop 1 harga sepuluh juta', 'Laptop', 1, 10000000],
    ['motor 1 harga dua puluh lima juta lima ratus ribu', 'Motor', 1, 25500000],
    ['sabun 1 harga seribu', 'Sabun', 1, 1000],
    ['sabun 1 harga sejuta', 'Sabun', 1, 1000000],
    ['sabun 1 harga sebelas ribu', 'Sabun', 1, 11000],
    ['sabun 1 harga seratus ribu', 'Sabun', 1, 100000],
    ['sabun 2 harga 8.500', 'Sabun', 2, 8500],
    ['sabun 2 harga 8,500', 'Sabun', 2, 8500],
    ['pensil 5 @ 2000', 'Pensil', 5, 2000],
    ['telur 2 kg per 28000', 'Telur', 2, 28000],
    ['gula 3 kg 15000', 'Gula', 3, 15000],
    ['SABUN CUCI 2 HARGA 5000', 'Sabun Cuci', 2, 5000],
  ])('%s', (transcript, product, qty, price) => {
    expect(items(transcript)).toEqual([{ product, qty, unit_price: price }]);
  });

  test('harga boleh mendahului produk', () => {
    expect(items('harga 5000 sabun')).toEqual([{ product: 'Sabun', qty: 1, unit_price: 5000 }]);
  });

  test('auto-split murni tanpa pemisah', () => {
    expect(items('mie ayam 2 porsi 15000 es jeruk 1 gelas 5000')).toEqual([
      { product: 'Mie Ayam', qty: 2, unit_price: 15000 },
      { product: 'Es Jeruk', qty: 1, unit_price: 5000 },
    ]);
  });

  test('tiga item dengan terus + dan', () => {
    expect(items('sabun 2 harga 5000 terus pensil 3 harga 2000 dan buku 1 harga 10000')).toHaveLength(3);
  });

  test('koma antar-field TIDAK memecah item (guard nextIsFieldKw)', () => {
    expect(items('sabun cuci, qty 10, harga 8500')).toEqual([
      { product: 'Sabun Cuci', qty: 10, unit_price: 8500 },
    ]);
  });

  test('transkrip kosong / semua noise → 0 item, confidence 0', () => {
    expect(parse('')).toMatchObject({ items: [], confidence: 0 });
    expect(parse('oke ya baik')).toMatchObject({ items: [], confidence: 0 });
  });

  test('invoice auto deterministik via now injeksi', () => {
    const r = parse('sabun 2 harga 5000');
    expect(r.invoice).toBe('INV-20260808-000');
    expect(r.customer).toBe('Walk-in');
    expect(r.country).toBe('Indonesia');
    expect(r.source).toBe('local-parser');
  });
});

describe('Blok C — known quirks (baseline = replikasi Dart persis)', () => {
  test('C1 ratus+puluh salah (bug Dart yang direplikasi)', () => {
    expect(parseNumberRun(['seratus', 'lima', 'puluh'])).toBe(1050);          // benar: 150
    expect(parseNumberRun(['seratus', 'dua', 'puluh', 'lima', 'ribu'])).toBe(1025000); // benar: 125000
    expect(parseNumberRun(['dua', 'ratus', 'lima', 'puluh', 'ribu'])).toBe(2050000);   // benar: 250000
    expect(parseNumberRun(['satu', 'juta', 'dua', 'ratus', 'lima', 'puluh', 'ribu'])).toBe(3050000); // benar: 1250000
  });

  test('C2 dua pemisah ribuan merusak token (bug Dart yang direplikasi)', () => {
    expect(items('sabun 2 harga Rp 1.250.000')).toEqual([
      { product: 'Sabun', qty: 2, unit_price: 0 },
      { product: '1250.000', qty: 1, unit_price: 0 },
    ]);
  });

  test('C3 qty telanjang >100 hilang diam-diam (bug Dart yang direplikasi)', () => {
    expect(items('beras 150 harga 12000')).toEqual([
      { product: 'Beras', qty: 1, unit_price: 12000 },
    ]);
    // workaround yang sudah jalan: kata kunci qty
    expect(items('beras sebanyak 150 harga 12000')).toEqual([
      { product: 'Beras', qty: 150, unit_price: 12000 },
    ]);
  });

  test('C4 customer serakah 2 kata memakan kata produk', () => {
    const r = parse('pelanggan budi sabun 2 harga 5000');
    expect(r.customer).toBe('Budi Sabun');
    expect(r.items).toEqual([{ product: 'Item', qty: 2, unit_price: 5000 }]);
  });

  test('C5 desimal koma jadi pemisah item', () => {
    expect(items('sabun 2 harga 8500,50')).toEqual([
      { product: 'Sabun', qty: 2, unit_price: 8500 },
      { product: 'Item', qty: 50, unit_price: 0 },
    ]);
  });

  test('C6 invoice tanpa digit bocor jadi nama produk', () => {
    const r = parse('invoice abc sabun 2 harga 5000');
    expect(r.invoice).toBe('INV-20260808-000'); // auto
    expect(r.items).toEqual([{ product: 'Abc Sabun', qty: 2, unit_price: 5000 }]);
  });

  test('C7 angka nyasar di depan mengunci qty', () => {
    expect(items('total 3 barang sabun 2 harga 5000')).toEqual([
      { product: 'Sabun', qty: 3, unit_price: 5000 },
    ]);
  });

  test('C8 masing-masing tidak memecah (dan datang sebelum angka)', () => {
    expect(items('sabun dan pensil masing masing 2 harga 5000')).toEqual([
      { product: 'Sabun Pensil', qty: 2, unit_price: 5000 },
    ]);
  });

  test('C9 omong kosong tetap jadi item (tanpa guard nama produk)', () => {
    const r = parse('halo apa kabar');
    expect(r.items).toEqual([{ product: 'Halo Apa Kabar', qty: 1, unit_price: 0 }]);
    expect(r.confidence).toBe(0.6);
  });
});
