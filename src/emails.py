"""Retention email generation (plain string formatting, no external APIs)."""

import pandas as pd

from src.scoring import expected_monthly_usage


def build_retention_email(row: pd.Series) -> str:
    """Build a personalized retention email from one enriched customer row."""
    customer_name = row["customer_name"]
    plan_type = row["plan_type"]
    monthly_usage_hours = row["monthly_usage_hours"]
    support_tickets = int(row["support_tickets"])
    account_age_months = int(row["account_age_months"])
    churn_score = row["Churn Risk Score (%)"]
    risk_category = row["Risk Category"]

    month_label = "month" if account_age_months == 1 else "months"
    ticket_label = "ticket" if support_tickets == 1 else "tickets"

    usage_is_low = monthly_usage_hours < expected_monthly_usage(account_age_months)

    if risk_category == "High Risk":
        urgency_line = (
            f"Our retention team has flagged your account with a churn risk score of "
            f"{churn_score}%, and we want to intervene early — before small friction "
            f"turns into a lost partnership."
        )
    else:
        urgency_line = (
            f"We've noticed a few signals (churn risk score: {churn_score}%) that suggest "
            f"you may not be getting the full value from your {plan_type} plan yet, "
            f"and we'd love to help turn that around."
        )

    if support_tickets == 0:
        support_paragraph = (
            "Even though you haven't opened support tickets recently, we know that "
            "technical hurdles don't always show up in a ticket queue. If anything has "
            "felt slow, confusing, or harder than it should be, we want to hear about it directly."
        )
    elif support_tickets == 1:
        support_paragraph = (
            f"We see you've had to open {support_tickets} support {ticket_label} recently, "
            f"and we want to make sure that issue is fully resolved — not just closed, "
            f"but genuinely fixed so your team can move forward with confidence."
        )
    else:
        support_paragraph = (
            f"We see you've had to open {support_tickets} support {ticket_label} recently, "
            f"and we sincerely apologize for the repeated friction. That is not the experience "
            f"we want for a {plan_type} customer, and we are committed to clearing every "
            f"technical hurdle standing in your way."
        )

    if usage_is_low:
        usage_paragraph = (
            f"We also noticed your team logged about {monthly_usage_hours:.1f} usage hours "
            f"this month. Based on your {account_age_months}-{month_label} history with us, "
            f"we believe there is significant untapped value waiting — and we'd like to "
            f"personally help you unlock it."
        )
    else:
        usage_paragraph = (
            f"Your team has been active with roughly {monthly_usage_hours:.1f} usage hours "
            f"this month, which tells us you're invested. We want to make sure that investment "
            f"continues to pay off as you grow with us."
        )

    subject = f"Let's make sure {customer_name} is getting everything you need from us"

    email_body = f"""Subject: {subject}

Dear {customer_name} Team,

Thank you for being with us for {account_age_months} {month_label} — your trust means a great deal to our team.

{urgency_line}

{support_paragraph}

{usage_paragraph}

As a valued {plan_type} customer, we'd like to offer you a complimentary 1-on-1 VIP support call with one of our senior product engineers. In 30 minutes, we can:
  • Walk through any open issues or recent support history
  • Review your current usage and recommend quick wins
  • Share a tailored plan to help your team get more value from your subscription

Would you be available for a brief call this week? Simply reply to this email with a time that works for you, and we'll send a calendar invite right away.

We're here for you,
Customer Success Team
Predictive CRM
"""

    return email_body.strip()
