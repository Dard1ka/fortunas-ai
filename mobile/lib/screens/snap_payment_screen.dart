import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

import '../theme/tokens.dart';

/// URL "selesai" yang dikonfigurasi di dashboard Midtrans (Finish/Unfinish/Error
/// redirect URL). Snap mengarahkan browser ke sini setelah pelanggan selesai —
/// dengan query param (`?order_id=…&status_code=…&transaction_status=…`) yang
/// SENGAJA diabaikan: status resmi datang dari webhook backend, bukan URL ini.
/// Override saat build: --dart-define=MIDTRANS_FINISH_URL=https://...
const kMidtransFinishUrl = String.fromEnvironment(
  'MIDTRANS_FINISH_URL',
  defaultValue: 'https://fortunas.local/payment-done',
);

/// True bila [url] adalah URL "selesai" Snap — cocok berdasarkan host + path
/// saja (query param Snap diabaikan). Pure & tak bergantung webview supaya
/// bisa diuji tanpa platform channel.
bool isSnapFinishUrl(String url, {String finish = kMidtransFinishUrl}) {
  final u = Uri.tryParse(url);
  final f = Uri.tryParse(finish);
  if (u == null || f == null) return false;
  return u.host == f.host && u.path == f.path;
}

/// Webview pembayaran Midtrans Snap. Me-load `redirectUrl` (halaman Snap dari
/// backend). Saat browser diarahkan ke [kMidtransFinishUrl] → `pop(true)`
/// (pelanggan menyelesaikan alur). Tombol kembali → `pop(false)` (batal/nanti).
///
/// Hasil pop TIDAK berarti "sudah lunas" — pemanggil WAJIB poll status ke
/// backend (lihat PublicOrderController.afterSnapReturn). Ini disengaja: satu-
/// satunya sumber kebenaran pembayaran adalah webhook Midtrans → backend.
class SnapPaymentScreen extends StatefulWidget {
  final String redirectUrl;
  const SnapPaymentScreen({super.key, required this.redirectUrl});

  @override
  State<SnapPaymentScreen> createState() => _SnapPaymentScreenState();
}

class _SnapPaymentScreenState extends State<SnapPaymentScreen> {
  late final WebViewController _controller;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(NavigationDelegate(
        onPageStarted: (_) {
          if (mounted) setState(() => _loading = true);
        },
        onPageFinished: (_) {
          if (mounted) setState(() => _loading = false);
        },
        onNavigationRequest: (req) {
          if (isSnapFinishUrl(req.url)) {
            Navigator.of(context).pop(true);
            return NavigationDecision.prevent;
          }
          return NavigationDecision.navigate;
        },
      ))
      ..loadRequest(Uri.parse(widget.redirectUrl));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FortunasColors.bg,
      appBar: AppBar(
        backgroundColor: FortunasColors.bg,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close, color: FortunasColors.ink),
          onPressed: () => Navigator.of(context).pop(false),
        ),
        title: Text('Pembayaran', style: display(fontSize: 18, letterSpacing: -0.3)),
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _controller),
          if (_loading) const Center(child: CircularProgressIndicator()),
        ],
      ),
    );
  }
}
