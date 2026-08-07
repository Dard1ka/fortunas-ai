// Satu sumber keputusan tier & rute phone-only untuk seluruh shell.
// Nilai dari spec R1a (jangan ubah tanpa update spec + test).
export const MEDIUM_MIN_WIDTH = 600;
export const EXPANDED_MIN_WIDTH = 1024;
export const MEDIUM_CONTENT_WIDTH = 720;
export const EXPANDED_CONTENT_WIDTH = 840;
export const PHONE_ONLY_FRAME_WIDTH = 430;
export const FORM_PANE_WIDTH = 420;
export const PHONE_ONLY_ROUTE_PREFIXES = ['/customer', '/order'];

export function tierForWidth(width) {
  if (width >= EXPANDED_MIN_WIDTH) return 'expanded';
  if (width >= MEDIUM_MIN_WIDTH) return 'medium';
  return 'compact';
}

export function isPhoneOnlyRoute(pathname) {
  return PHONE_ONLY_ROUTE_PREFIXES.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );
}
