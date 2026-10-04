"""Rule-based churn scoring. Pure functions: no Streamlit, no database."""

import pandas as pd

HIGH_RISK_THRESHOLD = 70
MEDIUM_RISK_THRESHOLD = 30
RISK_ORDER = ["Healthy", "Medium Risk", "High Risk"]

# Enterprise clients expect more support, so tickets weigh less for them.
PLAN_TICKET_MULTIPLIER = {"Basic": 1.15, "Pro": 1.0, "Enterprise": 0.85}


def expected_monthly_usage(account_age_months: int) -> float:
    """Minimum healthy monthly usage hours; grows slowly with account age (floor of 3h)."""
    return max(3.0, account_age_months * 0.4)


def calculate_churn_risk(
    monthly_usage_hours: float,
    support_tickets: int,
    account_age_months: int,
    plan_type: str,
) -> float:
    """
    Churn risk score from 0 to 100.

    - Support tickets: 10 points each, capped at 50, scaled by plan type.
    - Usage vs. expectation for the account's age: up to 50 points.
    """
    ticket_points = min(support_tickets * 10, 50)
    ticket_points *= PLAN_TICKET_MULTIPLIER.get(plan_type, 1.0)
    score = min(ticket_points, 50)

    expected = expected_monthly_usage(account_age_months)
    if monthly_usage_hours < expected:
        usage_gap = 1.0 - (monthly_usage_hours / expected)
        score += min(usage_gap * 50, 50)

    return round(min(max(score, 0.0), 100.0), 1)


def get_risk_category(score: float) -> str:
    """Map a numeric score to a risk label."""
    if score > HIGH_RISK_THRESHOLD:
        return "High Risk"
    if score >= MEDIUM_RISK_THRESHOLD:
        return "Medium Risk"
    return "Healthy"


def enrich_with_churn_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add 'Churn Risk Score (%)' and 'Risk Category' columns."""
    if df.empty:
        return df

    enriched = df.copy()
    enriched["Churn Risk Score (%)"] = enriched.apply(
        lambda row: calculate_churn_risk(
            row["monthly_usage_hours"],
            row["support_tickets"],
            row["account_age_months"],
            row["plan_type"],
        ),
        axis=1,
    )
    enriched["Risk Category"] = enriched["Churn Risk Score (%)"].apply(get_risk_category)
    return enriched


def build_risk_distribution_df(df: pd.DataFrame) -> pd.DataFrame:
    """Customer counts per risk category, always ordered Healthy -> Medium -> High."""
    counts = df["Risk Category"].value_counts() if not df.empty else pd.Series(dtype=int)
    return pd.DataFrame(
        {"Customers": [int(counts.get(category, 0)) for category in RISK_ORDER]},
        index=RISK_ORDER,
    )


def get_at_risk_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Medium and High Risk customers, highest score first."""
    if df.empty:
        return df
    at_risk = df[df["Risk Category"].isin(["High Risk", "Medium Risk"])].copy()
    return at_risk.sort_values("Churn Risk Score (%)", ascending=False)
