from app.analysis_registry import ANALYSIS_REGISTRY
from app.queries import QUERY_BUILDERS


def test_top_product_entry_present_and_enabled():
    entry = ANALYSIS_REGISTRY["top_product"]
    assert entry["enabled"] is True
    assert entry["label"]
    assert entry["description"]


def test_every_query_builder_has_registry_entry():
    for key in QUERY_BUILDERS:
        assert key in ANALYSIS_REGISTRY, f"{key} missing from ANALYSIS_REGISTRY"
