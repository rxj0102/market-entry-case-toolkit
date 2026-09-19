from market_entry_toolkit.market_sizing import Assumptions, reconcile, size_bottom_up, size_top_down


def test_top_down_positive_and_ordered():
    result = size_top_down()
    assert result.canada_online_grocery_market_cad > result.gta_online_grocery_market_cad
    assert result.gta_online_grocery_market_cad > result.gta_online_delivery_market_cad
    assert result.gta_online_delivery_market_cad > result.som_cad > 0


def test_bottom_up_positive_and_consistent():
    result = size_bottom_up()
    assert result.serviceable_households > result.active_customers_year5 > 0
    expected_som = result.active_customers_year5 * result.annual_spend_per_customer_cad
    assert result.som_cad == expected_som


def test_reconcile_gap_sign_and_magnitude():
    recon = reconcile()
    assert recon.gap_cad == recon.bottom_up.som_cad - recon.top_down.som_cad
    # Two independently-built estimates should land in the same ballpark.
    assert abs(recon.gap_pct_of_lower) < 0.5


def test_custom_assumptions_change_result():
    baseline = size_bottom_up()
    bigger = size_bottom_up(Assumptions(gta_households=baseline.serviceable_households * 100))
    assert bigger.som_cad > baseline.som_cad


def test_fx_conversion_applied():
    a = Assumptions(fx_cad_per_usd=2.0)
    result = size_top_down(a)
    assert result.som_usd == result.som_cad / 2.0
