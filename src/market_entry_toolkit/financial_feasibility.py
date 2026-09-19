"""Financial feasibility for the FreshRoute GTA entry.

Builds a simple 5-year P&L under base/upside/downside scenarios and
computes the numbers a client's finance team asks for first: payback
period, NPV, and IRR. This is intentionally a lean model -- a case team's
financial feasibility check is meant to answer "is this directionally
worth doing," not to be an investment-grade DCF. Complexity is kept to
what's needed to support the entry/no-entry recommendation; see the
README for why the model doesn't go further (e.g. no explicit working
capital or tax modeling).

DATA DISCLAIMER: cost ratios (fulfillment cost, marketing spend, G&A) are
illustrative planning assumptions, not derived from any real company's
financials. The year-5 revenue anchor comes from `market_sizing.py`'s
bottom-up SOM estimate for this same case.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy_financial as npf


@dataclass(frozen=True)
class ScenarioAssumptions:
    """All financial assumptions for one scenario, in one place.

    ramp_curve: fraction of year-5 steady-state revenue realized in each
        of years 1-5 (must end at 1.0).
    marketing_pct_of_revenue_by_year: CAC/marketing intensity is highest
        during the ramp and tapers as the brand establishes itself.
    ga_fixed_cad_by_year: fixed G&A/technology overhead allocated to the
        Canada entry, independent of revenue.
    """

    name: str
    year5_revenue_cad: float
    initial_investment_cad: float
    ramp_curve: tuple[float, float, float, float, float]
    gross_margin_pct: float
    fulfillment_cost_pct_of_revenue: float
    marketing_pct_of_revenue_by_year: tuple[float, float, float, float, float]
    ga_fixed_cad_by_year: tuple[float, float, float, float, float]
    discount_rate: float = 0.10


@dataclass(frozen=True)
class YearResult:
    year: int
    revenue_cad: float
    gross_profit_cad: float
    fulfillment_cost_cad: float
    marketing_cost_cad: float
    ga_cost_cad: float
    ebitda_cad: float


@dataclass(frozen=True)
class ScenarioResult:
    assumptions: ScenarioAssumptions
    years: list[YearResult]
    cash_flows_cad: list[float]  # [-investment, ebitda_y1, ..., ebitda_y5]
    payback_period_years: float | None
    npv_cad: float
    irr_pct: float | None

    def summary_line(self) -> str:
        payback = f"{self.payback_period_years:.1f}yr" if self.payback_period_years is not None else "no payback within 5yr"
        irr = f"{self.irr_pct:.1%}" if self.irr_pct is not None else "n/m"
        return (
            f"{self.assumptions.name}: Y5 revenue ${self.years[-1].revenue_cad / 1e6:.0f}M, "
            f"Y5 EBITDA ${self.years[-1].ebitda_cad / 1e6:.1f}M, "
            f"payback {payback}, NPV ${self.npv_cad / 1e6:.1f}M, IRR {irr}"
        )


def _build_years(a: ScenarioAssumptions) -> list[YearResult]:
    years = []
    for i in range(5):
        revenue = a.year5_revenue_cad * a.ramp_curve[i]
        gross_profit = revenue * a.gross_margin_pct
        fulfillment = revenue * a.fulfillment_cost_pct_of_revenue
        marketing = revenue * a.marketing_pct_of_revenue_by_year[i]
        ga = a.ga_fixed_cad_by_year[i]
        ebitda = gross_profit - fulfillment - marketing - ga
        years.append(
            YearResult(
                year=i + 1,
                revenue_cad=revenue,
                gross_profit_cad=gross_profit,
                fulfillment_cost_cad=fulfillment,
                marketing_cost_cad=marketing,
                ga_cost_cad=ga,
                ebitda_cad=ebitda,
            )
        )
    return years


def _payback_period(cash_flows: list[float]) -> float | None:
    """Fractional-year payback using cumulative cash flow, treating each
    year's EBITDA as realized evenly across the year. Returns None if the
    scenario never pays back within the modeled horizon.
    """
    cumulative = cash_flows[0]  # negative initial investment at t=0
    if cumulative >= 0:
        return 0.0
    for year_index, flow in enumerate(cash_flows[1:], start=1):
        prev_cumulative = cumulative
        cumulative += flow
        if cumulative >= 0:
            if flow == 0:
                return float(year_index)
            fraction = -prev_cumulative / flow
            return (year_index - 1) + fraction
    return None


def run_scenario(a: ScenarioAssumptions) -> ScenarioResult:
    years = _build_years(a)
    cash_flows = [-a.initial_investment_cad] + [y.ebitda_cad for y in years]
    payback = _payback_period(cash_flows)
    npv = npf.npv(a.discount_rate, cash_flows)
    try:
        irr = npf.irr(cash_flows)
        irr = float(irr) if irr == irr else None  # filter NaN
    except Exception:
        irr = None
    return ScenarioResult(
        assumptions=a,
        years=years,
        cash_flows_cad=cash_flows,
        payback_period_years=payback,
        npv_cad=float(npv),
        irr_pct=irr,
    )


def base_case(year5_revenue_cad: float) -> ScenarioAssumptions:
    """Base case: anchored to market_sizing's bottom-up SOM as the year-5
    revenue target, with a realistic ramp and moderate marketing spend.
    """
    return ScenarioAssumptions(
        name="Base",
        year5_revenue_cad=year5_revenue_cad,
        initial_investment_cad=18_000_000,
        ramp_curve=(0.12, 0.35, 0.60, 0.82, 1.00),
        gross_margin_pct=0.23,
        fulfillment_cost_pct_of_revenue=0.12,
        marketing_pct_of_revenue_by_year=(0.25, 0.18, 0.14, 0.11, 0.09),
        ga_fixed_cad_by_year=(4_000_000, 4_500_000, 5_000_000, 5_500_000, 6_000_000),
        discount_rate=0.10,
    )


def upside_case(year5_revenue_cad: float) -> ScenarioAssumptions:
    """Upside: faster ramp and 25% higher steady-state revenue, reflecting
    stronger-than-planned word-of-mouth and lower CAC as the brand takes
    hold faster than the base case assumes.
    """
    base = base_case(year5_revenue_cad)
    return ScenarioAssumptions(
        name="Upside",
        year5_revenue_cad=year5_revenue_cad * 1.25,
        initial_investment_cad=base.initial_investment_cad,
        ramp_curve=(0.18, 0.45, 0.70, 0.90, 1.00),
        gross_margin_pct=0.25,
        fulfillment_cost_pct_of_revenue=0.11,
        marketing_pct_of_revenue_by_year=(0.22, 0.15, 0.12, 0.10, 0.08),
        ga_fixed_cad_by_year=base.ga_fixed_cad_by_year,
        discount_rate=0.10,
    )


def downside_case(year5_revenue_cad: float) -> ScenarioAssumptions:
    """Downside: slower ramp, 30% lower steady-state revenue, higher CAC
    (competitive response from incumbents drives up marketing spend) and
    thinner margin (price competition).
    """
    base = base_case(year5_revenue_cad)
    return ScenarioAssumptions(
        name="Downside",
        year5_revenue_cad=year5_revenue_cad * 0.70,
        initial_investment_cad=base.initial_investment_cad,
        ramp_curve=(0.08, 0.24, 0.45, 0.68, 1.00),
        gross_margin_pct=0.20,
        fulfillment_cost_pct_of_revenue=0.13,
        marketing_pct_of_revenue_by_year=(0.30, 0.24, 0.20, 0.17, 0.14),
        ga_fixed_cad_by_year=base.ga_fixed_cad_by_year,
        discount_rate=0.10,
    )


def run_all_scenarios(year5_revenue_cad: float) -> dict[str, ScenarioResult]:
    """Convenience entry point: run base/upside/downside off one shared
    year-5 revenue anchor (typically market_sizing's bottom-up SOM).
    """
    return {
        "base": run_scenario(base_case(year5_revenue_cad)),
        "upside": run_scenario(upside_case(year5_revenue_cad)),
        "downside": run_scenario(downside_case(year5_revenue_cad)),
    }


def plot_scenario_cashflows(scenarios: dict[str, ScenarioResult], save_path: str | None = None):
    """Cumulative cash flow (post initial investment) by year across the
    three scenarios -- the chart a client asks for first: "when, if ever,
    do we get our money back, and how bad does downside get."
    """
    from . import _viz

    fig, ax = _viz.new_figure(figsize=(7.5, 5))
    colors = {"base": _viz.BLUE, "upside": _viz.AQUA, "downside": _viz.RED}
    years = list(range(0, 6))

    for key in ("base", "upside", "downside"):
        result = scenarios[key]
        cumulative = []
        running = 0.0
        for flow in result.cash_flows_cad:
            running += flow
            cumulative.append(running / 1e6)
        ax.plot(
            years,
            cumulative,
            color=colors[key],
            linewidth=2,
            marker="o",
            markersize=5,
            markerfacecolor=colors[key],
            markeredgecolor=_viz.SURFACE,
            markeredgewidth=1.5,
            label=result.assumptions.name,
            zorder=3,
        )
        ax.annotate(
            f"{result.assumptions.name}: ${cumulative[-1]:.0f}M",
            (years[-1], cumulative[-1]),
            textcoords="offset points",
            xytext=(8, 0),
            va="center",
            fontsize=9,
            color=colors[key],
            fontweight="bold",
        )

    ax.axhline(0, color=_viz.GRAY_AXIS, linewidth=1, zorder=1)
    ax.set_xlabel("Year (0 = initial investment)", color=_viz.SECONDARY_TEXT)
    ax.set_ylabel("Cumulative cash flow, CAD millions", color=_viz.SECONDARY_TEXT)
    ax.set_title("5-year cumulative cash flow by scenario", fontsize=11, color=_viz.PRIMARY_TEXT, loc="left")
    ax.set_xticks(years)
    ax.set_xlim(-0.3, 6.7)
    _viz.clean_axes(ax)
    ax.legend(frameon=False, loc="upper right", fontsize=9)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, facecolor=fig.get_facecolor())
    return fig
