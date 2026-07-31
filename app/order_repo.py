"""Repository pesanan publik (self-order pelanggan lewat kode UMKM).

Menyimpan state pesanan di SQLite/Postgres (bukan BigQuery) karena ini state
operasional pra-transaksi. Stok dipotong saat pesanan menjadi `paid`.

Pola mengikuti app/product_repo.py: modul-level function, SessionLocal, return dict.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update

from app import product_repo
from app.db_pg import SessionLocal
from app.models import PublicOrder

# Status yang valid untuk pesanan publik.
STATUS_PENDING = "pending_payment"
STATUS_PAID = "paid"
STATUS_ACCEPTED = "accepted"
STATUS_REJECTED = "rejected"
STATUS_COMPLETED = "completed"
STATUS_EXPIRED = "expired"
STATUS_CANCELLED = "cancelled"


class TransitionError(Exception):
    """Aksi UMKM tak sah dari status pesanan sekarang (route → 409)."""


# Aksi UMKM → himpunan status sumber yang sah. SATU sumber kebenaran: ketiga
# endpoint di routes/orders.py memvalidasi lewat tabel ini.
_ALLOWED_FROM: dict[str, set[str]] = {
    "accept": {STATUS_PAID},
    "reject": {STATUS_PAID},
    "complete": {STATUS_ACCEPTED},
}
_RESULT_STATUS: dict[str, str] = {
    "accept": STATUS_ACCEPTED,
    "reject": STATUS_REJECTED,
    "complete": STATUS_COMPLETED,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _to_dict(o: PublicOrder) -> dict[str, Any]:
    return {
        "id": o.id,
        "tenant_id": o.tenant_id,
        "code": o.code or "",
        "customer_name": o.customer_name or "",
        "customer_phone": o.customer_phone or "",
        "items": list(o.items or []),
        "total": o.total or 0,
        "status": o.status,
        "payment_provider": o.payment_provider,
        "payment_order_id": o.payment_order_id,
        "payment_token": o.payment_token,
        "payment_redirect_url": o.payment_redirect_url,
        "payment_status": o.payment_status,
        "paid_at": o.paid_at,
        "stock_restored_at": o.stock_restored_at,
        "created_at": o.created_at or "",
        "updated_at": o.updated_at or "",
    }


def create_order(tenant_id: int, *, code: str, customer_name: str,
                 customer_phone: str, items: list[dict[str, Any]],
                 total: int) -> dict[str, Any]:
    """Buat pesanan baru berstatus pending_payment. `payment_order_id` unik
    di-generate agar bisa dipetakan balik dari webhook gateway."""
    now = _now()
    with SessionLocal() as s:
        o = PublicOrder(
            tenant_id=tenant_id,
            code=code,
            customer_name=customer_name.strip(),
            customer_phone=customer_phone.strip(),
            items=items,
            total=total,
            status=STATUS_PENDING,
            created_at=now,
            updated_at=now,
        )
        s.add(o)
        s.flush()  # dapatkan o.id sebelum menyusun payment_order_id
        o.payment_order_id = f"ORD-{o.id}-{secrets.token_hex(16)}"
        s.commit()
        return _to_dict(o)


def attach_payment(order_id: int, *, provider: str, token: str | None,
                   redirect_url: str | None) -> dict[str, Any] | None:
    with SessionLocal() as s:
        o = s.get(PublicOrder, order_id)
        if o is None:
            return None
        o.payment_provider = provider
        o.payment_token = token
        o.payment_redirect_url = redirect_url
        o.updated_at = _now()
        s.commit()
        return _to_dict(o)


def get_order(order_id: int) -> dict[str, Any] | None:
    with SessionLocal() as s:
        o = s.get(PublicOrder, order_id)
        return _to_dict(o) if o else None


def get_by_payment_order_id(payment_order_id: str) -> dict[str, Any] | None:
    with SessionLocal() as s:
        o = s.scalars(
            select(PublicOrder).where(
                PublicOrder.payment_order_id == payment_order_id)
        ).first()
        return _to_dict(o) if o else None


def list_orders(tenant_id: int,
                statuses: list[str] | None = None) -> list[dict[str, Any]]:
    """Pesanan milik tenant, terbaru dulu. `statuses=None` → semua status.

    Menerima DAFTAR status (bukan satu) karena inbox default menampilkan dua
    status sekaligus: `paid` (perlu diterima) + `accepted` (perlu diselesaikan).
    """
    with SessionLocal() as s:
        q = select(PublicOrder).where(PublicOrder.tenant_id == tenant_id)
        if statuses:
            q = q.where(PublicOrder.status.in_(statuses))
        rows = s.scalars(q.order_by(PublicOrder.id.desc())).all()
        return [_to_dict(o) for o in rows]


def get_order_for_tenant(tenant_id: int, order_id: int) -> dict[str, Any] | None:
    """Ambil pesanan milik tenant. None bila tak ada ATAU milik tenant lain.

    `get_order` biasa tak kenal tenant karena dipakai jalur publik. Route UMKM
    WAJIB lewat sini: tanpa penyaringan tenant, UMKM A bisa menerima/menolak
    pesanan UMKM B hanya dengan menebak id. Route membalas 404 (bukan 403) untuk
    keduanya — 403 akan mengakui bahwa pesanan itu ada.
    """
    with SessionLocal() as s:
        o = s.get(PublicOrder, order_id)
        if o is None or o.tenant_id != tenant_id:
            return None
        return _to_dict(o)


def _update(order_id: int, **fields: Any) -> dict[str, Any] | None:
    """Terapkan perubahan field ke satu pesanan + stempel updated_at.

    BUKAN satu-satunya penulis baris pesanan: `mark_paid`, `restore_stock`,
    `cancel_by_gateway`, dan `apply_action` masing-masing punya compare-and-set
    atomik sendiri (satu `UPDATE` bersyarat per fungsi) dan tak lewat sini.
    Yang tersisa di sini cuma tulis `payment_status` mentah dari gateway saat
    status TIDAK digerakkan (`cancel_by_gateway` yang klaimnya kalah,
    `set_pending_by_gateway`) — plus `set_status`, yang kini tak punya pemanggil
    produksi lagi.
    """
    with SessionLocal() as s:
        o = s.get(PublicOrder, order_id)
        if o is None:
            return None
        for k, v in fields.items():
            setattr(o, k, v)
        o.updated_at = _now()
        s.commit()
        return _to_dict(o)


def set_status(order_id: int, status: str, *,
               payment_status: str | None = None) -> dict[str, Any] | None:
    """Tulis status TANPA SYARAT — tanpa pemanggil produksi sejak `apply_action`
    pindah ke compare-and-set.

    JANGAN pakai ini untuk transisi (aksi UMKM, job kedaluwarsa, webhook
    gateway): tulisan tanpa syarat menimpa apa pun yang ditulis penulis lain di
    jendela baca→tulis. Pola yang benar ada di `apply_action` /
    `cancel_by_gateway`: `UPDATE ... WHERE status IN (...)` lalu periksa
    `rowcount`.
    """
    fields: dict[str, Any] = {"status": status}
    if payment_status is not None:
        fields["payment_status"] = payment_status
    return _update(order_id, **fields)


def mark_paid(order_id: int, *, payment_status: str | None = None) -> dict[str, Any] | None:
    """Tandai pesanan lunas + potong stok — SEKALI saja, termasuk saat bersamaan.

    Idempoten lewat `paid_at`, BUKAN lewat status sekarang. Guard lama
    (`status == STATUS_PAID`) bocor begitu UMKM menerima pesanan: status jadi
    `accepted`, lalu notifikasi settlement ulang dari gateway (Midtrans mengirim
    ganda dan bisa di-retrigger manual dari dashboard) lolos guard → stok
    terpotong dua kali DAN status mundur ke `paid`, membatalkan penerimaan UMKM.

    Klaim hak potong stok lewat compare-and-set atomik pada satu UPDATE
    (`WHERE paid_at IS NULL`), bukan baca-lalu-tulis di sesi terpisah. Baca-lalu-
    tulis hanya memblokir replay yang terpisah WAKTU: dua notifikasi settlement
    yang tiba BERSAMAAN bisa sama-sama membaca `paid_at is None` sebelum salah
    satu sempat menulis, lalu keduanya lolos dan memotong stok dua kali. CAS
    memblokir keduanya — replay bersamaan maupun terpisah waktu — karena baris
    hanya bisa dimenangkan oleh SATU `UPDATE` yang benar-benar mengubah baris itu.

    `status` (dan `payment_status`) ditulis DALAM SATU UPDATE yang sama dengan
    `paid_at`, bukan lewat panggilan `_update` terpisah setelahnya. Ini
    disengaja: klaim `paid_at` adalah klaim PERMANEN — replay berikutnya yang
    kalah (`rowcount == 0`) tidak pernah mencoba lagi. Kalau status ditulis
    belakangan dan proses crash di antara klaim dan tulis-status, pesanan
    akan macet permanen di `pending_payment` walau pelanggan sudah bayar:
    replay Midtrans berikutnya kalah klaim (baris sudah `paid_at` terisi) dan
    pulang tanpa efek, tanpa pernah menulis status maupun memotong stok —
    tak kelihatan di inbox (yang cuma daftar `paid` + `accepted`), tanpa
    galat di mana pun. Menyatukan tulis-status ke klaim menutup celah itu:
    begitu klaim menang, `status` sudah `paid` seketika itu juga.

    Konsekuensi urutan yang TERSISA (disengaja): klaim (`paid_at` + `status`)
    lebih dulu, baru memotong stok. Kalau proses crash tepat di antara
    keduanya, pesanan tercatat `paid` tapi stoknya belum terpotong — oversell
    ringan, dipilih dengan sadar karena order creation sudah pre-check stok
    dan satu pesanan oversold jauh lebih ringan daripada stok yang diam-diam
    terpotong dua kali ATAU pesanan macet permanen. CAS TIDAK menutup window
    oversell-saat-crash ini; yang dijaminnya hanya bahwa `decrement_by_ids`
    dipanggil oleh paling banyak satu pemanggil per pesanan, DAN bahwa klaim
    yang menang selalu langsung terlihat sebagai `paid` walau proses mati
    sebelum sempat memotong stok.
    """
    now = _now()
    claim: dict[str, Any] = {"paid_at": now, "updated_at": now, "status": STATUS_PAID}
    if payment_status is not None:
        claim["payment_status"] = payment_status
    with SessionLocal() as s:
        # Klaim hak potong stok DAN status lunas secara atomik: hanya SATU
        # pemanggil bisa menang, bahkan kalau dua notifikasi gateway tiba
        # bersamaan — dan begitu menang, status sudah `paid` seketika (lihat
        # docstring di atas soal kenapa status tak boleh ditulis belakangan).
        res = s.execute(
            update(PublicOrder)
            .where(PublicOrder.id == order_id, PublicOrder.paid_at.is_(None))
            .values(**claim)
        )
        s.commit()
        o = s.get(PublicOrder, order_id)
        if o is None:
            return None
        if res.rowcount == 0:      # kalah balapan, atau memang pernah lunas
            return _to_dict(o)     # tanpa efek apa pun
        tenant_id = o.tenant_id
        items = list(o.items or [])
    # Potong stok di luar sesi klaim di atas (product_repo punya sesi sendiri).
    product_repo.decrement_by_ids(
        tenant_id, [{"product_id": it["product_id"], "qty": it["qty"]} for it in items])
    return get_order(order_id)


def restore_stock(order_id: int) -> bool:
    """Kembalikan stok pesanan yang PERNAH lunas. Idempoten via `stock_restored_at`,
    diklaim dengan compare-and-set atomik yang sama seperti `mark_paid` — dua
    panggilan `restore_stock` yang tiba bersamaan (mis. reject dobel-klik +
    proses retry) tak bisa sama-sama menang dan mengembalikan stok dua kali.

    Return True hanya bila stok benar-benar dikembalikan pada pemanggilan ini.
    False bila pesanan tak ada, belum pernah lunas (stok belum dipotong), atau
    stoknya sudah dikembalikan — ketiganya sama-sama tampak sebagai `rowcount
    == 0` dari sudut pandang UPDATE ini, jadi tak dibedakan di sini.
    """
    now = _now()
    with SessionLocal() as s:
        # Klaim hak kembalikan stok secara atomik, cermin dari mark_paid.
        res = s.execute(
            update(PublicOrder)
            .where(PublicOrder.id == order_id,
                   PublicOrder.paid_at.isnot(None),
                   PublicOrder.stock_restored_at.is_(None))
            .values(stock_restored_at=now, updated_at=now)
        )
        s.commit()
        if res.rowcount == 0:  # tak ada / belum lunas / sudah dikembalikan
            return False
        o = s.get(PublicOrder, order_id)
        tenant_id = o.tenant_id
        items = list(o.items or [])
    product_repo.restore_by_ids(
        tenant_id, [{"product_id": it["product_id"], "qty": it["qty"]} for it in items])
    return True


def apply_action(tenant_id: int, order_id: int,
                 action: str) -> dict[str, Any] | None:
    """Jalankan aksi UMKM (`accept` | `reject` | `complete`) dengan validasi transisi.

    Return order terbaru. None bila pesanan tak ada / bukan milik tenant.
    Raise `TransitionError` bila status sekarang tak mengizinkan aksi itu.

    Transisinya diklaim lewat compare-and-set atomik (`UPDATE ... WHERE status IN
    (...)`), cermin dari `mark_paid`/`restore_stock`/`cancel_by_gateway` — BUKAN
    baca-lalu-tulis. Tulis tanpa syarat punya dua korban yang bisa dicapai:
    (1) refund yang mendarat di dalam jendela baca→tulis `accept` akan tertimpa
    `accepted`, menghidupkan ulang pesanan yang uangnya sudah dikembalikan dan
    stoknya sudah dikembalikan gateway; (2) `_ALLOWED_FROM` membuat `accept` dan
    `reject` sama-sama berangkat dari `paid`, jadi dua staf di dua HP (satu
    Terima, satu Tolak) bisa sama-sama lolos cek lalu sama-sama menulis. Flag
    `busy` di UI tak menolong — itu state Riverpod per-klien.

    Pembacaan awal DIPERTAHANKAN, tapi bukan lagi yang mengotorisasi tulisan:
    tugasnya cuma membedakan 404 (tak ada / tenant lain) dari 409 (transisi tak
    sah). Begitu klaim CAS kalah, dibaca ULANG untuk membedakan keduanya lagi
    dari kenyataan terbaru.

    `reject` mengembalikan stok HANYA bila klaimnya menang — pesanan yang sudah
    lunas berarti stoknya sudah dipotong, dan menolak tanpa mengembalikan membuat
    barang yang tak terjual tercatat terjual. Urutannya (klaim dulu, stok
    kemudian) penting: versi lama mengembalikan stok lebih dulu tanpa syarat,
    jadi stok kembali walau tulisan statusnya kalah. Pengembalian UANG tidak
    otomatis (bucket B).
    """
    o = get_order_for_tenant(tenant_id, order_id)
    if o is None:
        return None
    if o["status"] not in _ALLOWED_FROM[action]:
        raise TransitionError(
            f"Pesanan berstatus '{o['status']}' tidak bisa di-{action}.")

    now = _now()
    with SessionLocal() as s:
        res = s.execute(
            update(PublicOrder)
            .where(PublicOrder.id == order_id,
                   PublicOrder.tenant_id == tenant_id,
                   PublicOrder.status.in_(_ALLOWED_FROM[action]))
            .values(status=_RESULT_STATUS[action], updated_at=now)
        )
        s.commit()
        # `!= 0`, bukan `== 1` (konvensi `mark_paid`; `cancel_by_gateway` masih
        # `== 1`, dicatat sebagai utang konsistensi di day-15). Driver yang
        # melaporkan rowcount `-1` ("tak tahu") akan membuat `== 1` menganggap
        # SETIAP klaim kalah: accept/reject selalu 409 dan stok pesanan yang
        # ditolak tak pernah kembali — salah, permanen, dan senyap. `!= 0`
        # menjaga jalur normal tetap benar di driver semacam itu.
        menang = res.rowcount != 0

    if not menang:
        # Baris tak bergerak. Baca ulang untuk memisahkan "hilang / tenant lain"
        # (404) dari "ada tapi statusnya sudah lain" (409) — pembacaan di atas
        # sudah basi begitu ada penulis lain di antaranya.
        fresh = get_order_for_tenant(tenant_id, order_id)
        if fresh is None:
            return None
        raise TransitionError(
            f"Pesanan berstatus '{fresh['status']}' tidak bisa di-{action}.")

    if action == "reject":
        restore_stock(order_id)
    return get_order(order_id)


#: Status yang masih boleh digerakkan gateway ke `cancelled`. Sengaja BUKAN
#: sekadar "belum pernah lunas" (`paid_at is None`): `paid_at` tetap terisi
#: selamanya begitu `mark_paid` pernah menang, baik pesanan baru `paid` maupun
#: sudah `accepted` — keduanya sama-sama "paid_at is not None". Yang membedakan
#: adalah STATUS sekarang: refund pada pesanan yang masih `paid` (UMKM belum
#: bersikap) wajar dibatalkan; refund pada pesanan yang sudah `accepted`/
#: `rejected`/`completed` (UMKM SUDAH bersikap) tidak boleh menghapus sikap itu.
_GATEWAY_CANCELLABLE: set[str] = {STATUS_PENDING, STATUS_PAID}


def cancel_by_gateway(order_id: int, *, payment_status: str | None = None) -> dict[str, Any] | None:
    """Gateway membatalkan pesanan (deny/cancel/expire/refund/chargeback).

    Status hanya boleh digerakkan gateway selama UMKM BELUM bersikap
    (`pending_payment` atau `paid`). Begitu UMKM menerima/menolak/menyelesaikan
    pesanan, status jadi wilayah UMKM — refund yang datang belakangan tak boleh
    menghapus keputusan itu.

    Klaimnya ATOMIK (satu UPDATE bersyarat, bukan baca-lalu-tulis): tanpa itu,
    `accept` yang mendarat antara pembacaan status dan penulisannya akan tertimpa
    `cancelled` — persis kerusakan yang fungsi ini ada untuk mencegah.
    Stok dikembalikan terpisah lewat `restore_stock` (idempoten), terlepas dari
    apakah status ikut berubah.
    """
    now = _now()
    values: dict[str, Any] = {"status": STATUS_CANCELLED, "updated_at": now}
    if payment_status is not None:
        values["payment_status"] = payment_status
    with SessionLocal() as s:
        res = s.execute(
            update(PublicOrder)
            .where(PublicOrder.id == order_id,
                   PublicOrder.status.in_(_GATEWAY_CANCELLABLE))
            .values(**values)
        )
        s.commit()
        o = s.get(PublicOrder, order_id)
        if o is None:
            return None
        if res.rowcount == 1:
            return _to_dict(o)
    # UMKM sudah bersikap → status dibekukan, tapi jejak gateway tetap dicatat.
    if payment_status is not None:
        return _update(order_id, payment_status=payment_status)
    return get_order(order_id)


def set_pending_by_gateway(order_id: int, *, payment_status: str | None = None) -> dict[str, Any] | None:
    """Notifikasi `pending` dari gateway: catat jejaknya, JANGAN gerakkan status.

    Satu-satunya status yang `pending` bisa berarti adalah `pending_payment` —
    dan itu status awal pesanan. Jadi tak ada transisi sah yang perlu ditulis,
    sementara MENULISnya justru berbahaya: notifikasi `pending` yang tiba
    terlambat bisa memundurkan pesanan yang sudah lunas (stoknya sudah
    terpotong, dan inbox tak lagi menampilkannya karena inbox hanya melihat
    `paid`/`accepted`), atau menghidupkan ulang pesanan yang sudah dibatalkan
    gateway.
    """
    if payment_status is None:
        return get_order(order_id)
    return _update(order_id, payment_status=payment_status)
