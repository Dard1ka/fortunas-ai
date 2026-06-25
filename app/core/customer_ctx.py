"""Customer identity context dari JWT (role=customer). Paralel tenancy.get_current_tenant."""
from __future__ import annotations

from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException, status

from app import customer_repo
from app.core.auth import decode_access_token


@dataclass
class CustomerContext:
    customer_user_id: str
    username: str
    phone_number: str = ""


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_customer(authorization: str | None = Header(default=None)) -> CustomerContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized("Token tidak ada. Sertakan header Authorization: Bearer <token>.")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise _unauthorized("Token kedaluwarsa. Silakan login lagi.") from exc
    except jwt.PyJWTError as exc:
        raise _unauthorized("Token tidak valid.") from exc

    if payload.get("role") != "customer":
        raise _unauthorized("Endpoint khusus customer.")
    cid = payload.get("customer_user_id")
    customer = customer_repo.get_customer(cid) if cid else None
    if not customer:
        raise _unauthorized("Customer tidak ditemukan.")
    return CustomerContext(
        customer_user_id=customer["customer_user_id"],
        username=customer["username"],
        phone_number=customer["phone_number"],
    )


CurrentCustomer = Depends(get_current_customer)
