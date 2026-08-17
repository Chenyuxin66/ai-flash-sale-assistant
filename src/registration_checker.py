"""
AI Registration Assistant
==========================
Validates seller submission completeness for Flash Sale registration.

Checks that all required fields are present and valid:
    - Product link
    - SKU
    - Discount information
    - Stock information

Outputs a checklist with missing items and follow-up suggestions.
"""

import pandas as pd
from dataclasses import dataclass, field
from typing import Optional


# Required fields for Flash Sale registration
REQUIRED_FIELDS = {
    "product_link": {
        "label": "Product Link",
        "description": "Direct product page URL on the platform",
        "validator": lambda x: isinstance(x, str) and x.startswith("http"),
    },
    "sku": {
        "label": "SKU",
        "description": "Stock Keeping Unit identifier for the product",
        "validator": lambda x: isinstance(x, str) and len(x.strip()) > 0,
    },
    "has_discount": {
        "label": "Discount Info",
        "description": "Whether a flash sale discount has been set",
        "validator": lambda x: isinstance(x, str) and x.lower() in ("yes", "true", "1"),
    },
    "has_stock": {
        "label": "Stock Info",
        "description": "Whether stock quantity has been confirmed",
        "validator": lambda x: isinstance(x, str) and x.lower() in ("yes", "true", "1"),
    },
}


@dataclass
class RegistrationCheckResult:
    """Result of a single product's registration check."""
    product_id: str
    product_name: str
    is_complete: bool
    missing_fields: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    follow_up_actions: list[str] = field(default_factory=list)


class RegistrationChecker:
    """
    Checks seller submission completeness for Flash Sale registration.

    This implements the "AI Registration Assistant" feature from the product spec.
    It automates the manual follow-up process where operators check each seller's
    submission for missing or invalid information.

    Usage:
        checker = RegistrationChecker()
        results = checker.check_all(df)
        incomplete = checker.get_incomplete(results)
        checker.generate_followup_message(results, "seller_name")
    """

    def check_single(self, row: pd.Series) -> RegistrationCheckResult:
        """Check a single product's registration completeness."""
        product_id = str(row.get("product_id", "Unknown"))
        product_name = str(row.get("product_name", "Unknown"))

        missing = []
        issues = []
        actions = []

        for field_name, config in REQUIRED_FIELDS.items():
            value = row.get(field_name, "")
            is_valid = config["validator"](value)

            if not is_valid:
                missing.append(config["label"])
                issues.append(f"Missing or invalid: {config['label']} - {config['description']}")
                actions.append(f"Please provide {config['label']} for product {product_id} ({product_name})")

        # Additional validation: stock units check
        stock = row.get("stock_units", 0)
        if isinstance(stock, (int, float)) and stock < 100:
            issues.append(f"Low stock ({stock} units) - recommend minimum 100 units for flash sale")
            actions.append(f"Increase stock for {product_name} (current: {stock}, recommended: >=100)")

        # Discount depth check
        discount = row.get("discount_pct", 0)
        if isinstance(discount, (int, float)) and discount < 20:
            issues.append(f"Low discount ({discount}%) - flash sale discounts should be >= 20%")
            actions.append(f"Increase discount for {product_name} (current: {discount}%, recommended: >=20%)")

        is_complete = len(missing) == 0

        return RegistrationCheckResult(
            product_id=product_id,
            product_name=product_name,
            is_complete=is_complete,
            missing_fields=missing,
            issues=issues,
            follow_up_actions=actions,
        )

    def check_all(self, df: pd.DataFrame) -> list[RegistrationCheckResult]:
        """Check all products in the dataframe."""
        results = []
        for _, row in df.iterrows():
            results.append(self.check_single(row))
        return results

    def get_incomplete(self, results: list[RegistrationCheckResult]) -> list[RegistrationCheckResult]:
        """Filter to only incomplete registrations."""
        return [r for r in results if not r.is_complete]

    def get_completion_rate(self, results: list[RegistrationCheckResult]) -> float:
        """Calculate the percentage of complete registrations."""
        if not results:
            return 0.0
        complete = sum(1 for r in results if r.is_complete)
        return round(complete / len(results) * 100, 1)

    def generate_followup_message(
        self, results: list[RegistrationCheckResult], seller_name: str = "Seller"
    ) -> str:
        """
        Generate a formatted follow-up message for sellers with incomplete submissions.
        This mimics the AM (Account Manager) outreach workflow.
        """
        incomplete = self.get_incomplete(results)

        if not incomplete:
            return f"Hi {seller_name}, all your Flash Sale submissions are complete. Thank you!"

        lines = [
            f"Hi {seller_name},",
            f"",
            f"Your Flash Sale registration has {len(incomplete)} product(s) with missing information:",
            f"",
        ]

        for r in incomplete:
            lines.append(f"  [{r.product_id}] {r.product_name}")
            if r.missing_fields:
                lines.append(f"    Missing: {', '.join(r.missing_fields)}")
            for issue in r.issues:
                lines.append(f"    - {issue}")
            lines.append("")

        lines.append("Please complete the above by [deadline] to secure your Flash Sale quota.")
        lines.append("")
        lines.append("Best regards,")
        lines.append("Flash Sale Operations Team")

        return "\n".join(lines)

    def format_summary(self, results: list[RegistrationCheckResult]) -> str:
        """Format a summary report of registration status."""
        total = len(results)
        complete = sum(1 for r in results if r.is_complete)
        incomplete = total - complete
        rate = self.get_completion_rate(results)

        lines = [
            "=" * 60,
            "  Flash Sale Registration Status Summary",
            "=" * 60,
            f"",
            f"  Total Products:     {total}",
            f"  Complete:           {complete}",
            f"  Incomplete:         {incomplete}",
            f"  Completion Rate:    {rate}%",
            f"",
        ]

        if incomplete > 0:
            lines.append("  [Incomplete Products]")
            for r in self.get_incomplete(results):
                missing_str = ", ".join(r.missing_fields) if r.missing_fields else "Other issues"
                lines.append(f"    {r.product_id} - {r.product_name}: {missing_str}")

        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)
