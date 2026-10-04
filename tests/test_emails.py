import pandas as pd

from src.emails import build_retention_email


def _row(**overrides) -> pd.Series:
    data = {
        "customer_name": "Acme Labs",
        "plan_type": "Pro",
        "monthly_usage_hours": 2.0,
        "support_tickets": 5,
        "account_age_months": 12,
        "Churn Risk Score (%)": 92.5,
        "Risk Category": "High Risk",
    }
    data.update(overrides)
    return pd.Series(data)


def test_email_uses_customer_fields():
    email = build_retention_email(_row())
    assert "Dear Acme Labs Team" in email
    assert "92.5%" in email
    assert "5 support tickets" in email


def test_high_risk_and_medium_risk_use_different_openers():
    high = build_retention_email(_row())
    medium = build_retention_email(_row(**{"Risk Category": "Medium Risk"}))
    assert "intervene early" in high
    assert "intervene early" not in medium


def test_singular_labels_for_one_month_and_one_ticket():
    email = build_retention_email(_row(account_age_months=1, support_tickets=1))
    assert "1 months" not in email
    assert "1 support ticket " in email


def test_zero_tickets_uses_proactive_wording():
    assert "haven't opened support tickets" in build_retention_email(_row(support_tickets=0))
