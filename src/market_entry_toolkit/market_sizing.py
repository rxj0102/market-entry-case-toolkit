"""Market sizing for FreshRoute's prospective GTA (Greater Toronto Area) entry.

Implements the two sizing approaches a case team runs in parallel and then
reconciles in front of the client:

* **Top-down**: start from a published/estimable total (Canadian grocery
  retail spend), narrow by online penetration, geography, and delivery
  (vs. pickup) mix, then apply a realistic obtainable share for a new
  entrant.
* **Bottom-up**: build up from the number of serviceable GTA households,
  the share FreshRoute could realistically convert, and per-customer
  spend (basket size x order frequency).

Both approaches land on a **Serviceable Obtainable Market (SOM)** -- the
revenue pool FreshRoute could realistically capture by year 5 of
operating in the GTA -- so they are directly comparable, and the gap
between them is diagnosed explicitly rather than averaged away.

DATA DISCLAIMER: every figure in `Assumptions` below is an illustrative,
order-of-magnitude proxy loosely anchored to public reporting on Canadian
grocery retail and e-commerce penetration (e.g. Statistics Canada retail
trade data, industry press on online grocery adoption). None of it is
scraped or licensed real data, and none of it should be treated as an
actual estimate of any real company's addressable market. See the
top-level README for the full disclaimer.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Assumptions:
    """All sizing inputs in one place, so every number is inspectable and
    changeable without hunting through function bodies. Units are noted
    per field. Defaults are the illustrative case assumptions used
    throughout the notebook and memo.
    """

    # --- Shared ---
    fx_cad_per_usd: float = 1.37  # CAD per 1 USD, illustrative

    # --- Top-down inputs ---
    canada_grocery_retail_spend_cad: float = 150_000_000_000
    online_grocery_penetration_pct: float = 0.085  # share of grocery spend online
    gta_population_share_of_canada_pct: float = 0.165
    gta_urban_online_adoption_premium: float = 1.25  # GTA over-indexes vs. national avg
    online_delivery_share_of_online_grocery_pct: float = 0.45  # vs. click-and-collect
    new_entrant_obtainable_share_pct: float = 0.17  # realistic year-5 share for a new entrant

    # --- Bottom-up inputs ---
    gta_households: int = 2_300_000
    serviceable_household_share_pct: float = 0.35  # in delivery zone, digitally engaged, income threshold
    year5_penetration_of_serviceable_pct: float = 0.05  # share of serviceable households as active customers
    avg_orders_per_week: float = 1.0
    avg_basket_size_cad: float = 105.0


@dataclass(frozen=True)
class TopDownResult:
    canada_online_grocery_market_cad: float
    gta_online_grocery_market_cad: float
    gta_online_delivery_market_cad: float
    som_cad: float
    som_usd: float

    def narrative(self) -> str:
        return (
            f"Top-down: CA online grocery market ≈ ${self.canada_online_grocery_market_cad / 1e9:.2f}B CAD → "
            f"GTA online grocery ≈ ${self.gta_online_grocery_market_cad / 1e9:.2f}B CAD → "
            f"GTA online *delivery* ≈ ${self.gta_online_delivery_market_cad / 1e6:.0f}M CAD → "
            f"realistic new-entrant SOM ≈ ${self.som_cad / 1e6:.0f}M CAD "
            f"(${self.som_usd / 1e6:.0f}M USD)."
        )


@dataclass(frozen=True)
class BottomUpResult:
    serviceable_households: int
    active_customers_year5: int
    annual_orders_per_customer: float
    annual_spend_per_customer_cad: float
    som_cad: float
    som_usd: float

    def narrative(self) -> str:
        return (
            f"Bottom-up: {self.serviceable_households:,} serviceable GTA households → "
            f"{self.active_customers_year5:,} active customers at maturity "
            f"(each ordering {self.annual_orders_per_customer:.0f}x/yr, "
            f"${self.annual_spend_per_customer_cad:,.0f} CAD/yr) → "
            f"SOM ≈ ${self.som_cad / 1e6:.0f}M CAD (${self.som_usd / 1e6:.0f}M USD)."
        )


@dataclass(frozen=True)
class Reconciliation:
    top_down: TopDownResult
    bottom_up: BottomUpResult
    gap_cad: float
    gap_pct_of_lower: float
    explanation: str


def size_top_down(a: Assumptions = Assumptions()) -> TopDownResult:
    """Top-down sizing: published-proxy total, narrowed to the GTA
    delivery-specific, new-entrant-obtainable slice.
    """
    canada_online = a.canada_grocery_retail_spend_cad * a.online_grocery_penetration_pct
    gta_online = (
        canada_online
        * a.gta_population_share_of_canada_pct
        * a.gta_urban_online_adoption_premium
    )
    gta_delivery = gta_online * a.online_delivery_share_of_online_grocery_pct
    som = gta_delivery * a.new_entrant_obtainable_share_pct
    return TopDownResult(
        canada_online_grocery_market_cad=canada_online,
        gta_online_grocery_market_cad=gta_online,
        gta_online_delivery_market_cad=gta_delivery,
        som_cad=som,
        som_usd=som / a.fx_cad_per_usd,
    )


def size_bottom_up(a: Assumptions = Assumptions()) -> BottomUpResult:
    """Bottom-up sizing: build up from households FreshRoute could
    actually serve and convert, and what each would realistically spend.
    """
    serviceable = int(round(a.gta_households * a.serviceable_household_share_pct))
    active_customers = int(round(serviceable * a.year5_penetration_of_serviceable_pct))
    annual_orders = a.avg_orders_per_week * 52
    annual_spend = annual_orders * a.avg_basket_size_cad
    som = active_customers * annual_spend
    return BottomUpResult(
        serviceable_households=serviceable,
        active_customers_year5=active_customers,
        annual_orders_per_customer=annual_orders,
        annual_spend_per_customer_cad=annual_spend,
        som_cad=som,
        som_usd=som / a.fx_cad_per_usd,
    )


def reconcile(a: Assumptions = Assumptions()) -> Reconciliation:
    """Run both approaches and produce a case-team-style reconciliation:
    quantify the gap and explain it in plain terms, the way you would in
    front of a client rather than just averaging the two numbers together.
    """
    td = size_top_down(a)
    bu = size_bottom_up(a)
    gap = bu.som_cad - td.som_cad
    lower = min(td.som_cad, bu.som_cad)
    gap_pct = gap / lower if lower else 0.0

    direction = "higher" if gap > 0 else "lower"
    explanation = (
        f"The bottom-up estimate comes in {abs(gap_pct):.0%} {direction} than top-down "
        f"(${bu.som_cad / 1e6:.0f}M vs. ${td.som_cad / 1e6:.0f}M CAD). This is expected and "
        "explainable, not a red flag: top-down applies an average obtainable "
        "share across the *entire* GTA online-delivery market, including "
        "households FreshRoute would never target (outside delivery zones, "
        "price-insensitive club-store shoppers, etc.). Bottom-up instead "
        "targets FreshRoute's actual go-to-market segment -- digitally "
        "engaged, dual-income households inside serviceable postal codes -- "
        "which converts at a higher rate than the market-wide average baked "
        "into the top-down share assumption. In a client meeting we would "
        "present the bottom-up number as the operating plan target and the "
        "top-down number as the sanity-check ceiling, and flag that the "
        f"{abs(gap_pct):.0%} gap is within the +/-20% range we'd expect from "
        "two independently-built estimates at this stage of diligence."
    )

    return Reconciliation(
        top_down=td,
        bottom_up=bu,
        gap_cad=gap,
        gap_pct_of_lower=gap_pct,
        explanation=explanation,
    )


def plot_reconciliation_waterfall(recon: Reconciliation, save_path: str | None = None):
    """Bridge/waterfall exhibit: top-down SOM, the reconciling delta, and
    bottom-up SOM, so the sizing gap is visualized rather than just stated.
    """
    from . import _viz

    fig, ax = _viz.new_figure(figsize=(7, 5))

    td = recon.top_down.som_cad / 1e6
    bu = recon.bottom_up.som_cad / 1e6
    gap = recon.gap_cad / 1e6

    labels = ["Top-down\nSOM", "Segment-targeting\nuplift", "Bottom-up\nSOM"]
    bottoms = [0, min(td, td + gap), 0]
    heights = [td, abs(gap), bu]
    colors = [_viz.BLUE, _viz.ORANGE, _viz.BLUE]

    bars = ax.bar(labels, heights, bottom=bottoms, width=0.5, color=colors, zorder=3)

    # Connector between the top-down total and the floating delta bar.
    ax.plot([0.25, 0.75], [td, td], color=_viz.GRAY_AXIS, linewidth=1, zorder=2)

    for bar, bottom, height in zip(bars, bottoms, heights):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bottom + height + 4,
            f"${height:.0f}M",
            ha="center",
            va="bottom",
            fontsize=10,
            color=_viz.PRIMARY_TEXT,
        )

    ax.set_ylabel("CAD, millions")
    ax.set_title("Market sizing reconciliation: top-down vs. bottom-up (CAD)", fontsize=11, color=_viz.PRIMARY_TEXT, loc="left")
    _viz.clean_axes(ax)
    ax.set_ylim(0, max(td, bu) * 1.25)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, facecolor=fig.get_facecolor())
    return fig
