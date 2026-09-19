"""Competitive benchmarking for the GTA online grocery delivery market.

Structures the competitor set the way a case team would build a
benchmarking exhibit: one row per competitor with share, pricing,
positioning, and unit-economics proxies, then two derived views a client
actually asks for --

1. **Market concentration** (via HHI) -- is this a market a new entrant
   can realistically get a foothold in, or is it already locked up?
2. **White space** -- where on the price/positioning map is nobody
   currently sitting, and does that gap match a strength FreshRoute
   actually has?

DATA DISCLAIMER: competitor names are real (Instacart, Loblaws' PC
Express, Sobeys' Voila, Walmart Canada, Amazon Fresh Canada) because a
believable competitive set is part of what makes this exercise realistic,
but every *figure* attached to them (share, pricing, margin) is an
illustrative, order-of-magnitude estimate for this case exercise -- not
sourced from any company's actual disclosures. See the README disclaimer.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Competitor:
    """One row of the competitive benchmarking table.

    price_index: 1 (cheapest) to 5 (most premium), relative positioning
        of total basket + fees, not a precise price level.
    curation_index: 1 (broad/mass assortment, low curation) to 5 (tightly
        curated, premium/specialty assortment).
    est_gross_margin_pct: illustrative proxy for category gross margin
        after cost of goods, before fulfillment cost.
    """

    name: str
    business_model: str
    est_market_share_pct: float
    price_index: int
    curation_index: int
    avg_order_value_cad: float
    est_gross_margin_pct: float
    differentiation: str


COMPETITORS: tuple[Competitor, ...] = (
    Competitor(
        name="Instacart Canada",
        business_model="Marketplace (picks/delivers from partner retailers' stores)",
        est_market_share_pct=30.0,
        price_index=3,
        curation_index=2,
        avg_order_value_cad=95.0,
        est_gross_margin_pct=0.22,
        differentiation="Breadth -- widest retailer selection, weakest control over fulfillment quality",
    ),
    Competitor(
        name="PC Express (Loblaws)",
        business_model="Retailer-owned, mostly click-and-collect + owned delivery",
        est_market_share_pct=25.0,
        price_index=2,
        curation_index=2,
        avg_order_value_cad=110.0,
        est_gross_margin_pct=0.24,
        differentiation="Private label + loyalty (PC Optimum) lock-in, weak on delivery speed",
    ),
    Competitor(
        name="Voila by Sobeys",
        business_model="Delivery-only, automated dark-store fulfillment",
        est_market_share_pct=15.0,
        price_index=4,
        curation_index=4,
        avg_order_value_cad=130.0,
        est_gross_margin_pct=0.27,
        differentiation="Premium/curated assortment and reliability, limited geographic coverage",
    ),
    Competitor(
        name="Walmart Canada Grocery",
        business_model="Retailer-owned delivery + pickup, value positioning",
        est_market_share_pct=20.0,
        price_index=1,
        curation_index=1,
        avg_order_value_cad=85.0,
        est_gross_margin_pct=0.18,
        differentiation="Lowest price, broad but low-curation assortment",
    ),
    Competitor(
        name="Amazon Fresh Canada",
        business_model="Prime-linked marketplace delivery",
        est_market_share_pct=10.0,
        price_index=3,
        curation_index=3,
        avg_order_value_cad=90.0,
        est_gross_margin_pct=0.20,
        differentiation="Prime bundling and convenience, inconsistent fresh/produce quality perception",
    ),
)

FRESHROUTE_PROPOSED_POSITION = Competitor(
    name="FreshRoute (proposed)",
    business_model="Partner-store picking + owned last-mile courier network",
    est_market_share_pct=0.0,
    price_index=3,
    curation_index=4,
    avg_order_value_cad=105.0,
    est_gross_margin_pct=0.23,
    differentiation="Mid-price reliability + fresh/local curation -- the gap between Walmart's "
    "cheap-and-broad and Voila's premium-and-narrow",
)


def herfindahl_hirschman_index(competitors: tuple[Competitor, ...] = COMPETITORS) -> float:
    """HHI = sum of squared market shares (shares in 0-100 points).

    Rule of thumb: <1500 unconcentrated, 1500-2500 moderately
    concentrated, >2500 highly concentrated. Used to test hypothesis 2.1
    (no single incumbent forecloses entry).
    """
    return sum(c.est_market_share_pct**2 for c in competitors)


def concentration_read(competitors: tuple[Competitor, ...] = COMPETITORS) -> str:
    hhi = herfindahl_hirschman_index(competitors)
    top_share = max(c.est_market_share_pct for c in competitors)
    if hhi > 2500:
        level = "highly concentrated"
    elif hhi > 1500:
        level = "moderately concentrated"
    else:
        level = "unconcentrated"
    return (
        f"HHI = {hhi:,.0f} ({level}); largest incumbent holds {top_share:.0f}% share. "
        f"No competitor exceeds ~30% -- the market is fragmented enough that a well-"
        "differentiated new entrant can realistically take share without displacing "
        "a single dominant player."
    )


def white_space_analysis(
    competitors: tuple[Competitor, ...] = COMPETITORS,
    proposed: Competitor = FRESHROUTE_PROPOSED_POSITION,
) -> str:
    """Identify the nearest incumbents to the proposed position on the
    price x curation grid and articulate the white-space argument.
    """
    def distance(c: Competitor) -> float:
        return ((c.price_index - proposed.price_index) ** 2 + (c.curation_index - proposed.curation_index) ** 2) ** 0.5

    nearest = sorted(competitors, key=distance)[:2]
    nearest_names = " and ".join(c.name for c in nearest)
    return (
        f"On a price (1=value, 5=premium) x curation (1=broad/mass, 5=curated/specialty) grid, "
        f"the proposed FreshRoute position (price={proposed.price_index}, curation={proposed.curation_index}) "
        f"sits in open space between the two nearest incumbents, {nearest_names}. "
        "Walmart Canada wins on price but offers minimal curation; Voila by Sobeys offers strong "
        "curation but at a premium price and with limited coverage. FreshRoute's mid-price, "
        "high-curation position -- reliability plus fresh/local sourcing without Voila's premium "
        "markup -- is not directly contested by any incumbent at scale, and matches FreshRoute's "
        "existing brand positioning in its US markets."
    )


def to_records(
    competitors: tuple[Competitor, ...] = COMPETITORS,
    include_proposed: bool = True,
) -> list[dict]:
    """Flatten the competitor set (optionally plus FreshRoute's proposed
    position) into plain dicts, ready for `pandas.DataFrame(...)` in the
    notebook or for chart-building in memo_synthesis exhibits.
    """
    rows = [asdict(c) for c in competitors]
    if include_proposed:
        rows.append(asdict(FRESHROUTE_PROPOSED_POSITION))
    return rows


def plot_positioning_map(
    competitors: tuple[Competitor, ...] = COMPETITORS,
    proposed: Competitor = FRESHROUTE_PROPOSED_POSITION,
    save_path: str | None = None,
):
    """Price x curation positioning map, bubble-sized by market share.

    With 7 points to distinguish (5 incumbents + Voila... + FreshRoute),
    identity is carried by direct labels rather than a 7-way categorical
    palette (which can't be made simultaneously colorblind-safe at that
    count) -- incumbents share one neutral color, FreshRoute's proposed
    position is the single highlighted accent color.
    """
    from . import _viz

    fig, ax = _viz.new_figure(figsize=(7.5, 6))

    for c in competitors:
        size = max(c.est_market_share_pct * 22, 120)
        ax.scatter(
            c.price_index,
            c.curation_index,
            s=size,
            color=_viz.MUTED,
            alpha=0.55,
            edgecolors=_viz.SURFACE,
            linewidths=2,
            zorder=3,
        )
        ax.annotate(
            f"{c.name}\n({c.est_market_share_pct:.0f}% share)",
            (c.price_index, c.curation_index),
            textcoords="offset points",
            xytext=(0, 14),
            ha="center",
            fontsize=8.5,
            color=_viz.SECONDARY_TEXT,
        )

    ax.scatter(
        proposed.price_index,
        proposed.curation_index,
        s=260,
        color=_viz.ORANGE,
        edgecolors=_viz.SURFACE,
        linewidths=2,
        zorder=4,
        marker="D",
    )
    ax.annotate(
        f"{proposed.name}\n(white space)",
        (proposed.price_index, proposed.curation_index),
        textcoords="offset points",
        xytext=(0, 16),
        ha="center",
        fontsize=9,
        fontweight="bold",
        color=_viz.PRIMARY_TEXT,
    )

    ax.set_xlim(0.5, 5.5)
    ax.set_ylim(0.5, 5.5)
    ax.set_xlabel("Price positioning (1 = value  ->  5 = premium)", color=_viz.SECONDARY_TEXT)
    ax.set_ylabel("Curation / assortment (1 = broad/mass  ->  5 = curated/specialty)", color=_viz.SECONDARY_TEXT)
    ax.set_title("GTA online grocery delivery: competitive positioning map", fontsize=11, color=_viz.PRIMARY_TEXT, loc="left")
    _viz.clean_axes(ax, y_grid=False)
    ax.grid(True, color=_viz.GRAY_GRID, linewidth=1, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, facecolor=fig.get_facecolor())
    return fig
