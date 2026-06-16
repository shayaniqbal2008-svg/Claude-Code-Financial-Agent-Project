# Financial Agent — CLAUDE.md

## What This Is

A personal automated financial analysis agent built for Shayan Iqbal. It runs
every morning at market open (8:30 AM CT — Dallas, TX) with no manual trigger,
reads Shayan's live Robinhood portfolio, evaluates holdings and researched
candidate stocks against a specific 15-point investment criteria, weighs current
news and political developments heavily, and produces a structured daily advisory
report that Shayan reviews and acts on.

Shayan executes all trades manually. There is no auto-execution in v1. This is a
recommendation and research engine, not a trading bot.

**This is not a generic financial advisor.** The 15 criteria and the halal filter
below are the sole basis for every decision. Do not substitute, supplement, or
override them with outside frameworks or independent judgment about what makes a
"good" stock.


---


## What the Agent Produces Every Morning

1. Portfolio Review — grade each current holding against all 15 criteria
2. Sell Alerts — holdings that now fail criteria OR carry news/political risk
3. Buy Candidates — researched stocks currently passing all 15 criteria
4. News Briefing — headlines materially affecting the portfolio and candidates
5. Market & Political Alerts — macro and political developments that could move
   the market that day or in the near term


---


## News & Politics Are First-Class Signals — Treat Them Seriously

This is critical and easy to underweight. **A single statement from the president,
a Fed decision, a tariff announcement, or a geopolitical escalation can move the
entire market more than any company fundamental.** The agent must treat news and
politics as primary inputs, not background color.

- Actively monitor market-moving political and macro events: presidential
  statements, executive actions, Fed/interest-rate moves, tariffs, regulation,
  major geopolitical conflict, elections, and policy shifts.
- A stock can pass all 15 fundamental criteria and still warrant a hold or sell
  because of a near-term political or macro catalyst. Surface that conflict
  explicitly in the report.
- Distinguish noise from genuine market-moving events. Flag what actually matters
  and explain the likely market impact in plain terms.
- News and political risk feed directly into the sell-alert logic. If something
  significant is happening or imminent, say so loudly and early.


---


## Research Philosophy — Look Wider, But the Criteria Are the Gate

The 15 criteria are the gate. Nothing passes that doesn't clear ALL of them —
period. Research never bends the criteria; it only finds more candidates to run
through them. If a name fails any criterion, it does not get surfaced, no matter
how promising it looks.

Within that hard boundary, don't be lazy or generic. A common failure mode is
defaulting to the obvious front-page large-cap names (NVDA, AAPL, GOOGL-tier) and
calling it research. Cast a wider net:

- Dig past the popular tickers to find less-obvious companies — the suppliers,
  enablers, and component players supporting AI data centers — that ALSO clear
  every single criterion, including the momentum filter (#7), the profitability
  requirement, and the one-year return threshold.
- Do NOT neglect reputable names where they qualify. The goal is breadth of
  *qualifying* candidates, not novelty for its own sake.
- The criteria always win. A less-obvious name that fails any criterion is out —
  including a beaten-down or under-followed name that fails the momentum filter.
  Do not surface or recommend it.
- The agent builds and maintains its own watchlist over time through ongoing
  research, seeded by the AI-infrastructure thesis (memory, storage, power,
  cooling, networking, chips, and direct suppliers/enablers to AI data centers).
  There is no pre-loaded watchlist — find the companies that qualify.


---


## The 15 Investment Criteria

These are the ONLY criteria used to evaluate any stock. Every recommendation must
be traceable back to them. Do not add, remove, or reinterpret.

### Quantitative (hard pass/fail — fundamental data)
1. Market cap greater than $1 billion
2. Profit margin positive (company must be profitable, not negative)
3. Total cash positive AND in the millions at minimum — a company with only
   thousands in cash fails this criterion
4. Forward P/E positive
5. One-year price return greater than 15%
6. Current stock price at or below the analyst average (mean) price target
7. Current price at or above 80% of the 52-week high (momentum filter)
8. More than 1,000 employees

### Qualitative (judgment — company profile, news, and context)
9. NOT an Israeli company and NOT primarily funded by Israel-based sources
10. No significant war, political, or geopolitical exposure materially affecting
    the stock right now or imminently
11. Strong, robust technology with genuine growth potential
12. Fits the AI-infrastructure theme — memory, storage, power, cooling,
    networking, or chips supporting AI data centers
13. Financial highlights overall positive — healthy trends, no major red flags
14. Acts as a supplier or enabler to AI hyperscalers (e.g., the data-center
    buildouts of NVDA, Google, Microsoft, Amazon, Meta) — parts, cables, memory,
    storage, power, cooling
15. GOOGL and AAPL are always standing positions — flag if underweight, never
    recommend selling without a significant and specific cause


---


## The Halal Filter — Non-Negotiable, Runs First

Applied before any other analysis. A stock that fails halal screening is excluded
entirely — no further work spent on it. The screen is twofold: ethical ownership
AND business activity.

Exclude any company that:
- Is headquartered in Israel or is primarily funded by Israel-based sources
- Derives significant revenue from **haram business activities**, including but
  not limited to:
  - Alcohol (production, distribution, or sale) — beer, wine, spirits
  - Pork or other non-halal food production
  - Gambling or casinos
  - Haram entertainment / content (e.g., a company like Netflix whose core
    content significantly involves haram material)
  - Adult content
  - Conventional banking or insurance built primarily on interest (riba)
- Carries interest-bearing debt exceeding roughly one-third of total assets,
  where that data is available (riba screen)

General principle: if a company's core business significantly conflicts with
Islamic values, exclude it — even if its fundamentals are excellent.

**Multi-user note (future):** This filter is hardcoded ON for Shayan. If the agent
is ever opened to other users, the halal filter must become an explicit opt-in
preference asked during onboarding, never applied automatically to others.


---


## Direction & Resources — Guidance, Not Mandates

You (Claude Code) are a capable agent. Architect the system yourself. The notes
below are direction and advice, not rigid specification — make your own sound
engineering decisions.

- **Language:** Python is a strong fit for this domain given its financial and
  data tooling. Reasonable default unless you have a better reason.
- **Financial data:** Yahoo Finance is genuinely powerful for pulling most of the
  quantitative criteria (market cap, margins, cash, forward P/E, price history,
  analyst targets, 52-week range, employee count). Shayan's dad relies on it and
  it serves him well. Look hard at Yahoo Finance (e.g., the `yfinance` library) as
  a primary source; supplement with others as needed.
- **Portfolio data — Robinhood MCP:** Shayan uses Robinhood. Robinhood now exposes
  an official MCP server for reading portfolio and account data:
  - URL: `https://agent.robinhood.com/mcp/trading`
  - Connect in Claude Code: `claude mcp add robinhood-trading --transport http https://agent.robinhood.com/mcp/trading`
  - Use it for live positions and prices. Execution is NOT used in v1 (advisory
    only). The feature is in beta rollout — if access isn't live yet, fall back to
    a manually maintained local holdings file until it is.
- **Qualitative reasoning:** The qualitative criteria, news analysis, and the
  final recommendations are well-suited to the Claude API. For efficiency on runs
  that analyze many stocks, consider prompt caching the static criteria block so
  it isn't re-billed on every call.
- **Always-on dashboard:** Shayan wants a viewable, always-running local dashboard
  he can check any time — a Jarvis-style interface. Pick a sensible approach for a
  fast, good-looking local UI.
- **Automatic daily run:** It must run on its own at 8:30 AM CT on Windows (with a
  path to Mac later). Point yourself toward a reliable scheduling mechanism that
  survives reboots; you choose the implementation.
- **Storage & structure:** Persist daily reports and history so the dashboard and
  future analysis can read them. Keep the codebase clean and modular — separate
  concerns sensibly so pieces can be built and tested one at a time. The exact file
  layout, libraries, and conventions are yours to decide.


---


## Constraints — Do Not Violate

1. Advisory only in v1 — the agent recommends, Shayan executes manually
2. The 15 criteria are the sole decision framework — no additions or overrides
3. The halal filter is mandatory and runs before everything else
4. Research looks beyond the obvious names — but only surfaces candidates that
   pass every criterion; the criteria always win
5. News and politics are primary signals, weighted heavily in every call
6. Run halal and quantitative screening before LLM calls to avoid wasted work


---


## Build Approach

Build incrementally, one component at a time, verifying each piece works before
moving on. Shayan is walking through this step by step to understand the workflow
and catch issues live. Explain non-obvious decisions as you go. Once the full
workflow is built and working, it will be captured as a reusable skill.
