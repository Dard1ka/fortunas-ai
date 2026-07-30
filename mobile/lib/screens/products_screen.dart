import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../api/models.dart';
import '../products/category_controller.dart';
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
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(productControllerProvider.notifier).load();
      ref.read(categoryControllerProvider.notifier).load();
    });
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

  Future<void> _openCategories() async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const _CategorySheet(),
    );
  }

  Future<void> _autoCategorize() async {
    final n = await ref.read(productControllerProvider.notifier).autoCategorize();
    if (!mounted) return;
    // Kategori baru mungkin dibuat AI → segarkan daftar kategori juga.
    ref.read(categoryControllerProvider.notifier).load();
    final msg = n == null
        ? 'Gagal menjalankan auto-kategori. Coba lagi.'
        : n == 0
            ? 'Semua produk sudah punya kategori.'
            : 'AI mengelompokkan $n produk. Kamu tetap bisa mengubahnya.';
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(productControllerProvider);
    final categoryNames = {
      for (final c in ref.watch(categoryControllerProvider).categories) c.id: c.name,
    };
    final uncategorizedCount =
        state.products.where((p) => p.categoryId == null).length;
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
              Row(children: [
                Expanded(
                  child: Text('Produk Saya', style: display(fontSize: 22, letterSpacing: -0.4)),
                ),
                TextButton.icon(
                  key: const Key('products_manage_categories'),
                  onPressed: _openCategories,
                  icon: const Icon(Icons.sell_outlined, size: 16, color: FortunasColors.violet),
                  label: Text('Kategori',
                      style: body(
                          fontSize: 12, weight: FontWeight.w700, color: FortunasColors.violet)),
                ),
              ]),
              const SizedBox(height: 4),
              Text('Kode barang dibuat otomatis dari 2 huruf awal nama.',
                  style: body(fontSize: 12.5, color: FortunasColors.ink3)),
              const SizedBox(height: 16),
              if (!state.needsOnboarding && uncategorizedCount > 0) ...[
                _autoCatBanner(uncategorizedCount, state.submitting),
                const SizedBox(height: 12),
              ],
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
                      categoryName: p.categoryId == null ? null : categoryNames[p.categoryId],
                      onDelete: () =>
                          ref.read(productControllerProvider.notifier).remove(p.id),
                      onEditStock: () => _editStock(p),
                      onEditPrice: () => _editPrice(p),
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

  Future<void> _editStock(ProductItem p) async {
    final ctrl = TextEditingController(text: p.stock?.toString() ?? '');
    String? result;
    try {
      result = await showDialog<String?>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: Text('Stok ${p.name}'),
          content: TextField(
            key: const Key('edit_stock_field'),
            controller: ctrl,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: 'Jumlah stok',
              helperText: 'Kosongkan bila stok tidak dilacak.',
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Batal'),
            ),
            TextButton(
              key: const Key('edit_stock_save'),
              onPressed: () => Navigator.pop(ctx, ctrl.text.trim()),
              child: const Text('Simpan'),
            ),
          ],
        ),
      );
    } finally {
      // Deferred one frame ON PURPOSE: AlertDialog's pop-future resolves before
      // its exit transition finishes rebuilding the TextField, so a synchronous
      // ctrl.dispose() here crashes (ChangeNotifier used after dispose). Do not
      // "simplify" to a plain ctrl.dispose().
      WidgetsBinding.instance.addPostFrameCallback((_) => ctrl.dispose());
    }
    if (result == null) return; // Batal / dismiss: no-op
    final stock = result.isEmpty ? null : int.tryParse(result);
    await ref.read(productControllerProvider.notifier).setStock(p.id, stock);
  }

  Future<void> _editPrice(ProductItem p) async {
    final ctrl = TextEditingController(text: p.price?.toString() ?? '');
    String? result;
    try {
      result = await showDialog<String?>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: Text('Harga ${p.name}'),
          content: TextField(
            key: const Key('edit_price_field'),
            controller: ctrl,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: 'Harga jual',
              prefixText: 'Rp ',
              helperText: 'Kosongkan bila harga belum diset.',
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Batal'),
            ),
            TextButton(
              key: const Key('edit_price_save'),
              onPressed: () => Navigator.pop(ctx, ctrl.text.trim()),
              child: const Text('Simpan'),
            ),
          ],
        ),
      );
    } finally {
      // Sama seperti _editStock: dispose ditunda satu frame agar tidak crash.
      WidgetsBinding.instance.addPostFrameCallback((_) => ctrl.dispose());
    }
    if (result == null) return; // Batal / dismiss: no-op
    final price = result.isEmpty ? null : int.tryParse(result);
    await ref.read(productControllerProvider.notifier).setPrice(p.id, price);
  }

  Widget _autoCatBanner(int count, bool busy) => Container(
        key: const Key('auto_categorize_banner'),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: FortunasColors.violetSoft,
          border: Border.all(color: FortunasColors.violet, width: 1.5),
          borderRadius: BorderRadius.circular(FortunasRadius.lg),
          boxShadow: popShadow(offset: 2),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Icon(Icons.auto_awesome, size: 18, color: FortunasColors.violetDeep),
            const SizedBox(width: 8),
            Expanded(
              child: Text('$count produk belum berkategori',
                  style: body(
                      fontSize: 13.5,
                      weight: FontWeight.w700,
                      color: FortunasColors.violetDeep)),
            ),
          ]),
          const SizedBox(height: 4),
          Text('Biarkan AI mengelompokkannya otomatis. Kamu tetap bisa mengubah '
              'kategori tiap produk kapan saja.',
              style: body(fontSize: 12, color: FortunasColors.ink2)),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              key: const Key('auto_categorize_banner_btn'),
              onPressed: busy ? null : _autoCategorize,
              style: FilledButton.styleFrom(
                backgroundColor: FortunasColors.violet,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(FortunasRadius.md),
                  side: const BorderSide(color: FortunasColors.ink, width: 1.5),
                ),
              ),
              icon: busy
                  ? const SizedBox(
                      width: 16, height: 16,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.auto_awesome, size: 18),
              label: Text(busy ? 'Mengelompokkan…' : 'Kelompokkan dengan AI',
                  style: body(fontSize: 13, weight: FontWeight.w700, color: Colors.white)),
            ),
          ),
        ]),
      );

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
  final String? categoryName;
  final VoidCallback onDelete;
  final VoidCallback onEditStock;
  final VoidCallback onEditPrice;
  const _ProductTile(
      {required this.product,
      this.categoryName,
      required this.onDelete,
      required this.onEditStock,
      required this.onEditPrice});

  static String _rupiah(int n) {
    final s = n.toString();
    final buf = StringBuffer('Rp ');
    for (int i = 0; i < s.length; i++) {
      if (i > 0 && (s.length - i) % 3 == 0) buf.write('.');
      buf.write(s[i]);
    }
    return buf.toString();
  }

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
              Container(
                key: const Key('product_price_badge'),
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: product.price == null
                      ? FortunasColors.warning
                      : FortunasColors.limeDeep,
                  border: Border.all(color: FortunasColors.ink, width: 1),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                    product.price == null ? 'Harga belum diset' : _rupiah(product.price!),
                    style: body(
                        fontSize: 10, weight: FontWeight.w700, color: FortunasColors.ink)),
              ),
              if (categoryName != null)
                Container(
                  key: const Key('product_category_label'),
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: FortunasColors.violetSoft,
                    border: Border.all(color: FortunasColors.violet, width: 1),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Row(mainAxisSize: MainAxisSize.min, children: [
                    const Icon(Icons.local_offer,
                        size: 10, color: FortunasColors.violetDeep),
                    const SizedBox(width: 3),
                    Text(categoryName!,
                        style: body(
                            fontSize: 10,
                            weight: FontWeight.w700,
                            color: FortunasColors.violetDeep)),
                  ]),
                )
              else
                Container(
                  key: const Key('product_no_category_label'),
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: FortunasColors.surfaceSoft,
                    border: Border.all(color: FortunasColors.ink4, width: 1),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text('Tanpa kategori',
                      style: body(
                          fontSize: 10, weight: FontWeight.w600, color: FortunasColors.ink4)),
                ),
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
          key: const Key('product_edit_price'),
          onPressed: onEditPrice,
          icon: const Icon(Icons.sell_outlined, color: FortunasColors.ink4),
          tooltip: 'Ubah harga',
        ),
        IconButton(
          key: const Key('product_edit_stock'),
          onPressed: onEditStock,
          icon: const Icon(Icons.inventory_2_outlined, color: FortunasColors.ink4),
          tooltip: 'Ubah stok',
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
  final _price = TextEditingController();
  Uint8List? _imageBytes;
  String _imageName = '';
  String? _localError;
  int? _categoryId;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback(
        (_) => ref.read(categoryControllerProvider.notifier).load());
  }

  @override
  void dispose() {
    _name.dispose();
    _desc.dispose();
    _stock.dispose();
    _price.dispose();
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
    final priceText = _price.text.trim();
    final price = priceText.isEmpty ? null : int.tryParse(priceText);
    final ok = await ref.read(productControllerProvider.notifier).create(
          name: _name.text.trim(),
          description: _desc.text.trim(),
          imageBytes: _imageBytes!,
          imageFilename: _imageName.isEmpty ? 'produk.jpg' : _imageName,
          stock: stock,
          price: price,
          categoryId: _categoryId,
        );
    if (ok && mounted) Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(productControllerProvider);
    final cats = ref.watch(categoryControllerProvider).categories;
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
            const SizedBox(height: 12),
            TextField(
              key: const Key('product_price'),
              controller: _price,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Harga (Rp)',
                prefixText: 'Rp ',
                helperText: 'Wajib bila mau terima pesanan online.',
              ),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<int?>(
              key: const Key('product_category_dropdown'),
              value: _categoryId,
              decoration: const InputDecoration(labelText: 'Kategori (opsional)'),
              items: [
                const DropdownMenuItem<int?>(value: null, child: Text('Tanpa kategori')),
                ...cats.map((c) => DropdownMenuItem<int?>(value: c.id, child: Text(c.name))),
              ],
              onChanged: (v) => setState(() => _categoryId = v),
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

/// Sheet kelola kategori: tambah, daftar, dan hapus (dengan dialog konfirmasi
/// yang menyebut jumlah produk yang akan jadi tanpa kategori).
class _CategorySheet extends ConsumerStatefulWidget {
  const _CategorySheet();
  @override
  ConsumerState<_CategorySheet> createState() => _CategorySheetState();
}

class _CategorySheetState extends ConsumerState<_CategorySheet> {
  final _name = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback(
        (_) => ref.read(categoryControllerProvider.notifier).load());
  }

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  Future<void> _add() async {
    final name = _name.text.trim();
    if (name.isEmpty) return;
    final ok = await ref.read(categoryControllerProvider.notifier).create(name);
    if (ok) _name.clear();
  }

  Future<void> _confirmDelete(Category c, List<ProductItem> products) async {
    final affected = products.where((p) => p.categoryId == c.id).length;
    // Dialog ini TIDAK punya TextField/controller sendiri, jadi tidak ada
    // TextEditingController yang perlu dispose (lihat _editStock di atas
    // untuk kasus yang butuh deferred dispose).
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Hapus kategori ${c.name}?'),
        content: Text(affected == 0
            ? 'Tidak ada produk di kategori ini.'
            : '$affected produk akan jadi tanpa kategori.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Batal'),
          ),
          TextButton(
            key: const Key('category_delete_confirm'),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Hapus'),
          ),
        ],
      ),
    );
    if (confirmed != true) return; // Batal / dismiss: no-op
    await ref.read(categoryControllerProvider.notifier).remove(c.id);
    // Refresh produk supaya label kategori pada tile langsung hilang.
    await ref.read(productControllerProvider.notifier).load();
  }

  @override
  Widget build(BuildContext context) {
    final catState = ref.watch(categoryControllerProvider);
    final products = ref.watch(productControllerProvider).products;
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
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 44,
                  height: 4,
                  decoration: BoxDecoration(
                    color: FortunasColors.ink4,
                    borderRadius: BorderRadius.circular(999),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text('Kelola Kategori', style: display(fontSize: 20, letterSpacing: -0.4)),
              const SizedBox(height: 4),
              Text('Hapus kategori tidak menghapus produknya — produk jadi tanpa kategori.',
                  style: body(fontSize: 12, color: FortunasColors.ink3)),
              const SizedBox(height: 16),
              Row(children: [
                Expanded(
                  child: TextField(
                    key: const Key('category_add_field'),
                    controller: _name,
                    decoration: const InputDecoration(labelText: 'Nama kategori baru'),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  key: const Key('category_add_btn'),
                  onPressed: _add,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: FortunasColors.violet,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(FortunasRadius.lg),
                      side: const BorderSide(color: FortunasColors.ink, width: 1.5),
                    ),
                  ),
                  child: const Text('Tambah'),
                ),
              ]),
              if (catState.errorMessage != null) ...[
                const SizedBox(height: 8),
                Text(catState.errorMessage!,
                    style: body(fontSize: 12.5, color: FortunasColors.error)),
              ],
              const SizedBox(height: 16),
              if (catState.loading && catState.categories.isEmpty)
                const Padding(
                    padding: EdgeInsets.symmetric(vertical: 24),
                    child: Center(child: CircularProgressIndicator()))
              else if (catState.categories.isEmpty)
                Text('Belum ada kategori.', style: body(fontSize: 12.5, color: FortunasColors.ink3))
              else
                ...catState.categories.map((c) => _CategoryRow(
                      category: c,
                      onDelete: () => _confirmDelete(c, products),
                    )),
            ],
          ),
        ),
      ),
    );
  }
}

class _CategoryRow extends StatelessWidget {
  final Category category;
  final VoidCallback onDelete;
  const _CategoryRow({required this.category, required this.onDelete});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: FortunasColors.surface,
        border: Border.all(color: FortunasColors.ink, width: 1.5),
        borderRadius: BorderRadius.circular(FortunasRadius.lg),
      ),
      child: Row(children: [
        Expanded(
          child: Text(category.name,
              style: body(fontSize: 13.5, weight: FontWeight.w600, color: FortunasColors.ink)),
        ),
        IconButton(
          key: Key('category_delete_${category.id}'),
          onPressed: onDelete,
          icon: const Icon(Icons.delete_outline, color: FortunasColors.ink4),
          tooltip: 'Hapus kategori',
        ),
      ]),
    );
  }
}
