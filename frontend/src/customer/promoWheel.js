// Konstanta & pemetaan roda promo — dipisah dari komponen supaya bisa
// dipakai test tanpa melanggar react-refresh/only-export-components.
// 6 segmen visual (paritas Flutter; duplikasi 25rb/10rb kosmetik — default
// spin_wheel backend hanya 4 segmen berbobot).
export const SEGMENTS = [100000, 50000, 25000, 10000, 25000, 10000];
export const SEG_DEG = 360 / SEGMENTS.length;
export const SPIN_MS = 4000;

// Nilai di luar daftar segmen → segmen bernilai TERDEKAT (perbaikan atas bug
// indexOf Flutter yang mendarat di 100rb untuk nilai tak dikenal); kartu
// menang SELALU menampilkan angka server, roda hanya aproksimasi visual.
export function segmentIndexForAmount(amount) {
  const exact = SEGMENTS.indexOf(amount);
  if (exact >= 0) return exact;
  let best = 0;
  let bestDiff = Infinity;
  SEGMENTS.forEach((v, i) => {
    const d = Math.abs(v - amount);
    if (d < bestDiff) { bestDiff = d; best = i; }
  });
  return best;
}
