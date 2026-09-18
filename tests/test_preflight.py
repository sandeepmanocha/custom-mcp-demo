from server.tools import (
    get_data_product,
    overall_preflight_status,
    quality_dimension_status,
    run_quality_checks,
)


def _status_for(name: str) -> str:
    product = get_data_product(name)
    assert product is not None
    return overall_preflight_status(run_quality_checks(product))


def test_unknown_product_returns_none():
    assert get_data_product("UNKNOWN") is None


def test_claims_preflight_passes():
    product = get_data_product("CLAIMS")
    assert product is not None
    checks = run_quality_checks(product)
    assert overall_preflight_status(checks) == "PASS"
    assert all(c["result"] == "PASS" for c in checks)


def test_customer_quality_has_accuracy_warning():
    product = get_data_product("CUSTOMER")
    assert product is not None
    assert overall_preflight_status(run_quality_checks(product)) == "PASS"
    dims = quality_dimension_status(product)
    assert dims["accuracy"] == "WARN"
    assert dims["completeness"] == "PASS"


def test_revenue_preflight_fails():
    product = get_data_product("REVENUE")
    assert product is not None
    checks = run_quality_checks(product)
    assert overall_preflight_status(checks) == "FAIL"
    by_name = {c["check"]: c for c in checks}
    assert by_name["Certification Status"]["result"] == "FAIL"
    assert by_name["Timeliness"]["result"] == "FAIL"
    assert by_name["Data Contract"]["result"] == "FAIL"
    assert by_name["SLA Compliance"]["result"] == "FAIL"
    assert by_name["Data Quality Score"]["result"] == "WARN"
    assert by_name["Completeness"]["result"] == "WARN"


def test_case_insensitive_lookup():
    assert _status_for("claims") == "PASS"
    assert _status_for("revenue") == "FAIL"
