"""Token customer (role=customer) + role claim default umkm. Pure (decode)."""
from __future__ import annotations

from app.core.auth import create_access_token, create_customer_token, decode_access_token


def test_customer_token_carries_role_and_id():
    payload = decode_access_token(create_customer_token(customer_user_id="cu_abc"))
    assert payload["role"] == "customer"
    assert payload["customer_user_id"] == "cu_abc"
    assert payload["sub"] == "cu_abc"


def test_access_token_default_role_umkm():
    payload = decode_access_token(
        create_access_token(user_id=1, email="a@b.com", tenant_id=2)
    )
    assert payload["role"] == "umkm"
    assert payload["tenant_id"] == 2
