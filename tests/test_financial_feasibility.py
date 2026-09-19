from market_entry_toolkit.financial_feasibility import (
    ScenarioAssumptions,
    run_all_scenarios,
    run_scenario,
)


def _flat_scenario(initial_investment: float) -> ScenarioAssumptions:
    """A deliberately simple scenario (flat $100/yr revenue, flat $40/yr
    EBITDA) so payback/NPV/IRR can be checked against hand-computed values
    rather than just "did it run."
    """
    return ScenarioAssumptions(
        name="Flat",
        year5_revenue_cad=100.0,
        initial_investment_cad=initial_investment,
        ramp_curve=(1.0, 1.0, 1.0, 1.0, 1.0),
        gross_margin_pct=0.6,
        fulfillment_cost_pct_of_revenue=0.1,
        marketing_pct_of_revenue_by_year=(0.1, 0.1, 0.1, 0.1, 0.1),
        ga_fixed_cad_by_year=(0.0, 0.0, 0.0, 0.0, 0.0),
        discount_rate=0.10,
    )


def test_flat_scenario_ebitda_is_constant_40_per_year():
    result = run_scenario(_flat_scenario(100.0))
    for year in result.years:
        assert year.ebitda_cad == 40.0


def test_payback_period_hand_computed():
    # cash flows: [-100, 40, 40, 40, 40, 40] -> cumulative crosses zero
    # exactly 2.5 years in.
    result = run_scenario(_flat_scenario(100.0))
    assert result.payback_period_years == 2.5


def test_payback_period_zero_when_investment_is_zero():
    result = run_scenario(_flat_scenario(0.0))
    assert result.payback_period_years == 0.0


def test_payback_none_when_never_recovered():
    result = run_scenario(_flat_scenario(1_000_000.0))
    assert result.payback_period_years is None


def test_npv_positive_for_profitable_flat_scenario():
    result = run_scenario(_flat_scenario(100.0))
    assert result.npv_cad > 0


def test_run_all_scenarios_returns_three_keys_with_ordered_revenue():
    scenarios = run_all_scenarios(year5_revenue_cad=200_000_000)
    assert set(scenarios) == {"base", "upside", "downside"}
    upside_rev = scenarios["upside"].years[-1].revenue_cad
    base_rev = scenarios["base"].years[-1].revenue_cad
    downside_rev = scenarios["downside"].years[-1].revenue_cad
    assert downside_rev < base_rev < upside_rev
