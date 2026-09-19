import os

import pytest

from market_entry_toolkit.memo_synthesis import (
    REVIEW_CHECKLIST,
    CaseInputs,
    LiveSynthesisUnavailable,
    draft_memo_live,
    draft_memo_template,
    synthesize_memo,
    verify_traceability,
)


@pytest.fixture
def sample_inputs() -> CaseInputs:
    return CaseInputs(
        client_name="FreshRoute",
        core_question="Should FreshRoute enter the GTA?",
        hypothesis_tree_markdown="- [0] full tree detail",
        supporting_evidence_bullets="- Market attractiveness: supported",
        overall_verdict="partially supported",
        market_sizing_summary="Bottom-up SOM is $220M CAD.",
        competitive_summary="HHI is 2250.",
        financial_summary="Base case NPV is -$45M CAD.",
        recommendation_hint="Conditional go via phased pilot.",
    )


def test_template_mode_contains_scr_structure(sample_inputs):
    memo = draft_memo_template(sample_inputs)
    assert "## Situation" in memo
    assert "## Complication" in memo
    assert "## Resolution" in memo
    assert "## Supporting evidence" in memo
    assert sample_inputs.recommendation_hint in memo
    assert sample_inputs.supporting_evidence_bullets in memo


def test_template_mode_does_not_leak_full_tree_into_memo(sample_inputs):
    memo = draft_memo_template(sample_inputs)
    assert sample_inputs.hypothesis_tree_markdown not in memo


def test_synthesize_memo_falls_back_to_template_without_api_key(sample_inputs, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    memo, mode = synthesize_memo(sample_inputs)
    assert mode == "template"
    assert memo == draft_memo_template(sample_inputs)


def test_live_mode_raises_clear_error_without_api_key(sample_inputs, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(LiveSynthesisUnavailable, match="ANTHROPIC_API_KEY"):
        draft_memo_live(sample_inputs)


def test_forcing_live_mode_without_key_raises_rather_than_silently_falling_back(sample_inputs, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(LiveSynthesisUnavailable):
        synthesize_memo(sample_inputs, use_live_llm=True)


def test_verify_traceability_flags_dropped_figure(sample_inputs):
    memo_missing_figure = "A memo that never mentions the dollar figures at all."
    warnings = verify_traceability(sample_inputs, memo_missing_figure)
    assert any("$220M" in w for w in warnings)


def test_verify_traceability_clean_when_figures_present(sample_inputs):
    memo = draft_memo_template(sample_inputs)
    warnings = verify_traceability(sample_inputs, memo)
    assert warnings == []


def test_review_checklist_nonempty_and_mentions_traceability():
    assert len(REVIEW_CHECKLIST) >= 3
    assert any("trace" in item.lower() for item in REVIEW_CHECKLIST)
