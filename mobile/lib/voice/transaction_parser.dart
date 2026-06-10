import '../api/models.dart';

/// Smart on-device parser that turns a free-form Indonesian voice transcript
/// into a [ParsedTransaction] with one or more [LineItem]s.
///
/// It intelligently distinguishes each product mentioned in a single
/// utterance, e.g.:
///
///   "Invoice INV-2024, sabun cuci qty 10 harga delapan ribu lima ratus,
///    minyak goreng 5 harga dua puluh ribu, beras dua karung enam puluh ribu"
///
///   → 3 line items, shared invoice INV-2024:
///       • Sabun Cuci   ×10  @ Rp 8.500
///       • Minyak Goreng ×5  @ Rp 20.000
///       • Beras         ×2  @ Rp 60.000
///
/// Handles:
///   • Indonesian number words (delapan ribu lima ratus → 8500)
///   • Item separation by conjunctions (dan / lalu / terus / kemudian) and
///     commas — without breaking field commas inside a single item
///   • qty keywords (qty / jumlah / sebanyak) and units (biji, karung, kg…)
///   • price keywords (harga / seharga / @ / per)
///   • invoice + customer extraction
class TransactionParser {
  // ── Vocabulary ────────────────────────────────────────────────
  static const _ones = {
    'nol': 0, 'kosong': 0,
    'satu': 1, 'se': 1,
    'dua': 2, 'tiga': 3, 'empat': 4, 'lima': 5,
    'enam': 6, 'tujuh': 7, 'delapan': 8, 'sembilan': 9,
  };

  static const _qtyKeywords = {
    'qty', 'jumlah', 'sebanyak', 'banyaknya', 'sejumlah', 'jml',
  };

  static const _priceKeywords = {
    'harga', 'seharga', 'harganya', '@', 'per',
  };

  static const _units = {
    'biji', 'buah', 'pcs', 'pc', 'pieces', 'pack', 'paket', 'bungkus',
    'karung', 'kg', 'kilogram', 'kilo', 'gram', 'gr', 'liter', 'ltr',
    'dus', 'box', 'lusin', 'unit', 'botol', 'kaleng', 'sachet', 'renteng',
    'ikat', 'butir', 'lembar', 'batang', 'potong', 'porsi', 'gelas', 'cup',
    'rim', 'roll', 'meter', 'm', 'ekor', 'tablet', 'strip',
  };

  /// Strong separators — split items even when only qty is known.
  static const _strongConj = {
    'dan', 'lalu', 'terus', 'kemudian', 'plus', 'ditambah', 'tambah',
    'sama', 'juga', 'serta',
  };

  /// Words that never form part of a product name (filler / preamble).
  static const _noise = {
    // commerce / structural
    'invoice', 'transaksi', 'catat', 'mencatat', 'tambah', 'beli', 'membeli',
    'pesan', 'pesanan', 'pesanannya', 'order', 'orderan', 'barang', 'barangnya',
    'barangnnya', 'item', 'produk', 'produknya', 'total', 'masing', 'masingmasing',
    // currency
    'rupiah', 'rp', 'idr',
    // conversational filler / preamble
    'baik', 'baiklah', 'oke', 'ok', 'okay', 'ya', 'yah', 'iya', 'sip', 'nah',
    'jadi', 'saya', 'aku', 'kami', 'konfirmasi', 'konfirmasikan', 'mengkonfirmasi',
    'untuk', 'buat', 'dengan', 'yang', 'itu', 'ini', 'sebuah', 'ada', 'adalah',
    'yaitu', 'terdiri', 'dari', 'atas', 'tolong', 'mau', 'mohon', 'nih', 'dong',
    'sih', 'kira', 'sekitar', 'kurang', 'lebih',
  };

  /// Parse a transcript into a multi-item [ParsedTransaction].
  static ParsedTransaction parse(String rawTranscript) {
    var text = ' ${rawTranscript.toLowerCase().trim()} ';

    // 1) Extract invoice (e.g. "invoice inv-2024" / "invoice 2024").
    String invoice = '';
    final invMatch = RegExp(r'invoice\s+([a-z]*[-\s]?\d[\w-]*)').firstMatch(text);
    if (invMatch != null) {
      invoice = invMatch.group(1)!.replaceAll(RegExp(r'\s+'), '').toUpperCase();
      if (!invoice.contains('-') && RegExp(r'^\d').hasMatch(invoice)) {
        invoice = 'INV-$invoice';
      }
      text = text.replaceRange(invMatch.start, invMatch.end, ' ');
    }

    // 2) Extract customer ("pelanggan budi" / "atas nama bu siti").
    String customer = '';
    final custMatch = RegExp(
      r'(?:pelanggan|atas\s+nama|pembeli|customer)\s+([a-z]+(?:\s+[a-z]+)?)',
    ).firstMatch(text);
    if (custMatch != null) {
      customer = _titleCase(custMatch.group(1)!.trim());
      text = text.replaceRange(custMatch.start, custMatch.end, ' ');
    }

    // 3) Tokenize + collapse number runs into NUM tokens.
    final tokens = _tokenize(text);

    // 4) Scan tokens building line items.
    final items = <LineItem>[];
    _ItemDraft cur = _ItemDraft();
    String? expecting; // 'qty' | 'price'

    void flush() {
      if (cur.hasContent) items.add(cur.build());
      cur = _ItemDraft();
      expecting = null;
    }

    for (int i = 0; i < tokens.length; i++) {
      final tok = tokens[i];
      if (tok.isQtyKw) {
        expecting = 'qty';
        continue;
      }
      if (tok.isPriceKw) {
        expecting = 'price';
        continue;
      }
      if (tok.isUnit) {
        // A unit follows its qty number, which we already captured. Skip.
        continue;
      }
      if (tok.isConj) {
        // Split into a new item when the current one already has a product
        // AND a number (qty or price) — UNLESS the next token is a field
        // keyword (qty/harga), which means the comma just separates fields
        // of the same item (e.g. "sabun cuci, qty 10, harga 8500").
        final next = (i + 1 < tokens.length) ? tokens[i + 1] : null;
        final nextIsFieldKw = next != null && (next.isQtyKw || next.isPriceKw);
        final canSplit = cur.product.isNotEmpty &&
            (cur.qtySeen || cur.priceSeen) &&
            !nextIsFieldKw;
        if (canSplit) flush();
        expecting = null;
        continue;
      }
      if (tok.isNum) {
        final v = tok.value!;
        if (expecting == 'qty') {
          cur.qty = v;
          cur.qtySeen = true;
        } else if (expecting == 'price') {
          cur.unitPrice = v;
          cur.priceSeen = true;
        } else if (!cur.qtySeen && v <= 100 && !cur.priceSeen) {
          cur.qty = v;
          cur.qtySeen = true;
        } else if (!cur.priceSeen) {
          cur.unitPrice = v;
          cur.priceSeen = true;
        } else if (!cur.qtySeen) {
          cur.qty = v;
          cur.qtySeen = true;
        }
        expecting = null;
        continue;
      }
      // Plain word → part of product name (unless noise).
      if (!_noise.contains(tok.word)) {
        // Auto-split: a new product word arriving after the current item
        // already has a number (qty/price) starts the NEXT item — handles
        // utterances without explicit separators, e.g.
        // "sabun cuci 10 harga 8500 minyak goreng 5 harga 20000".
        if (cur.product.isNotEmpty && (cur.qtySeen || cur.priceSeen)) {
          flush();
        }
        cur.productWords.add(tok.word!);
      }
    }
    flush();

    // 5) Defaults + invoice generation.
    if (invoice.isEmpty) invoice = _generateInvoice();
    if (customer.isEmpty) customer = 'Walk-in';

    // 6) Confidence heuristic.
    double confidence;
    if (items.isEmpty) {
      confidence = 0.0;
    } else {
      final complete =
          items.where((i) => i.qty > 0 && i.unitPrice > 0).length;
      confidence = complete == items.length ? 0.92 : 0.6;
    }

    return ParsedTransaction(
      invoice: invoice,
      customer: customer,
      country: 'Indonesia',
      items: items,
      confidence: confidence,
      source: 'local-parser',
    );
  }

  // ── Tokenizer ─────────────────────────────────────────────────
  static List<_Tok> _tokenize(String text) {
    // Normalize, in order:
    //  1) drop currency prefix glued/loose to a number ("rp8.500" → "8.500")
    //  2) join thousand groups ("8.500" / "8,500" → "8500")
    //  3) space out @ and turn ; , into item separators
    var t = text
        .replaceAll(RegExp(r'\b(?:rp|idr)\.?\s*'), ' ')
        .replaceAllMapped(
          RegExp(r'(\d)[.,](\d{3})'),
          (m) => '${m[1]}${m[2]}',
        )
        .replaceAll('@', ' @ ')
        .replaceAll(';', ' , ')
        .replaceAll(',', ' , ');

    final rawWords = t
        .split(RegExp(r'\s+'))
        .where((w) => w.isNotEmpty)
        .toList();

    final out = <_Tok>[];
    var i = 0;
    while (i < rawWords.length) {
      final w = rawWords[i];

      // Collapse a maximal run of number-words / digits into one NUM.
      if (_isNumberWord(w)) {
        final run = <String>[];
        while (i < rawWords.length && _isNumberWord(rawWords[i])) {
          run.add(rawWords[i]);
          i++;
        }
        out.add(_Tok.num(_parseNumberRun(run)));
        continue;
      }

      out.add(_Tok.word(w));
      i++;
    }
    return out;
  }

  static bool _isNumberWord(String w) {
    if (RegExp(r'^\d+$').hasMatch(w)) return true;
    return _ones.containsKey(w) ||
        const {
          'sepuluh', 'sebelas', 'belas', 'puluh', 'ratus', 'seratus',
          'ribu', 'seribu', 'juta', 'sejuta', 'miliar', 'milyar',
        }.contains(w);
  }

  /// Convert a run of Indonesian number-words (and/or digits) to an int.
  static int _parseNumberRun(List<String> toks) {
    int total = 0;
    int current = 0;
    for (final t in toks) {
      if (RegExp(r'^\d+$').hasMatch(t)) {
        current += int.parse(t);
        continue;
      }
      switch (t) {
        case 'sepuluh':
          current += 10;
          break;
        case 'sebelas':
          current += 11;
          break;
        case 'belas':
          current += 10; // preceding ones already added (e.g. dua belas = 12)
          break;
        case 'puluh':
          current = (current == 0 ? 1 : current) * 10;
          break;
        case 'seratus':
          current += 100;
          break;
        case 'ratus':
          current = (current == 0 ? 1 : current) * 100;
          break;
        case 'seribu':
          total += 1000;
          current = 0;
          break;
        case 'ribu':
          total += (current == 0 ? 1 : current) * 1000;
          current = 0;
          break;
        case 'sejuta':
          total += 1000000;
          current = 0;
          break;
        case 'juta':
          total += (current == 0 ? 1 : current) * 1000000;
          current = 0;
          break;
        case 'miliar':
        case 'milyar':
          total += (current == 0 ? 1 : current) * 1000000000;
          current = 0;
          break;
        default:
          final v = _ones[t];
          if (v != null) current += v;
      }
    }
    return total + current;
  }

  static String _titleCase(String s) => s
      .split(RegExp(r'\s+'))
      .where((w) => w.isNotEmpty)
      .map((w) => w[0].toUpperCase() + w.substring(1))
      .join(' ');

  static String _generateInvoice() {
    final now = DateTime.now();
    String two(int n) => n.toString().padLeft(2, '0');
    final seq = (now.millisecondsSinceEpoch % 1000).toString().padLeft(3, '0');
    return 'INV-${now.year}${two(now.month)}${two(now.day)}-$seq';
  }
}

// ── Internal helpers ────────────────────────────────────────────
class _ItemDraft {
  final List<String> productWords = [];
  int qty = 1;
  int unitPrice = 0;
  bool qtySeen = false;
  bool priceSeen = false;

  String get product => TransactionParser._titleCase(productWords.join(' '));
  bool get hasContent => productWords.isNotEmpty || qtySeen || priceSeen;

  LineItem build() => LineItem(
        product: product.isEmpty ? 'Item' : product,
        qty: qty < 1 ? 1 : qty,
        unitPrice: unitPrice,
      );
}

class _Tok {
  final String? word;
  final int? value;

  const _Tok.word(this.word) : value = null;
  const _Tok.num(this.value) : word = null;

  bool get isNum => value != null;
  bool get isQtyKw => word != null && TransactionParser._qtyKeywords.contains(word);
  bool get isPriceKw => word != null && TransactionParser._priceKeywords.contains(word);
  bool get isUnit => word != null && TransactionParser._units.contains(word);
  bool get isConj =>
      word != null && (word == ',' || TransactionParser._strongConj.contains(word));
  bool get isStrongConj =>
      word != null && TransactionParser._strongConj.contains(word);
}
