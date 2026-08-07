"""Endpoint publik (tanpa auth UMKM) untuk pelanggan memesan lewat KODE UMKM.

Pelanggan memasukkan kode publik UMKM (mis. 'KDS-001') → dapat info toko + daftar
menu (produk bergambar). Tidak perlu scan QR. Checkout pelanggan menyusul di Fase 2.
"""
from __future__ import annotations

import time

import jwt
from fastapi import APIRouter, Header, HTTPException, Request

from app import db, order_repo, product_repo
from app.core.auth import decode_access_token
from app.schemas import PublicOrderCreateRequest, PublicOrderResponse
from app.services import payment

router = APIRouter(tags=["public"])

# Pengganjal spam untuk endpoint order publik (tanpa auth).
# JUJUR SOAL BATASNYA: in-process → hitungan per worker uvicorn dan hilang saat
# restart. Ini bukan kontrol abuse sungguhan, cukup untuk MVP. Kalau butuh
# serius, tempatnya di reverse-proxy (nginx `limit_req`) saat VPS ditata.
# Batas KETIGA (review Task 6): kunci per-IP tak dibuang otomatis begitu
# jendelanya lewat — pruning di bawah cuma jalan saat IP yang SAMA memesan
# lagi, jadi IP yang mampir sekali lalu tak pernah balik numpuk selamanya dan
# dict ini tumbuh terus mengikuti jumlah IP anonim yang pernah singgah. Sapuan
# oportunistik (`_sweep_stale_order_hits`) menahan itu: begitu dict melewati
# `_ORDER_HITS_SWEEP_THRESHOLD`, kunci basi dibuang. Masih in-process (bukan
# proses/timer terpisah), jadi tetap sejalan dengan batas di atas.
_ORDER_RATE_LIMIT = 10        # order per IP per jendela
_ORDER_RATE_WINDOW = 60.0     # detik
_ORDER_HITS_SWEEP_THRESHOLD = 500  # sapu kunci basi begitu dict selebar ini
_order_hits: dict[str, list[float]] = {}


def _sweep_stale_order_hits(now: float) -> None:
    """Buang kunci IP yang seluruh riwayat hit-nya sudah di luar jendela.

    Dipanggil oportunistik dari `_rate_limit_order` (bukan lewat proses/timer
    terpisah — lihat komentar batas limiter di atas), jadi biayanya cuma satu
    scan dict setiap kali populasinya melewati threshold, bukan tiap request.
    """
    for ip in list(_order_hits.keys()):
        # `.get`, bukan subscript: `create_public_order` sync → Starlette
        # menjalankannya di threadpool anyio tanpa lock, jadi kunci ini bisa
        # sudah di-pop thread lain di antara snapshot di atas dan baris ini.
        hits_raw = _order_hits.get(ip)
        if not hits_raw:
            continue
        hits = [t for t in hits_raw if now - t < _ORDER_RATE_WINDOW]
        if hits:
            _order_hits[ip] = hits
        else:
            _order_hits.pop(ip, None)


def _rate_limit_order(request: Request) -> None:
    ip = request.client.host if request.client else "?"
    now = time.monotonic()
    hits = [t for t in _order_hits.get(ip, []) if now - t < _ORDER_RATE_WINDOW]
    if len(hits) >= _ORDER_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Terlalu banyak pesanan dari perangkat ini. Coba lagi sebentar.")
    hits.append(now)
    _order_hits[ip] = hits
    if len(_order_hits) > _ORDER_HITS_SWEEP_THRESHOLD:
        _sweep_stale_order_hits(now)


def _optional_customer_id(authorization: str | None) -> str | None:
    """Baca `customer_user_id` dari bearer pelanggan bila ADA & sah — best-effort.

    Jalur order publik SENGAJA tanpa auth: tamu tetap boleh memesan. Jadi token
    yang tak ada / kedaluwarsa / bukan token customer TIDAK menolak request —
    cuma berarti pesanan tak tertaut ke akun (tetap tercatat, tapi tak menaut
    loyalty saat `completed`). Token yang sah bertanda tangan, jadi id-nya
    dipercaya tanpa lookup DB tambahan; keberadaan akun diverifikasi belakangan
    saat penautan loyalty (juga best-effort).
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        return None
    if payload.get("role") != "customer":
        return None
    return payload.get("customer_user_id") or None


@router.get("/public/umkm/{code}")
def get_umkm_by_code(code: str) -> dict:
    tenant = db.get_tenant_by_code(code)
    if tenant is None:
        raise HTTPException(status_code=404, detail="UMKM dengan kode itu tidak ditemukan.")
    bp = tenant.get("business_profile") or {}
    products = product_repo.list_products(tenant["id"])
    return {
        "code": bp.get("code", ""),
        "name": tenant["name"],
        "city": bp.get("city", ""),
        "address": bp.get("address", ""),
        "products": [
            {
                "id": p["id"],
                "name": p["name"],
                "description": p["description"],
                "image_url": p["image_url"],
                "category_id": p["category_id"],
                "stock": p["stock"],
                "price": p["price"],
            }
            for p in products
        ],
        "count": len(products),
    }


def _order_out(o: dict) -> PublicOrderResponse:
    return PublicOrderResponse(
        id=o["id"], code=o["code"],
        customer_name=o["customer_name"], customer_phone=o["customer_phone"],
        items=o["items"], total=o["total"], status=o["status"],
        payment_provider=o["payment_provider"], payment_token=o["payment_token"],
        payment_redirect_url=o["payment_redirect_url"],
        payment_order_id=o["payment_order_id"],
        created_at=o["created_at"], updated_at=o["updated_at"],
    )


@router.post("/public/umkm/{code}/orders", response_model=PublicOrderResponse,
             status_code=201)
def create_public_order(code: str, req: PublicOrderCreateRequest,
                        request: Request,
                        authorization: str | None = Header(default=None),
                        ) -> PublicOrderResponse:
    """Pelanggan membuat pesanan lewat kode UMKM → buat order pending_payment +
    inisiasi pembayaran. Validasi: produk milik UMKM, punya harga, stok cukup.

    Header `Authorization` OPSIONAL: bila memuat bearer pelanggan yang sah,
    pesanan ditautkan ke akunnya (`customer_user_id`) supaya penjualan online
    masuk ke loyalty saat `completed`. Tanpa/token tak sah → tetap diproses
    sebagai pesanan tamu (endpoint ini tanpa auth by design)."""
    _rate_limit_order(request)
    customer_user_id = _optional_customer_id(authorization)
    tenant = db.get_tenant_by_code(code)
    if tenant is None:
        raise HTTPException(status_code=404, detail="UMKM dengan kode itu tidak ditemukan.")
    tenant_id = tenant["id"]

    items: list[dict] = []
    total = 0
    for line in req.items:
        p = product_repo.get_product(tenant_id, line.product_id)
        if p is None:
            raise HTTPException(status_code=400,
                                detail=f"Produk id {line.product_id} tidak ada di UMKM ini.")
        if p["price"] is None:
            raise HTTPException(status_code=400,
                                detail=f"Produk '{p['name']}' belum punya harga.")
        if p["stock"] is not None and p["stock"] < line.qty:
            raise HTTPException(status_code=409,
                                detail=f"Stok '{p['name']}' tidak cukup (sisa {p['stock']}).")
        subtotal = int(p["price"]) * line.qty
        total += subtotal
        items.append({
            "product_id": p["id"], "name": p["name"], "qty": line.qty,
            "unit_price": int(p["price"]), "subtotal": subtotal,
        })

    order = order_repo.create_order(
        tenant_id, code=tenant.get("business_profile", {}).get("code", code),
        customer_name=req.customer_name, customer_phone=req.customer_phone,
        items=items, total=total, customer_user_id=customer_user_id)

    charge = payment.create_charge(order)
    order = order_repo.attach_payment(
        order["id"], provider=charge["provider"], token=charge["token"],
        redirect_url=charge["redirect_url"]) or order
    return _order_out(order)


@router.get("/public/orders/{payment_order_id}", response_model=PublicOrderResponse)
def get_public_order(payment_order_id: str) -> PublicOrderResponse:
    """Pantau status pesanan. Kuncinya `payment_order_id` (`ORD-{id}-{32 hex}`,
    128 bit acak — lihat `order_repo.create_order`), BUKAN id berurutan: respons
    memuat nama & nomor HP pelanggan, jadi kunci yang bisa dienumerasi akan
    membocorkan PII seluruh UMKM (UU 27/2022 PDP)."""
    o = order_repo.get_by_payment_order_id(payment_order_id)
    if o is None:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan.")
    return _order_out(o)


@router.api_route("/public/orders/{payment_order_id}/confirm-payment",
                  methods=["GET", "POST"])
def confirm_payment(payment_order_id: str) -> dict:
    """Konfirmasi pembayaran **QRIS statis** oleh pelanggan ("Saya sudah bayar").

    QRIS statis tak punya callback per-transaksi, jadi pelanggan menyatakan
    sendiri sudah membayar → pesanan ditandai lunas (stok dipotong, idempoten
    via `mark_paid`). Ini KLAIM, bukan bukti: UMKM WAJIB memverifikasi dana
    benar-benar masuk di aplikasi QRIS-nya sebelum menekan Terima, dan menekan
    Tolak (stok kembali otomatis) bila ternyata belum dibayar.

    Sengaja tanpa guard `is_live`: Midtrans = future scope, jadi tak ada jalur
    otomatis yang bisa "di-bypass" endpoint ini. Saat Midtrans diaktifkan nanti,
    jalur lunas pindah ke webhook (`verify_notification`) dan endpoint ini bisa
    dibatasi/di-nonaktifkan."""
    o = order_repo.get_by_payment_order_id(payment_order_id)
    if o is None:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan.")
    o = order_repo.mark_paid(o["id"], payment_status="qris_manual_confirmed")
    return {"ok": True, "status": o["status"], "order_id": o["id"]}


@router.post("/public/payment/webhook")
async def payment_webhook(request: Request) -> dict:
    """Notifikasi pembayaran dari Midtrans. Verifikasi signature, lalu update
    status pesanan (potong stok saat lunas, kembalikan stok saat gagal/refund)."""
    # Cermin dari guard di simulate_pay: tanpa server key, `expected` dihitung
    # dengan komponen rahasia KOSONG → siapa pun bisa memalsukan notifikasi lunas.
    if not payment.is_live():
        raise HTTPException(
            status_code=400,
            detail="Webhook nonaktif saat Midtrans tidak dikonfigurasi.")
    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError("payload webhook harus objek JSON")
        result = payment.verify_notification(payload)
    except (ValueError, AttributeError, UnicodeError) as exc:
        # Permukaan TANPA AUTH: input sembarang dari internet tak boleh jadi 500.
        # Termasuk body bukan-JSON, body bukan-objek, dan signature_key yang
        # memuat lone surrogate (str.encode menolaknya).
        raise HTTPException(status_code=400, detail="Payload webhook tidak valid.") from exc
    if not result["valid"]:
        raise HTTPException(status_code=403, detail="Signature tidak valid.")
    o = order_repo.get_by_payment_order_id(result["payment_order_id"])
    if o is None:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan.")
    outcome = result["outcome"]
    raw = result["transaction_status"]
    if outcome == "paid":
        order_repo.mark_paid(o["id"], payment_status=raw)
    elif outcome == "failed":
        # `refund` & `chargeback` juga jatuh ke sini: kalau pesanan sudah pernah
        # lunas, stoknya sudah dipotong → kembalikan (idempoten).
        #
        # KECUALI pesanan yang sudah `completed`: barangnya sudah diserahkan ke
        # pelanggan, jadi chargeback yang datang belakangan tak boleh menambah
        # stok yang secara fisik tak pernah kembali. `cancel_by_gateway` memang
        # menolak menggerakkan STATUS pesanan completed, tapi stok jalan lewat
        # panggilan terpisah ini dan butuh pagarnya sendiri.
        #
        # `partial_refund` DISENGAJA diperlakukan sebagai pembatalan penuh untuk
        # MVP: `payment._map_status` memetakan setiap status tak dikenal ke
        # `failed`, jadi refund sebagian mengembalikan stok SELURUH pesanan lalu
        # membatalkannya. Diterima sadar karena pengembalian UANG di sistem ini
        # memang manual di luar aplikasi (lihat day-15 §Utang) — UMKM tetap harus
        # merekonsiliasi nominalnya sendiri, dan membatalkan penuh lebih aman
        # daripada membiarkan pesanan yang dananya sebagian ditarik tetap
        # tampak lunas. Refund per-item yang benar adalah scope slice sendiri.
        if o["status"] != order_repo.STATUS_COMPLETED:
            order_repo.restore_stock(o["id"])
        order_repo.cancel_by_gateway(o["id"], payment_status=raw)
    else:  # pending
        order_repo.set_pending_by_gateway(o["id"], payment_status=raw)
    return {"ok": True}
