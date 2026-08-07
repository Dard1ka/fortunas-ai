import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/screens/snap_payment_screen.dart';

void main() {
  const finish = 'https://fortunas.local/payment-done';

  test('cocok pada host+path yang sama, mengabaikan query Snap', () {
    expect(isSnapFinishUrl('$finish?order_id=ORD-1&transaction_status=settlement',
        finish: finish), isTrue);
    expect(isSnapFinishUrl(finish, finish: finish), isTrue);
    expect(isSnapFinishUrl('$finish/', finish: finish), isFalse); // path beda
  });

  test('tak cocok untuk halaman Snap / host lain', () {
    expect(isSnapFinishUrl('https://app.sandbox.midtrans.com/snap/v3/redirect/xyz',
        finish: finish), isFalse);
    expect(isSnapFinishUrl('https://evil.example/payment-done', finish: finish),
        isFalse); // host beda
    expect(isSnapFinishUrl('https://fortunas.local/other', finish: finish),
        isFalse); // path beda
  });

  test('url tak valid → false, tak melempar', () {
    expect(isSnapFinishUrl('::::', finish: finish), isFalse);
    expect(isSnapFinishUrl('', finish: finish), isFalse);
  });
}
