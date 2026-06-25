"""Customer routes: bootstrap (no-auth) + profile + QR session."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app import customer_repo
from app.core.auth import create_customer_token
from app.core.customer_ctx import CustomerContext, get_current_customer
from app.core.firebase_auth import (
    FirebaseAuthError,
    FirebaseNotConfigured,
    verify_firebase_token,
)
from app.schemas import (
    CustomerBootstrapRequest,
    CustomerBootstrapResponse,
    CustomerProfile,
    CustomerProfileUpdate,
    QRSessionResponse,
)
from app.services.qr_service import issue_qr

router = APIRouter(tags=["customer"])


@router.post("/customer/auth/bootstrap", response_model=CustomerBootstrapResponse)
def bootstrap(payload: CustomerBootstrapRequest) -> CustomerBootstrapResponse:
    try:
        claims = verify_firebase_token(payload.firebase_id_token)
    except FirebaseNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Layanan login customer belum dikonfigurasi.",
        ) from exc
    except FirebaseAuthError as exc:
        raise HTTPException(status_code=401, detail="Token Firebase tidak valid.") from exc

    customer, is_new = customer_repo.upsert_customer(
        firebase_uid=claims["firebase_uid"],
        phone_number=claims["phone_number"],
        username=payload.username,
        birth_date=payload.birth_date,
    )
    token = create_customer_token(customer_user_id=customer["customer_user_id"])
    return CustomerBootstrapResponse(
        access_token=token, role="customer", is_new_user=is_new,
        profile=CustomerProfile(**customer),
    )


@router.get("/customer/me", response_model=CustomerProfile)
def get_me(ctx: CustomerContext = Depends(get_current_customer)) -> CustomerProfile:
    return CustomerProfile(**customer_repo.get_customer(ctx.customer_user_id))


@router.put("/customer/me", response_model=CustomerProfile)
def put_me(payload: CustomerProfileUpdate,
           ctx: CustomerContext = Depends(get_current_customer)) -> CustomerProfile:
    customer = customer_repo.update_customer(
        ctx.customer_user_id, username=payload.username, birth_date=payload.birth_date,
    )
    return CustomerProfile(**customer)


@router.post("/customer/qr/session", response_model=QRSessionResponse)
def qr_session(ctx: CustomerContext = Depends(get_current_customer)) -> QRSessionResponse:
    return QRSessionResponse(**issue_qr(ctx.customer_user_id))
