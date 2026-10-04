import pandas as pd

from src.scoring import (
    build_risk_distribution_df,
    calculate_churn_risk,
    enrich_with_churn_metrics,
    expected_monthly_usage,
    get_at_risk_customers,
    get_risk_category,
)


def test_expected_usage_has_a_floor_and_grows_with_age():
    assert expected_monthly_usage(1) == 3.0
    assert expected_monthly_usage(20) == 8.0


def test_healthy_account_scores_zero():
    # age 10 -> expected usage 4.0h; 10h usage and no tickets means no risk
    assert calculate_churn_risk(10, 0, 10, "Pro") == 0.0


def test_each_ticket_adds_ten_points_for_pro():
    assert calculate_churn_risk(10, 3, 10, "Pro") == 30.0


def test_plan_type_scales_ticket_risk():
    basic = calculate_churn_risk(10, 3, 10, "Basic")
    pro = calculate_churn_risk(10, 3, 10, "Pro")
    enterprise = calculate_churn_risk(10, 3, 10, "Enterprise")
    assert (basic, pro, enterprise) == (34.5, 30.0, 25.5)


def test_ticket_points_are_capped_at_fifty():
    assert calculate_churn_risk(10, 10, 10, "Pro") == 50.0
    assert calculate_churn_risk(10, 10, 10, "Basic") == 50.0


def test_low_usage_adds_proportional_risk():
    # age 20 -> expected 8h. Zero usage = 50 points, half expected = 25 points.
    assert calculate_churn_risk(0, 0, 20, "Pro") == 50.0
    assert calculate_churn_risk(4, 0, 20, "Pro") == 25.0


def test_worst_case_is_one_hundred():
    assert calculate_churn_risk(0, 10, 20, "Pro") == 100.0


def test_more_tickets_means_higher_risk():
    assert calculate_churn_risk(10, 5, 10, "Pro") > calculate_churn_risk(10, 1, 10, "Pro")


def test_risk_category_boundaries():
    assert get_risk_category(29.9) == "Healthy"
    assert get_risk_category(30) == "Medium Risk"
    assert get_risk_category(70) == "Medium Risk"
    assert get_risk_category(70.1) == "High Risk"


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"customer_name": "Healthy Co", "plan_type": "Pro",
             "monthly_usage_hours": 20, "support_tickets": 0, "account_age_months": 10},
            {"customer_name": "Risky Co", "plan_type": "Basic",
             "monthly_usage_hours": 0, "support_tickets": 10, "account_age_months": 20},
        ]
    )


def test_enrich_adds_score_and_category_columns():
    enriched = enrich_with_churn_metrics(_sample_df())
    assert list(enriched["Risk Category"]) == ["Healthy", "High Risk"]
    assert list(enriched["Churn Risk Score (%)"]) == [0.0, 100.0]


def test_enrich_handles_empty_dataframe():
    assert enrich_with_churn_metrics(pd.DataFrame()).empty


def test_distribution_is_ordered_and_counts_correctly():
    dist = build_risk_distribution_df(enrich_with_churn_metrics(_sample_df()))
    assert list(dist.index) == ["Healthy", "Medium Risk", "High Risk"]
    assert list(dist["Customers"]) == [1, 0, 1]


def test_distribution_of_empty_data_is_all_zero():
    assert list(build_risk_distribution_df(pd.DataFrame())["Customers"]) == [0, 0, 0]


def test_at_risk_excludes_healthy_and_sorts_descending():
    at_risk = get_at_risk_customers(enrich_with_churn_metrics(_sample_df()))
    assert list(at_risk["customer_name"]) == ["Risky Co"]
