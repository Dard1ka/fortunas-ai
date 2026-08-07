import { tierForWidth, isPhoneOnlyRoute, PHONE_ONLY_ROUTE_PREFIXES, FORM_PANE_WIDTH } from './shell.js';

test('tier: batas 600/1024 (diskriminatif, band 1024-1223 = expanded)', () => {
  expect(tierForWidth(599)).toBe('compact');
  expect(tierForWidth(600)).toBe('medium');
  expect(tierForWidth(1023)).toBe('medium');
  expect(tierForWidth(1024)).toBe('expanded');
  expect(tierForWidth(1440)).toBe('expanded');
});

test('phone-only: exact-atau-slash; /orders (inbox UMKM) TIDAK match', () => {
  expect(isPhoneOnlyRoute('/order')).toBe(true);
  expect(isPhoneOnlyRoute('/order/status')).toBe(true);
  expect(isPhoneOnlyRoute('/orders')).toBe(false);
  expect(isPhoneOnlyRoute('/customer/qr')).toBe(true);
  expect(isPhoneOnlyRoute('/')).toBe(false);
});

test('daftar rute phone-only ter-pin (mekanisme, bukan konvensi)', () => {
  expect(PHONE_ONLY_ROUTE_PREFIXES).toEqual(['/customer', '/order']);
});

test('lebar form pane = konstanta bernama 420', () => {
  expect(FORM_PANE_WIDTH).toBe(420);
});
