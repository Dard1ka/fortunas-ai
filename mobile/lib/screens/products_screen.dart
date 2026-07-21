import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../api/models.dart';
import '../products/product_controller.dart';
import '../theme/tokens.dart';
import '../ui/screen_header.dart';

/// Base URL backend — cermin dari api/client.dart (dipakai untuk URL gambar).
const _apiBase = String.fromEnvironment(
  'FORTUNAS_API',
  defaultValue: 'http://127.0.0.1:8000',
);

/// Kelola produk UMKM: daftar barang + tambah barang (gambar WAJIB).
/// Kode barang di-generate backend (2 huruf awal + urut, mis. ko-001).
class ProductsScreen extends ConsumerStatefulWidget {
  const ProductsScreen({super.key});
  @override
  ConsumerState<ProductsScreen> createState() => _ProductsScreenState();
}

class _ProductsScreenState extends ConsumerState<ProductsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback(
        (_) => ref.read(productControllerProvider.notifier).load());
  }

  Future<void> _openForm() async {
    final created = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const _ProductFormSheet(),
    );
    if (created == true && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Produk berhasil ditambahkan.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(productControllerProvider);
    return Scaffold(
      backgroundColor: FortunasColors.bg,
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () => ref.read(productControllerProvider.notifier).load(),
          child: ListView(
            padding: const EdgeInsets.fromLTRB(18, 8, 18, 100),
            children: [
              const ScreenHeader(subtitle: 'Kelola Produk'),
              Align(
                alignment: Alignment.centerLeft,
                child: TextButton.icon(
                  key: const Key('products_back'),
                  onPressed: () => context.pop(),
                  icon: const Icon(Icons.arrow_back, size: 18),
                  style: TextButton.styleFrom(
                    foregroundColor: FortunasColors.ink,
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                  ),
                  label: Text('Kembali',
                      style: body(
                          fontSize: 13,
                          weight: FontWeight.w600,
                          color: FortunasColors.ink)),
                ),
              ),
              const SizedBox(height: 4),
              Text('Produk Saya', style: display(fontSize: 22, letterSpacing: -0.4)),
              const SizedBox(height: 4),
              Text('Kode barang dibuat otomatis dari 2 huruf awal nama.',
                  style: body(fontSize: 12.5, color: FortunasColors.ink3)),
              const SizedBox(height: 16),
              if (state.needsOnboarding && !state.loading) _mandatoryBanner(),
              if (state.loading && state.products.isEmpty)
                const Padding(
                    padding: EdgeInsets.symmetric(vertical: 48),
                    child: Center(child: CircularProgressIndicator()))
              else if (state.products.isEmpty && !state.needsOnboarding)
                Text('Belum ada produk.',
                    style: body(fontSize: 12.5, color: FortunasColors.ink3))
              else
                ...state.products.map((p) => _ProductTile(
                      product: p,
                      onDelete: () =>
                          ref.read(productControllerProvider.notifier).remove(p.id),
                    )),
              if (state.errorMessage != null) ...[
                const SizedBox(height: 12),
                Text(state.errorMessage!,
                    style: body(fontSize: 12.5, color: FortunasColors.error)),
              ],
            ],
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        key: const Key('product_add_fab'),
        onPressed: _openForm,
        backgroundColor: FortunasColors.violet,
        foregroundColor: Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(FortunasRadius.lg),
          side: const BorderSide(color: FortunasColors.ink, width: 1.5),
        ),
        icon: const Icon(Icons.add),
        label: Text('Tambah Produk',
            style: body(fontSize: 13.5, weight: FontWeight.w700, color: Colors.white)),
      ),
    );
  }

  Widget _mandatoryBanner() => Container(
        margin: const EdgeInsets.only(bottom: 14),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: FortunasColors.peachSoft,
          border: Border.all(color: FortunasColors.ink, width: 1.5),
          borderRadius: BorderRadius.circular(FortunasRadius.lg),
          boxShadow: popShadow(offset: 2),
        ),
        child: Row(children: [
          const Icon(Icons.info_outline, color: FortunasColors.ink),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              'Kamu wajib menambahkan minimal 1 produk sebelum mulai berjualan.',
              style: body(fontSize: 12.5, color: FortunasColors.ink),
            ),
          ),
        ]),
      );
}

class _ProductTile extends StatelessWidget {
  final ProductItem product;
  final VoidCallback onDelete;
  const _ProductTile({required this.product, required this.onDelete});

  (String, Color) _stockBadge() {
    final s = product.stock;
    if (s == null) return ('Tak dilacak', FortunasColors.surfaceSoft);
    if (s == 0) return ('Habis', FortunasColors.error);
    if (s <= 5) return ('Menipis', FortunasColors.warning);
    return ('Stok: $s', FortunasColors.lime);
  }

  @override
  Widget build(BuildContext context) {
    final imgUrl = product.imageUrl.isEmpty ? null : '$_apiBase${product.imageUrl}';
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: FortunasColors.surface,
        border: Border.all(color: FortunasColors.ink, width: 1.5),
        borderRadius: BorderRadius.circular(FortunasRadius.lg),
        boxShadow: popShadow(offset: 2),
      ),
      child: Row(children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(10),
          child: Container(
            width: 56,
            height: 56,
            color: FortunasColors.surfaceSoft,
            child: imgUrl == null
                ? const Icon(Icons.image_not_supported, color: FortunasColors.ink4)
                : Image.network(imgUrl, fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) =>
                        const Icon(Icons.broken_image, color: FortunasColors.ink4)),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(product.name,
                style: body(fontSize: 14, weight: FontWeight.w700, color: FortunasColors.ink)),
            const SizedBox(height: 3),
            Wrap(spacing: 6, runSpacing: 4, children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: FortunasColors.lime,
                  border: Border.all(color: FortunasColors.ink, width: 1),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(product.stockCode.toUpperCase(),
                    style: mono(fontSize: 10, color: FortunasColors.ink)),
              ),
              Builder(builder: (_) {
                final (label, bg) = _stockBadge();
                return Container(
                  key: const Key('product_stock_badge'),
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: bg,
                    border: Border.all(color: FortunasColors.ink, width: 1),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(label,
                      style: body(
                          fontSize: 10, weight: FontWeight.w600, color: FortunasColors.ink)),
                );
              }),
            ]),
            if (product.description.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(product.description,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: body(fontSize: 11.5, color: FortunasColors.ink3)),
            ],
          ]),
        ),
        IconButton(
          onPressed: onDelete,
          icon: const Icon(Icons.delete_outline, color: FortunasColors.ink4),
          tooltip: 'Hapus produk',
        ),
      ]),
    );
  }
}

/// Form tambah produk: nama + deskripsi + gambar (wajib).
class _ProductFormSheet extends ConsumerStatefulWidget {
  const _ProductFormSheet();
  @override
  ConsumerState<_ProductFormSheet> createState() => _ProductFormSheetState();
}

class _ProductFormSheetState extends ConsumerState<_ProductFormSheet> {
  final _name = TextEditingController();
  final _desc = TextEditingController();
  final _stock = TextEditingController();
  Uint8List? _imageBytes;
  String _imageName = '';
  String? _localError;

  @override
  void dispose() {
    _name.dispose();
    _desc.dispose();
    _stock.dispose();
    super.dispose();
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final file = await picker.pickImage(source: ImageSource.gallery, imageQuality: 85);
    if (file == null) return;
    final bytes = await file.readAsBytes();
    setState(() {
      _imageBytes = bytes;
      _imageName = file.name;
      _localError = null;
    });
  }

  Future<void> _submit() async {
    if (_name.text.trim().isEmpty) {
      setState(() => _localError = 'Nama produk wajib diisi.');
      return;
    }
    if (_imageBytes == null) {
      setState(() => _localError = 'Gambar produk wajib dipilih.');
      return;
    }
    setState(() => _localError = null);
    final stockText = _stock.text.trim();
    final stock = stockText.isEmpty ? null : int.tryParse(stockText);
    final ok = await ref.read(productControllerProvider.notifier).create(
          name: _name.text.trim(),
          description: _desc.text.trim(),
          imageBytes: _imageBytes!,
          imageFilename: _imageName.isEmpty ? 'produk.jpg' : _imageName,
          stock: stock,
        );
    if (ok && mounted) Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(productControllerProvider);
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;
    return Padding(
      padding: EdgeInsets.only(bottom: bottomInset),
      child: Container(
        decoration: const BoxDecoration(
          color: FortunasColors.bg,
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          border: Border(top: BorderSide(color: FortunasColors.ink, width: 1.5)),
        ),
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 24),
        child: SingleChildScrollView(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Container(
              width: 44,
              height: 4,
              decoration: BoxDecoration(
                color: FortunasColors.ink4,
                borderRadius: BorderRadius.circular(999),
              ),
            ),
            const SizedBox(height: 16),
            Align(
              alignment: Alignment.centerLeft,
              child: Text('Tambah Produk', style: display(fontSize: 20, letterSpacing: -0.4)),
            ),
            const SizedBox(height: 4),
            Align(
              alignment: Alignment.centerLeft,
              child: Text('Kode barang otomatis dari 2 huruf awal nama.',
                  style: body(fontSize: 12, color: FortunasColors.ink3)),
            ),
            const SizedBox(height: 16),
            TextField(
              key: const Key('product_name'),
              controller: _name,
              decoration: const InputDecoration(labelText: 'Nama produk *'),
            ),
            const SizedBox(height: 12),
            TextField(
              key: const Key('product_desc'),
              controller: _desc,
              maxLines: 3,
              maxLength: 1000, // sama dengan batas backend; counter tampil di UI
              decoration: const InputDecoration(labelText: 'Deskripsi'),
            ),
            const SizedBox(height: 12),
            TextField(
              key: const Key('product_stock'),
              controller: _stock,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Stok (opsional)',
                helperText: 'Kosongkan bila stok tidak dilacak.',
              ),
            ),
            const SizedBox(height: 16),
            _imagePickerBox(),
            if (_localError != null) ...[
              const SizedBox(height: 8),
              Align(
                alignment: Alignment.centerLeft,
                child: Text(_localError!,
                    style: body(fontSize: 12.5, color: FortunasColors.error)),
              ),
            ],
            if (state.errorMessage != null) ...[
              const SizedBox(height: 8),
              Align(
                alignment: Alignment.centerLeft,
                child: Text(state.errorMessage!,
                    style: body(fontSize: 12.5, color: FortunasColors.error)),
              ),
            ],
            const SizedBox(height: 18),
            ElevatedButton(
              key: const Key('product_submit'),
              onPressed: state.submitting ? null : _submit,
              style: ElevatedButton.styleFrom(
                backgroundColor: FortunasColors.violet,
                foregroundColor: Colors.white,
                minimumSize: const Size.fromHeight(50),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(FortunasRadius.lg),
                  side: const BorderSide(color: FortunasColors.ink, width: 1.5),
                ),
              ),
              child: Text(state.submitting ? 'Menyimpan…' : 'SIMPAN PRODUK',
                  style: body(fontSize: 14, weight: FontWeight.w800, color: Colors.white)),
            ),
          ]),
        ),
      ),
    );
  }

  Widget _imagePickerBox() {
    return InkWell(
      key: const Key('product_pick_image'),
      onTap: _pickImage,
      borderRadius: BorderRadius.circular(FortunasRadius.lg),
      child: Container(
        height: 120,
        width: double.infinity,
        decoration: BoxDecoration(
          color: FortunasColors.surface,
          border: Border.all(color: FortunasColors.ink, width: 1.5),
          borderRadius: BorderRadius.circular(FortunasRadius.lg),
        ),
        child: _imageBytes == null
            ? Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                const Icon(Icons.add_a_photo_outlined, color: FortunasColors.ink3),
                const SizedBox(height: 6),
                Text('Pilih gambar produk *',
                    style: body(fontSize: 12.5, color: FortunasColors.ink3)),
              ])
            : ClipRRect(
                borderRadius: BorderRadius.circular(FortunasRadius.lg - 2),
                child: Image.memory(_imageBytes!,
                    fit: BoxFit.cover, width: double.infinity),
              ),
      ),
    );
  }
}
