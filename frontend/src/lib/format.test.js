import { describe, expect, test } from 'vitest';
import { formatRupiah, parseIntOrNull } from './format.js';

describe('formatRupiah', () => {
  test('pemisah ribuan id-ID', () => {
    expect(formatRupiah(1250000)).toBe('Rp 1.250.000');
    expect(formatRupiah(8500)).toBe('Rp 8.500');
  });

  test('nol dan nilai kosong jatuh ke Rp 0', () => {
    expect(formatRupiah(0)).toBe('Rp 0');
    expect(formatRupiah(null)).toBe('Rp 0');
    expect(formatRupiah(undefined)).toBe('Rp 0');
    expect(formatRupiah('bukan angka')).toBe('Rp 0');
  });
});

describe('parseIntOrNull (tri-state: kosong = null, BUKAN 0)', () => {
  test('string kosong / spasi → null', () => {
    expect(parseIntOrNull('')).toBeNull();
    expect(parseIntOrNull('   ')).toBeNull();
    expect(parseIntOrNull(null)).toBeNull();
    expect(parseIntOrNull(undefined)).toBeNull();
  });

  test('non-angka → null (padanan int.tryParse Dart)', () => {
    expect(parseIntOrNull('abc')).toBeNull();
  });

  test('angka valid di-parse, dengan trim', () => {
    expect(parseIntOrNull('12')).toBe(12);
    expect(parseIntOrNull(' 7 ')).toBe(7);
    expect(parseIntOrNull('0')).toBe(0);
  });

  test('negatif diteruskan (validasi negatif urusan backend, paritas Flutter)', () => {
    expect(parseIntOrNull('-3')).toBe(-3);
  });
});
