"""get_current_customer: terima token customer valid, tolak selain itu. Panggil dependency langsung."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from app import customer_repo
from app.core.auth import create_access_token, create_customer_token
from app.core.customer_ctx import get_current_customer


def _make_customer() -> str:
    cust, _ = customer_repo.upsert_customer(
        firebase_uid="fb1", phone_number="+628", username="Budi", birth_date="1995-08-17")
    return cust["customer_user_id"]


def test_valid_customer_token():
    cid = _make_customer()
    ctx = get_current_customer(authorization=f"Bearer {create_customer_token(customer_user_id=cid)}")
    assert ctx.customer_user_id == cid
    assert ctx.username == "Budi"


def test_missing_header_401():
    with pytest.raises(HTTPException) as e:
        get_current_customer(authorization=None)
    assert e.value.status_code == 401


def test_umkm_token_rejected_401():
    token = create_access_token(user_id=1, email="a@b.com", tenant_id=2)  # role=umkm
    with pytest.raises(HTTPException) as e:
        get_current_customer(authorization=f"Bearer {token}")
    assert e.value.status_code == 401


def test_unknown_customer_401():
    token = create_customer_token(customer_user_id="cu_ghost")  # tak ada di DB
    with pytest.raises(HTTPException) as e:
        get_current_customer(authorization=f"Bearer {token}")
    assert e.value.status_code == 401
