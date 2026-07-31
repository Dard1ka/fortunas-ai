"""Endpoint publik (tanpa auth UMKM) untuk pelanggan memesan lewat KODE UMKM.

Pelanggan memasukkan kode publik UMKM (mis. 'KDS-001') → dapat info toko + daftar
menu (produk bergambar). Tidak perlu scan QR. Checkout pelanggan menyusul di Fase 2.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app import db, order_repo, product_repo
from app.schemas import PublicOrderCreateRequest, PublicOrderResponse
from app.services import payment

router = APIRouter(tags=["public"])


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
def create_public_order(code: str, req: PublicOrderCreateRequest) -> PublicOrderResponse:
    """Pelanggan membuat pesanan lewat kode UMKM → buat order pending_payment +
    inisiasi pembayaran. Validasi: produk milik UMKM, punya harga, stok cukup."""
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
        items=items, total=total)

    charge = payment.create_charge(order)
    order = order_repo.attach_payment(
        order["id"], provider=charge["provider"], token=charge["token"],
        redirect_url=charge["redirect_url"]) or order
    return _order_out(order)


@router.get("/public/orders/{payment_order_id}", response_model=PublicOrderResponse)
def get_public_order(payment_order_id: str) -> PublicOrderResponse:
    """Pantau status pesanan. Kuncinya `payment_order_id` (`ORD-{id}-{8 hex}`),
    BUKAN id berurutan: respons memuat nama & nomor HP pelanggan, jadi kunci yang
    bisa dienumerasi akan membocorkan PII seluruh UMKM (UU 27/2022 PDP)."""
    o = order_repo.get_by_payment_order_id(payment_order_id)
    if o is None:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan.")
    return _order_out(o)


@router.api_route("/public/orders/{payment_order_id}/simulate-pay",
                  methods=["GET", "POST"])
def simulate_pay(payment_order_id: str) -> dict:
    """Mode simulasi (tanpa Midtrans): tandai pesanan lunas. Untuk demo/testing.
    Ditolak bila Midtrans live agar tidak jadi celah bypass pembayaran."""
    if payment.is_live():
        raise HTTPException(status_code=400,
                            detail="Simulasi dinonaktifkan saat Midtrans aktif.")
    o = order_repo.get_by_payment_order_id(payment_order_id)
    if o is None:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan.")
    o = order_repo.mark_paid(o["id"], payment_status="simulated_settlement")
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
    payload = await request.json()
    result = payment.verify_notification(payload)
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
        order_repo.restore_stock(o["id"])
        order_repo.cancel_by_gateway(o["id"], payment_status=raw)
    else:  # pending
        order_repo.set_pending_by_gateway(o["id"], payment_status=raw)
    return {"ok": True}
