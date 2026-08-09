// Mark merek Fortunas. Sumber tunggal: /logo-mark.png — dihasilkan
// scripts/gen_brand_assets.py dari assets/brand/logo-mark-source.png.
// Logo tampil tegak apa adanya: tanpa tile, tanpa rotasi, tanpa bayangan
// (mark lama berupa huruf "F" CSS miring -4°; diganti agar logo di dalam
// app identik dengan favicon/ikon PWA).
export default function BrandMark({ size = 36 }) {
  return (
    <img
      src="/logo-mark.png"
      alt="Fortunas AI"
      width={size}
      height={size}
      draggable={false}
      style={{ display: 'block', objectFit: 'contain', flexShrink: 0 }}
    />
  );
}
