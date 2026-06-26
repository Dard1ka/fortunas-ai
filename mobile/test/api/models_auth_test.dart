import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/models.dart';

void main() {
  test('AuthResponse.fromJson parses login/register payload', () {
    final r = AuthResponse.fromJson({
      'access_token': 'jwt.abc.def',
      'token_type': 'bearer',
      'tenant_id': 7,
      'tenant_name': 'Toko Budi',
      'table_prefix': 'toko_budi',
    });
    expect(r.accessToken, 'jwt.abc.def');
    expect(r.tokenType, 'bearer');
    expect(r.tenantId, 7);
    expect(r.tenantName, 'Toko Budi');
    expect(r.tablePrefix, 'toko_budi');
  });

  test('UmkmAccount.fromJson parses /auth/me incl business_profile', () {
    final a = UmkmAccount.fromJson({
      'email': 'budi@toko.id',
      'tenant_id': 7,
      'tenant_name': 'Toko Budi',
      'table_prefix': 'toko_budi',
      'business_profile': {'jenis': 'kelontong'},
    });
    expect(a.email, 'budi@toko.id');
    expect(a.tenantId, 7);
    expect(a.businessProfile['jenis'], 'kelontong');
  });

  test('UmkmAccount.fromJson tolerates missing business_profile', () {
    final a = UmkmAccount.fromJson({'email': 'x@y.id'});
    expect(a.businessProfile, isEmpty);
  });
}
