---
stepsCompleted: [1]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'market'
research_topic: 'PolicyEngine competitive gap analysis for ReformLab'
research_goals: 'Identify important missing features in ReformLab by analyzing PolicyEngine capabilities'
user_name: 'Lucas'
date: '2026-03-24'
web_research_enabled: true
source_verification: true
---

# Market Research: PolicyEngine Competitive Gap Analysis for ReformLab

## Research Initialization

### Research Understanding Confirmed

**Topic**: PolicyEngine competitive gap analysis — identifying important missing capabilities in ReformLab
**Goals**: Systematic comparison of PolicyEngine.org features vs. ReformLab to surface critical gaps
**Research Type**: Market / Competitive Analysis
**Date**: 2026-03-24

### Research Scope

**Market Analysis Focus Areas:**

- Feature-by-feature capability comparison (PolicyEngine vs. ReformLab)
- User experience and accessibility gaps
- Data and methodology gaps
- API and integration gaps
- Strategic recommendations for ReformLab roadmap prioritization

**Research Methodology:**

- Direct analysis of PolicyEngine.org website, GitHub repos, and documentation
- Cross-reference with ReformLab's PRD, architecture, and current implementation status
- Gap classification by severity and strategic importance

### Next Steps

**Research Workflow:**

1. ✅ Initialization and scope setting (current step)
2. Customer Insights and Behavior Analysis
3. Competitive Landscape Analysis
4. Strategic Synthesis and Recommendations

**Research Status**: Scope confirmed, ready to proceed with detailed gap analysis

---

## Customer Behavior and Segments

### Customer Behavior Patterns

The policy microsimulation tools market spans a wide behavioral spectrum — from government agencies running real-time revenue scores during live legislative markup, to citizens checking benefit eligibility in under 2 minutes.

_Behavior Drivers: Institutional mandate (government), publication/grant pressure (academia), mission advancement (NGOs/think tanks), personal financial impact (citizens), deadline pressure (journalists)_

_Interaction Preferences: Government and academic users tolerate complex interfaces if they deliver methodological depth. Citizens and journalists demand immediate, personalized results with zero learning curve. Think tanks need customizable analysis that produces quotable, shareable outputs._

_Decision Habits: Tool adoption is path-dependent — researchers use what their advisors/peers use; government agencies build or procure long-lived models; citizens arrive via media coverage or shared links and may never return. The most successful platforms (PolicyEngine, En-ROADS) serve multiple tiers simultaneously._

_Sources: [PolicyEngine Case Study](https://www.citizencodex.com/case-studies/transforming-tax-policy-analysis-with-policyengine), [Tax Microsimulation in US Policymaking](https://www.microsimulation.pub/articles/00314), [En-ROADS Impact](https://www.nature.com/articles/s44168-026-00348-4)_

### Demographic Segmentation

**By Role:**

| Segment | Estimated Size | Engagement Pattern | Budget for Tools |
|---|---|---|---|
| Government agencies | Dozens of major entities globally | Continuous/daily | High ($100K-$10M+ contracts) |
| Think tanks | ~3,800+ globally | Campaign/project bursts | Low-Medium ($0-$50K, grant-funded) |
| Academic researchers | Hundreds of active microsim users (EUROMOD alone) | Weekly/grant-cycle | Near-zero (expect open-source) |
| Environmental/climate | 1.4M+ En-ROADS users; growing ministerial demand | Mission-driven | Foundation-funded ($5K-$50K workshops) |
| Citizens/public | Millions (event-driven spikes) | Episodic, life-event driven | Zero (must be free) |
| Journalists | Thousands on policy beats | Deadline-driven | Zero (need fast, quotable results) |
| Nonprofit advocates | Tens of thousands of organizations | Campaign-cycle aligned | Very low ($0-$5K) |

_Geographic Distribution: Strongest adoption in France (OpenFisca origin — MesAides reached 1.6M households, LexImpact used in National Assembly), UK (EUROMOD/UKMOD, PolicyEngine-UK used by HM Treasury), US (PolicyEngine-US, TPC, JCT/CBO), Australia/New Zealand (Rules as Code pilots), and across 27 EU member states via EUROMOD._

_Sources: [On Think Tanks 2025 Survey](https://onthinktanks.org/state-of-the-sector-report-2025/), [OpenFisca Digital Commons](https://labo.societenumerique.gouv.fr/en/articles/openfisca-quand-un-commun-numerique-transforme-la-loi-en-code/), [EUROMOD](https://euromod-web.jrc.ec.europa.eu/overview/what-is-euromod)_

### Psychographic Profiles

**Profile 1: The Rigorous Institutionalist (Government/Official Scoring Bodies)**
Values defensibility, nonpartisanship, and institutional continuity above all. Risk-averse with long procurement cycles. Will not adopt a tool unless it matches established official methodologies. Trust comes from track record, peer review, and ability to replicate official baselines (JCT, CBO scores).

**Profile 2: The Independent Analyst (Think Tanks/Researchers)**
Values intellectual independence, methodological flexibility, and publication potential. Early adopter of analytical tools when they enhance research capability. Skeptical of tools that constrain methodology. Open-source strongly preferred. 71% of think tanks now use AI tools (up from 57% in 2024).

**Profile 3: The Mission-Driven Advocate (NGOs/Climate Organizations)**
Values equity, accessibility, and systems thinking. Needs outputs that support storytelling and campaigns. Strong preference for distributional analysis (who wins/loses). En-ROADS demonstrates that interactive climate tools drive measurable empowerment gains (effect size r=0.286, p<0.001).

**Profile 4: The Concerned Citizen**
Values simplicity, personal relevance, and trust. Zero tolerance for complexity. Arrives via media or shared links — engagement is event-driven (elections, major policy debates). PolicyEngine found that "the complex nature of tax policy analysis and the current UI design meant many potential users couldn't intuitively access or leverage the tool's full capabilities."

_Sources: [On Think Tanks 2025](https://onthinktanks.org/state-of-the-sector-report-2025/), [npj Climate Action](https://www.nature.com/articles/s44168-026-00348-4), [PolicyEngine UX](https://www.citizencodex.com/case-studies/transforming-tax-policy-analysis-with-policyengine)_

### Customer Segment Profiles

**Segment A: French Environmental Policy Community (ReformLab's Beachhead)**
France has the strongest OpenFisca adoption globally, active carbon tax microsimulation research, and government infrastructure already in place. Researchers use Phebus survey data for fuel poverty analysis. The National Assembly's LexImpact ran 122 simulations during live debates. ADEME and SDES provide environmental datasets. This is the natural first market where ReformLab's environmental focus, French data loaders (INSEE, Eurostat, ADEME, SDES), and OpenFisca-first approach create a defensible niche.

**Segment B: EU Climate Policy Analysts**
Finance Ministers increasingly need climate-economic modeling tools (Coalition of Finance Ministers for Climate Action). EUROMOD covers 27 EU states for tax-benefit but has no environmental policy layer. The gap between fiscal microsimulation (EUROMOD) and climate system models (En-ROADS) is exactly where ReformLab sits.

**Segment C: Academic Carbon Tax Researchers**
A growing subfield with researchers producing one-off custom models. Key challenge: distributional impact estimates differ across models due to different assumptions, data sources, and metrics. ReformLab's assumption transparency and replication packages directly address this reproducibility crisis.

_Sources: [French Carbon Tax Microsimulation](https://www.sciencedirect.com/science/article/abs/pii/S0301421518306268), [Carbon Tax Distributional Meta-Analysis](https://arxiv.org/html/2601.07713), [CFMCA Report](https://www.financeministersforclimate.org/sites/default/files/2025-10/CFCMA%20HP4%20report%20-%20Overview%20of%20Economic%20Analysis%20And%20Modeling%20Tools_0.pdf)_

### Behavior Drivers and Influences

_Emotional Drivers: Climate urgency and sense of agency for environmental segment; political engagement during elections for citizens; career advancement and publication pressure for academics; institutional mandate compliance for government_

_Rational Drivers: Methodological rigor, data quality, reproducibility, cost-effectiveness, time-to-insight. Government users need "defensible numbers" — if a tool can't match official baselines, it won't be adopted. Researchers need citation-worthy methodology._

_Social Influences: Peer adoption is the strongest predictor of tool choice across all segments. Academic advisors shape student tool selection. Think tank networks share tools within coalitions. Government agencies follow precedent set by peer agencies. OpenFisca's World Government Summit award (2023, selected from 1,000+ candidates) is a powerful social proof signal._

_Economic Influences: Open-source expectation is near-universal outside government. 97% of nonprofits operate on budgets under $5M/year; tech spending averages 2.8-13.2% of budget. The environmental compliance software market (USD 3.94B in 2025, projected USD 10.59B by 2035) indicates growing commercial opportunity, but microsimulation tools specifically remain grant/foundation-funded._

_Sources: [Environmental Compliance Software Market](https://www.insightaceanalytic.com/report/environmental-compliance-software-market-/3491), [Grand View Research Nonprofit Tech](https://www.grandviewresearch.com/horizon/outlook/non-profit-organization-technology-spending-market/united-states), [OECD Rules as Code](https://oecd-opsi.org/innovations/rac-as-shared-utility/)_

### Customer Interaction Patterns

_Research and Discovery: Government agencies build internally or procure via formal RFPs. Academics discover tools through conferences (NTA, IMA World Congress, APPAM), journal citations, and advisor recommendations. Think tanks learn from peer networks. Citizens arrive through media coverage, social sharing, or campaign links. OpenFisca hackathons (e.g., modeling Senegal's income tax in 36 hours at the 2016 OGP Paris summit) drive developer awareness._

_Purchase Decision Process: For government — multi-year procurement with formal evaluation criteria. For academia — zero-cost expected; evaluation based on methodological fit, data compatibility, and community support. For think tanks — grant-budget constrained; tool must fit the funded research question. For citizens — no "purchase"; must be free, instant, and mobile-friendly._

_Post-Use Behavior: Expert users integrate tools into weekly workflows (per PolicyEngine observation). Citizen-facing tools see high volume but low retention — MesAides informed 1.6M households but many never returned. Legislative tools (LexImpact) see burst usage around debate sessions. API-powered downstream tools (MyFriendBen: 55,000+ households, $33M in benefits) create sticky, recurring usage patterns._

_Loyalty and Retention: Driven by data lock-in (built analyses depend on the tool), ecosystem effects (API integrations, downstream tools), and community membership. EUROMOD's several hundred active users represent deep institutional loyalty built over decades. PolicyEngine's shareable reform URLs create network effects — each shared analysis brings new users._

_Sources: [PolicyEngine Year in Review 2024](https://www.policyengine.org/us/research/us-year-in-review-2024), [OpenFisca About](https://openfisca.org/en/about/), [MyFriendBen](https://www.myfriendben.org/about-us/)_
