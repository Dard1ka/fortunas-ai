import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

/// The rotated "F" tile — Fortunas brand mark.
/// React equivalent: frontend/src/ui/BrandMark.jsx
/// Renders the vector asset assets/icons/logo-mark.svg for pixel-perfect
/// parity with the design hand-off (artboard thumbnail SVG).
class BrandMark extends StatelessWidget {
  final double size;
  const BrandMark({super.key, this.size = 36});

  @override
  Widget build(BuildContext context) {
    return SvgPicture.asset(
      'assets/icons/logo-mark.svg',
      width: size,
      height: size,
      fit: BoxFit.contain,
    );
  }
}
