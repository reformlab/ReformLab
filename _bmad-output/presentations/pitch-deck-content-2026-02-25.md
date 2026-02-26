# ReformLab — Pitch Deck Content

**Author:** Lucas
**Date:** 2026-02-25
**Purpose:** Customer adoption pitch — presentation content for PPT creation
**Audience:** Potential customers/adopters (policy analysts, researchers, engaged citizens)

---

## Slide 1: TITLE

**ReformLab**
*See the impact before the vote.*

Tagline: Simulate environmental reforms. Understand who wins, who loses. Trust the results.

> **Design note:** Bold, clean. One visual element — a stylized before/after showing households affected differently by a policy. No technical jargon. Zero mention of engines or backends.

---

## Slide 2: THE CONTEXT — What Are Environmental Reforms?

**Governments are transforming how we live, move, and consume energy.**

Every year, new policies reshape household budgets:

- **Energy pricing** — Carbon taxes, energy tariffs, fuel levies
- **Transport** — Vehicle emission standards, low-emission zones, mobility subsidies
- **Housing** — Renovation incentives, heating system regulations, energy efficiency mandates
- **Redistribution** — Green dividends, targeted rebates, progressive compensation schemes

These reforms affect every household differently — by income, by region, by lifestyle.

**The question is always the same: who pays, who benefits, and by how much?**

> **Design note:** Grid of 4 policy domains, each with an icon (energy/lightning, transport/car, housing/building, redistribution/balance scale). Below the grid, the unifying question in bold. This slide educates — don't assume the audience knows the landscape.

---

## Slide 3: THE AUDIENCE — Who Needs Answers?

**Three groups need rigorous, fast environmental policy assessment.**

| | Policy Analyst | Researcher | Engaged Citizen |
|---|---|---|---|
| **Context** | Government evaluation department, consulting firm, think tank | University or research institute | Voter, activist, journalist |
| **Needs** | Assess proposed reforms before they're enacted | Project estimated effects on real populations | Understand how reforms affect their household |
| **Today's reality** | Weeks of manual work chaining tools for each assessment | Custom throwaway code for each paper | Abstract numbers in media, no personal relevance |
| **Wants** | Fast, reproducible, briefing-ready analysis | Clean, reproducible projection of research estimates | "Show me what this means for people like me" |

> **Design note:** Three columns with avatar silhouettes (not named personas). Each column is a card. Keep it human — these are real people with real frustrations.

---

## Slide 4: THE PROBLEM

**Every environmental policy assessment starts from scratch.**

Today, answering "what's the impact of this reform?" requires:

1. **Finding and preparing data** — population surveys, energy consumption, emission factors — scattered across sources, incompatible formats
2. **Building the simulation** — custom scripts connecting income models, energy models, behavioral assumptions — rebuilt every time
3. **Running projections** — manually looping year by year, tracking what changes over time (fleet turnover, heating transitions)
4. **Computing who wins and loses** — custom analysis code for distributional impact, fiscal cost, welfare effects
5. **Documenting methodology** — usually skipped, making results impossible to audit or reproduce

**Result:** Weeks of work. Fragile pipelines. Undocumented assumptions. No reproducibility.

And when the minister asks "what about low-income rural households?" — you start over.

> **Design note:** Numbered steps down the left side, each with a "pain icon" (clock, broken chain, question mark). The final line is the emotional gut punch — isolated, bigger font, maybe in red.

---

## Slide 5: THE GAP

**No existing tool covers the full workflow.**

| | Tax-benefit tools | Energy/building tools | Ad-hoc scripts |
|---|---|---|---|
| Cross-domain (income + energy + transport) | No | No | Fragile |
| Multi-year projections | No | No | Manual |
| Distributional impact (who wins/loses) | Partial | No | Manual |
| Built-in reproducibility | No | No | No |
| No-code access for non-programmers | No | No | No |
| Environmental policy focus | No | No | Rebuilt each time |

**There is no integrated platform for environmental reform assessment.**

> **Design note:** Table with red/green cells. The bottom row ("no-code access") is new and important — it sets up the solution. The conclusion line sits below the table in bold.

---

## Slide 6: THE SOLUTION

**ReformLab: end-to-end environmental policy assessment — no code required.**

A platform where you configure a reform, run it against a population, and see who wins and who loses — all from a visual interface.

**The workflow:**

**Configure** — Pick a policy template (carbon tax, subsidy, renovation incentive). Adjust parameters. Define the timeline. No coding.

**Simulate** — Run against a realistic population. Multi-year projections with automatic tracking of what changes over time (vehicle fleet, heating systems, household transitions).

**Analyze** — Distributional impact by income, region, household type. Winners and losers. Fiscal cost. Side-by-side scenario comparison.

**Trust** — Every run is fully documented. Every assumption is logged. Every result is reproducible.

> **Design note:** Four-step horizontal flow. Each step is a panel with an icon and a short description. The visual hero is a mockup/wireframe of the GUI showing a scenario comparison dashboard. THIS is the product — make it feel tangible.

---

## Slide 7: WHAT MAKES REFORMLAB DIFFERENT

1. **No-code, end-to-end workflow** — From policy definition to distributional charts without writing a single line of code. Researchers can use the Python API and notebooks when they need full control.

2. **Environmental policy templates** — Pre-built, reusable templates for carbon taxes, energy subsidies, transport policies, renovation incentives. Configure and run — don't rebuild.

3. **Dynamic multi-year projection** — Not just a snapshot. See how impacts evolve over 10+ years as vehicle fleets turn over, heating systems transition, and policies phase in.

4. **Assumption transparency** — Every parameter, data source, and methodological choice is logged automatically. Full reproducibility without extra effort.

5. **Open-data default** — Works out of the box with public data. No restricted datasets required. Bring your own data when you have it.

> **Design note:** Five stacked cards or tiles. Each has a bold title and one-sentence explanation. The no-code workflow is #1 — it's the headline differentiator for this audience. Make it visually dominant.

---

## Slide 8: FOR THE POLICY ANALYST

**"I modified one parameter and got updated charts instantly. This used to take me weeks."**

**Before ReformLab:**
- Chain three tools for every assessment
- Rebuild pipelines each quarter
- Manual methodology documentation
- Hours to answer follow-up questions

**With ReformLab:**
- Configure the reform in the GUI
- Run against the built-in population
- Get distributional charts, fiscal costs, welfare analysis — instantly
- When someone questions an assumption, open the log and re-run with an alternative in minutes

> **Design note:** Before/after split. Left side gray and cluttered, right side clean and bright. The quote at the top is the hook.

---

## Slide 9: FOR THE RESEARCHER

**"I was able to project my estimated results onto a clean, reproducible simulation — and my co-author reproduced them on a different machine."**

**Before ReformLab:**
- 800 lines of custom code per paper
- Results impossible to replicate
- Co-authors can't run your simulation
- Replication packages are incomplete

**With ReformLab:**
- Use the Python API or Jupyter notebooks for full programmatic control
- Define reforms, run multi-year projections, get indicators
- Every run produces an immutable manifest — parameters, data sources, assumptions, versions
- Share the configuration, share the results. Reproducibility by default.

> **Design note:** Same before/after split structure as the analyst slide. The quote emphasizes projection + reproducibility. Show a notebook screenshot mockup.

---

## Slide 10: FOR THE ENGAGED CITIZEN

**"I finally understand who wins and who loses."**

A public web application built on ReformLab lets citizens:

- **Enter their household profile** — income, region, housing type, commuting pattern
- **Compare reform proposals side by side** — "Under Proposal A, your household pays €340 more but receives €420 in rebates"
- **See the big picture** — distributional impact across income groups, regions, household types
- **Understand "people like me"** — how households with a similar profile are affected

**Use case:** Before elections, compare candidates' environmental platforms. Before a vote, understand the real household impact.

> **Design note:** Mockup of a citizen-facing comparison dashboard. Two candidate proposals side by side, household impact highlighted. This is the emotional climax — make it vivid. This is the "why this matters to society" slide.

---

## Slide 11: COMPETITIVE LANDSCAPE

**The field is clearing — and no one occupies this space.**

- **General tax-benefit tools** (OpenFisca, EUROMOD) — Strong on income/tax rules, but no environmental workflow, no multi-year projection, no no-code interface
- **Energy/building tools** (ResStock, demod) — Physical models only, no distributional analysis, no household income dimension
- **Legacy frameworks** — LIAM2 discontinued, OpenM++ archived. Teams need alternatives now.
- **PolicyEngine** — Public-facing tax-benefit delivery, not environmental policy operations

**ReformLab sits at the intersection no one else occupies:** environmental + distributional + dynamic + no-code.

> **Design note:** Positioning map. X-axis: tax-benefit focused <-> environmental focused. Y-axis: static/code-only <-> dynamic/no-code. ReformLab alone in the top-right. Other tools clustered in other quadrants.

---

## Slide 12: WHY NOW

**Three forces converging:**

1. **The policy moment** — EU Green Deal, carbon border adjustment, national carbon taxes. Governments need assessment tools faster than ever.

2. **The tool gap** — Legacy platforms are dying (LIAM2, OpenM++). No replacement serves the environmental policy workflow.

3. **The technology shift** — Mature open-source computation engines, powerful scientific Python stack, and AI-assisted development make this buildable now by a focused team.

> **Design note:** Three columns with large icons. Urgency without panic. These are opportunities, not threats.

---

## Slide 13: GET STARTED

**ReformLab**
*See the impact before the vote.*

- Open-source, no vendor lock-in
- Works offline, no cloud dependency
- Open-data default — functional out of the box
- 30 minutes from install to first meaningful output

**Let's talk:** [contact / GitHub / demo link]

> **Design note:** Return to the title slide visual language. Big tagline. Clean call-to-action. The closing mirror of the opening creates narrative closure.

---

## Speaker Notes — Narrative Arc

| Slide | Job | Emotional beat |
|---|---|---|
| 1 — Title | Hook | Curiosity |
| 2 — Context | Educate | "Oh, these are real policies affecting real people" |
| 3 — Audience | Identify | "That's me / that's my team" |
| 4 — Problem | Pain | "Yes, this is exactly what we deal with" |
| 5 — Gap | Frustration | "Right, nothing solves this properly" |
| 6 — Solution | Relief | "Wait, this does everything in one place?" |
| 7 — Differentiators | Conviction | "Okay, this is genuinely different" |
| 8 — Analyst | Recognition | "I see myself using this" |
| 9 — Researcher | Trust | "This solves my reproducibility problem" |
| 10 — Citizen | Inspiration | "This could change how people understand policy" |
| 11 — Landscape | Confidence | "No one else is doing this" |
| 12 — Why now | Urgency | "The timing is right" |
| 13 — Get started | Action | "I want to try this" |
