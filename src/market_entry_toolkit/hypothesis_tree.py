"""Hypothesis tree (issue tree) for the FreshRoute Canada market-entry case.

This module is the structural backbone of the case. Before any numbers are
run, a case team frames the core client question as a tree of mutually
exclusive, collectively exhaustive (MECE) sub-hypotheses, each of which is
individually testable with a named piece of analysis. The rest of the
toolkit (market_sizing, competitive_benchmarking, financial_feasibility)
exists to *answer* the leaves of this tree; memo_synthesis exists to roll
the answers back up into a recommendation.

The tree is a plain data structure (no LLM involved) so that the logic of
the case -- what would have to be true for entry to make sense, and what
analysis proves or disproves it -- is fully transparent and inspectable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Verdict(str, Enum):
    """The evidence status of a single hypothesis node."""

    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially supported"
    NOT_SUPPORTED = "not supported"
    PENDING = "pending analysis"


_VERDICT_ICONS = {
    Verdict.SUPPORTED: "✅",
    Verdict.PARTIALLY_SUPPORTED: "⚠️",
    Verdict.NOT_SUPPORTED: "❌",
    Verdict.PENDING: "⏳",
}


@dataclass
class Hypothesis:
    """A single node in the issue tree.

    Attributes:
        id: Short stable identifier (e.g. "1.2") used for cross-referencing
            from other modules when they set a finding.
        statement: The testable claim, phrased so it can be true or false
            (e.g. "The addressable market is large and growing").
        analysis: The specific analysis that would prove or disprove the
            statement -- named the way a case team would name a workstream
            (e.g. "Top-down/bottom-up market sizing reconciliation").
        finding: Filled in once the analysis has been run. Left as an
            empty string until then.
        verdict: Evidence status; defaults to PENDING until `resolve()`
            is called.
        children: Sub-hypotheses that decompose this node further. Leaf
            nodes (no children) are where analysis actually happens;
            parent nodes are resolved by rolling up their children.
    """

    id: str
    statement: str
    analysis: str
    finding: str = ""
    verdict: Verdict = Verdict.PENDING
    children: list["Hypothesis"] = field(default_factory=list)

    def resolve(self, finding: str, verdict: Verdict) -> None:
        """Attach the result of running `self.analysis` to this node."""
        self.finding = finding
        self.verdict = verdict

    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def rollup_verdict(self) -> Verdict:
        """Compute this node's verdict from its children, if it has any.

        A parent is SUPPORTED only if every child is SUPPORTED; NOT_SUPPORTED
        if any child is NOT_SUPPORTED (a single disqualifying sub-hypothesis
        sinks the branch); otherwise PARTIALLY_SUPPORTED. Leaf nodes just
        return their own (directly resolved) verdict.
        """
        if self.is_leaf():
            return self.verdict

        child_verdicts = [c.rollup_verdict() for c in self.children]
        if any(v == Verdict.PENDING for v in child_verdicts):
            return Verdict.PENDING
        if any(v == Verdict.NOT_SUPPORTED for v in child_verdicts):
            return Verdict.NOT_SUPPORTED
        if all(v == Verdict.SUPPORTED for v in child_verdicts):
            return Verdict.SUPPORTED
        return Verdict.PARTIALLY_SUPPORTED

    def find(self, node_id: str) -> "Hypothesis | None":
        """Depth-first search for a node by id, anywhere in this subtree."""
        if self.id == node_id:
            return self
        for child in self.children:
            found = child.find(node_id)
            if found is not None:
                return found
        return None

    def to_markdown(self, _depth: int = 0) -> str:
        """Render this node and its subtree as an indented markdown list."""
        icon = _VERDICT_ICONS[self.rollup_verdict()]
        indent = "  " * _depth
        bullet = f"{indent}- **[{self.id}] {self.statement}** {icon}"
        lines = [bullet]
        if self.analysis:
            lines.append(f"{indent}  *Analysis:* {self.analysis}")
        if self.finding:
            lines.append(f"{indent}  *Finding:* {self.finding}")
        for child in self.children:
            lines.append(child.to_markdown(_depth + 1))
        return "\n".join(lines)

    def branch_summary_bullets(self) -> list[str]:
        """One line per immediate child, statement + rollup verdict only --
        no analysis/finding detail. This is what belongs in a client-facing
        memo's "supporting evidence" section; the full `to_markdown()` tree
        (with every finding) belongs in the working notebook, not the memo.
        """
        return [
            f"{_VERDICT_ICONS[child.rollup_verdict()]} **{child.statement}** "
            f"({child.rollup_verdict().value})"
            for child in self.children
        ]

    def leaves(self) -> list["Hypothesis"]:
        """Return all leaf nodes in this subtree, in tree order."""
        if self.is_leaf():
            return [self]
        result: list[Hypothesis] = []
        for child in self.children:
            result.extend(child.leaves())
        return result


def build_case_tree() -> Hypothesis:
    """Construct the FreshRoute Canada issue tree.

    Core question: "Should FreshRoute enter the Greater Toronto Area (GTA)
    grocery delivery market?" decomposed into the four classic market-entry
    sub-hypotheses. Each leaf names the exact analysis (implemented
    elsewhere in this package) that resolves it; `finding`/`verdict` start
    empty and are filled in by `run_case.resolve_tree_from_modules()`
    (see the notebook) once market_sizing, competitive_benchmarking, and
    financial_feasibility have actually been run.
    """

    market_attractiveness = Hypothesis(
        id="1",
        statement="The Canadian (GTA) online grocery market is large enough "
        "and growing fast enough to be worth entering",
        analysis="Roll-up of market sizing and demand-trend sub-analyses",
        children=[
            Hypothesis(
                id="1.1",
                statement="Top-down and bottom-up sizing agree the "
                "addressable market clears FreshRoute's minimum bar "
                "(~US$150M in year-5 category revenue)",
                analysis="Top-down TAM from Canadian grocery e-commerce "
                "spend proxies, reconciled against a bottom-up build from "
                "GTA households x penetration x basket size x frequency "
                "(market_sizing.py)",
            ),
            Hypothesis(
                id="1.2",
                statement="Online grocery penetration in Canada is still "
                "rising, not saturating",
                analysis="Trend read on online grocery penetration rate "
                "used in the bottom-up build (market_sizing.py)",
            ),
        ],
    )

    competitive_intensity = Hypothesis(
        id="2",
        statement="Competitive intensity is manageable -- there is a "
        "defensible white-space position for a new entrant",
        analysis="Roll-up of competitive benchmarking sub-analyses",
        children=[
            Hypothesis(
                id="2.1",
                statement="No single incumbent already dominates the "
                "market to the point of foreclosing entry",
                analysis="Market share and concentration read across the "
                "competitor set (competitive_benchmarking.py)",
            ),
            Hypothesis(
                id="2.2",
                statement="There is a clear, defensible positioning gap "
                "FreshRoute can occupy rather than competing head-on on "
                "price",
                analysis="Price/positioning map and white-space "
                "identification across incumbents "
                "(competitive_benchmarking.py)",
            ),
        ],
    )

    capability_fit = Hypothesis(
        id="3",
        statement="FreshRoute's operating model transfers to Canada "
        "without a fundamentally new capability build",
        analysis="Qualitative capability-fit assessment (this case; not "
        "separately quantified given illustrative scope)",
        children=[
            Hypothesis(
                id="3.1",
                statement="Fulfillment model (partner-store picking + "
                "last-mile courier network) is replicable in the GTA "
                "without a new warehouse buildout",
                analysis="Operating-model fit review against known GTA "
                "grocery partner landscape",
            ),
            Hypothesis(
                id="3.2",
                statement="Regulatory, payments, and labor differences "
                "(GST/HST, cross-border data, employment law) are "
                "navigable within FreshRoute's existing compliance "
                "capability",
                analysis="Regulatory/compliance delta review",
            ),
        ],
    )

    financial_viability = Hypothesis(
        id="4",
        statement="The entry is financially worth it on a risk-adjusted "
        "basis",
        analysis="Roll-up of financial feasibility sub-analyses",
        children=[
            Hypothesis(
                id="4.1",
                statement="The base case reaches payback within "
                "FreshRoute's board-level bar (4 years)",
                analysis="5-year P&L build and payback period calculation "
                "(financial_feasibility.py)",
            ),
            Hypothesis(
                id="4.2",
                statement="NPV is positive and the downside scenario is "
                "not catastrophic (does not threaten a capital call "
                "beyond the approved budget)",
                analysis="NPV/IRR under base/upside/downside scenarios "
                "(financial_feasibility.py)",
            ),
        ],
    )

    root = Hypothesis(
        id="0",
        statement="FreshRoute should enter the Greater Toronto Area "
        "online grocery delivery market",
        analysis="Synthesis of the four branches below "
        "(memo_synthesis.py)",
        children=[
            market_attractiveness,
            competitive_intensity,
            capability_fit,
            financial_viability,
        ],
    )
    return root


def print_tree(root: Hypothesis) -> None:
    """Convenience wrapper to print the tree as markdown to stdout."""
    print(root.to_markdown())
