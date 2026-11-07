# market-entry-case-toolkit

[![CI](https://github.com/rxj0102/market-entry-case-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/rxj0102/market-entry-case-toolkit/actions/workflows/ci.yml)

A hypothesis-led market-entry strategy toolkit, built the way a management-consulting
case team would frame and solve the question — not a finance model, and not generic
data science.

This repository works one concrete, realistic case end to end: **should FreshRoute, a
mid-size U.S. online grocery delivery company, enter the Greater Toronto Area (GTA)
online grocery delivery market in Canada?** Every module, chart, and the final memo
are built around this single case, not an abstract framework.

> **Disclaimer:** FreshRoute is a fictional company built for this exercise. Competitor
> names (Instacart Canada, PC Express/Loblaws, Voilà by Sobeys, Walmart Canada,
> Amazon Fresh Canada) are real, but every figure attached to them — market share,
> pricing, unit economics — is an illustrative, order-of-magnitude proxy, not sourced
> from any company's actual disclosures. All market-sizing and financial figures are
> similarly illustrative/public-proxy estimates for the purposes of this case exercise.
> **Nothing here is real client data, investment advice, or a real assessment of any
> named company's market opportunity.**

## Why this exists

This project was built as a portfolio piece for consulting recruiting (specifically,
Bain & Company's Associate Consultant program). The goal isn't to demonstrate "I can
code a financial model" — plenty of toolkits do that. The goal is to demonstrate
**structured, hypothesis-led problem-solving**: framing an ambiguous business question
as an explicit, testable issue tree; running the right analysis against each branch;
being honest when the analysis doesn't support a clean "yes"; and reframing the
recommendation accordingly, the way a real case team does when the first-pass answer
is "no, not like this — but yes, like this instead."

## The case, in one paragraph

FreshRoute (~US$400M revenue, ~15 U.S. metro markets) is considering a first
international expansion into the GTA. We frame the question as four testable
hypotheses — **is the market attractive, is competitive intensity manageable, does
FreshRoute's operating model transfer, and is the entry financially worth it** — and
run a dedicated analysis against each. Market sizing and competitive positioning both
come back supportive. The financial case for a full-scale, ~$18M CAD upfront launch
does **not** clear payback within five years under any modeled scenario — a realistic
finding, consistent with how capital-intensive and slow-to-profit on-demand grocery
delivery has proven to be industry-wide. Rather than stopping at "no," the case
reframes the ask: **a conditional go, restructured as a milestone-gated phased pilot**
that proves out unit economics before the full build-out is committed. The full
reasoning is in [`outputs/recommendation_memo.md`](outputs/recommendation_memo.md) and
[`notebooks/case_walkthrough.ipynb`](notebooks/case_walkthrough.ipynb).

## Methodology: hypothesis-led, not data-led

A case team doesn't start with a spreadsheet — it starts with the question, broken
into a **hypothesis tree** (a.k.a. issue tree): a set of mutually exclusive,
collectively exhaustive sub-hypotheses that, if all true, prove the core question, and
if any is false, disprove it. Every other module in this package exists to resolve one
leaf of that tree; the tree itself is the spine of the whole project.

```
[0] FreshRoute should enter the GTA online grocery delivery market
├── [1] Market attractiveness
│   ├── [1.1] Top-down/bottom-up sizing clears the minimum bar   → market_sizing.py
│   └── [1.2] Online grocery penetration is still rising          → market_sizing.py
├── [2] Competitive intensity is manageable
│   ├── [2.1] No single incumbent forecloses entry                → competitive_benchmarking.py
│   └── [2.2] A defensible white-space position exists             → competitive_benchmarking.py
├── [3] Capability fit
│   ├── [3.1] Fulfillment model transfers without a new buildout  → qualitative review
│   └── [3.2] Regulatory/compliance differences are navigable      → qualitative review
└── [4] Financial viability
    ├── [4.1] Base case pays back within the board-level bar      → financial_feasibility.py
    └── [4.2] NPV is positive; downside is not catastrophic        → financial_feasibility.py
```

A parent hypothesis only rolls up to "supported" if **every** child is supported; any
one "not supported" child sinks the branch (see `Hypothesis.rollup_verdict()` in
`hypothesis_tree.py`). In this case, that strict rule produces a root verdict of "not
supported... for a full-scale launch as originally framed" — which is the correct,
honest answer to the question as posed, and exactly the finding that drives the
memo's actual recommendation: don't close the door, reframe the ask.

## Package layout

```
src/market_entry_toolkit/
├── hypothesis_tree.py           # the issue tree: data model, MECE rollup logic, rendering
├── market_sizing.py              # top-down + bottom-up TAM/SOM, reconciliation, waterfall exhibit
├── competitive_benchmarking.py   # competitor table, HHI concentration, white-space/positioning exhibit
├── financial_feasibility.py      # 5yr P&L, base/upside/downside, payback/NPV/IRR, scenario exhibit
├── memo_synthesis.py             # prompt library + template/live LLM synthesis + human review checklist
└── _viz.py                       # shared chart styling (not a case module — just shared plot theme)

notebooks/case_walkthrough.ipynb  # the case, worked end-to-end in the case team's own voice
outputs/recommendation_memo.md    # the final client-ready memo (generated by the notebook)
outputs/exhibits/*.png            # the three supporting exhibits (generated by the notebook)
tests/                            # unit tests for the quantitative/structural logic in each module
```

## Module 1 — Market sizing (`market_sizing.py`)

Runs the market two independent ways and reconciles them rather than averaging them
together, because the gap itself is informative and a client will always ask about it:

- **Top-down**: Canadian grocery retail spend → online penetration → GTA share
  (with an urban-adoption premium) → delivery-vs-pickup split → a realistic
  new-entrant-obtainable share.
- **Bottom-up**: serviceable GTA households → FreshRoute's realistic year-5
  penetration of that segment → orders/week × basket size → annual spend per customer.

Both land on a **Serviceable Obtainable Market (SOM)**, so they're directly
comparable. `reconcile()` returns both figures, the dollar/percentage gap between
them, and a written explanation of *why* the gap exists (bottom-up targets
FreshRoute's actual go-to-market segment, which converts above the market-wide
average baked into the top-down share assumption) — the way you'd explain it in a
client meeting, not just report a number.

## Module 2 — Competitive benchmarking (`competitive_benchmarking.py`)

Structures the five-competitor set on market share, price positioning, curation/
assortment breadth, and unit-economics proxies. Two derived views:

- **Concentration** (`concentration_read()`): Herfindahl-Hirschman Index — is this a
  market a new entrant can realistically get a foothold in, or is it already locked up?
- **White space** (`white_space_analysis()`): where on the price × curation grid is
  nobody currently sitting, and does that gap match a strength FreshRoute actually has?

## Module 3 — Hypothesis tree (`hypothesis_tree.py`)

The structural backbone described above. Plain dataclasses, no external dependencies —
the logic of the case (what would have to be true, and what analysis proves or
disproves it) is fully transparent and testable, not hidden inside prose.

## Module 4 — Financial feasibility (`financial_feasibility.py`)

A simple 5-year P&L under base/upside/downside scenarios, anchored to the bottom-up
SOM as the year-5 revenue target. Computes payback period and NPV/IRR at a 10%
discount rate. Deliberately lean: no working-capital or tax modeling, no terminal
value beyond year 5 — a case team's financial feasibility check answers "is this
directionally worth doing," not "give me an investment-grade DCF," and the toolkit's
quality bar prioritizes the hypothesis tree and memo over financial-modeling
sophistication. That said limitation is stated explicitly in both the code and the
memo, not hidden.

## Module 5 — Memo synthesis (`memo_synthesis.py`) — the AI-assisted step

This is the "emerging capabilities such as generative AI" piece, built to be legible
and auditable rather than a black box:

- **`SYSTEM_PROMPT`** and **`build_user_prompt()`** are plain, printable strings — the
  exact prompt sent to the model is inspectable and unit-tested independent of whether
  a live call happens.
- The LLM is handed the case team's own findings (market sizing, competitive
  benchmarking, financial feasibility, the full hypothesis tree) **and the bottom-line
  recommendation the case team already reached** (`recommendation_hint`). Its job is
  to *write up* that recommendation in Situation/Complication/Resolution form, citing
  only the facts it's given — never to originate a number or independently decide the
  recommendation. That's the main guardrail against drift.
- **Two synthesis modes**, auto-selected by `synthesize_memo()`:
  - **Template mode** (`draft_memo_template()`): fully offline, deterministic, no
    network access or API key required. **This is what produced
    `outputs/recommendation_memo.md` and the notebook's memo cell in this
    repository** — no LLM API access was available in the environment this toolkit was
    built in.
  - **Live mode** (`draft_memo_live()`): calls the Anthropic API if the optional
    `anthropic` package is installed and `ANTHROPIC_API_KEY` is set. Included,
    documented, and covered by tests (against the no-key/no-package failure path) so a
    user with their own API key can opt in — set the environment variable and rerun
    the notebook; `synthesize_memo()` will pick it up automatically.
- **Human-in-the-loop review is explicit, not implied.** `REVIEW_CHECKLIST` is a
  concrete list a case-team member works through before a draft goes near a client
  (every number traces to source, the recommendation wasn't softened, no invented
  competitor claims, tone/length are client-appropriate, a named reviewer signed off).
  `verify_traceability()` is a lightweight automated *complement* to that checklist —
  it flags source figures that silently dropped out of the draft — but it explicitly
  does **not** try to catch fabrication by string-matching, which is exactly why the
  human checklist exists.

## The notebook and the memo

[`notebooks/case_walkthrough.ipynb`](notebooks/case_walkthrough.ipynb) is written as
the case team's own working notes: frame the question, run each piece of analysis,
read the result, resolve the relevant hypothesis-tree leaf, and move on — ending with
the synthesis step and the human review checklist. It's the source of truth; running
it end to end regenerates `outputs/recommendation_memo.md` and the three exhibits in
`outputs/exhibits/`.

The final memo is a ~750-word Situation/Complication/Resolution document with three
embedded exhibits:

1. **Market sizing reconciliation** (waterfall/bridge chart) — top-down SOM,
   bottom-up SOM, and the delta between them.
2. **Competitive positioning map** — price × curation, bubble-sized by market share,
   with FreshRoute's proposed white-space position highlighted.
3. **5-year cumulative cash flow by scenario** — base/upside/downside, so "when do we
   get our money back, and how bad does downside get" is visual, not just a table.

## Running it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"        # add ".[llm]" too if you want to try live synthesis

# Run the full case end-to-end and regenerate the memo + exhibits:
jupyter nbconvert --to notebook --execute --inplace notebooks/case_walkthrough.ipynb
# ...or just open notebooks/case_walkthrough.ipynb and run all cells.

# Run the tests:
pytest
```

To try **live LLM synthesis** instead of the offline template: `pip install
anthropic`, `export ANTHROPIC_API_KEY=...`, and rerun the notebook — the synthesis
cell auto-detects the key and switches modes (it prints which mode it used).

## What's intentionally out of scope

- **No real data.** Every input is an illustrative, hand-set proxy (see
  `Assumptions` dataclasses in `market_sizing.py` and `financial_feasibility.py`) —
  the point is to demonstrate the *method*, not to scrape or license real market data.
- **No investment-grade financial model.** No working capital, tax, or terminal-value
  modeling; see `financial_feasibility.py`'s module docstring. The quality bar for
  this project is the hypothesis tree and the memo, not the DCF.
- **No live LLM call baked into the committed outputs.** No API key was available in
  the build environment; the live path is implemented, documented, and tested, but
  `outputs/recommendation_memo.md` was generated in template mode. This is stated in
  the memo's own footer, not hidden.

## License

MIT — see [`LICENSE`](LICENSE).
