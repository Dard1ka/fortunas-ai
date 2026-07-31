import 'package:flutter/material.dart';

import '../theme/tokens.dart';

class QuickActionCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final Color iconBg;
  final VoidCallback onTap;
  const QuickActionCard({
    super.key,
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.iconBg,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(FortunasRadius.lg),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: FortunasColors.ink,
            border: Border.all(color: FortunasColors.ink, width: 1.5),
            borderRadius: BorderRadius.circular(FortunasRadius.lg),
            boxShadow: popShadow(offset: 3),
          ),
          child: Row(
            children: [
              Container(
                width: 40, height: 40,
                decoration: BoxDecoration(
                  color: iconBg,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: FortunasColors.ink, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(title,
                        style: display(
                          fontSize: 14, weight: FontWeight.w600,
                          color: Colors.white, letterSpacing: -0.3, height: 1.2,
                        )),
                    const SizedBox(height: 2),
                    Text(subtitle, style: body(fontSize: 11, color: const Color(0xB3FFFFFF))),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: Colors.white, size: 18),
            ],
          ),
        ),
      ),
    );
  }
}
