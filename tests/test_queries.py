from app.queries import NAMED_QUERIES, QUERY_BUILDERS, build_query

TX = "proj.ds.tokoA_transactions"


def test_build_query_top_product_structure():
    sql = build_query("top_product", TX)
    assert sql is not None
    assert f"`{TX}`" in sql
    assert "GROUP BY Description" in sql
    assert "SUM(Quantity) AS total_qty" in sql
    assert "SUM(Quantity * Price)" in sql
    assert "AS total_omzet" in sql
    assert "ORDER BY total_omzet DESC" in sql
    assert "LIMIT 10" in sql


def test_build_query_unknown_returns_none():
    assert build_query("ngawur", TX) is None


def test_top_product_registered():
    assert "top_product" in QUERY_BUILDERS
    assert NAMED_QUERIES["top_product"]["cost_tier"] == "cheap"
