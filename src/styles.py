"""Streamlit CSS injection and styled dataframe helpers."""

import pandas as pd
import streamlit as st


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
