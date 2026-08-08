// Parser transaksi suara multi-item — port setia dari
// mobile/lib/voice/transaction_parser.dart (Wave C area E, ADR-0002).
// 100% lokal & sinkron: tanpa jaringan, tanpa token — transkrip Bahasa
// Indonesia bebas → { invoice, customer, items[], confidence }.
//
// Pipeline (urutan WAJIB dipertahankan):
//   1) lowercase + trim + bungkus spasi   2) ekstrak & buang invoice
//   3) ekstrak & buang customer           4) tokenize + gabung deret angka
//   5) scan token jadi line item          6) default invoice/customer
//   7) hitung confidence

// ── Kamus (disalin persis dari sumber Dart) ─────────────────────
const ONES = {
  nol: 0, kosong: 0,
  satu: 1, se: 1,
  dua: 2, tiga: 3, empat: 4, lima: 5,
  enam: 6, tujuh: 7, delapan: 8, sembilan: 9,
};

const SCALE_WORDS = new Set([
  'sepuluh', 'sebelas', 'belas', 'puluh', 'ratus', 'seratus',
  'ribu', 'seribu', 'juta', 'sejuta', 'miliar', 'milyar',
]);

const QTY_KEYWORDS = new Set(['qty', 'jumlah', 'sebanyak', 'banyaknya', 'sejumlah', 'jml']);

const PRICE_KEYWORDS = new Set(['harga', 'seharga', 'harganya', '@', 'per']);

const UNITS = new Set([
  'biji', 'buah', 'pcs', 'pc', 'pieces', 'pack', 'paket', 'bungkus',
  'karung', 'kg', 'kilogram', 'kilo', 'gram', 'gr', 'liter', 'ltr',
  'dus', 'box', 'lusin', 'unit', 'botol', 'kaleng', 'sachet', 'renteng',
  'ikat', 'butir', 'lembar', 'batang', 'potong', 'porsi', 'gelas', 'cup',
  'rim', 'roll', 'meter', 'm', 'ekor', 'tablet', 'strip',
]);

// Pemisah kuat — memecah item bahkan saat baru qty yang diketahui.
const STRONG_CONJ = new Set([
  'dan', 'lalu', 'terus', 'kemudian', 'plus', 'ditambah', 'tambah',
  'sama', 'juga', 'serta',
]);

// Kata yang tidak pernah jadi bagian nama produk. CATATAN: 'tambah' ada di
// STRONG_CONJ juga — cek konjungsi berjalan SEBELUM cabang kata/noise, jadi
// 'tambah' selalu berperilaku pemisah (paritas Dart).
const NOISE = new Set([
  // komersial / struktural
  'invoice', 'transaksi', 'catat', 'mencatat', 'tambah', 'beli', 'membeli',
  'pesan', 'pesanan', 'pesanannya', 'order', 'orderan', 'barang', 'barangnya',
  'barangnnya', 'item', 'produk', 'produknya', 'total', 'masing', 'masingmasing',
  // mata uang
  'rupiah', 'rp', 'idr',
  // filler percakapan / preambul
  'baik', 'baiklah', 'oke', 'ok', 'okay', 'ya', 'yah', 'iya', 'sip', 'nah',
  'jadi', 'saya', 'aku', 'kami', 'konfirmasi', 'konfirmasikan', 'mengkonfirmasi',
  'untuk', 'buat', 'dengan', 'yang', 'itu', 'ini', 'sebuah', 'ada', 'adalah',
  'yaitu', 'terdiri', 'dari', 'atas', 'tolong', 'mau', 'mohon', 'nih', 'dong',
  'sih', 'kira', 'sekitar', 'kurang', 'lebih',
]);

const DIGITS_RE = /^\d+$/;

const isNumberWord = (w) => DIGITS_RE.test(w) || w in ONES || SCALE_WORDS.has(w);

// Akumulator angka Indonesia. PERBAIKAN atas Dart (bug C1): slot RATUSAN
// dipisah dari slot puluhan/satuan supaya 'puluh' tidak mengalikan ratusan
// yang sudah masuk — 'seratus lima puluh' = 150 (Dart lama: 1050).
// Nilai kelompok berjalan = hundreds + current; skala besar (ribu/juta/
// miliar) mengalikan seluruh kelompok lalu mereset keduanya.
export function parseNumberRun(toks) {
  let total = 0;
  let hundreds = 0;
  let current = 0;
  const group = () => hundreds + current;
  const flushGroup = (factor) => {
    total += (group() === 0 ? 1 : group()) * factor;
    hundreds = 0;
    current = 0;
  };
  for (const t of toks) {
    if (DIGITS_RE.test(t)) { current += Number.parseInt(t, 10); continue; }
    switch (t) {
      case 'sepuluh': current += 10; break;
      case 'sebelas': current += 11; break;
      case 'belas': current += 10; break; // satuan sudah ditambah (dua belas = 12)
      case 'puluh': current = (current === 0 ? 1 : current) * 10; break;
      case 'seratus': hundreds += 100; break;
      case 'ratus': hundreds += (current === 0 ? 1 : current) * 100; current = 0; break;
      case 'seribu': total += 1000; hundreds = 0; current = 0; break;
      case 'ribu': flushGroup(1000); break;
      case 'sejuta': total += 1000000; hundreds = 0; current = 0; break;
      case 'juta': flushGroup(1000000); break;
      case 'miliar':
      case 'milyar': flushGroup(1000000000); break;
      default: {
        const v = ONES[t];
        if (v != null) current += v;
      }
    }
  }
  return total + hundreds + current;
}

const titleCase = (s) => s
  .split(/\s+/)
  .filter(Boolean)
  .map((w) => w[0].toUpperCase() + w.slice(1))
  .join(' ');

function generateInvoice(now) {
  const two = (n) => String(n).padStart(2, '0');
  const seq = String(now.getTime() % 1000).padStart(3, '0');
  return `INV-${now.getFullYear()}${two(now.getMonth() + 1)}${two(now.getDate())}-${seq}`;
}

// Tokenizer: normalisasi (rp/idr → spasi; gabung grup ribuan; '@'/';'/','
// dispasikan), split, lalu deret MAKSIMAL token angka dikolaps jadi SATU
// token NUM. PERBAIKAN atas Dart (bug C2): pemisah ribuan memakai lookahead
// /(\d)[.,](?=\d{3}\b)/g sehingga '1.250.000' tergabung PENUH → 1250000
// (regex Dart satu lintasan non-overlapping menyisakan '1250.000').
function tokenize(text) {
  const t = text
    .replace(/\b(?:rp|idr)\.?\s*/g, ' ')
    .replace(/(\d)[.,](?=\d{3}\b)/g, '$1')
    .replaceAll('@', ' @ ')
    .replaceAll(';', ' , ')
    .replaceAll(',', ' , ');

  const rawWords = t.split(/\s+/).filter(Boolean);

  const out = [];
  let i = 0;
  while (i < rawWords.length) {
    const w = rawWords[i];
    if (isNumberWord(w)) {
      const run = [];
      while (i < rawWords.length && isNumberWord(rawWords[i])) {
        run.push(rawWords[i]);
        i += 1;
      }
      out.push({ num: true, value: parseNumberRun(run) });
      continue;
    }
    out.push({ num: false, word: w });
    i += 1;
  }
  return out;
}

function newDraft() {
  return { productWords: [], qty: 1, unitPrice: 0, qtySeen: false, priceSeen: false };
}
const draftHasContent = (d) => d.productWords.length > 0 || d.qtySeen || d.priceSeen;
function buildItem(d) {
  const product = titleCase(d.productWords.join(' '));
  return {
    product: product === '' ? 'Item' : product,
    qty: d.qty < 1 ? 1 : d.qty,
    unit_price: d.unitPrice,
  };
}

/**
 * Parse transkrip Bahasa Indonesia → transaksi multi-item.
 * `now` injectable supaya invoice auto bisa dites deterministik.
 * Bentuk kembalian langsung siap /checkout/confirm (items snake_case).
 */
export function parseTransaction(rawTranscript, { now = new Date() } = {}) {
  let text = ` ${String(rawTranscript || '').toLowerCase().trim()} `;

  // 1) Invoice — wajib mengandung digit; tanpa '-' dan berawal digit → INV-.
  let invoice = '';
  const invMatch = text.match(/invoice\s+([a-z]*[-\s]?\d[\w-]*)/);
  if (invMatch) {
    invoice = invMatch[1].replace(/\s+/g, '').toUpperCase();
    if (!invoice.includes('-') && /^\d/.test(invoice)) invoice = `INV-${invoice}`;
    text = `${text.slice(0, invMatch.index)} ${text.slice(invMatch.index + invMatch[0].length)}`;
  }

  // 2) Customer — maksimal 2 kata, Title Case.
  let customer = '';
  const custMatch = text.match(/(?:pelanggan|atas\s+nama|pembeli|customer)\s+([a-z]+(?:\s+[a-z]+)?)/);
  if (custMatch) {
    customer = titleCase(custMatch[1].trim());
    text = `${text.slice(0, custMatch.index)} ${text.slice(custMatch.index + custMatch[0].length)}`;
  }

  // 3-4) Tokenize + scan.
  const tokens = tokenize(text);
  const items = [];
  let cur = newDraft();
  let expecting = null; // 'qty' | 'price' | null

  const flush = () => {
    if (draftHasContent(cur)) items.push(buildItem(cur));
    cur = newDraft();
    expecting = null;
  };

  for (let i = 0; i < tokens.length; i += 1) {
    const tok = tokens[i];
    const word = tok.num ? null : tok.word;

    if (word && QTY_KEYWORDS.has(word)) { expecting = 'qty'; continue; }
    if (word && PRICE_KEYWORDS.has(word)) { expecting = 'price'; continue; }
    if (word && UNITS.has(word)) continue; // satuan mengikuti qty yang sudah tertangkap

    if (word && (word === ',' || STRONG_CONJ.has(word))) {
      // Split hanya bila item berjalan sudah punya produk DAN angka —
      // KECUALI token berikutnya kata kunci field (koma antar-field:
      // "sabun cuci, qty 10, harga 8500" tetap SATU item).
      const next = i + 1 < tokens.length ? tokens[i + 1] : null;
      const nextIsFieldKw = next != null && !next.num
        && (QTY_KEYWORDS.has(next.word) || PRICE_KEYWORDS.has(next.word));
      const canSplit = cur.productWords.length > 0
        && (cur.qtySeen || cur.priceSeen)
        && !nextIsFieldKw;
      if (canSplit) flush();
      expecting = null;
      continue;
    }

    if (tok.num) {
      const v = tok.value;
      if (expecting === 'qty') {
        cur.qty = v; cur.qtySeen = true;
      } else if (expecting === 'price') {
        // PERBAIKAN atas Dart (bug C3): bila kata kunci harga akan MENIMPA
        // unit_price yang terisi dari angka telanjang dan qty belum terisi,
        // nilai lama dipindah ke qty alih-alih hilang diam-diam —
        // 'beras 150 harga 12000' → qty 150 @12000 (Dart lama: qty 1).
        if (cur.priceSeen && !cur.qtySeen) {
          cur.qty = cur.unitPrice;
          cur.qtySeen = true;
        }
        cur.unitPrice = v; cur.priceSeen = true;
      } else if (!cur.qtySeen && v <= 100 && !cur.priceSeen) {
        // ATURAN BISNIS: angka telanjang >100 dianggap harga, bukan qty.
        cur.qty = v; cur.qtySeen = true;
      } else if (!cur.priceSeen) {
        cur.unitPrice = v; cur.priceSeen = true;
      } else if (!cur.qtySeen) {
        cur.qty = v; cur.qtySeen = true;
      }
      expecting = null;
      continue;
    }

    // Kata biasa → bagian nama produk (kecuali noise; noise TIDAK mereset
    // expecting dan TIDAK memicu split — 'dengan harga' tetap bekerja).
    if (!NOISE.has(word)) {
      // Auto-split: kata produk baru saat item berjalan sudah punya produk
      // + angka → item berikutnya, tanpa pemisah eksplisit.
      if (cur.productWords.length > 0 && (cur.qtySeen || cur.priceSeen)) flush();
      cur.productWords.push(word);
    }
  }
  flush();

  // 5) Default.
  if (invoice === '') invoice = generateInvoice(now);
  if (customer === '') customer = 'Walk-in';

  // 6) Confidence: 0 tanpa item; 0.92 bila SEMUA item lengkap (qty>0 &
  // harga>0 — qty sudah di-clamp ≥1, jadi efektifnya semua berharga); 0.6 sisanya.
  let confidence;
  if (items.length === 0) {
    confidence = 0;
  } else {
    const complete = items.filter((it) => it.qty > 0 && it.unit_price > 0).length;
    confidence = complete === items.length ? 0.92 : 0.6;
  }

  return {
    invoice,
    customer,
    country: 'Indonesia',
    items,
    confidence,
    source: 'local-parser',
  };
}
