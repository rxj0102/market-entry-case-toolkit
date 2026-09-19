from market_entry_toolkit.competitive_benchmarking import (
    COMPETITORS,
    Competitor,
    herfindahl_hirschman_index,
    to_records,
    white_space_analysis,
)


def test_market_shares_sum_to_100():
    total = sum(c.est_market_share_pct for c in COMPETITORS)
    assert total == 100.0


def test_hhi_known_value():
    competitors = (
        Competitor("A", "m", 50.0, 1, 1, 100.0, 0.2, "d"),
        Competitor("B", "m", 50.0, 1, 1, 100.0, 0.2, "d"),
    )
    # Two equal 50% players: HHI = 50^2 + 50^2 = 5000.
    assert herfindahl_hirschman_index(competitors) == 5000.0


def test_hhi_matches_live_competitor_set():
    expected = sum(c.est_market_share_pct**2 for c in COMPETITORS)
    assert herfindahl_hirschman_index() == expected


def test_white_space_analysis_mentions_freshroute():
    text = white_space_analysis()
    assert "FreshRoute" in text
    assert len(text) > 0


def test_to_records_includes_proposed_by_default():
    records = to_records()
    assert len(records) == len(COMPETITORS) + 1
    assert any(r["name"] == "FreshRoute (proposed)" for r in records)


def test_to_records_can_exclude_proposed():
    records = to_records(include_proposed=False)
    assert len(records) == len(COMPETITORS)
