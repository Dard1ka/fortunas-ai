import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../api/models.dart';
import '../theme/tokens.dart';
import '../ui/icon_set.dart';

/// VoiceSuccess — check mark + ROI nudge.
/// React equivalent: frontend/src/voice/VoiceSuccess.jsx
class VoiceSuccess extends StatefulWidget {
  final ParsedTransaction? tx;
  const VoiceSuccess({super.key, this.tx});

  @override
  State<VoiceSuccess> createState() => _VoiceSuccessState();
}

class _VoiceSuccessState extends State<VoiceSuccess>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pop;

  static final _rp = NumberFormat.currency(locale: 'id_ID', symbol: 'Rp ', decimalDigits: 0);

  @override
  void initState() {
    super.initState();
    _pop = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    )..forward();
  }

  @override
  void dispose() {
    _pop.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 20, 24, 80),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const SizedBox(height: 40),
          ScaleTransition(
            scale: Tween<double>(begin: 0.6, end: 1.0).animate(
              CurvedAnimation(parent: _pop, curve: Curves.elasticOut),
            ),
            child: Container(
              width: 96, height: 96,
              decoration: BoxDecoration(
                color: FortunasColors.lime,
                shape: BoxShape.circle,
                border: Border.all(color: FortunasColors.ink, width: 2.5),
                boxShadow: popShadow(offset: 4),
              ),
              child: const Center(child: Icon(Icons.check, size: 46, color: FortunasColors.ink)),
            ),
          ),
          const SizedBox(height: 18),
          Text(
            'Tersimpan!',
            style: display(fontSize: 24, letterSpacing: -0.4, height: 1.15),
          ),
          const SizedBox(height: 6),
          ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 280),
            child: Text(
              widget.tx != null
                  ? '${widget.tx!.invoice} · ${widget.tx!.itemCount} barang · ${_rp.format(widget.tx!.grandTotal)} sudah tercatat di Google Sheets dan BigQuery.'
                  : 'Transaksi tersimpan ke Google Sheets dan BigQuery.',
              textAlign: TextAlign.center,
              style: body(fontSize: 13.5, color: FortunasColors.ink3),
            ),
          ),
          const SizedBox(height: 22),
          ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 320),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: FortunasColors.violet,
                border: Border.all(color: FortunasColors.ink, width: 1.5),
                borderRadius: BorderRadius.circular(14),
                boxShadow: popShadow(offset: 2),
              ),
              child: Row(
                children: [
                  const AppIcon(name: 'bolt', size: 20, color: FortunasColors.lime),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '+18 detik dihemat',
                          style: display(fontSize: 13.5, weight: FontWeight.w600, color: Colors.white, letterSpacing: -0.2, height: 1.2),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'vs input manual via keyboard',
                          style: body(fontSize: 11, color: Color(0xC0FFFFFF)),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
