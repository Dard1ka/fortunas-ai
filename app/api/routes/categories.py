"""Kategori produk per-UMKM (tenant-scoped). Pola: app/api/routes/products.py."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app import category_repo
from app.core.tenancy import TenantContext, get_current_tenant
from app.schemas import Category, CategoryCreateRequest, CategoryListResponse

router = APIRouter(tags=["categories"])


@router.get("/umkm/categories", response_model=CategoryListResponse)
def list_categories(tenant: TenantContext = Depends(get_current_tenant)) -> CategoryListResponse:
    cats = category_repo.list_categories(tenant.tenant_id)
    return CategoryListResponse(categories=[Category(**c) for c in cats], count=len(cats))


@router.post("/umkm/categories", response_model=Category, status_code=201)
def create_category(body: CategoryCreateRequest,
                    tenant: TenantContext = Depends(get_current_tenant)) -> Category:
    try:
        c = category_repo.create_category(tenant.tenant_id, body.name)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Category(**c)


@router.delete("/umkm/categories/{category_id}")
def delete_category(category_id: int,
                    tenant: TenantContext = Depends(get_current_tenant)) -> dict:
    res = category_repo.delete_category(tenant.tenant_id, category_id)
    if not res["deleted"]:
        raise HTTPException(status_code=404, detail="Kategori tidak ditemukan.")
    return {"status": "ok", "deleted": True, "reassigned": res["reassigned"]}
