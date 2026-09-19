"""AI-assisted synthesis of the case findings into a recommendation memo.

This is the "emerging capabilities" piece of the toolkit: an LLM is used
to *draft* the executive memo from the toolkit's own quantitative
outputs, not to invent analysis. The design goal is to make the
prompt engineering and the human-in-the-loop review step fully visible,
so this is legible as a documented, auditable process rather than a
black box.

Two synthesis modes, selected automatically (or explicitly):

* **Live mode** -- calls the Anthropic Claude API using `CaseInputs` as
  grounding context, if the optional `anthropic` package is installed
  and `ANTHROPIC_API_KEY` is set in the environment.
* **Template mode** -- a fully offline, deterministic fallback that fills
  the same Situation/Complication/Resolution structure directly from
  `CaseInputs`, no network access or API key required.

No live API key was available in the environment this toolkit was built
in, so the notebook and generated `outputs/recommendation_memo.md` in
this repository were produced in **template mode**. Live mode is
included, documented, and unit-testable (with a stubbed client) so a
user with their own API key can opt into it -- see the README.

Whichever mode produces a draft, it is exactly that: a *draft*. The
`REVIEW_CHECKLIST` below and `verify_traceability()` exist because an
LLM-drafted client memo must never ship un-reviewed -- a human case-team
member is expected to work through the checklist against the draft
before it goes anywhere near a client.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CaseInputs:
    """Everything the memo-writing prompt is grounded in. Every field is
    text or numbers produced by the other four modules -- the LLM is
    never asked to originate a fact, only to structure and write up
    facts it's handed.
    """

    client_name: str
    core_question: str
    hypothesis_tree_markdown: str
    """Full tree with every leaf's analysis + finding -- grounding context
    for the LLM prompt (so it can cite accurately) and for the working
    notebook's own detailed walkthrough. NOT what belongs in the memo
    itself -- see `supporting_evidence_bullets`."""
    supporting_evidence_bullets: str
    """Concise, one-line-per-branch verdict summary (see
    `Hypothesis.branch_summary_bullets()`), already newline-joined. This is
    what the memo's own "Supporting evidence" section uses -- a client memo
    cites conclusions, not the full analysis trail."""
    overall_verdict: str
    market_sizing_summary: str
    competitive_summary: str
    financial_summary: str
    recommendation_hint: str
    """A short, human/analyst-authored steer on the bottom-line
    recommendation (e.g. "conditional go via phased pilot"). The prompt
    treats this as a constraint, not a suggestion -- the LLM is writing
    up a recommendation the case team has already reached from the
    analysis, not independently deciding what to recommend. This is the
    clearest guardrail against the LLM drifting from the numbers."""


# ---------------------------------------------------------------------------
# Prompt library
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a senior case-team member at a top-tier management consultancy, \
writing the executive recommendation memo at the end of a market-entry \
strategy engagement. You write in the Situation-Complication-Resolution \
structure: crisp, declarative, numbers-forward, no hedging, no filler, \
no restating the obvious. One to two pages maximum.

Hard rules:
1. Use ONLY the facts, figures, and conclusions given to you in the case \
findings below. Do not introduce any statistic, competitor fact, or \
financial figure that is not present in the input. If you need a \
transition or framing sentence, keep it qualitative -- never invent a \
number to make a sentence flow better.
2. The bottom-line recommendation is given to you (see "Required \
recommendation stance" in the user message). Your job is to write it up \
persuasively and precisely from the evidence provided, not to reach your \
own independent recommendation or to soften/contradict the given stance.
3. Structure: a short **Situation** paragraph (why this question, why \
now), a **Complication** paragraph (what the analysis actually found --\
lead with the tension, not just a data recap), and a **Resolution** \
section with the recommendation and its 2-4 key conditions or next steps.
4. Close with a short "Supporting evidence" bullet list mapping each \
hypothesis-tree branch to its verdict, so a reader can trace the \
recommendation back to the analysis.
5. Write for a client CEO audience: assume financial and strategic \
literacy, zero patience for jargon or padding.
"""


def build_user_prompt(inputs: CaseInputs) -> str:
    """Assemble the user-turn prompt from structured case findings.

    Kept as a plain function (not a method) so the exact prompt sent to
    the model is easy to print, log, and unit-test independent of
    whether a live call is actually made.
    """
    return f"""\
CLIENT: {inputs.client_name}
CORE QUESTION: {inputs.core_question}

=== HYPOTHESIS TREE (issue tree with verdicts) ===
{inputs.hypothesis_tree_markdown}

Overall hypothesis-tree rollup verdict: {inputs.overall_verdict}

=== MARKET SIZING FINDINGS ===
{inputs.market_sizing_summary}

=== COMPETITIVE BENCHMARKING FINDINGS ===
{inputs.competitive_summary}

=== FINANCIAL FEASIBILITY FINDINGS ===
{inputs.financial_summary}

=== REQUIRED RECOMMENDATION STANCE ===
{inputs.recommendation_hint}

Write the one-to-two-page recommendation memo now, per the system \
instructions.
"""


# ---------------------------------------------------------------------------
# Template mode (offline, deterministic, no LLM)
# ---------------------------------------------------------------------------


def draft_memo_template(inputs: CaseInputs) -> str:
    """Fill the same Situation/Complication/Resolution structure directly
    from `CaseInputs`, with no LLM call. This is the default synthesis
    path and is what produced `outputs/recommendation_memo.md` in this
    repository.
    """
    return f"""\
# Recommendation Memo: {inputs.client_name}

**Question:** {inputs.core_question}

## Situation

{inputs.client_name} asked us to determine whether entering the Greater \
Toronto Area online grocery delivery market is a good use of capital, \
and if so, how. We structured the question into four testable \
hypotheses -- market attractiveness, competitive intensity, capability \
fit, and financial viability -- and ran a dedicated analysis against \
each.

## Complication

{inputs.market_sizing_summary}

{inputs.competitive_summary}

{inputs.financial_summary}

Taken together, the hypothesis tree rolls up to **{inputs.overall_verdict}**

## Resolution

**Recommendation:** {inputs.recommendation_hint}

## Supporting evidence

{inputs.supporting_evidence_bullets}
"""


# ---------------------------------------------------------------------------
# Live mode (optional, requires `anthropic` package + ANTHROPIC_API_KEY)
# ---------------------------------------------------------------------------


class LiveSynthesisUnavailable(RuntimeError):
    """Raised when live mode is requested but the `anthropic` package or
    an API key isn't available -- callers should catch this and fall
    back to `draft_memo_template()` rather than crash the case run.
    """


def draft_memo_live(
    inputs: CaseInputs,
    model: str = "claude-sonnet-4-5-20250929",
    max_tokens: int = 1500,
) -> str:
    """Call the Anthropic API to draft the memo from `inputs`.

    Requires the optional `anthropic` package (`pip install anthropic`,
    or `pip install -e ".[llm]"`) and `ANTHROPIC_API_KEY` set in the
    environment. Raises `LiveSynthesisUnavailable` with a clear message
    if either precondition isn't met, so callers can fall back to
    `draft_memo_template()` -- see `synthesize_memo()` below.

    `model` defaults to a Claude Sonnet model id current as of this
    toolkit's development; pass a different id if it's been retired or
    if a different model is preferred.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise LiveSynthesisUnavailable(
            "ANTHROPIC_API_KEY is not set. Set it to use live LLM synthesis, "
            "or call draft_memo_template() / synthesize_memo(use_live_llm=False) "
            "for the offline template path."
        )
    try:
        import anthropic
    except ImportError as exc:
        raise LiveSynthesisUnavailable(
            "The 'anthropic' package is not installed. Install it with "
            "`pip install anthropic` (or `pip install -e \".[llm]\"`) to use "
            "live synthesis, or call draft_memo_template() instead."
        ) from exc

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt(inputs)}],
    )
    return "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )


def synthesize_memo(
    inputs: CaseInputs, use_live_llm: bool | None = None
) -> tuple[str, str]:
    """Top-level synthesis entry point used by the notebook.

    If `use_live_llm` is None (the default), auto-detects: uses live mode
    if `ANTHROPIC_API_KEY` is set and the `anthropic` package is
    importable, otherwise falls back to template mode. Pass True/False to
    force a mode explicitly (e.g. in tests).

    Returns (memo_text, mode) where mode is "live" or "template", so
    callers/notebooks can label the output honestly.
    """
    should_try_live = use_live_llm if use_live_llm is not None else bool(
        os.environ.get("ANTHROPIC_API_KEY")
    )
    if should_try_live:
        try:
            return draft_memo_live(inputs), "live"
        except LiveSynthesisUnavailable:
            if use_live_llm is True:
                raise
            # Auto-detect path: fall back silently to template mode.
    return draft_memo_template(inputs), "template"


# ---------------------------------------------------------------------------
# Human-in-the-loop review
# ---------------------------------------------------------------------------

REVIEW_CHECKLIST: tuple[str, ...] = (
    "Every number in the draft traces back to market_sizing.py, "
    "competitive_benchmarking.py, or financial_feasibility.py output -- "
    "none were introduced by the LLM.",
    "The recommendation stated in the memo matches `recommendation_hint` "
    "and the hypothesis-tree rollup verdict; the LLM did not soften, "
    "hedge, or override the given stance.",
    "No competitor claim in the memo goes beyond what's in "
    "competitive_benchmarking.py (no invented market share, pricing, or "
    "positioning detail).",
    "Tone and length are appropriate for a client CEO audience (one to "
    "two pages, no jargon, no padding).",
    "The 'Supporting evidence' section correctly reflects the hypothesis "
    "tree's per-branch verdicts.",
    "A named case-team reviewer has read the full draft end-to-end and "
    "signed off before it is shared outside the team.",
)


def print_review_checklist() -> None:
    print("Human-in-the-loop review checklist (complete before sharing):")
    for i, item in enumerate(REVIEW_CHECKLIST, start=1):
        print(f"  [ ] {i}. {item}")


def verify_traceability(inputs: CaseInputs, memo_text: str) -> list[str]:
    """Lightweight automated guardrail (a complement to, not a substitute
    for, the human review checklist above): flag if figures mentioned in
    the source summaries don't show up anywhere in the drafted memo,
    which would suggest the draft dropped load-bearing evidence.

    This intentionally checks for *omission*, not fabrication -- an LLM
    can't be reliably self-checked for invented numbers by string
    matching, which is exactly why REVIEW_CHECKLIST item 1 requires a
    human to trace every figure back to source.
    """
    import re

    warnings: list[str] = []
    source_text = " ".join(
        [inputs.market_sizing_summary, inputs.competitive_summary, inputs.financial_summary]
    )
    # Pull out standalone dollar figures like "$220M" or "$1.2B" from the
    # source summaries and check each appears verbatim in the draft.
    figures = set(re.findall(r"\$[\d,.]+[MBK]?", source_text))
    for figure in sorted(figures):
        if figure not in memo_text:
            warnings.append(f"Source figure '{figure}' does not appear in the drafted memo.")
    return warnings
