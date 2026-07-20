import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../api/models.dart';
import '../customer/customer_loyalty_controllers.dart';
import '../theme/tokens.dart';
import '../ui/screen_header.dart';

/// Customer Promo generator (REQUIREMENTS §6.5): spin wheel + promo hasil.
/// Backend memutuskan hasil spin (server-side weighted). Wheel di sini hanya
/// animasi yang BERHENTI pada segmen yang dikembalikan backend — bukan RNG klien.
class CustomerPromoScreen extends ConsumerStatefulWidget {
  final MembershipSummary membership;
  const CustomerPromoScreen({super.key, required this.membership});
  @override
  ConsumerState<CustomerPromoScreen> createState() => _CustomerPromoScreenState();
}

class _CustomerPromoScreenState extends ConsumerState<CustomerPromoScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _spin;
  double _angle = 0;
  bool _spinning = false;
  PromoInstance? _wonPromo;

  // Segmen tampilan wheel (nilai diskon). Urutan visual tetap; hasil dari server
  // dipetakan ke indeks segmen ini.
  static const _segments = [100000, 50000, 25000, 10000, 25000, 10000];

  @override
  void initState() {
    super.initState();
    _spin = AnimationController(vsync: this, duration: const Duration(seconds: 4));
  }

  @override
  void dispose() {
    _spin.dispose();
    super.dispose();
  }

  Future<void> _onSpin() async {
    if (_spinning) return;
    setState(() {
      _spinning = true;
      _wonPromo = null;
    });
    final resp = await ref
        .read(customerPromoControllerProvider.notifier)
        .generate(widget.membership.tenantId);
    if (resp == null) {
      setState(() => _spinning = false);
      return; // error ditampilkan via watch di build
    }
    // Pilih indeks segmen yang cocok dengan discount hasil server.
    final amount = resp.spinResult.discountAmount;
    var idx = _segments.indexOf(amount);
    if (idx < 0) idx = 0;
    final seg = 2 * math.pi / _segments.length;
    // 5 putaran penuh + berhenti dengan pointer (atas) di tengah segmen idx.
    final target = 5 * 2 * math.pi + (2 * math.pi - (idx * seg + seg / 2)) - math.pi / 2;
    final begin = _angle % (2 * math.pi);
    _spin.reset();
    final anim = Tween<double>(begin: begin, end: target)
        .chain(CurveTween(curve: Curves.easeOutCubic))
        .animate(_spin);
    void tick() => setState(() => _angle = anim.value);
    anim.addListener(tick);
    await _spin.forward();
    anim.removeListener(tick);
    setState(() {
      _spinning = false;
      _wonPromo = resp.promo;
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(customerPromoControllerProvider);
    return Scaffold(
      backgroundColor: FortunasColors.bg,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 8, 18, 32),
          children: [
            ScreenHeader(subtitle: widget.membership.tenantName),
            const SizedBox(height: 8),
            Text('Putar & Menangkan Promo',
                style: display(fontSize: 22, letterSpacing: -0.4)),
            const SizedBox(height: 4),
            Text('Tukar poin jadi voucher diskon di ${widget.membership.tenantName}.',
                style: body(fontSize: 12.5, color: FortunasColors.ink3)),
            const SizedBox(height: 24),
            Center(child: _wheel()),
            const SizedBox(height: 24),
            if (_wonPromo != null)
              _wonCard(_wonPromo!)
            else
              ElevatedButton(
                onPressed: (_spinning || state.generating) ? null : _onSpin,
                style: ElevatedButton.styleFrom(
                  backgroundColor: FortunasColors.violet,
                  foregroundColor: Colors.white,
                  minimumSize: const Size.fromHeight(52),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(FortunasRadius.lg),
                    side: const BorderSide(color: FortunasColors.ink, width: 1.5),
                  ),
                ),
                child: Text(_spinning ? 'Memutar…' : 'PUTAR SEKARANG',
                    style: body(fontSize: 15, weight: FontWeight.w800, color: Colors.white)),
              ),
            if (state.errorMessage != null && _wonPromo == null) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: FortunasColors.peachSoft,
                  border: Border.all(color: FortunasColors.ink, width: 1.5),
                  borderRadius: BorderRadius.circular(FortunasRadius.lg),
                ),
                child: Text(state.errorMessage!,
                    style: body(fontSize: 12.5, color: FortunasColors.ink)),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _wheel() {
    return SizedBox(
      width: 260,
      height: 280,
      child: Stack(alignment: Alignment.topCenter, children: [
        Padding(
          padding: const EdgeInsets.only(top: 20),
          child: Transform.rotate(
            angle: _angle,
            child: CustomPaint(
              size: const Size(240, 240),
              painter: _WheelPainter(_segments),
            ),
          ),
        ),
        // Pointer (segitiga) di atas.
        Positioned(
          top: 0,
          child: CustomPaint(size: const Size(28, 22), painter: _PointerPainter()),
        ),
        // Hub tengah.
        Positioned(
          top: 20 + 120 - 22,
          child: Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: FortunasColors.surface,
              shape: BoxShape.circle,
              border: Border.all(color: FortunasColors.ink, width: 1.5),
              boxShadow: popShadow(offset: 2),
            ),
            child: const Icon(Icons.star, size: 22, color: FortunasColors.violet),
          ),
        ),
      ]),
    );
  }

  Widget _wonCard(PromoInstance p) => Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: FortunasColors.lime,
          border: Border.all(color: FortunasColors.ink, width: 1.5),
          borderRadius: BorderRadius.circular(FortunasRadius.xl),
          boxShadow: popShadow(),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text('🎉 SELAMAT!', style: mono(fontSize: 11, color: FortunasColors.ink2)),
          const SizedBox(height: 6),
          Text(p.name, style: display(fontSize: 20, letterSpacing: -0.4)),
          if (p.targetProduct != null) ...[
            const SizedBox(height: 2),
            Text('Untuk produk favoritmu: ${p.targetProduct}',
                style: body(fontSize: 12, color: FortunasColors.ink2)),
          ],
          const SizedBox(height: 14),
          if (p.qrPayload != null)
            Center(
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: FortunasColors.ink, width: 1.5),
                ),
                child: QrImageView(
                    data: p.qrPayload!, version: QrVersions.auto, size: 150),
              ),
            ),
          const SizedBox(height: 12),
          Center(
            child: Text('Kode: ${p.code}',
                style: mono(fontSize: 13, color: FortunasColors.ink)),
          ),
          const SizedBox(height: 4),
          Center(
            child: Text('Tunjukkan QR/kode ini ke kasir · berlaku s/d ${p.expiresAt.split('T').first}',
                textAlign: TextAlign.center,
                style: body(fontSize: 11, color: FortunasColors.ink2)),
          ),
        ]),
      );
}

class _WheelPainter extends CustomPainter {
  final List<int> segments;
  _WheelPainter(this.segments);

  static const _colors = [
    FortunasColors.violet,
    FortunasColors.lime,
    FortunasColors.peach,
    FortunasColors.sky,
    FortunasColors.limeDeep,
    FortunasColors.violetSoft,
  ];

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final radius = size.width / 2;
    final seg = 2 * math.pi / segments.length;
    final border = Paint()
      ..color = FortunasColors.ink
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;

    for (var i = 0; i < segments.length; i++) {
      final start = i * seg - math.pi / 2;
      final paint = Paint()..color = _colors[i % _colors.length];
      canvas.drawArc(Rect.fromCircle(center: center, radius: radius), start, seg, true, paint);
      canvas.drawArc(Rect.fromCircle(center: center, radius: radius), start, seg, true, border);

      // Label diskon.
      final mid = start + seg / 2;
      final tp = TextPainter(
        text: TextSpan(
          text: 'Rp${(segments[i] / 1000).round()}rb',
          style: const TextStyle(
            fontFamily: 'SpaceGrotesk',
            fontSize: 13,
            fontWeight: FontWeight.w800,
            color: FortunasColors.ink,
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      final lr = radius * 0.62;
      final pos = Offset(
        center.dx + lr * math.cos(mid) - tp.width / 2,
        center.dy + lr * math.sin(mid) - tp.height / 2,
      );
      tp.paint(canvas, pos);
    }
    // Lingkaran luar tebal.
    canvas.drawCircle(center, radius, border..strokeWidth = 3);
  }

  @override
  bool shouldRepaint(covariant _WheelPainter oldDelegate) => false;
}

class _PointerPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final path = Path()
      ..moveTo(size.width / 2, size.height)
      ..lineTo(0, 0)
      ..lineTo(size.width, 0)
      ..close();
    canvas.drawPath(path, Paint()..color = FortunasColors.ink);
    canvas.drawPath(
        path,
        Paint()
          ..color = FortunasColors.violet
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
