"""Hover-tooltip copy shown across the dashboard."""

UI_TOOLTIPS = {
    "total_customers": "Total number of customer accounts stored in your SQLite CRM database.",
    "at_risk_customers": "Customers flagged as Medium Risk (30–70%) or High Risk (>70%) based on usage and support signals.",
    "healthy_customers": "Customers with a Churn Risk Score below 30% — strong engagement and low friction indicators.",
    "risk_chart": "Bar chart showing how your portfolio splits across Healthy, Medium Risk, and High Risk segments.",
    "retention_table": "Live customer portfolio with rule-based churn scoring. Hover column tags below for definitions.",
    "col_customer_name": "The company or account name stored in the CRM.",
    "col_plan_type": "Subscription tier: Basic, Pro, or Enterprise.",
    "col_monthly_usage": "Average product usage hours logged by the customer this month.",
    "col_support_tickets": "Number of support tickets raised — more tickets increase churn risk.",
    "col_account_age": "How long the customer has been subscribed, measured in months.",
    "col_churn_score": "Rule-based score from 0–100% estimating likelihood of churn. Higher = more urgent.",
    "col_risk_category": "Health label derived from the churn score: Healthy, Medium Risk, or High Risk.",
    "sidebar_total": "All customer records currently saved in the database.",
    "sidebar_at_risk": "Accounts that need proactive retention outreach.",
    "sidebar_healthy": "Accounts showing stable engagement patterns.",
}
