"""Pre-flight check tools backed by mock Collibra data."""

from datetime import datetime, timedelta

from fastmcp import FastMCP

MOCK_DATA_PRODUCTS = {
    "CLAIMS": {
        "id": "dp-claims-001",
        "name": "CLAIMS",
        "display_name": "Claims Data Product",
        "domain": "Insurance Analytics",
        "status": "Certified",
        "owner": "Claims Data Owner",
        "steward": "Data Steward",
        "description": (
            "Enterprise claims data product containing all insurance claim records, "
            "adjudication results, and payment information."
        ),
        "sensitivity": "Confidential",
        "last_updated": (datetime.now() - timedelta(hours=3)).isoformat(),
        "last_profiled": (datetime.now() - timedelta(hours=6)).isoformat(),
        "tables": [
            {
                "name": "claims_raw",
                "schema": "insurance.claims",
                "row_count": 12_450_000,
                "freshness_hours": 2,
            },
            {
                "name": "claims_adjudicated",
                "schema": "insurance.claims",
                "row_count": 11_200_000,
                "freshness_hours": 4,
            },
            {
                "name": "claims_payments",
                "schema": "insurance.finance",
                "row_count": 9_800_000,
                "freshness_hours": 6,
            },
        ],
        "quality_score": 94.2,
        "completeness": 97.8,
        "accuracy": 96.1,
        "timeliness": 88.5,
        "uniqueness": 99.2,
        "data_contract_status": "Active",
        "sla_met": True,
    },
    "CUSTOMER": {
        "id": "dp-customer-002",
        "name": "CUSTOMER",
        "display_name": "Customer Master Data Product",
        "domain": "Customer Analytics",
        "status": "Certified",
        "owner": "Data Governance Team",
        "steward": "MDM Team",
        "description": "Golden customer record combining CRM, billing, and interaction data.",
        "sensitivity": "Highly Confidential",
        "last_updated": (datetime.now() - timedelta(hours=1)).isoformat(),
        "last_profiled": (datetime.now() - timedelta(hours=12)).isoformat(),
        "tables": [
            {
                "name": "customer_master",
                "schema": "mdm.customer",
                "row_count": 5_200_000,
                "freshness_hours": 1,
            },
            {
                "name": "customer_interactions",
                "schema": "mdm.customer",
                "row_count": 45_000_000,
                "freshness_hours": 3,
            },
        ],
        "quality_score": 91.5,
        "completeness": 95.3,
        "accuracy": 93.7,
        "timeliness": 85.2,
        "uniqueness": 98.8,
        "data_contract_status": "Active",
        "sla_met": True,
    },
    "REVENUE": {
        "id": "dp-revenue-003",
        "name": "REVENUE",
        "display_name": "Revenue Data Product",
        "domain": "Finance",
        "status": "Under Review",
        "owner": "Finance Analytics",
        "steward": "Revenue Ops",
        "description": "Revenue recognition and billing data product.",
        "sensitivity": "Highly Confidential",
        "last_updated": (datetime.now() - timedelta(days=3)).isoformat(),
        "last_profiled": (datetime.now() - timedelta(days=5)).isoformat(),
        "tables": [
            {
                "name": "revenue_daily",
                "schema": "finance.revenue",
                "row_count": 2_100_000,
                "freshness_hours": 72,
            },
            {
                "name": "billing_records",
                "schema": "finance.billing",
                "row_count": 8_400_000,
                "freshness_hours": 48,
            },
        ],
        "quality_score": 78.3,
        "completeness": 82.1,
        "accuracy": 89.4,
        "timeliness": 62.0,
        "uniqueness": 97.5,
        "data_contract_status": "Expired",
        "sla_met": False,
    },
}


def get_data_product(name: str) -> dict | None:
    """Look up a data product by name.

    Mock: in-memory dictionary.
    Real: GET https://<collibra>/rest/2.0/assets?name=<name>&typeId=<data_product_type>
    """
    return MOCK_DATA_PRODUCTS.get(name.upper())


def run_quality_checks(product: dict) -> list[dict]:
    """Run pre-flight quality checks against a data product profile."""
    checks = []

    is_certified = product["status"] == "Certified"
    checks.append(
        {
            "check": "Certification Status",
            "result": "PASS" if is_certified else "FAIL",
            "detail": (
                f"Status is '{product['status']}'. Must be 'Certified' for production use."
            ),
            "severity": "CRITICAL" if not is_certified else "INFO",
        }
    )

    dq_score = product["quality_score"]
    dq_pass = dq_score >= 90.0
    checks.append(
        {
            "check": "Data Quality Score",
            "result": "PASS" if dq_pass else "WARN",
            "detail": f"Quality score is {dq_score}%. Threshold: 90%.",
            "severity": "WARNING" if not dq_pass else "INFO",
        }
    )

    comp = product["completeness"]
    comp_pass = comp >= 95.0
    checks.append(
        {
            "check": "Completeness",
            "result": "PASS" if comp_pass else "WARN",
            "detail": f"Completeness is {comp}%. Threshold: 95%.",
            "severity": "WARNING" if not comp_pass else "INFO",
        }
    )

    time_score = product["timeliness"]
    time_pass = time_score >= 80.0
    checks.append(
        {
            "check": "Timeliness",
            "result": "PASS" if time_pass else "FAIL",
            "detail": f"Timeliness score is {time_score}%. Threshold: 80%.",
            "severity": "CRITICAL" if not time_pass else "INFO",
        }
    )

    contract_active = product["data_contract_status"] == "Active"
    checks.append(
        {
            "check": "Data Contract",
            "result": "PASS" if contract_active else "FAIL",
            "detail": f"Contract status: '{product['data_contract_status']}'. Must be 'Active'.",
            "severity": "CRITICAL" if not contract_active else "INFO",
        }
    )

    sla = product["sla_met"]
    checks.append(
        {
            "check": "SLA Compliance",
            "result": "PASS" if sla else "FAIL",
            "detail": f"SLA {'met' if sla else 'NOT met'}.",
            "severity": "CRITICAL" if not sla else "INFO",
        }
    )

    has_owner = bool(product.get("owner"))
    checks.append(
        {
            "check": "Owner Assigned",
            "result": "PASS" if has_owner else "FAIL",
            "detail": f"Owner: {product.get('owner', 'NONE')}.",
            "severity": "WARNING" if not has_owner else "INFO",
        }
    )

    has_sensitivity = bool(product.get("sensitivity"))
    checks.append(
        {
            "check": "Sensitivity Classification",
            "result": "PASS" if has_sensitivity else "WARN",
            "detail": f"Classification: {product.get('sensitivity', 'NOT SET')}.",
            "severity": "WARNING" if not has_sensitivity else "INFO",
        }
    )

    return checks


def overall_preflight_status(checks: list[dict]) -> str:
    """Return PASS, PASS WITH WARNINGS, or FAIL from check results."""
    has_critical = any(c["severity"] == "CRITICAL" and c["result"] == "FAIL" for c in checks)
    has_warning = any(c["result"] == "WARN" for c in checks)
    if has_critical:
        return "FAIL"
    if has_warning:
        return "PASS WITH WARNINGS"
    return "PASS"


def quality_dimension_status(product: dict) -> dict[str, str]:
    """Per-dimension pass/warn/fail used by the focused quality tool."""
    return {
        "completeness": "PASS" if product["completeness"] >= 95 else "WARN",
        "accuracy": "PASS" if product["accuracy"] >= 95 else "WARN",
        "timeliness": "PASS" if product["timeliness"] >= 80 else "FAIL",
        "uniqueness": "PASS" if product["uniqueness"] >= 98 else "WARN",
    }


def format_preflight_report(product: dict, checks: list[dict]) -> str:
    status = overall_preflight_status(checks)
    status_label = {
        "FAIL": "FAIL",
        "PASS WITH WARNINGS": "PASS WITH WARNINGS",
        "PASS": "PASS",
    }[status]

    passed = sum(1 for c in checks if c["result"] == "PASS")
    failed = sum(1 for c in checks if c["result"] == "FAIL")
    warned = sum(1 for c in checks if c["result"] == "WARN")

    lines = [
        f"# Pre-Flight Check Report: {product['display_name']}",
        f"**Overall Status: {status_label}**",
        "",
        "## Summary",
        f"- Data Product: {product['display_name']}",
        f"- Domain: {product['domain']}",
        f"- Owner: {product['owner']}",
        f"- Steward: {product['steward']}",
        f"- Sensitivity: {product['sensitivity']}",
        f"- Last Updated: {product['last_updated']}",
        f"- Last Profiled: {product['last_profiled']}",
        "",
        f"## Check Results ({passed} passed, {failed} failed, {warned} warnings)",
        "",
    ]

    for check in checks:
        icon = {"PASS": "PASS", "FAIL": "FAIL", "WARN": "WARN"}.get(check["result"], "?")
        lines.append(f"- {icon} **{check['check']}**: {check['result']} — {check['detail']}")

    lines.extend(["", "## Underlying Tables"])
    for table in product["tables"]:
        lines.append(
            f"- `{table['schema']}.{table['name']}` — "
            f"{table['row_count']:,} rows, last refreshed {table['freshness_hours']}h ago"
        )

    lines.append(f"\n---\n*Report generated at {datetime.now().isoformat()} (Mock Collibra)*")
    return "\n".join(lines)


def register_tools(mcp: FastMCP) -> None:
    """Register all pre-flight check tools on the MCP server."""

    @mcp.tool()
    def health() -> dict:
        """Check that the MCP server is running."""
        return {"status": "healthy", "service": "collibra-preflight-check"}

    @mcp.tool()
    def preflight_check(data_product_name: str) -> str:
        """
        Perform a comprehensive pre-flight check on a data product.
        Connects to Collibra to retrieve the data product profile and
        runs a series of governance, quality, and compliance checks.

        Args:
            data_product_name: Name of the data product (e.g., "CLAIMS", "CUSTOMER", "REVENUE")
        """
        product = get_data_product(data_product_name)
        if not product:
            available = ", ".join(MOCK_DATA_PRODUCTS.keys())
            return (
                f"Data product '{data_product_name}' not found in Collibra.\n"
                f"Available data products: {available}"
            )
        checks = run_quality_checks(product)
        return format_preflight_report(product, checks)

    @mcp.tool()
    def list_data_products() -> str:
        """List all available data products registered in Collibra."""
        lines = ["# Available Data Products\n"]
        for name, product in MOCK_DATA_PRODUCTS.items():
            lines.append(
                f"- **{product['display_name']}** ({name}) — "
                f"{product['status']} | Domain: {product['domain']} | "
                f"Quality: {product['quality_score']}%"
            )
        return "\n".join(lines)

    @mcp.tool()
    def get_data_product_details(data_product_name: str) -> str:
        """
        Get detailed metadata for a specific data product from Collibra,
        including its profile, quality scores, and table inventory.

        Args:
            data_product_name: Name of the data product (e.g., "CLAIMS")
        """
        product = get_data_product(data_product_name)
        if not product:
            available = ", ".join(MOCK_DATA_PRODUCTS.keys())
            return f"Data product '{data_product_name}' not found. Available: {available}"

        lines = [
            f"# {product['display_name']}",
            "",
            "## Metadata",
            f"- **ID**: {product['id']}",
            f"- **Domain**: {product['domain']}",
            f"- **Status**: {product['status']}",
            f"- **Owner**: {product['owner']}",
            f"- **Steward**: {product['steward']}",
            f"- **Sensitivity**: {product['sensitivity']}",
            f"- **Description**: {product['description']}",
            "",
            "## Quality Scores",
            f"- Overall Quality: **{product['quality_score']}%**",
            f"- Completeness: {product['completeness']}%",
            f"- Accuracy: {product['accuracy']}%",
            f"- Timeliness: {product['timeliness']}%",
            f"- Uniqueness: {product['uniqueness']}%",
            "",
            "## Data Contract",
            f"- Contract Status: {product['data_contract_status']}",
            f"- SLA Met: {'Yes' if product['sla_met'] else 'No'}",
            "",
            "## Tables",
        ]
        for table in product["tables"]:
            lines.append(
                f"- `{table['schema']}.{table['name']}` — "
                f"{table['row_count']:,} rows, refreshed {table['freshness_hours']}h ago"
            )
        return "\n".join(lines)

    @mcp.tool()
    def get_lineage(data_product_name: str) -> str:
        """
        Get the data lineage for a data product — upstream sources and downstream consumers.

        Args:
            data_product_name: Name of the data product (e.g., "CLAIMS")
        """
        product = get_data_product(data_product_name)
        if not product:
            return f"Data product '{data_product_name}' not found."

        first_table = product["tables"][0]
        return "\n".join(
            [
                f"# Lineage: {product['display_name']}",
                "",
                "## Upstream Sources",
                (
                    f"- `source_system.claims_extract` → ETL Pipeline → "
                    f"`{first_table['schema']}.{first_table['name']}`"
                ),
                (
                    f"- `source_system.adjudication_feed` → Streaming Ingest → "
                    f"`{first_table['schema']}.{first_table['name']}`"
                ),
                "",
                "## Downstream Consumers",
                "- `analytics.claims_dashboard` (BI Report)",
                "- `ml.claims_fraud_model` (ML Pipeline)",
                "- `reporting.regulatory_claims_extract` (Regulatory Filing)",
            ]
        )

    @mcp.tool()
    def check_data_quality(data_product_name: str) -> str:
        """
        Run a focused data quality assessment on a data product.
        Returns detailed quality metrics and dimension scores.

        Args:
            data_product_name: Name of the data product (e.g., "CLAIMS")
        """
        product = get_data_product(data_product_name)
        if not product:
            return f"Data product '{data_product_name}' not found."

        overall = product["quality_score"]
        grade = (
            "A"
            if overall >= 95
            else "B"
            if overall >= 90
            else "C"
            if overall >= 80
            else "D"
            if overall >= 70
            else "F"
        )
        dims = quality_dimension_status(product)
        return "\n".join(
            [
                f"# Data Quality Report: {product['display_name']}",
                "",
                f"## Overall Score: {overall}% (Grade: {grade})",
                "",
                "| Dimension      | Score  | Status |",
                "|----------------|--------|--------|",
                f"| Completeness   | {product['completeness']}% | {dims['completeness']} |",
                f"| Accuracy       | {product['accuracy']}%  | {dims['accuracy']} |",
                f"| Timeliness     | {product['timeliness']}%  | {dims['timeliness']} |",
                f"| Uniqueness     | {product['uniqueness']}%  | {dims['uniqueness']} |",
            ]
        )
