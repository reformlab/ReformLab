---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/research/market-funding-and-credits-for-govtech-policy-tools-research-2026-02-28.md
session_topic: 'Governance model and sustainability strategy for ReformLab'
session_goals: 'Identify the right organizational structure, licensing model, and revenue/funding approach that maximizes both impact and sustainability'
selected_approach: 'ai-recommended'
techniques_used: ['Assumption Reversal', 'Morphological Analysis', 'Values Archaeology']
ideas_generated: 12
technique_execution_complete: true
session_active: false
workflow_completed: true
facilitation_notes: 'Lucas is a pragmatic builder — driven by seeing broken tooling in ministries firsthand, not ideology. Values autonomy, learning, and impact over profit. Makes decisions quickly once the logic is clear. Responds well to concrete comparisons and real-world examples (PolicyEngine, GitLab, OpenFisca). The session naturally converged toward a staged open-source governance model.'
---

# Brainstorming Session Results

**Facilitator:** Lucas
**Date:** 2026-03-03

## Session Overview

**Topic:** Governance model and sustainability strategy for ReformLab — open-source vs. proprietary, commercial vs. non-profit, funding mechanisms
**Goals:** Identify the right organizational structure, licensing model, and revenue/funding approach that maximizes both impact and sustainability given the market realities

### Context Guidance

_ReformLab is an OpenFisca-first environmental policy analysis platform targeting French/European policy simulation. Small niche market (govtech/policy tools). Built on open-source foundations (OpenFisca). Key tensions: open-source alignment vs. commercial viability, small addressable market vs. sustainability needs, non-profit funding access vs. commercial flexibility._

### Session Setup

_Lucas is exploring fundamental governance questions: whether to open-source the tool (aligning with OpenFisca ecosystem but complicating sales), whether the market is large enough for a commercial play, and whether a non-profit or association structure would unlock better funding sources (grants, public contracts, EU funding). These are interdependent decisions that shape the entire project trajectory._

## Technique Selection

**Approach:** AI-Recommended Techniques
**Analysis Context:** Governance model and sustainability strategy for ReformLab with focus on organizational structure, licensing, and funding

**Recommended Techniques:**

- **Assumption Reversal:** Challenge and flip core assumptions about open-source, market size, and funding to clear the mental space before exploring options
- **Morphological Analysis:** Systematically map all governance dimensions (licensing x org structure x revenue model x funding) to discover non-obvious combinations
- **Values Archaeology:** Excavate deep personal values driving the governance decision to filter options through what authentically matters

**AI Rationale:** Strategic governance decisions carry heavy assumption load ("open-source = can't sell", "market is small", "non-profit = better funding"). Clearing assumptions first, then systematically mapping the full option space, then filtering through values produces higher-quality decisions than jumping straight to pros/cons of binary choices.

---

## Technique Execution Results

### Technique 1: Assumption Reversal

**Interactive Focus:** Systematically surfaced and flipped 5 core assumptions about open-source, competition, market size, non-profit funding, and governance timing.

**Assumptions Challenged:**

| # | Original Assumption | Flipped Insight | Status |
|---|---|---|---|
| 1 | "Open-source = can't monetize" | Value lives in maintained service layer (data, scenarios, expertise), not code. Credibility/transparency essential for policy tools. | Partially true, partially limiting |
| 2 | "Competitors will fork my work" | The same market conditions that make you doubt viability make competitor entry unlikely. PhD + dev teams could build from scratch with OpenFisca today — they haven't because the unglamorous work (data pipelines, vintage tracking) isn't attractive for a small market. | Real but overstated |
| 3 | "The market is small" | The market is concentrated (few institutional buyers, significant budgets), not small. It's a high-value, low-volume market that works through grants and procurement, not SaaS sales. | Reframed — wrong metric |
| 4 | "Non-profit = better funding" | Open-source is the funding prerequisite regardless of legal structure. Almost every major grant (NGI, Sovereign Tech, Mozilla, DINUM) requires OSS — not non-profit status. | Partially wrong — it's about open-source, not legal form |
| 5 | "Must choose one governance model upfront" (hidden) | Staged governance is legal and common. Start lightweight, formalize later based on real data. | Assumption surfaced and challenged |

**Key Breakthroughs:**

- The "Competitor Paradox": if the market is too small for you to confidently sell into, it's too small for competitors to enter just because you made the code available
- Open-source isn't the obstacle to revenue — it's the entry ticket to the best funding (€100k-300k+ in grants that require OSS)
- The real competitive moat is domain expertise + maintained data + being the recognized reference, not proprietary code

### Technique 2: Morphological Analysis

**Interactive Focus:** Mapped all realistic combinations across 4 dimensions (legal structure, licensing, revenue/funding, timeline) and discovered that Lucas's existing auto-entrepreneur (NAF 7490B) is already a near-perfect vehicle.

**Key Discovery — The Auto-Entrepreneur Shortcut:**

Lucas already has an active auto-entrepreneur (since May 2024) with NAF code 7490B ("Activités spécialisées, scientifiques et techniques diverses") — a broad code that perfectly covers building a policy simulation platform. Only action needed: add "ReformLab" as nom commercial (free, 15 minutes online).

**Staged Governance Configuration:**

**Stage 1: NOW → NGI deadline (March–April 2026)**

| Dimension | Choice | Rationale |
|---|---|---|
| Legal structure | Existing auto-entrepreneur + nom commercial "ReformLab" | Already exists, NAF code fits, zero friction |
| License | AGPL v3 (switch from current Apache 2.0) | Grant-eligible, protects against proprietary forks, aligns with OpenFisca |
| Funding | NGI Zero (individual or AE), GitHub programs, free AI/cloud tiers | Highest-value, lowest-friction grants |
| Revenue | €0 — focus on building + grant applications | Don't distract with revenue yet |

**Stage 2: First grant lands (H2 2026)**

| Dimension | Choice | Rationale |
|---|---|---|
| Legal structure | Auto-entrepreneur + Open Collective for community funding | AE for grants/contracts, OCE for donations |
| License | Still AGPL | Consistent, grant-compliant |
| Funding | NGI grant + BPI Bourse French Tech (€30k) + cloud credits | Stack grants — not mutually exclusive |
| Revenue | Small consulting/training around the tool | Natural first revenue: institutions want help using it |

**Stage 3: Established product (2027–2028)**

| Dimension | Choice | Rationale |
|---|---|---|
| Legal structure | Decide based on actual traction: stay AE, or SASU, or Association, or SCIC | Real data, not speculation |
| License | AGPL core stays. Open-core with proprietary frontend only if competitive pressure materializes | "Open until proven otherwise" — reversible in one direction only |
| Funding | Sovereign Tech, ADEME, EU Digital Europe, institutional contracts | Larger grants need track record — by then you have it |
| Revenue | Grants + consulting + SaaS for institutions | Multiple streams |

**Licensing Deep Dive:**

Current Apache 2.0 license allows competitors to take the code, add a proprietary frontend, and sell it without sharing anything. AGPL closes this: anyone serving users over a network must publish their modifications. This directly addresses the "PhD + developer competitor" fear.

Key licensing decisions:
- **AGPL v3 on everything now** (engine + future frontend)
- **Retain dual-licensing right** as sole copyright holder — can offer commercial licenses to institutions that can't use copyleft (zero cost to set up, pure optionality)
- **Frontend licensing deferred by design** — frontend doesn't exist yet, decision revisited when competitive pressure is real
- **"Open until proven otherwise"** — can tighten from open to proprietary for new code, but can't easily go the other direction

**Revenue Model Exploration:**

| Segment | What they need | How they pay | What you'd offer |
|---|---|---|---|
| Researchers & Academics | Tool, reproducible methodology | Research grants, project budgets | Free tool (AGPL), paid consulting/training |
| Government administrations | Turnkey analysis, trusted results, accountability | Public procurement, consulting contracts | Hosted SaaS + maintained scenarios + support |
| International organizations | Cross-country comparisons, methodology credibility | Project-based contracts (€800-2000+/day) | Custom country configs, methodology partnerships |
| NGOs & advocacy | Policy impact arguments backed by credible simulation | Campaign/grant budgets | Ready-made scenario reports, on-demand analysis |

**Core insight:** Nobody pays for the software — everybody pays for what you do WITH the software. The tool is a credibility engine, not the product.

**Product Architecture Ideas:**

- **Freemium Funnel (Idea #8):** Free self-host (AGPL engine + API) → Free SaaS tier (limited scenarios, single user) → Paid SaaS (unlimited, teams, support, €200-500/month per institution)
- **Grant-Funded Open Core (Idea #9):** Public money funds public goods (engine), private revenue funds private value (SaaS). Clean narrative that grant-makers love.

### Technique 3: Values Archaeology

**Interactive Focus:** Excavated personal values driving the governance decision to ensure strategy alignment.

**Values Discovered:**

| Value | Evidence | Governance Implication |
|---|---|---|
| **Pragmatic impact** | "Ministries aren't using the right tools" — saw broken tooling firsthand in interviews | Product-first, not business-model-first. Build something they'll use. |
| **Learning as value** | "Doing that much for the experience" — outcome uncertainty is OK | Low-overhead structure (AE), low-risk licensing (AGPL), grant-funded exploration |
| **Autonomy** | Solo developer by choice. No co-founders, no investors, no board. | AE not SASU. Defer structural complexity. |
| **Impact > profit, but both** | "Adopt it is already great but both is the objective" | Open-core SaaS model: free for impact, paid for sustainability |
| **Honesty about uncertainty** | "See if they'll be willing to use" — not assuming success | Staged governance: don't over-commit before validation |

**Values-Strategy Alignment Test:** Every governance decision passes the values test. Nothing requires Lucas to be someone he's not, promise something he can't deliver, or optimize for a goal he doesn't have. The strategy is authentic.

**Key insight:** The strategy doesn't require choosing between impact and income — they feed each other. AGPL + open = maximizes adoption and trust (impact) = maximizes grant eligibility (sustainability) = enables the SaaS (revenue).

---

## Idea Organization and Prioritization

### Thematic Organization

**Theme 1: Licensing & Intellectual Property**

- **Idea #5 (License Mismatch):** Current Apache 2.0 doesn't protect against competitive forks. AGPL aligns with OpenFisca and closes that gap. _Novelty: The license you already have is the one that enables the exact scenario you fear._
- **Idea #10 (Dual-License Ace Card):** AGPL as default, retain dual-licensing right as sole copyright holder. Commercial license option for institutions that can't use copyleft. _Novelty: Zero-cost optionality — don't need to decide now, just don't give away the right._
- **Idea #11 (Open Until Proven Otherwise):** Ship everything AGPL now including future frontend. Tighten to open-core only if competitive pressure materializes. _Novelty: The licensing decision is reversible in one direction (open→proprietary for new code) but not the other._

**Theme 2: Organizational Structure & Legal**

- **Idea #1 (PolicyEngine Path — Staged Open Governance):** Start with existing AE, evolve later based on real data. Not choosing IS the governance model for Stage 1. _Novelty: Deferred decision-making as explicit strategy, not procrastination._
- **Idea #12 (Complete Stage 1 Configuration):** Auto-entrepreneur with nom commercial "ReformLab" + AGPL v3 + NGI application. Every decision reinforces the others. _Novelty: Coherent configuration where licensing, structure, and funding all amplify each other._

**Theme 3: Revenue & Funding Model**

- **Idea #3 (Grant Stacking as Business Model):** Grants aren't charity — they're how concentrated markets pay for public-interest tools. NGI + BPI + Sovereign Tech + Mozilla = potentially €100k+ annually. _Novelty: Reframes grants from consolation prize to primary revenue channel._
- **Idea #4 (Expert-in-Residence):** The tool is free and open. Revenue = consulting + grants. The tool is your credibility engine, not your product. _Novelty: Open-sourcing increases revenue by making you the obvious expert._
- **Idea #9 (Grant-Funded Open Core, Revenue-Funded Frontend):** Public money builds public goods, private money builds private value. _Novelty: Turns the open/proprietary split into a narrative feature, not a compromise._

**Theme 4: Product Architecture & Competitive Moat**

- **Idea #2 (AGPL Shield + Service Layer):** Code is a commons; operations are the business. Maintained data, curated scenarios, domain expertise can't be cloned. _Novelty: Separates "what's shared" (code) from "what's sold" (expertise + maintained service)._
- **Idea #7 (Engine vs. Experience Split):** Computation layers = AGPL open. Experience layer (frontend, SaaS) = the product. Clear architectural boundary. _Novelty: Open layer builds trust and unlocks grants. Proprietary layer captures value. They reinforce each other._
- **Idea #8 (Freemium Funnel):** Three tiers — Free self-host, Free SaaS (limited), Paid SaaS (full). The free tier is how policy analysts discover you. _Novelty: Bridge between "open-source for developers" and "paid product for institutions."_

### Breakthrough Insights

- **Insight #1 (Competitor Paradox):** The same market conditions that make you doubt commercial viability also make it unlikely a competitor would invest in forking your work.
- **Insight #2 (Market Framing Problem):** The market isn't small — it's concentrated. Few buyers, significant budgets, long procurement cycles. PolicyEngine's grant model isn't a compromise — it may be the natural fit.
- **Insight #3 (Open-Source Funding Flywheel):** Being open-source is the entry ticket to €100k-300k+ in grants specifically designed for projects like ReformLab.
- **Insight #4 (Auto-Entrepreneur Shortcut):** Existing AE with NAF 7490B is already the right vehicle. No new entity needed.
- **Insight #5 (License Mismatch):** Current Apache 2.0 enables the exact competitive scenario Lucas fears. AGPL resolves it.
- **Insight #6 (Values-Strategy Alignment):** Every governance decision aligns with Lucas's actual values (pragmatic impact, autonomy, sustainability). Nothing requires being someone he's not.

### Prioritization Results

**Top Priority — Do Now (This Week):**

1. **Switch license from Apache 2.0 to AGPL v3**
   - Replace LICENSE file, update file headers, update pyproject.toml
   - No obstacles — sole author, no external contributors, no dependents
   - Success metric: LICENSE file is AGPL v3, repo clearly marked

2. **Add "ReformLab" nom commercial to auto-entrepreneur**
   - Where: guichet-entreprises.fr or INPI guichet unique
   - Cost: Free. Time: 15 minutes online
   - Success metric: Official nom commercial registered

3. **Begin NGI Zero Commons Fund application**
   - Deadline: April 1, 2026 (29 days)
   - Key narrative: Open-source environmental policy simulation platform built on OpenFisca, making policy impact analysis accessible and transparent. Digital commons for democratic accountability.
   - Success metric: Application submitted before deadline

**Quick Wins — Also This Week:**

4. Set up GitHub Sponsors on ReformLab repo
5. Sign up Gemini API free tier + Mistral free experiment tier
6. Sign up Azure Founders Hub ($1k instant credits)

**Near-Term — This Month (March 2026):**

7. Apply OpenAI Researcher Access Program (March review cycle)
8. Apply OpenAI Codex Open Source Fund
9. Apply GitHub Secure Open Source Fund ($10k)
10. Check GitHub Accelerator next cohort dates ($20k)
11. Start BPI Bourse French Tech application (up to €30k)

**Deferred By Design:**

12. Frontend licensing decision — revisit when frontend code exists and competitive pressure is measurable
13. Legal structure evolution — revisit when grant revenue exceeds €30k/year or multiple streams require separation
14. SaaS pricing model — revisit when product has active users
15. Open Collective setup — revisit when community contributions are relevant

---

## Session Summary and Insights

### Key Achievements

- Entered the session with a paralyzing three-way choice (open-source vs. proprietary vs. non-profit) and exited with a clear, staged, values-aligned governance strategy
- Discovered that the existing auto-entrepreneur is already the right legal vehicle — no new entity creation needed
- Identified that current Apache 2.0 license actively undermines competitive protection — AGPL switch is urgent and easy
- Mapped €100k-300k+ in grant funding specifically accessible to open-source projects like ReformLab
- Resolved the "open-source vs. revenue" false dichotomy: open-source IS the revenue enabler in this market
- Created a concrete 3-stage governance evolution plan with clear trigger points for each decision

### Creative Facilitation Narrative

_Lucas came in carrying the weight of a seemingly impossible three-way choice — open-source the tool and risk losing control, go commercial in a tiny market, or become a non-profit for better funding. The Assumption Reversal technique revealed that these were false binaries built on untested assumptions. The Competitor Paradox (Insight #1) and the Open-Source Funding Flywheel (Insight #3) were the session's breakthrough moments — the realization that open-source doesn't compete with revenue but enables it, and that the market's concentrated nature means grants ARE the business model, not a backup plan. The Morphological Analysis then built a concrete, staged configuration. The discovery that his existing auto-entrepreneur with NAF 7490B was already the right vehicle brought visible relief — no bureaucratic hurdles to clear. Values Archaeology confirmed that every strategic decision aligned with who Lucas actually is: a pragmatic builder who saw broken tools in ministries and wants to fix them, willing to learn from the process regardless of commercial outcome, but determined to give it every chance to sustain itself._

### Session Highlights

**User Creative Strengths:** Direct, honest self-assessment. Quick to identify the real concern underneath surface-level questions. Pragmatic decision-making — once the logic was clear, decisions were fast.
**Breakthrough Moments:** The Competitor Paradox realization; discovering the Apache 2.0 vulnerability; the "Open Until Proven Otherwise" licensing strategy.
**Energy Flow:** Started anxious and stuck in binary thinking, progressively opened up as assumptions were challenged, ended with clear conviction and a concrete action plan.

---

_Session completed 2026-03-03. Generated 12 ideas, 6 key insights, and a prioritized governance action plan across 3 brainstorming techniques._
