import 'package:flutter/material.dart';

/// Maps the 18-icon stroke set used in the React app to Material icons.
/// React equivalent: frontend/src/ui/Icon.jsx
/// For pixel-perfect parity later, swap individual entries with flutter_svg
/// custom assets in assets/icons/.
class FortunasIcons {
  static const Map<String, IconData> _map = {
    'mic':         Icons.mic_outlined,
    'micFilled':   Icons.mic,
    'plus':        Icons.add,
    'arrowRight':  Icons.arrow_forward,
    'arrowLeft':   Icons.arrow_back,
    'sparkle':     Icons.auto_awesome,
    'check':       Icons.check,
    'chevron':     Icons.chevron_right,
    'close':       Icons.close,
    'home':        Icons.home_outlined,
    'chat':        Icons.chat_bubble_outline,
    'chart':       Icons.bar_chart,
    'user':        Icons.person_outline,
    'waveform':    Icons.graphic_eq,
    'bolt':        Icons.bolt,
    'coin':        Icons.monetization_on_outlined,
    'bag':         Icons.shopping_bag_outlined,
    'clock':       Icons.access_time,
    'upload':      Icons.upload,
    'keyboard':    Icons.keyboard_outlined,
    'edit':        Icons.edit_outlined,
    'trash':       Icons.delete_outline,
    'history':     Icons.history,
    'flame':       Icons.local_fire_department_outlined,
  };

  static IconData iconFor(String name) {
    return _map[name] ?? Icons.help_outline;
  }
}

/// Helper widget mirroring the React `<Icon name="..." />` API.
class AppIcon extends StatelessWidget {
  final String name;
  final double size;
  final Color? color;

  const AppIcon({super.key, required this.name, this.size = 22, this.color});

  @override
  Widget build(BuildContext context) {
    return Icon(
      FortunasIcons.iconFor(name),
      size: size,
      color: color ?? IconTheme.of(context).color,
    );
  }
}
