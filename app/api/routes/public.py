"""Endpoint publik (tanpa auth UMKM) untuk pelanggan memesan lewat KODE UMKM.

Pelanggan memasukkan kode publik UMKM (mis. 'KDS-001') → dapat info toko + daftar
menu (produk bergambar). Tidak perlu scan QR. Checkout pelanggan menyusul di Fase 2.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import db, product_repo

router = APIRouter(tags=["public"])


@router.get("/public/umkm/{code}")
def get_umkm_by_code(code: str) -> dict:
    tenant = db.get_tenant_by_code(code)
    if tenant is None:
        raise HTTPException(status_code=404, detail="UMKM dengan kode itu tidak ditemukan.")
    bp = tenant.get("business_profile") or {}
    products = product_repo.list_products(tenant["id"])
    return {
        "tenant_id": tenant["id"],
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
            }
            for p in products
        ],
        "count": len(products),
    }
