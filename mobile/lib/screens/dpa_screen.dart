import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../dpa/dpa_controller.dart';
import '../dpa/dpa_state.dart';
import '../theme/tokens.dart';

/// DPA ("Pagar AI") screen — UMKM views & edits the rules that constrain the
/// AI. Read mode shows current rules; edit mode is a form with chip editors +
/// inline password confirm (PUT /umkm/dpa requires the login password).
class DpaScreen extends ConsumerStatefulWidget {
  const DpaScreen({super.key});
  @override
  ConsumerState<DpaScreen> createState() => _DpaScreenState();
}

class _DpaScreenState extends ConsumerState<DpaScreen> {
  final _formKey = GlobalKey<FormState>();
  final _rawText = TextEditingController();
  final _password = TextEditingController();
  final _allowedInput = TextEditingController();
  final _forbiddenInput = TextEditingController();

  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(dpaControllerProvider.notifier).load());
  }

  @override
  void dispose() {
    _rawText.dispose();
    _password.dispose();
    _allowedInput.dispose();
    _forbiddenInput.dispose();
    super.dispose();
  }

  void _enterEdit() {
    ref.read(dpaControllerProvider.notifier).startEdit();
    _rawText.text = ref.read(dpaControllerProvider).draftRawText;
    _password.clear();
    _allowedInput.clear();
    _forbiddenInput.clear();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    await ref.read(dpaControllerProvider.notifier).save(_password.text);
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(dpaControllerProvider);
    return Scaffold(
      backgroundColor: FortunasColors.bg,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _header(context),
            Expanded(child: _body(s)),
          ],
        ),
      ),
    );
  }

  Widget _header(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(6, 8, 18, 6),
      child: Row(
        children: [
          IconButton(
            key: const Key('dpa_back'),
            icon: const Icon(Icons.arrow_back),
            onPressed: () => context.pop(),
          ),
          Text('Pagar AI', style: display(fontSize: 20, letterSpacing: -0.4)),
        ],
      ),
    );
  }

  Widget _body(DpaState s) {
    if (s.loading) return const Center(child: CircularProgressIndicator());
    if (s.loadError != null) return _loadError(s.loadError!);
    if (s.editing) return _editForm(s);
    return _readMode(s);
  }

  Widget _loadError(String msg) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(msg,
                textAlign: TextAlign.center,
                style: body(color: FortunasColors.error)),
            const SizedBox(height: 12),
            ElevatedButton(
              key: const Key('dpa_retry'),
              onPressed: () => ref.read(dpaControllerProvider.notifier).load(),
              child: const Text('Coba lagi'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _readMode(DpaState s) {
    if (s.isEmpty) {
      return ListView(
        padding: const EdgeInsets.fromLTRB(18, 8, 18, 30),
        children: [
          _card(children: [
            Text('Belum ada Pagar AI',
                style: display(fontSize: 18, letterSpacing: -0.3)),
            const SizedBox(height: 8),
            Text(
              'Atur aturan agar AI selalu patuh kebijakan tokomu — '
              'misalnya melarang merekomendasikan produk tertentu.',
              style: body(fontSize: 12.5, color: FortunasColors.ink3),
            ),
            const SizedBox(height: 14),
            ElevatedButton(
              key: const Key('dpa_setup_cta'),
              onPressed: _enterEdit,
              child: const Text('Atur Pagar AI'),
            ),
          ]),
        ],
      );
    }
    final p = s.payload!;
    return ListView(
      padding: const EdgeInsets.fromLTRB(18, 8, 18, 30),
      children: [
        if (p.rawText.isNotEmpty) ...[
          _card(children: [
            Text('CATATAN', style: mono(fontSize: 10, color: FortunasColors.ink3)),
            const SizedBox(height: 8),
            Text(p.rawText, style: body(fontSize: 13)),
          ]),
          const SizedBox(height: 12),
        ],
        _card(children: [
          Text('BOLEH', style: mono(fontSize: 10, color: FortunasColors.ink3)),
          const SizedBox(height: 10),
          _chipsReadOnly(p.allowedRules, FortunasColors.lime),
        ]),
        const SizedBox(height: 12),
        _card(children: [
          Text('DILARANG', style: mono(fontSize: 10, color: FortunasColors.ink3)),
          const SizedBox(height: 10),
          _chipsReadOnly(p.forbiddenRules, FortunasColors.peach),
        ]),
        const SizedBox(height: 14),
        Text(
          'Versi ${p.version}'
          '${p.updatedAt != null ? ' · diperbarui ${p.updatedAt}' : ''}',
          style: mono(fontSize: 10, color: FortunasColors.ink3),
        ),
        const SizedBox(height: 14),
        ElevatedButton(
          key: const Key('dpa_edit_button'),
          onPressed: _enterEdit,
          child: const Text('Edit'),
        ),
      ],
    );
  }

  Widget _editForm(DpaState s) {
    return Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 8, 18, 30),
        children: [
          Text('Catatan kebijakan',
              style: body(fontSize: 12.5, weight: FontWeight.w600)),
          const SizedBox(height: 6),
          TextFormField(
            key: const Key('dpa_raw_text'),
            controller: _rawText,
            minLines: 2,
            maxLines: 5,
            decoration: const InputDecoration(
                hintText: 'mis. Tidak menjual produk tembakau.'),
            onChanged: (v) =>
                ref.read(dpaControllerProvider.notifier).setRawText(v),
          ),
          const SizedBox(height: 16),
          _chipEditor(
            label: 'Boleh',
            keyPrefix: 'allowed',
            inputCtrl: _allowedInput,
            rules: s.draftAllowed,
            onAdd: (v) => ref.read(dpaControllerProvider.notifier).addAllowed(v),
            onRemove: (i) =>
                ref.read(dpaControllerProvider.notifier).removeAllowed(i),
            chipColor: FortunasColors.lime,
          ),
          const SizedBox(height: 16),
          _chipEditor(
            label: 'Dilarang',
            keyPrefix: 'forbidden',
            inputCtrl: _forbiddenInput,
            rules: s.draftForbidden,
            onAdd: (v) =>
                ref.read(dpaControllerProvider.notifier).addForbidden(v),
            onRemove: (i) =>
                ref.read(dpaControllerProvider.notifier).removeForbidden(i),
            chipColor: FortunasColors.peach,
          ),
          const SizedBox(height: 16),
          TextFormField(
            key: const Key('dpa_password'),
            controller: _password,
            obscureText: true,
            decoration:
                const InputDecoration(labelText: 'Konfirmasi password'),
            validator: (v) =>
                (v == null || v.isEmpty) ? 'Password wajib diisi' : null,
          ),
          if (s.errorMessage != null) ...[
            const SizedBox(height: 8),
            Text(s.errorMessage!,
                style: body(fontSize: 12.5, color: FortunasColors.error)),
          ],
          const SizedBox(height: 16),
          ElevatedButton(
            key: const Key('dpa_save'),
            onPressed: s.submitting ? null : _save,
            child: s.submitting
                ? const SizedBox(
                    height: 18,
                    width: 18,
                    child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('Simpan'),
          ),
          const SizedBox(height: 6),
          OutlinedButton(
            key: const Key('dpa_cancel'),
            onPressed: s.submitting
                ? null
                : () => ref.read(dpaControllerProvider.notifier).cancelEdit(),
            child: const Text('Batal'),
          ),
        ],
      ),
    );
  }

  Widget _chipEditor({
    required String label,
    required String keyPrefix,
    required TextEditingController inputCtrl,
    required List<String> rules,
    required void Function(String) onAdd,
    required void Function(int) onRemove,
    required Color chipColor,
  }) {
    void add() {
      onAdd(inputCtrl.text);
      inputCtrl.clear();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: body(fontSize: 12.5, weight: FontWeight.w600)),
        const SizedBox(height: 6),
        Row(
          children: [
            Expanded(
              child: TextField(
                key: Key('dpa_${keyPrefix}_input'),
                controller: inputCtrl,
                decoration: const InputDecoration(hintText: 'Tambah aturan'),
                onSubmitted: (_) => add(),
              ),
            ),
            const SizedBox(width: 8),
            ElevatedButton(
              key: Key('dpa_${keyPrefix}_add'),
              onPressed: add,
              child: const Text('Tambah'),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (var i = 0; i < rules.length; i++)
              _EditableChip(
                label: rules[i],
                color: chipColor,
                onRemove: () => onRemove(i),
              ),
          ],
        ),
      ],
    );
  }

  Widget _chipsReadOnly(List<String> rules, Color color) {
    if (rules.isEmpty) {
      return Text('—', style: body(fontSize: 12.5, color: FortunasColors.ink3));
    }
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final r in rules)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(
              color: color,
              border: Border.all(color: FortunasColors.ink, width: 1.5),
              borderRadius: BorderRadius.circular(999),
            ),
            child: Text(r, style: body(fontSize: 12, weight: FontWeight.w600)),
          ),
      ],
    );
  }

  Widget _card({required List<Widget> children}) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 16),
      decoration: BoxDecoration(
        color: FortunasColors.surface,
        border: Border.all(color: FortunasColors.ink, width: 1.5),
        borderRadius: BorderRadius.circular(18),
        boxShadow: popShadow(offset: 2),
      ),
      child: Column(
          crossAxisAlignment: CrossAxisAlignment.start, children: children),
    );
  }
}

class _EditableChip extends StatelessWidget {
  final String label;
  final Color color;
  final VoidCallback onRemove;
  const _EditableChip(
      {required this.label, required this.color, required this.onRemove});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(10, 5, 6, 5),
      decoration: BoxDecoration(
        color: color,
        border: Border.all(color: FortunasColors.ink, width: 1.5),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label, style: body(fontSize: 12, weight: FontWeight.w600)),
          const SizedBox(width: 4),
          GestureDetector(
            key: Key('dpa_chip_remove_$label'),
            onTap: onRemove,
            child: const Icon(Icons.close, size: 14),
          ),
        ],
      ),
    );
  }
}
