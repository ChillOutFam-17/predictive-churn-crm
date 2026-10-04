"""
Predictive Churn & Retention CRM Engine — Phase 1
Streamlit UI entry point. Business logic lives under src/.
"""

import pandas as pd
import streamlit as st

from src.config import PLAN_TYPES
from src.db import delete_customer, fetch_all_customers, init_database, insert_customer
from src.demo_data import insert_demo_customers, seed_if_empty
from src.emails import build_retention_email
from src.scoring import (
    build_risk_distribution_df,
    enrich_with_churn_metrics,
    get_at_risk_customers,
)
from src.styles import inject_global_styles, style_risk_table
from src.tooltips import UI_TOOLTIPS


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

    if not st.session_state.get("seed_if_empty_done"):
        seed_if_empty()
        st.session_state["seed_if_empty_done"] = True

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
