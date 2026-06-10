// Smoke test for the smart multi-item voice parser.
// Run: dart run tool/parser_check.dart
import 'package:fortunas_ai/voice/transaction_parser.dart';

void main() {
  final samples = <String>[
    // The exact failing utterance from the user
    'penghapus 10 dengan harga 100.000 dan pensil 2 dengan harga Rp20.000',
    // Preamble + items with qty only (NO prices), comma-separated
    'baik saya konfirmasi untuk barangnya ada sabun cuci 10, penghapus 2, pensil 5',
    // Preamble + items with qty AND price
    'baik saya konfirmasi pesanannya ada sabun cuci 10 dengan harga rp8.500 minyak goreng 5 dengan harga Rp20.000 lalu ada beras 2 kilo dengan harga Rp60.000',
    // Single item, fields separated by commas + Indonesian number words
    'Invoice INV-2024, sabun cuci qty 10 harga delapan ribu lima ratus',
    // Three items separated by commas/conjunctions, mixed number formats
    'sabun cuci qty 10 harga delapan ribu lima ratus, minyak goreng 5 harga dua puluh ribu, dan beras dua karung enam puluh ribu',
    // Conjunctions only, units, no explicit qty/price keywords
    'beli kopi sachet 12 seharga seribu lima ratus lalu gula 3 kg harga lima belas ribu',
    // Customer + invoice + 2 items
    'invoice 7781 atas nama Bu Siti, teh kotak 24 harga 4500 dan air mineral 12 harga 3000',
  ];

  for (final s in samples) {
    final tx = TransactionParser.parse(s);
    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    print('TRANSCRIPT: $s');
    print('INVOICE   : ${tx.invoice}   PELANGGAN: ${tx.customer}');
    print('ITEMS (${tx.itemCount}):');
    for (var i = 0; i < tx.items.length; i++) {
      final it = tx.items[i];
      print('  ${i + 1}. ${it.product}  ×${it.qty}  @ Rp ${it.unitPrice}  = Rp ${it.total}');
    }
    print('GRAND TOTAL: Rp ${tx.grandTotal}   (confidence ${tx.confidence})');
  }
}
