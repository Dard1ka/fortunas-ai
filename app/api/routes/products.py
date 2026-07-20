"""Produk per-UMKM (katalog) + riwayat belanja per-barang pelanggan.

UMKM wajib punya >=1 produk (gate onboarding: needs_onboarding di list response).
Riwayat per-barang pelanggan (Indomaret Point) di-upsert saat checkout.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app import db, product_repo
from app.core.customer_ctx import CustomerContext, get_current_customer
from app.core.tenancy import TenantContext, get_current_tenant
from app.schemas import (
    CustomerProductHistoryResponse,
    CustomerProductStatItem,
    Product,
    ProductCreateRequest,
    ProductListResponse,
)

router = APIRouter(tags=["products"])


@router.get("/umkm/products", response_model=ProductListResponse)
def list_products(tenant: TenantContext = Depends(get_current_tenant)) -> ProductListResponse:
    products = product_repo.list_products(tenant.tenant_id)
    return ProductListResponse(
        products=[Product(**p) for p in products],
        count=len(products),
        needs_onboarding=len(products) == 0,
    )


@router.post("/umkm/products", response_model=Product, status_code=201)
def create_product(payload: ProductCreateRequest,
                   tenant: TenantContext = Depends(get_current_tenant)) -> Product:
    p = product_repo.create_product(
        tenant.tenant_id, name=payload.name, description=payload.description)
    return Product(**p)


@router.delete("/umkm/products/{product_id}")
def delete_product(product_id: int,
                   tenant: TenantContext = Depends(get_current_tenant)) -> dict:
    ok = product_repo.delete_product(tenant.tenant_id, product_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan.")
    return {"status": "ok", "deleted": product_id}


@router.get("/customer/product-history", response_model=CustomerProductHistoryResponse)
def customer_product_history(
        ctx: CustomerContext = Depends(get_current_customer)) -> CustomerProductHistoryResponse:
    stats = product_repo.customer_product_stats(ctx.customer_user_id)
    items = []
    for st in stats:
        tenant = db.get_tenant(st["tenant_id"])
        items.append(CustomerProductStatItem(
            tenant_id=st["tenant_id"],
            tenant_name=tenant["name"] if tenant else "",
            product_name=st["product_name"],
            purchase_count=st["purchase_count"],
            total_amount=st["total_amount"],
            last_purchased_at=st["last_purchased_at"],
        ))
    return CustomerProductHistoryResponse(items=items)
