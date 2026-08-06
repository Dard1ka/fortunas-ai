import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/ui/nav_spec.dart';

void main() {
  test('5 slot UMKM, tepat satu primary (mic FAB) yaitu voice', () {
    expect(kUmkmNavItems.length, 5);
    expect(kUmkmNavItems.where((i) => i.primary).length, 1);
    expect(kUmkmNavItems.firstWhere((i) => i.primary).id, 'voice');
  });

  test('urutan & path slot tidak berubah dari bottom nav lama', () {
    expect(kUmkmNavItems.map((i) => i.path).toList(),
        ['/', '/briefing', '/voice', '/history', '/me']);
    expect(kUmkmNavItems.map((i) => i.label).toList(),
        ['Tanya', 'Briefing', 'Voice', 'Riwayat', 'Saya']);
  });

  test('navItemIsActive: tab / juga memiliki /result', () {
    expect(navItemIsActive('/', '/'), isTrue);
    expect(navItemIsActive('/', '/result'), isTrue);
    expect(navItemIsActive('/', '/briefing'), isFalse);
  });

  test('navItemIsActive: path lain cocok persis', () {
    expect(navItemIsActive('/briefing', '/briefing'), isTrue);
    expect(navItemIsActive('/briefing', '/'), isFalse);
    expect(navItemIsActive('/me', '/me'), isTrue);
    expect(navItemIsActive('/history', '/me'), isFalse);
  });
}
