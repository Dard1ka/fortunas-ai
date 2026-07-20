import 'package:flutter/material.dart';

import '../theme/tokens.dart';

/// Field tanggal yang membuka kalender interaktif (showDatePicker).
///
/// Dipakai untuk tanggal lahir (customer, dan UMKM bila nanti ada). Nilai
/// disimpan sebagai ISO "YYYY-MM-DD" — format yang diminta backend — tetapi
/// ditampilkan ke user dalam format Indonesia ("10 Mei 1998").
///
/// [lastDate] default kemarin karena backend menolak tanggal lahir hari ini
/// atau di masa depan (schemas._validate_past_date).
class DateField extends StatelessWidget {
  final String label;
  final String value; // ISO "YYYY-MM-DD", boleh kosong
  final ValueChanged<String> onChanged;
  final DateTime? firstDate;
  final DateTime? lastDate;
  final Key? fieldKey;

  const DateField({
    super.key,
    required this.label,
    required this.value,
    required this.onChanged,
    this.firstDate,
    this.lastDate,
    this.fieldKey,
  });

  static const _months = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
  ];

  static String formatIndo(String iso) {
    final d = DateTime.tryParse(iso);
    if (d == null) return '';
    return '${d.day} ${_months[d.month - 1]} ${d.year}';
  }

  static String _toIso(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-'
      '${d.month.toString().padLeft(2, '0')}-'
      '${d.day.toString().padLeft(2, '0')}';

  Future<void> _pick(BuildContext context) async {
    final now = DateTime.now();
    final last = lastDate ?? now.subtract(const Duration(days: 1));
    final first = firstDate ?? DateTime(1900);
    final current = DateTime.tryParse(value);
    // Default ke 20 tahun lalu supaya user tidak scroll jauh dari tahun ini.
    var initial = current ?? DateTime(now.year - 20, now.month, now.day);
    if (initial.isAfter(last)) initial = last;
    if (initial.isBefore(first)) initial = first;

    final picked = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: first,
      lastDate: last,
      helpText: 'Pilih tanggal lahir',
      cancelText: 'Batal',
      confirmText: 'Pilih',
      fieldLabelText: 'Tanggal lahir',
      initialDatePickerMode: DatePickerMode.year, // mulai dari tahun: lebih cepat
      builder: (ctx, child) => Theme(
        data: Theme.of(ctx).copyWith(
          colorScheme: const ColorScheme.light(
            primary: FortunasColors.violet,
            onPrimary: Colors.white,
            onSurface: FortunasColors.ink,
          ),
        ),
        child: child!,
      ),
    );
    if (picked != null) onChanged(_toIso(picked));
  }

  @override
  Widget build(BuildContext context) {
    final hasValue = value.isNotEmpty;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: body(fontSize: 12, color: FortunasColors.ink3)),
        const SizedBox(height: 6),
        InkWell(
          key: fieldKey,
          onTap: () => _pick(context),
          borderRadius: BorderRadius.circular(FortunasRadius.md),
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
            decoration: BoxDecoration(
              color: FortunasColors.surface,
              border: Border.all(color: FortunasColors.ink, width: 1.5),
              borderRadius: BorderRadius.circular(FortunasRadius.md),
            ),
            child: Row(
              children: [
                const Icon(Icons.calendar_today_outlined,
                    size: 18, color: FortunasColors.ink3),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    hasValue ? formatIndo(value) : 'Pilih tanggal',
                    style: body(
                      fontSize: 14,
                      color: hasValue ? FortunasColors.ink : FortunasColors.ink4,
                      weight: hasValue ? FontWeight.w600 : FontWeight.w400,
                    ),
                  ),
                ),
                if (hasValue)
                  InkWell(
                    onTap: () => onChanged(''),
                    borderRadius: BorderRadius.circular(999),
                    child: const Padding(
                      padding: EdgeInsets.all(2),
                      child: Icon(Icons.close, size: 18, color: FortunasColors.ink4),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
