---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments: []
workflowType: 'research'
lastStep: 6
research_type: 'market'
research_topic: 'Environmental Policy Microsimulation Platform — Commercial Viability'
research_goals: 'Business model validation, pricing strategy, cost breakdown, investor/grant pitch support'
user_name: 'Lucas'
date: '2026-02-25'
web_research_enabled: true
source_verification: true
---

# Market Research: Environmental Policy Microsimulation Platform

**Date:** 2026-02-25
**Author:** Lucas
**Research Type:** Market Research — Commercial Viability & Business Model

---

## Executive Summary

The environmental policy microsimulation space is dominated by **free, publicly-funded tools** (EUROMOD, PolicyEngine, OpenFisca). No dominant commercial player exists for the specific niche of **household-level carbon-tax and redistribution microsimulation with a user-friendly interface**. This creates a clear opportunity, but also means the market must be created rather than captured.

**Key finding:** A **hybrid model** (open-core + consulting + grants) is the most viable path. Pure SaaS is risky given that competitors are free. Pure nonprofit/grants is viable but caps your upside and makes you grant-dependent. The sweet spot is **open-source core + paid hosted platform + consulting/training + grant funding for R&D**.

**Revenue potential:** €150K–€500K/year within 2–3 years (realistic scenario). €1M+ if you land 2–3 government framework contracts.

**Total cost to launch (Year 1):** €15K–€35K if you build it yourself. €80K–€150K if you hire help.

---

## 1. Market Size & Opportunity

### Simulation Software Market (Macro)

- Global simulation software market: **$15.5B in 2026**, projected to **$28.6B by 2031** (13% CAGR)
- SaaS delivery growing faster at 13.2% CAGR — 40% of new seats sold via SaaS in 2025 (up from 28% in 2023)
- Cloud adoption lowering barriers for SMEs

> Sources: [Mordor Intelligence](https://www.mordorintelligence.com/industry-reports/simulation-software-market), [Grand View Research](https://www.grandviewresearch.com/industry-analysis/simulation-software-market)

### Addressable Market (Micro — Your Niche)

The **policy microsimulation** niche is much smaller than the general simulation market. Key buyer segments:

| Segment | Est. Size (Europe) | Willingness to Pay | Notes |
|---------|-------------------|-------------------|-------|
| **National governments** | ~30 ministries across EU | €50K–€500K/year per contract | Long procurement cycles, high ACV |
| **Think tanks & policy institutes** | ~200 in EU | €5K–€30K/year | Price-sensitive, grant-funded themselves |
| **Consulting firms** (Big 4, Deloitte, etc.) | ~50 teams | €20K–€100K/year per license | High willingness, need white-label |
| **NGOs & advocacy orgs** | ~500+ in EU | €1K–€10K/year | Often free-tier users, good for brand |
| **Universities & researchers** | ~300+ depts | €0–€5K/year | Low pay but high volume, credibility |
| **Regional/local governments** | ~100+ metro areas | €10K–€50K/year | Growing interest in carbon budgets |

**Estimated Total Addressable Market (Europe):** €50M–€150M/year for policy analysis tools broadly.
**Serviceable Addressable Market (your niche):** €5M–€15M/year for carbon-tax/redistribution microsimulation specifically.
**Realistic Year 3 target:** €150K–€500K (0.5–1% SAM capture).

---

## 2. Competitive Landscape

### Direct Competitors

| Tool | Model | Pricing | Strengths | Weaknesses |
|------|-------|---------|-----------|------------|
| **[PolicyEngine](https://policyengine.org)** | Nonprofit (501c3) | Free | Beautiful UI, US/UK focus, strong brand | Grant-dependent, no EU/France focus, no carbon-tax models |
| **[EUROMOD](https://euromod-web.jrc.ec.europa.eu/)** | EU-funded public good | Free | Gold standard for EU tax-benefit, 27 countries | Desktop-only, steep learning curve, no carbon focus |
| **[OpenFisca](https://openfisca.org)** | Open-source association | Free (3% rev-share for commercial use) | France-first, your backend, flexible | No UI, requires Python skills, small team |
| **[UKMOD](https://www.microsimulation.ac.uk/ukmod/)** | Academic public good | Free | UK-specific, good data | UK-only, academic-focused |

### Indirect Competitors

| Tool | Model | Pricing | Notes |
|------|-------|---------|-------|
| **[Rhodium Group / ClimateDeck](https://rhg.com)** | Consulting + free data tools | Consulting: $500K+/project | Premium consulting, US-focused |
| **[Budget Lab at Yale](https://budgetlab.yale.edu)** | Academic | Free research | US tax focus, no self-serve tool |
| **Big 4 consulting** (Deloitte, PwC) | Consulting | €1,000–€2,500/day | Build custom models per project |

### Key Insight: The Gap

**Nobody offers a self-serve, user-friendly, Europe-focused carbon-tax microsimulation platform.** PolicyEngine is closest but focused on US/UK income tax, not environmental policy. EUROMOD covers EU but is a desktop tool for experts. Rhodium is US climate but enterprise consulting only.

**Your differentiation: OpenFisca backbone + carbon-tax focus + no-code UI + France/EU first.**

---

## 3. Business Model Analysis: The Three Options

### Option A: Pure Nonprofit / Grant-Funded (PolicyEngine Model)

**How it works:** Register as nonprofit (or association loi 1901 in France), seek grants from foundations, government agencies, and EU programs.

| Pros | Cons |
|------|------|
| Easier to get initial funding (grants favor nonprofits) | Revenue capped by grant availability |
| Tax-deductible donations | Grant cycles are slow (6–18 months) |
| Credibility with governments and academia | Grant dependency = existential risk |
| PolicyEngine proven model | Can't attract equity investors |
| Open-source community building | Limited ability to hire/scale |

**PolicyEngine's funding:** Arnold Ventures, Nuffield Foundation, NEO Philanthropy, Gerald Huff Fund for Humanity, PSL Foundation. Fiscally sponsored by PSL Foundation. Team of ~5 + 60 volunteers.

**Revenue potential:** €100K–€300K/year in grants (realistically for a small org).

> Sources: [PSL Blog — Year in Review](https://blog.pslmodels.org/posts/2023-12-28-2023-year-in-review.html), [FFWD — PolicyEngine](https://www.ffwd.org/tech-nonprofits/s/policyengine/)

### Option B: Pure Commercial SaaS

**How it works:** Build a SaaS platform, charge subscriptions.

| Pros | Cons |
|------|------|
| Scalable revenue | Competing with free tools (EUROMOD, PolicyEngine) |
| Attractive to investors | Government procurement is slow and complex |
| Clear unit economics | High customer acquisition cost for niche market |
| Can hire and grow | Need to prove value over free alternatives |

**Pricing benchmarks (GovTech SaaS):**
- 82% of public agencies prefer fixed, multi-year pricing
- Typical GovTech SaaS ACV: €10K–€250K/year
- Net retention target: 110–120%

> Source: [Monetizely — GovTech SaaS Pricing](https://www.getmonetizely.com/articles/how-to-price-your-saas-product-for-government-clients-comprehensive-research-guide)

### Option C: Hybrid — Open-Core + Consulting + Grants (RECOMMENDED)

**How it works:** Open-source core (builds credibility and community), hosted SaaS (recurring revenue), consulting/training (high-margin services), grants for R&D.

| Revenue Stream | Year 1 | Year 2 | Year 3 |
|---------------|--------|--------|--------|
| **Grants** (EU, ADEME, foundations) | €30K–€80K | €50K–€100K | €50K–€100K |
| **Consulting** (policy analysis projects) | €20K–€50K | €50K–€150K | €100K–€200K |
| **SaaS subscriptions** | €0–€5K | €10K–€30K | €30K–€100K |
| **Training & workshops** | €5K–€10K | €10K–€30K | €20K–€50K |
| **TOTAL** | **€55K–€145K** | **€120K–€310K** | **€200K–€450K** |

**This is the WordPress/Automattic model:** Free open-source core → paid hosted version → premium services.

**Why this wins:**
1. Grants fund R&D without dilution
2. Open-source builds trust with government buyers
3. Consulting generates revenue immediately (no product-market fit needed)
4. SaaS scales over time as the product matures
5. You can register as a société (SAS) and still receive grants

---

## 4. Pricing Strategy

### SaaS Tiers

| Tier | Price | Target | Features |
|------|-------|--------|----------|
| **Free / Community** | €0 | Researchers, students, advocates | Open-source self-hosted, basic scenarios, public data |
| **Pro** | €49–€99/mo | Think tanks, small NGOs, journalists | Hosted platform, saved scenarios, export, basic support |
| **Team** | €199–€499/mo | Policy institutes, consultancies | Multi-user, custom data upload, API access, priority support |
| **Enterprise / Government** | €1,000–€5,000/mo (annual contract) | Ministries, large consultancies | White-label, custom models, SLA, dedicated support, on-prem option |

### Consulting Rates

| Service | Rate | Notes |
|---------|------|-------|
| **Policy impact analysis** (project-based) | €5K–€30K per project | Custom scenario modeling and report |
| **Platform customization** | €1K–€3K/day | Custom data integration, model configuration |
| **Training workshops** | €500–€1,500/half-day | For government teams, think tanks |
| **Ongoing advisory** | €2K–€5K/mo retainer | For regular policy simulation needs |

### Comparison: Big 4 Consulting

Big 4 firms charge **€1,000–€2,500/day** for policy analysis consulting. A custom microsimulation project typically runs **€50K–€200K**. Your platform can undercut this dramatically while delivering faster, more transparent results.

---

## 5. Cost Breakdown

### Year 1 Costs (Solo Developer — You Build It)

| Category | Monthly | Annual | Notes |
|----------|---------|--------|-------|
| **Infrastructure** | | | |
| Hosting (Vercel/Railway + Supabase) | €20–€100 | €240–€1,200 | Free tiers available at start |
| Domain + DNS | €2 | €24 | |
| **AI/Model Costs** | | | |
| Claude API (Sonnet 4.6 for AI features) | €50–€200 | €600–€2,400 | $3/$15 per M tokens; ~100 users doing 10 queries/day |
| Alternative: OpenAI GPT-4o Mini | €20–€80 | €240–€960 | Cheaper for simple tasks |
| **Software & Services** | | | |
| GitHub (free for open-source) | €0 | €0 | |
| Analytics (PostHog free tier) | €0 | €0 | |
| Email (Resend/Postmark) | €0–€20 | €0–€240 | |
| Error tracking (Sentry free tier) | €0 | €0 | |
| **Marketing** | | | |
| Marketing website (part of app) | €0 | €0 | Build it yourself with Next.js |
| Content/SEO (your time) | €0 cash | €0 cash | Major time investment |
| Conference attendance (1–2) | — | €500–€2,000 | Microsimulation conferences, GovTech events |
| **Legal & Admin** | | | |
| Company registration (SAS in France) | — | €500–€1,000 | One-time |
| Accounting (micro-enterprise or SAS) | €50–€150 | €600–€1,800 | |
| **OpenFisca Membership** | | | |
| 3% of OpenFisca-related revenue | Variable | Variable | Per OpenFisca Association rules |
| | | | |
| **TOTAL (Year 1, Solo)** | **€150–€550** | **€2,700–€9,600** | Cash costs only, excluding your time |

### Year 1 Costs (If Hiring Help)

| Category | Cost | Notes |
|----------|------|-------|
| Freelance frontend dev (3 months) | €15K–€30K | For polished no-code UI |
| Freelance designer (1 month) | €3K–€8K | Brand, marketing site, product design |
| Total with contractors | **€20K–€40K** | On top of solo costs |

### Scaling Costs (Year 2–3, Growing Usage)

| Category | Monthly at 500 users | Monthly at 2,000 users |
|----------|---------------------|----------------------|
| Hosting | €100–€300 | €500–€1,500 |
| AI API costs | €200–€500 | €800–€2,000 |
| Database | €50–€100 | €200–€500 |
| Support tools | €50–€100 | €100–€300 |
| **Total infra** | **€400–€1,000** | **€1,600–€4,300** |

### Key Insight: Margins

At **€99/mo Pro tier** with 100 paying users = **€9,900/mo revenue** vs ~€1,000/mo costs = **~90% gross margin**. SaaS economics are excellent once you have paying users. The challenge is getting there.

---

## 6. Funding & Grant Opportunities

### EU Grants (Active 2026)

| Program | Amount | Fit | Deadline |
|---------|--------|-----|----------|
| **[Horizon Europe 2026–2027](https://research-and-innovation.ec.europa.eu/funding/funding-opportunities/funding-programmes-and-open-calls/horizon-europe_en)** | €14B total, €4.9B for climate | High — climate + digital innovation | Various 2026 |
| **[EU Innovation Fund](https://climate.ec.europa.eu/eu-action/eu-funding-climate-action/innovation-fund_en)** | €5B+ in 2025–2026 | Medium — min €2.5M investment threshold (may be too large) | Apr 2026 |
| **Horizon Europe — Digital, Industry & Space** | €307.3M for AI + digital | High — AI-powered policy tools | 2026 |
| **[EU GovTech Collection](https://interoperable-europe.ec.europa.eu/collection/eugovtech/news/startups-corner-digest-february-2026)** | Visibility + matchmaking | High — GovTech startup dashboard | Ongoing |

### French National Grants

| Program | Amount | Fit | Notes |
|---------|--------|-----|-------|
| **[ADEME](https://www.ademe.fr/en/our-missions/funding/)** | Variable | High — ecological transition digital tools | Funds R&D through industrialization |
| **France 2030** | Variable | Medium — decarbonization, digital | Competitive, larger companies favored |
| **BPI France (innovation grants)** | €30K–€500K | High — innovation aid for startups | Bourse French Tech, aide à l'innovation |
| **Région grants** (Île-de-France, etc.) | €10K–€50K | Medium | Depends on your region |

### Philanthropic / Foundation Grants

| Funder | Notes |
|--------|-------|
| **Arnold Ventures** | Funds PolicyEngine, interested in policy simulation tools |
| **Nuffield Foundation** | UK-based, funds social policy research tools |
| **Open Philanthropy** | Funds effective policy research tools |
| **Mozilla Foundation** | Funds open-source internet health projects |
| **NLNet Foundation** | Funds open-source internet projects in Europe |
| **Prototype Fund** (Germany) | Funds open-source civic tech |

### Investor Profile (If Seeking Equity)

- **Pre-seed / Angel:** €50K–€200K for 5–15% equity. Look for GovTech/climate-focused angels.
- **Seed:** €500K–€1.5M (need traction first — 10+ paying customers, €50K+ ARR)
- **Relevant VCs:** 2050 (climate), Pale Blue Dot, Demeter, Breega, Kima (French early-stage)

---

## 7. Strategic Recommendation

### The Recommended Path: "Open-Core GovTech" Hybrid

**Phase 1 (Months 1–6): Build + First Revenue**
- Build the open-source platform (you're already doing this)
- Launch marketing site + hosted free tier
- Start 1–2 consulting projects (€5K–€20K each) to fund development
- Apply for BPI France innovation aid + ADEME

**Phase 2 (Months 6–12): Traction + Grants**
- Launch Pro tier (€49–€99/mo)
- Target 5–10 paying think tanks / NGOs
- Apply for Horizon Europe consortium (partner with a university)
- Submit to EU GovTech startup dashboard
- Present at International Microsimulation Association conference

**Phase 3 (Year 2): Scale**
- Launch Enterprise tier, target 1–2 government contracts
- Hire first employee (with grant or revenue funding)
- Target €120K–€300K total revenue

### Why NOT Pure Nonprofit

PolicyEngine's model works but has serious constraints:
1. **Grant dependency** — if Arnold Ventures stops funding, they're in trouble
2. **Can't attract equity investment** — limits growth
3. **Harder to hire** — can't offer competitive salaries or equity
4. **You're in France** — the SAS structure with mixed revenue (commercial + grants) is well-supported by BPI France and ADEME. The French ecosystem supports this hybrid better than the US nonprofit model.

### Why NOT Pure SaaS (Yet)

1. Competitors are free — you need the open-source credibility first
2. Government procurement takes 6–18 months — you need bridge revenue
3. The niche is too small for pure venture-backed SaaS (VCs want billion-dollar markets)

### The Sweet Spot

**Register a SAS (simplified joint-stock company), keep the core open-source, sell hosted + consulting + training.** This lets you:
- Receive grants (BPI, ADEME, Horizon Europe)
- Take consulting revenue immediately
- Build toward SaaS recurring revenue
- Optionally raise angel/pre-seed later if needed
- Maintain credibility with government and academic buyers

---

## 8. Key Metrics for Investor/Grant Pitch

| Metric | Target (Year 1) | Target (Year 3) |
|--------|-----------------|-----------------|
| Monthly Active Users (free) | 100–500 | 2,000–5,000 |
| Paying customers | 5–15 | 50–100 |
| ARR (annual recurring revenue) | €10K–€50K | €100K–€300K |
| Total revenue (incl. consulting) | €55K–€145K | €200K–€450K |
| Gross margin (SaaS) | 85–90% | 85–90% |
| CAC (customer acquisition cost) | < €500 | < €1,000 |
| LTV (lifetime value, Pro tier) | €1,200–€2,400 | €2,400–€4,800 |
| LTV:CAC ratio | > 3:1 | > 5:1 |

---

## 9. Sources & References

- [Mordor Intelligence — Simulation Software Market](https://www.mordorintelligence.com/industry-reports/simulation-software-market)
- [Grand View Research — Simulation Software](https://www.grandviewresearch.com/industry-analysis/simulation-software-market)
- [PolicyEngine](https://policyengine.org) | [PSL Blog](https://blog.pslmodels.org/posts/2023-12-28-2023-year-in-review.html) | [FFWD Profile](https://www.ffwd.org/tech-nonprofits/s/policyengine/)
- [EUROMOD](https://euromod-web.jrc.ec.europa.eu/) | [Centre for Microsimulation](https://www.microsimulation.ac.uk/)
- [OpenFisca Association](https://openfisca.org/en/association/) | [OpenFisca Open Collective](https://opencollective.com/openfisca)
- [Rhodium Group — ClimateDeck](https://rhg.com/impact/climate-service/)
- [Budget Lab at Yale — Tax Microsimulation](https://budgetlab.yale.edu/research/tax-microsimulation-budget-lab)
- [Monetizely — GovTech SaaS Pricing](https://www.getmonetizely.com/articles/how-to-price-your-saas-product-for-government-clients-comprehensive-research-guide)
- [GovTech.com — SaaS Metrics](https://www.govtech.com/5-saas-metrics-that-really-matter-for-gov-tech-companies)
- [Horizon Europe 2026–2027](https://research-and-innovation.ec.europa.eu/funding/funding-opportunities/funding-programmes-and-open-calls/horizon-europe_en) | [€4.9B Climate](https://climate.ec.europa.eu/news-other-reads/news/commission-adopts-main-horizon-europe-work-programme-2026-2027-and-dedicates-eu49-billion-climate-2025-12-11_en)
- [EU Innovation Fund](https://climate.ec.europa.eu/eu-action/eu-funding-climate-action/innovation-fund_en)
- [ADEME Funding](https://www.ademe.fr/en/our-missions/funding/)
- [EU GovTech Startups Dashboard](https://interoperable-europe.ec.europa.eu/collection/eugovtech/news/startups-corner-digest-february-2026)
- [Anthropic Claude Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [Vercel Pricing](https://vercel.com/pricing) | [Supabase Pricing](https://supabase.com/pricing)
- [Open-Core Business Model — Wikipedia](https://en.wikipedia.org/wiki/Open-core_model)

---

**Research Status**: Complete
**Confidence Level**: Medium-High (market sizing is estimated; pricing benchmarks are well-sourced; cost breakdown is verified)
**Next Steps**: Use this research to build investor pitch deck and grant applications
