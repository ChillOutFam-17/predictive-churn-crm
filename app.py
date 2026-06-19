"""
Predictive Churn & Retention CRM Engine — Phase 1
A beginner-friendly Streamlit app with SQLite storage and rule-based churn scoring.
"""

import random
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

# Custom CSS for Modern SaaS Typography
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        /* Apply Inter font to the entire app */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Make headers look crisp and bold */
        h1, h2, h3 {
            font-weight: 600 !important;
            letter-spacing: -0.02em;
        }
        
        /* Style the metric cards slightly */
        div[data-testid="metric-container"] {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).parent / "crm.db"
PLAN_TYPES = ["Basic", "Pro", "Enterprise"]

# Name parts used when generating demo customers
COMPANY_PREFIXES = [
    "Acme", "Nova", "BlueSky", "TechFlow", "DataPeak", "CloudNine",
    "PixelWorks", "Zenith", "BrightPath", "CoreLogic", "SwiftScale",
    "NorthStar", "Pulse", "Vertex", "Ironclad", "Summit", "Horizon",
]
COMPANY_SUFFIXES = ["Labs", "Inc", "Corp", "Solutions", "Systems", "Co", "Analytics"]


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """Open a connection to the local SQLite database."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    """
    Create the customers table if it does not exist yet.
    Called once when the app starts.
    """
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                plan_type TEXT NOT NULL,
                monthly_usage_hours REAL NOT NULL,
                support_tickets INTEGER NOT NULL,
                account_age_months INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def insert_customer(
    customer_name: str,
    plan_type: str,
    monthly_usage_hours: float,
    support_tickets: int,
    account_age_months: int,
) -> None:
    """Save a new customer record to SQLite."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO customers
                (customer_name, plan_type, monthly_usage_hours,
                 support_tickets, account_age_months)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                customer_name.strip(),
                plan_type,
                monthly_usage_hours,
                support_tickets,
                account_age_months,
            ),
        )
        conn.commit()


def fetch_all_customers() -> pd.DataFrame:
    """Load every customer row from the database as a pandas DataFrame."""
    with get_connection() as conn:
        df = pd.read_sql_query(
            "SELECT * FROM customers ORDER BY id DESC",
            conn,
        )
    return df


def delete_customer(customer_id: int) -> None:
    """Remove a single customer by primary key."""
    with get_connection() as conn:
        conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        conn.commit()


def _random_demo_name(used_names: set[str]) -> str:
    """Build a unique fake company name for demo data."""
    for _ in range(50):
        name = f"{random.choice(COMPANY_PREFIXES)} {random.choice(COMPANY_SUFFIXES)}"
        if name not in used_names:
            used_names.add(name)
            return name
    # Fallback if we somehow exhaust combinations
    fallback = f"Demo Customer {random.randint(1000, 9999)}"
    used_names.add(fallback)
    return fallback


def _random_realistic_metrics() -> tuple[str, float, int, int]:
    """
    Generate one set of believable customer metrics.

    Returns: (plan_type, monthly_usage_hours, support_tickets, account_age_months)
    """
    # Mix of healthy, medium, and high-risk profiles for a realistic dashboard
    profile = random.choices(
        ["healthy", "medium", "high_risk"],
        weights=[40, 35, 25],
        k=1,
    )[0]
    plan_type = random.choices(PLAN_TYPES, weights=[50, 35, 15], k=1)[0]
    account_age_months = random.randint(1, 36)
    expected_usage = max(3.0, account_age_months * 0.4)

    if profile == "healthy":
        support_tickets = random.randint(0, 1)
        monthly_usage_hours = random.uniform(expected_usage, expected_usage + 25)
    elif profile == "medium":
        support_tickets = random.randint(2, 4)
        monthly_usage_hours = random.uniform(expected_usage * 0.35, expected_usage * 0.9)
    else:
        support_tickets = random.randint(4, 8)
        monthly_usage_hours = random.uniform(0.5, expected_usage * 0.35)

    # Higher-tier plans tend to have heavier product usage
    plan_usage_boost = {"Basic": 0.0, "Pro": 5.0, "Enterprise": 12.0}
    monthly_usage_hours += plan_usage_boost[plan_type] * random.uniform(0.4, 1.0)

    return (
        plan_type,
        round(monthly_usage_hours, 1),
        support_tickets,
        account_age_months,
    )


def generate_demo_customers(count: int = 20) -> list[tuple[str, str, float, int, int]]:
    """Build a list of fake customer rows ready for database insert."""
    used_names: set[str] = set()
    rows = []
    for _ in range(count):
        plan_type, usage, tickets, age = _random_realistic_metrics()
        rows.append((_random_demo_name(used_names), plan_type, usage, tickets, age))
    return rows


def insert_demo_customers(count: int = 20) -> int:
    """Insert randomly generated demo customers into SQLite."""
    rows = generate_demo_customers(count)
    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO customers
                (customer_name, plan_type, monthly_usage_hours,
                 support_tickets, account_age_months)
            VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
    return len(rows)


# ---------------------------------------------------------------------------
# Churn risk scoring (rule-based, no ML)
# ---------------------------------------------------------------------------

def calculate_churn_risk(
    monthly_usage_hours: float,
    support_tickets: int,
    account_age_months: int,
    plan_type: str,
) -> float:
    """
    Calculate a churn risk score from 0% to 100% using simple business rules.

    Rules:
    - More support tickets  -> higher risk (up to 50 points)
    - Low usage vs account age -> higher risk (up to 50 points)
    - Plan type slightly adjusts ticket sensitivity
    """
    score = 0.0

    # --- Factor 1: Support tickets (max 50 points) ---
    # Each ticket adds 10% risk; cap at 50%.
    ticket_points = min(support_tickets * 10, 50)

    # Enterprise clients often expect more support, so weight tickets a bit lower.
    # Basic clients with many tickets are a stronger churn signal.
    plan_ticket_multiplier = {
        "Basic": 1.15,
        "Pro": 1.0,
        "Enterprise": 0.85,
    }
    ticket_points *= plan_ticket_multiplier.get(plan_type, 1.0)
    score += min(ticket_points, 50)

    # --- Factor 2: Usage vs account age (max 50 points) ---
    # Longer-tenured customers should show reasonable monthly usage.
    # Expected minimum usage grows slowly with account age (at least 3 hours).
    expected_usage = max(3.0, account_age_months * 0.4)

    if monthly_usage_hours >= expected_usage:
        usage_points = 0.0
    else:
        # How far below the expected usage (0 = at expected, 1 = zero usage)
        usage_gap = 1.0 - (monthly_usage_hours / expected_usage)
        usage_points = min(usage_gap * 50, 50)

    score += usage_points

    # Keep the final score inside 0–100
    return round(min(max(score, 0.0), 100.0), 1)


def get_risk_category(score: float) -> str:
    """Map a numeric score to a human-readable risk label."""
    if score > 70:
        return "High Risk"
    if score >= 30:
        return "Medium Risk"
    return "Healthy"


def enrich_with_churn_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add Churn Risk Score and Risk Category columns to a customer DataFrame."""
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
    """
    Count customers in each risk category for the dashboard bar chart.
    Categories are always shown in Healthy -> Medium -> High order.
    """
    risk_order = ["Healthy", "Medium Risk", "High Risk"]
    counts = df["Risk Category"].value_counts() if not df.empty else pd.Series(dtype=int)
    return pd.DataFrame(
        {"Customers": [int(counts.get(category, 0)) for category in risk_order]},
        index=risk_order,
    )


def style_risk_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a styled DataFrame for Streamlit display.
    Applies dark-theme pill badges to churn scores and risk categories.
    """
    pill_base = (
        "border-radius: 999px; padding: 6px 14px; font-weight: 700; "
        "text-align: center; letter-spacing: 0.02em; display: inline-block; "
        "min-width: 88px;"
    )

    def color_risk_category(value: str) -> str:
        colors = {
            "High Risk": (
                f"{pill_base} background: rgba(248, 113, 113, 0.16); "
                "color: #fca5a5; border: 1px solid rgba(248, 113, 113, 0.55); "
                "box-shadow: 0 0 12px rgba(248, 113, 113, 0.25);"
            ),
            "Medium Risk": (
                f"{pill_base} background: rgba(251, 191, 36, 0.16); "
                "color: #fcd34d; border: 1px solid rgba(251, 191, 36, 0.55); "
                "box-shadow: 0 0 12px rgba(251, 191, 36, 0.2);"
            ),
            "Healthy": (
                f"{pill_base} background: rgba(45, 212, 191, 0.16); "
                "color: #5eead4; border: 1px solid rgba(45, 212, 191, 0.55); "
                "box-shadow: 0 0 12px rgba(45, 212, 191, 0.22);"
            ),
        }
        return colors.get(value, "")

    def color_churn_score(value: float) -> str:
        if value > 70:
            return (
                f"{pill_base} background: rgba(248, 113, 113, 0.12); "
                "color: #fca5a5; border: 1px solid rgba(248, 113, 113, 0.45); "
                "box-shadow: 0 0 10px rgba(248, 113, 113, 0.18);"
            )
        if value >= 30:
            return (
                f"{pill_base} background: rgba(251, 191, 36, 0.12); "
                "color: #fcd34d; border: 1px solid rgba(251, 191, 36, 0.45); "
                "box-shadow: 0 0 10px rgba(251, 191, 36, 0.16);"
            )
        return (
            f"{pill_base} background: rgba(45, 212, 191, 0.12); "
            "color: #5eead4; border: 1px solid rgba(45, 212, 191, 0.45); "
            "box-shadow: 0 0 10px rgba(45, 212, 191, 0.18);"
        )

    display_columns = [
        "customer_name",
        "plan_type",
        "monthly_usage_hours",
        "support_tickets",
        "account_age_months",
        "Churn Risk Score (%)",
        "Risk Category",
    ]
    display_df = df[display_columns].rename(
        columns={
            "customer_name": "Customer Name",
            "plan_type": "Plan Type",
            "monthly_usage_hours": "Monthly Usage (hrs)",
            "support_tickets": "Support Tickets",
            "account_age_months": "Account Age (months)",
        }
    )

    table_styles = [
        {
            "selector": "thead th",
            "props": [
                ("background-color", "rgba(15, 23, 42, 0.95)"),
                ("color", "#94a3b8"),
                ("border", "none"),
                ("border-bottom", "1px solid rgba(148, 163, 184, 0.12)"),
                ("font-size", "0.78rem"),
                ("font-weight", "700"),
                ("text-transform", "uppercase"),
                ("letter-spacing", "0.06em"),
                ("padding", "14px 12px"),
            ],
        },
        {
            "selector": "tbody td",
            "props": [
                ("background-color", "rgba(15, 23, 42, 0.35)"),
                ("color", "#e2e8f0"),
                ("border", "none"),
                ("border-bottom", "1px solid rgba(148, 163, 184, 0.06)"),
                ("padding", "12px"),
            ],
        },
        {
            "selector": "tbody tr:hover td",
            "props": [
                ("background-color", "rgba(51, 65, 85, 0.45)"),
            ],
        },
        {
            "selector": "table",
            "props": [
                ("border-collapse", "collapse"),
                ("border", "none"),
                ("width", "100%"),
            ],
        },
    ]

    styled = (
        display_df.style.set_table_styles(table_styles)
        .map(color_churn_score, subset=["Churn Risk Score (%)"])
        .map(color_risk_category, subset=["Risk Category"])
        .format({"Churn Risk Score (%)": "{:.1f}%"})
    )
    return styled


def get_at_risk_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Return customers tagged as High Risk or Medium Risk, sorted by score descending."""
    if df.empty:
        return df

    at_risk = df[df["Risk Category"].isin(["High Risk", "Medium Risk"])].copy()
    return at_risk.sort_values("Churn Risk Score (%)", ascending=False)


def build_retention_email(row: pd.Series) -> str:
    """
    Build a personalized retention email using the customer's database fields.
    Pure Python string formatting — no external APIs or ML.
    """
    customer_name = row["customer_name"]
    plan_type = row["plan_type"]
    monthly_usage_hours = row["monthly_usage_hours"]
    support_tickets = int(row["support_tickets"])
    account_age_months = int(row["account_age_months"])
    churn_score = row["Churn Risk Score (%)"]
    risk_category = row["Risk Category"]

    month_label = "month" if account_age_months == 1 else "months"
    ticket_label = "ticket" if support_tickets == 1 else "tickets"

    expected_usage = max(3.0, account_age_months * 0.4)
    usage_is_low = monthly_usage_hours < expected_usage

    # Tone shifts slightly based on how urgent the churn signal is
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

    # Support ticket paragraph — empathetic and specific to their count
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

    # Usage paragraph — references their actual hours vs expectations
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


def render_retention_action_tool(enriched_df: pd.DataFrame) -> None:
    """Dashboard section: pick an at-risk customer and generate a retention email."""
    st.markdown("### ✉️ Customer Retention Action Tool")
    st.caption(
        "Select an at-risk customer and generate a tailored outreach email for your sales team."
    )

    at_risk_df = get_at_risk_customers(enriched_df)

    if at_risk_df.empty:
        st.info(
            "No **High Risk** or **Medium Risk** customers right now. "
            "Add more data or generate demo customers to use this tool."
        )
        return

    with st.container(border=True):
        at_risk_df = at_risk_df.copy()
        at_risk_df["select_label"] = at_risk_df.apply(
            lambda row: (
                f"{row['customer_name']} — {row['Risk Category']} "
                f"({row['Churn Risk Score (%)']}%)"
            ),
            axis=1,
        )

        selected_label = st.selectbox(
            "🎯 Select an at-risk customer",
            at_risk_df["select_label"].tolist(),
            help="Only customers flagged as Medium Risk or High Risk appear here.",
        )
        selected_row = at_risk_df[at_risk_df["select_label"] == selected_label].iloc[0]

        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
        summary_col1.metric(
            "Plan",
            selected_row["plan_type"],
            help=UI_TOOLTIPS["col_plan_type"],
        )
        summary_col2.metric(
            "Churn Score",
            f"{selected_row['Churn Risk Score (%)']}%",
            help=UI_TOOLTIPS["col_churn_score"],
        )
        summary_col3.metric(
            "Support Tickets",
            int(selected_row["support_tickets"]),
            help=UI_TOOLTIPS["col_support_tickets"],
        )
        summary_col4.metric(
            "Account Age",
            f"{int(selected_row['account_age_months'])} mo",
            help=UI_TOOLTIPS["col_account_age"],
        )

        st.divider()

        if st.button("Generate Personalized Retention Email", type="primary", use_container_width=True):
            st.session_state["retention_email"] = build_retention_email(selected_row)
            st.session_state["retention_email_customer"] = selected_row["customer_name"]

        if st.session_state.get("retention_email"):
            if st.session_state.get("retention_email_customer") != selected_row["customer_name"]:
                st.caption(
                    "Showing the last generated email. Click the button again to refresh "
                    "for the newly selected customer."
                )

            st.text_area(
                "Generated retention email (select all and copy)",
                value=st.session_state["retention_email"],
                height=420,
                label_visibility="collapsed",
            )


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

# Hover tooltips shown across dashboard metrics, charts, and table columns
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


def inject_global_styles() -> None:
    """Apply dark glassmorphism theme with neon accents across the Streamlit app."""
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

            :root {
                --bg-deep: #070b14;
                --bg-slate: #0f172a;
                --glass: rgba(15, 23, 42, 0.62);
                --glass-border: rgba(148, 163, 184, 0.14);
                --text-primary: #f1f5f9;
                --text-muted: #94a3b8;
                --neon-teal: #2dd4bf;
                --neon-amber: #fbbf24;
                --neon-coral: #f87171;
                --neon-violet: #a78bfa;
            }

            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif;
            }

            .stApp {
                background:
                    radial-gradient(circle at 10% 10%, rgba(45, 212, 191, 0.08), transparent 28%),
                    radial-gradient(circle at 90% 0%, rgba(167, 139, 250, 0.10), transparent 30%),
                    radial-gradient(circle at 50% 100%, rgba(251, 191, 36, 0.06), transparent 35%),
                    linear-gradient(180deg, #070b14 0%, #0b1220 45%, #0a1020 100%);
                color: var(--text-primary);
            }

            .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
                max-width: 1440px;
            }

            [data-testid="stSidebar"] {
                background: rgba(7, 11, 20, 0.92);
                border-right: 1px solid rgba(45, 212, 191, 0.12);
                backdrop-filter: blur(16px);
            }

            [data-testid="stSidebar"] .crm-subtitle,
            [data-testid="stSidebar"] .crm-section-label,
            [data-testid="stSidebar"] p,
            [data-testid="stSidebar"] span,
            [data-testid="stSidebar"] label {
                color: var(--text-muted) !important;
            }

            h1, h2, h3, h4, h5, h6,
            [data-testid="stMarkdownContainer"] p,
            [data-testid="stMarkdownContainer"] li {
                color: var(--text-primary) !important;
            }

            .crm-subtitle {
                color: var(--text-muted) !important;
                font-size: 1.02rem;
                line-height: 1.6;
                margin-bottom: 0.75rem;
            }

            .crm-section-label {
                color: #64748b !important;
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                margin: 1.75rem 0 1rem 0;
            }

            .dashboard-spacer {
                height: 2rem;
            }

            .dashboard-spacer-lg {
                height: 2.75rem;
            }

            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 1.5rem;
                margin: 1.5rem 0 2.75rem 0;
            }

            .metric-card {
                position: relative;
                overflow: hidden;
                padding: 1.35rem 1.4rem 1.2rem 1.4rem;
                border-radius: 18px;
                background: rgba(15, 23, 42, 0.55);
                backdrop-filter: blur(18px);
                border: 1px solid rgba(148, 163, 184, 0.14);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.28);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }

            .metric-card:hover {
                transform: translateY(-2px);
            }

            .metric-card::before {
                content: "";
                position: absolute;
                inset: 0;
                background: linear-gradient(135deg, rgba(255,255,255,0.05), transparent 55%);
                pointer-events: none;
            }

            .metric-icon {
                font-size: 1.45rem;
                margin-bottom: 0.65rem;
            }

            .metric-label {
                color: #94a3b8;
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin-bottom: 0.45rem;
                cursor: help;
            }

            .metric-value {
                color: #f8fafc;
                font-size: 2.35rem;
                font-weight: 800;
                line-height: 1;
            }

            .metric-total {
                border-color: rgba(167, 139, 250, 0.35);
                box-shadow: 0 0 24px rgba(167, 139, 250, 0.12), inset 0 0 0 1px rgba(167, 139, 250, 0.08);
            }

            .metric-at-risk {
                border-color: rgba(251, 191, 36, 0.42);
                box-shadow: 0 0 28px rgba(251, 191, 36, 0.16), inset 0 0 0 1px rgba(251, 191, 36, 0.08);
            }

            .metric-healthy {
                border-color: rgba(45, 212, 191, 0.42);
                box-shadow: 0 0 28px rgba(45, 212, 191, 0.16), inset 0 0 0 1px rgba(45, 212, 191, 0.08);
            }

            .glass-panel-title {
                color: #f8fafc;
                font-size: 1.05rem;
                font-weight: 700;
                margin-bottom: 0.35rem;
            }

            .glass-panel-caption {
                color: #94a3b8;
                font-size: 0.92rem;
                margin-bottom: 1rem;
            }

            .tooltip-chip-row {
                display: flex;
                flex-wrap: wrap;
                gap: 0.55rem;
                margin: 0 0 1rem 0;
            }

            .tooltip-chip {
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                padding: 0.35rem 0.7rem;
                border-radius: 999px;
                background: rgba(30, 41, 59, 0.75);
                border: 1px solid rgba(148, 163, 184, 0.14);
                color: #cbd5e1;
                font-size: 0.72rem;
                font-weight: 600;
                cursor: help;
            }

            .legend-pill {
                display: inline-block;
                padding: 0.45rem 0.75rem;
                border-radius: 999px;
                margin: 0.25rem 0;
                font-size: 0.82rem;
                font-weight: 600;
            }

            .legend-healthy {
                color: #5eead4;
                background: rgba(45, 212, 191, 0.12);
                border: 1px solid rgba(45, 212, 191, 0.28);
            }

            .legend-medium {
                color: #fcd34d;
                background: rgba(251, 191, 36, 0.12);
                border: 1px solid rgba(251, 191, 36, 0.28);
            }

            .legend-high {
                color: #fca5a5;
                background: rgba(248, 113, 113, 0.12);
                border: 1px solid rgba(248, 113, 113, 0.28);
            }

            div[data-testid="stMetric"] {
                background: rgba(15, 23, 42, 0.55);
                border: 1px solid rgba(148, 163, 184, 0.14);
                border-radius: 14px;
                padding: 0.85rem 1rem;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);
                backdrop-filter: blur(12px);
            }

            div[data-testid="stMetric"] label {
                color: #94a3b8 !important;
            }

            div[data-testid="stMetric"] [data-testid="stMetricValue"] {
                color: #f8fafc !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: rgba(15, 23, 42, 0.48) !important;
                border: 1px solid rgba(148, 163, 184, 0.14) !important;
                border-radius: 18px !important;
                backdrop-filter: blur(16px);
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.24);
                padding: 1.25rem !important;
                margin-bottom: 1.75rem;
            }

            [data-testid="stDataFrame"],
            [data-testid="stDataFrame"] > div {
                background: transparent !important;
                border: none !important;
            }

            [data-testid="stDataFrame"] table {
                border: none !important;
            }

            [data-testid="stTabs"] [data-baseweb="tab-list"] {
                gap: 0.5rem;
                background: rgba(15, 23, 42, 0.45);
                padding: 0.35rem;
                border-radius: 14px;
                border: 1px solid rgba(148, 163, 184, 0.12);
            }

            [data-testid="stTabs"] [data-baseweb="tab"] {
                border-radius: 10px;
                color: #94a3b8;
                padding: 0.55rem 1rem;
            }

            [data-testid="stTabs"] [aria-selected="true"] {
                background: rgba(45, 212, 191, 0.12) !important;
                color: #5eead4 !important;
                border: 1px solid rgba(45, 212, 191, 0.25) !important;
            }

            .stButton > button {
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.18);
                background: rgba(30, 41, 59, 0.85);
                color: #e2e8f0;
                font-weight: 600;
                transition: all 0.2s ease;
            }

            .stButton > button:hover {
                border-color: rgba(45, 212, 191, 0.45);
                box-shadow: 0 0 18px rgba(45, 212, 191, 0.18);
                color: #5eead4;
            }

            .stButton > button[kind="primary"] {
                background: linear-gradient(135deg, rgba(45, 212, 191, 0.85), rgba(20, 184, 166, 0.85));
                color: #042f2e;
                border: none;
                box-shadow: 0 0 22px rgba(45, 212, 191, 0.25);
            }

            .stTextInput input, .stNumberInput input, .stSelectbox div, .stTextArea textarea {
                background: rgba(15, 23, 42, 0.75) !important;
                color: #e2e8f0 !important;
                border: 1px solid rgba(148, 163, 184, 0.18) !important;
                border-radius: 12px !important;
            }

            hr {
                border-color: rgba(148, 163, 184, 0.12) !important;
                margin: 2rem 0 !important;
            }

            [data-testid="stAlert"] {
                background: rgba(15, 23, 42, 0.72);
                border: 1px solid rgba(148, 163, 184, 0.14);
                border-radius: 14px;
                color: #e2e8f0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard_metric_cards(total: int, at_risk: int, healthy: int) -> None:
    """Render glowing glass metric cards for the dashboard header row."""
    st.markdown(
        f"""
        <div class="metrics-grid">
            <div class="metric-card metric-total">
                <div class="metric-icon">👥</div>
                <div class="metric-label" title="{UI_TOOLTIPS['total_customers']}">Total Customers</div>
                <div class="metric-value">{total}</div>
            </div>
            <div class="metric-card metric-at-risk">
                <div class="metric-icon">⚠️</div>
                <div class="metric-label" title="{UI_TOOLTIPS['at_risk_customers']}">At-Risk Customers</div>
                <div class="metric-value">{at_risk}</div>
            </div>
            <div class="metric-card metric-healthy">
                <div class="metric-icon">✅</div>
                <div class="metric-label" title="{UI_TOOLTIPS['healthy_customers']}">Healthy Customers</div>
                <div class="metric-value">{healthy}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_table_column_tooltips() -> None:
    """Show hover-friendly column definitions above the retention table."""
    st.markdown(
        f"""
        <div class="tooltip-chip-row">
            <span class="tooltip-chip" title="{UI_TOOLTIPS['col_customer_name']}">🏢 Customer Name</span>
            <span class="tooltip-chip" title="{UI_TOOLTIPS['col_plan_type']}">💳 Plan Type</span>
            <span class="tooltip-chip" title="{UI_TOOLTIPS['col_monthly_usage']}">⏱️ Monthly Usage</span>
            <span class="tooltip-chip" title="{UI_TOOLTIPS['col_support_tickets']}">🎫 Support Tickets</span>
            <span class="tooltip-chip" title="{UI_TOOLTIPS['col_account_age']}">📅 Account Age</span>
            <span class="tooltip-chip" title="{UI_TOOLTIPS['col_churn_score']}">📉 Churn Risk Score</span>
            <span class="tooltip-chip" title="{UI_TOOLTIPS['col_risk_category']}">🚦 Risk Category</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_heading(title: str, caption: str, tooltip: str = "") -> None:
    """Render a section title with optional hover tooltip on the heading."""
    tooltip_attr = f'title="{tooltip}"' if tooltip else ""
    st.markdown(
        f'<div class="glass-panel-title" {tooltip_attr}>{title}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="glass-panel-caption">{caption}</div>', unsafe_allow_html=True)


def render_sidebar() -> None:
    """Sidebar navigation, branding, and live database snapshot."""
    with st.sidebar:
        st.markdown("## 💼 Retention CRM")
        st.markdown(
            '<p class="crm-subtitle">Predictive churn intelligence for customer success teams.</p>',
            unsafe_allow_html=True,
        )
        st.divider()

        st.markdown('<p class="crm-section-label">Workspace</p>', unsafe_allow_html=True)
        st.markdown("📋 **Add/Manage** — Capture and edit customer records")
        st.markdown("📈 **Dashboard** — Monitor risk, trends, and outreach")
        st.divider()

        st.markdown('<p class="crm-section-label">Live Snapshot</p>', unsafe_allow_html=True)
        customers_df = fetch_all_customers()
        enriched_df = enrich_with_churn_metrics(customers_df)
        at_risk_count = 0
        healthy_count = 0
        if not enriched_df.empty:
            at_risk_count = enriched_df["Risk Category"].isin(["High Risk", "Medium Risk"]).sum()
            healthy_count = (enriched_df["Risk Category"] == "Healthy").sum()

        snap1, snap2 = st.columns(2)
        snap1.metric(
            "Total",
            len(customers_df),
            help=UI_TOOLTIPS["sidebar_total"],
        )
        snap2.metric(
            "At-Risk",
            at_risk_count,
            help=UI_TOOLTIPS["sidebar_at_risk"],
        )
        st.metric(
            "Healthy Accounts",
            healthy_count,
            help=UI_TOOLTIPS["sidebar_healthy"],
        )

        st.divider()
        st.caption("Phase 1 · Rule-based scoring · SQLite backend")


def render_page_header() -> None:
    """Main page hero with title and product description."""
    st.markdown('<p class="crm-section-label">Enterprise SaaS · Customer Success</p>', unsafe_allow_html=True)
    st.title("📊 Predictive Churn & Retention CRM")
    st.markdown(
        '<p class="crm-subtitle">Monitor account health, identify churn signals early, '
        "and take personalized retention action — all in one workspace.</p>",
        unsafe_allow_html=True,
    )
    st.divider()


def render_add_manage_tab() -> None:
    """Tab 1: Form to add customers and a simple manage/delete section."""
    st.markdown("### 👤 Customer Management")
    st.caption("Create new customer records and maintain your local CRM database.")

    with st.container(border=True):
        st.markdown("#### ➕ Add a New Customer")
        st.caption("Fill in the details below and click **Save Customer**.")

        with st.form("customer_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                customer_name = st.text_input(
                    "Customer Name *",
                    placeholder="e.g. Acme Corp",
                    help=UI_TOOLTIPS["col_customer_name"],
                )
                plan_type = st.selectbox(
                    "Plan Type *",
                    PLAN_TYPES,
                    help=UI_TOOLTIPS["col_plan_type"],
                )
                monthly_usage_hours = st.number_input(
                    "Monthly Usage Hours *",
                    min_value=0.0,
                    step=0.5,
                    format="%.1f",
                    help=UI_TOOLTIPS["col_monthly_usage"],
                )

            with col2:
                support_tickets = st.number_input(
                    "Support Tickets Raised *",
                    min_value=0,
                    step=1,
                    help=UI_TOOLTIPS["col_support_tickets"],
                )
                account_age_months = st.number_input(
                    "Account Age (months) *",
                    min_value=0,
                    step=1,
                    help=UI_TOOLTIPS["col_account_age"],
                )

            submitted = st.form_submit_button("💾 Save Customer", type="primary", use_container_width=True)

    if submitted:
        if not customer_name.strip():
            st.error("Customer Name is required.")
        else:
            insert_customer(
                customer_name=customer_name,
                plan_type=plan_type,
                monthly_usage_hours=monthly_usage_hours,
                support_tickets=int(support_tickets),
                account_age_months=int(account_age_months),
            )
            st.success(f"Customer **{customer_name.strip()}** saved successfully!")
            st.balloons()

    st.divider()
    st.markdown("### 🗂️ Manage Existing Customers")

    customers_df = fetch_all_customers()
    if customers_df.empty:
        st.info("No customers yet. Add your first customer using the form above.")
        return

    with st.container(border=True):
        manage_df = customers_df[
            ["id", "customer_name", "plan_type", "monthly_usage_hours", "support_tickets", "account_age_months"]
        ].rename(
            columns={
                "id": "ID",
                "customer_name": "Customer Name",
                "plan_type": "Plan Type",
                "monthly_usage_hours": "Monthly Usage (hrs)",
                "support_tickets": "Support Tickets",
                "account_age_months": "Account Age (months)",
            }
        )
        st.dataframe(manage_df, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("#### 🗑️ Remove a Customer")
    delete_col1, delete_col2 = st.columns([1, 3])
    with delete_col1:
        delete_id = st.number_input(
            "Customer ID to delete",
            min_value=1,
            step=1,
            label_visibility="collapsed",
        )
    with delete_col2:
        if st.button("Delete Customer", type="secondary"):
            matching = customers_df[customers_df["id"] == delete_id]
            if matching.empty:
                st.warning(f"No customer found with ID {delete_id}.")
            else:
                name = matching.iloc[0]["customer_name"]
                delete_customer(int(delete_id))
                st.success(f"Deleted customer **{name}** (ID {delete_id}).")
                st.rerun()


def render_dashboard_tab() -> None:
    """Tab 2: Retention dashboard with churn scores and color-coded risk tags."""
    header_col, action_col = st.columns([3, 1])
    with header_col:
        st.markdown("### 📈 Retention Dashboard")
        st.caption("Live portfolio view with rule-based churn scoring and retention workflows.")
    with action_col:
        if st.button("🎲 Generate Demo Data", type="secondary", use_container_width=True):
            inserted = insert_demo_customers(20)
            st.success(f"Added {inserted} demo customers.")
            st.rerun()

    st.divider()

    customers_df = fetch_all_customers()

    if customers_df.empty:
        st.info(
            "📭 **No customer data yet.** Click **Generate Demo Data** above or add customers "
            "manually under **Add/Manage Customers**."
        )
        return

    st.markdown('<div class="dashboard-spacer"></div>', unsafe_allow_html=True)

    enriched_df = enrich_with_churn_metrics(customers_df)

    at_risk = enriched_df["Risk Category"].isin(["High Risk", "Medium Risk"]).sum()
    healthy = (enriched_df["Risk Category"] == "Healthy").sum()
    total = len(enriched_df)

    st.markdown('<p class="crm-section-label">Key Business Metrics</p>', unsafe_allow_html=True)
    render_dashboard_metric_cards(total, at_risk, healthy)

    st.markdown('<div class="dashboard-spacer-lg"></div>', unsafe_allow_html=True)
    st.markdown('<p class="crm-section-label">Analytics & Portfolio Data</p>', unsafe_allow_html=True)

    chart_col, table_col = st.columns([2, 3], gap="large")

    with chart_col:
        with st.container(border=True):
            render_section_heading(
                "📊 Risk Distribution",
                "Customer counts by churn risk category.",
                UI_TOOLTIPS["risk_chart"],
            )
            risk_chart_df = build_risk_distribution_df(enriched_df)
            st.bar_chart(risk_chart_df, use_container_width=True)

            st.markdown("##### Risk Legend")
            st.markdown(
                f'<span class="legend-pill legend-healthy" title="{UI_TOOLTIPS["healthy_customers"]}">'
                "🟢 Healthy — Churn Risk &lt; 30%</span>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<span class="legend-pill legend-medium" title="{UI_TOOLTIPS["at_risk_customers"]}">'
                "🟡 Medium Risk — Churn Risk 30%–70%</span>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<span class="legend-pill legend-high" title="{UI_TOOLTIPS["at_risk_customers"]}">'
                "🔴 High Risk — Churn Risk &gt; 70%</span>",
                unsafe_allow_html=True,
            )

    with table_col:
        with st.container(border=True):
            render_section_heading(
                "📋 Customer Retention Table",
                "Interactive portfolio view with live churn scoring and color-coded risk pills.",
                UI_TOOLTIPS["retention_table"],
            )
            render_table_column_tooltips()
            st.dataframe(
                style_risk_table(enriched_df),
                use_container_width=True,
                hide_index=True,
            )

    st.markdown('<div class="dashboard-spacer-lg"></div>', unsafe_allow_html=True)
    render_retention_action_tool(enriched_df)


def main() -> None:
    """App entry point: configure page, init DB, and render tabs."""
    st.set_page_config(
        page_title="Predictive Churn CRM",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_global_styles()
    init_database()
    render_sidebar()
    render_page_header()

    tab_add, tab_dashboard = st.tabs(
        ["👤 Add / Manage Customers", "📈 Retention Dashboard"]
    )

    with tab_add:
        render_add_manage_tab()

    with tab_dashboard:
        render_dashboard_tab()


if __name__ == "__main__":
    main()
