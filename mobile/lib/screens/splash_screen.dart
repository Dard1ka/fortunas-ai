import 'package:flutter/material.dart';

import '../theme/tokens.dart';
import '../ui/brand_mark.dart';

/// Shown while AuthController.bootstrap() resolves the stored token.
class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FortunasColors.bg,
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: const [
            BrandMark(size: 56),
            SizedBox(height: 24),
            SizedBox(
              width: 22,
              height: 22,
              child: CircularProgressIndicator(strokeWidth: 2.5),
            ),
          ],
        ),
      ),
    );
  }
}
