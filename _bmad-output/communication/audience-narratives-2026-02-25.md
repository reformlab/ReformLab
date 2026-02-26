# Audience Narratives and Story Pack

**Created:** 2026-02-25
**Storyteller:** Master Storyteller Sophia (with contributions from Victor, John, Sally in Party Mode)
**Author:** Lucas

## Story Information

**Story Type:** Multi-audience adaptive narratives

**Frameworks Used:**
- **Expert/Institutional:** Vision Narrative -- bold future your platform enables
- **General Public:** Pixar Story Spine / Challenge-Overcome -- simple, emotional, relatable
- **Investors:** Pitch Narrative -- problem, solution, proof, opportunity, call to action

**Purpose:** Tell the story of a microsimulation platform across multiple audiences -- what it is, why it matters, and why it's different

**Target Audiences:**
1. **Expert/Institutional** -- Government authorities, policy analysts, and researchers who understand microsimulation and policy assessment
2. **General Public** -- Family, friends, people with no technical background
3. **Investors** -- People evaluating the market opportunity and potential

**Key Messages:**
- No-code platform with a clear GUI, like PolicyEngine, but fully customizable
- Built on OpenData (which is notoriously hard for people to connect and use without privileged access)
- France and Europe-focused
- Makes the real impact of policies on real people visible and understandable

## Story Structure

### Opening Hook

**Terminology note:** Avoid "microsimulation" in public/investor versions. Use "policy impact modeling" or describe concretely. Keep "microsimulation" for expert audience only where appropriate.

**Family / Public:**
> Every year, governments create policies that affect millions of people -- energy subsidies, electric vehicle programs, housing benefits. And most of the time, nobody actually checks who those policies help and who they hurt. Are they well-targeted? Do they reach the right people? Often, nobody knows -- because they rely on legacy tools or have to call researchers who take months to deliver. So the analysis just doesn't happen, and policies end up poorly targeted.

**Expert / Institutional:**
> The people who need policy impact modeling the most -- the ones actually designing environmental subsidies, social programs, public transfers -- can't run the analysis themselves. They depend on fragmented data pipelines, legacy tools, and researcher availability. Meanwhile, publicly available data exists but remains practically inaccessible. What if there was an end-to-end platform that connected open data to policy models and put that power directly in their hands?

**Investor:**
> In Europe, every government needs to assess policy impact -- who benefits, who loses, whether the targeting actually works. The tooling for this barely exists. There's Excel, fragmented public data that's hard to connect, and researchers working without software engineering practices. PolicyEngine proved the model in the US and UK. In continental Europe -- starting with France and its rich open data ecosystem -- there's nothing. Same need, same public data infrastructure, zero product. That's the gap.

### Core Narrative

---

#### Family / Public Version

Every year, governments create policies that affect millions of people -- energy subsidies, electric vehicle programs, housing benefits. And checking who those policies actually help and who they hurt is difficult, time-consuming, and technically challenging. Are they well-targeted? Do they reach the right people? Often, it's hard to tell.

Take a concrete example. France recently launched a social leasing program for electric vehicles -- subsidized leases so lower-income households could afford EVs. The people designing this policy understand it deeply. But when they need to check who actually qualifies, which income brackets benefit the most, whether the money reaches the people who need it -- that's where it gets complicated. Answering that question means downloading massive public datasets, cleaning them, joining them together, running calculations. The data is publicly available, but it's scattered, heavy, and requires technical skills that aren't part of their job. They're policy experts, not data engineers. So they either ask a research team and wait months, or they work with what they have -- usually Excel -- and end up with results they're not fully confident about. Sometimes they just move forward without checking.

That's what I'm building: a web platform where someone in government can open a browser, pick a policy, select the data they need, and get a clear report -- with figures, an executive summary, who wins, who loses, broken down however they need. No coding. No waiting.

For those who want to go deeper, there's an advanced mode where they can test different versions of a policy side by side, or even optimize the targeting -- asking: "Given this budget, what's the best way to distribute it?"

The idea isn't to replace anyone. It's to give capable people the right tool. Sometimes that's the difference between a well-targeted policy and one that misses. And sometimes it's the difference between doing the analysis and just moving on without it.

It's possible now because France and Europe have invested heavily in open public data -- the information is there, it's just hard to use. And AI has changed what a small team can build.

It's not going to change the world overnight. But the next time someone asks "who does this policy actually help?" -- they'll be able to answer.

---

#### Expert / Institutional Version

The people who need policy impact modeling the most -- the ones actually designing environmental subsidies, social programs, public transfers -- can't easily run the analysis themselves. They depend on fragmented data pipelines, legacy tools, and researcher availability. Meanwhile, publicly available data exists but remains practically inaccessible. What if there was an end-to-end platform that connected open data to policy models and put that power directly in their hands?

You know the current workflow. Someone in the administration needs to assess the distributional impact of a new energy renovation subsidy or a social EV leasing program. The options: reach out to a research team -- conventions, budget transfers, months of lead time. Hire a consulting firm -- expensive, and you're dependent on their timeline and methodology. Ask the internal policy evaluation department -- if one exists, it's likely backlogged. Coordinate with another ministry that may have done similar work -- which creates its own coordination overhead and political friction. Or try it yourself: raw open data files too large for Excel, jointures across datasets that don't share identifiers cleanly, interpolation, synthetic population generation, reweighting -- all built in R, VBA, Matlab, or other not perfectly targeted programming languages, without software engineering best practices. Competent people, producing valuable work, but trapped in tooling that doesn't scale and isn't reproducible.

We're building a platform that handles the full pipeline: data ingestion from European and French open data sources, population synthesis, microsimulation modeling built on proven engines, and clear output -- executive summaries, distributional charts, targeting analysis. No coding required. A policy analyst can select their data sources, define or modify a policy, and get results they can trust.

But the real shift is in the advanced capabilities. Multi-scenario comparison: test three versions of a subsidy side by side. Optimization: given a fixed budget envelope, what targeting would maximize impact for a given population? These are questions that currently require dedicated research projects or expensive consulting engagements. We're making them routine.

The platform is fully customizable -- you can bring your own policy models, connect additional data sources, adapt it to your specific institutional context. It's built on open data and open modeling standards, starting with France and designed for European expansion.

This isn't about replacing researchers, evaluation departments, or existing expertise. It's about giving the people closest to policy design the autonomy to iterate, test, and validate -- without waiting for someone else to run the numbers, without the coordination costs. The expertise stays with you. The tooling finally catches up.

---

#### Investor Version

In Europe, every government needs to assess policy impact -- who benefits, who loses, whether the targeting actually works. The tooling for this barely exists. There's Excel, fragmented public data that's hard to connect, and researchers working in R, VBA, Matlab -- without software engineering best practices. PolicyEngine proved the model in the US and UK. In continental Europe -- starting with France and its rich open data ecosystem -- there's nothing. Same need, same public data infrastructure, zero product. That's the gap.

Today, when a ministry needs to evaluate the distributional impact of a policy -- say, energy renovation subsidies or a social electric vehicle leasing program -- their options are slow and expensive. Commission a research team: months of lead time, conventions, budget transfers. Hire a consulting firm: costly, black-box methodology. Coordinate across ministries: political friction and overhead. Or build it internally with scripts that don't scale and results that aren't reproducible. Most of the time, the analysis either takes too long to be useful or doesn't happen at all. Policies worth billions of euros get implemented with incomplete targeting assessments.

We're building a no-code platform for policy impact modeling. End-to-end: from open data ingestion and population synthesis to microsimulation and clear reporting. A policy analyst -- not a data scientist -- can select data sources, define a policy scenario, and get distributional results with executive summaries and figures. No coding, no waiting for external teams.

The product has two layers. The entry point is straightforward: clear reports, targeting analysis, who wins and who loses. That gets us in the door with any administration. The advanced layer is where retention lives: multi-scenario comparison, budget-constrained optimization, custom model integration. Once teams experience the ability to test three policy variants side by side or ask "what's the optimal targeting given this envelope?" -- they don't go back to spreadsheets.

Why now? Two converging forces. First, France and the EU have invested heavily in open public data -- the raw material exists but lacks tooling. Second, AI has fundamentally changed what a small team can build. The kind of platform that would have required a full engineering department can now be built by a domain expert with the right technical skills and AI-assisted development.

The competitive landscape is effectively empty in continental Europe. PolicyEngine operates in the US/UK. Research labs build custom tools that aren't productized. Consulting firms charge for bespoke analyses. Nobody is building a scalable, self-service product for the people who actually design policy.

This is happening. The product is being built. The market is large -- every European government, every ministry dealing with social, environmental, or fiscal policy. The question isn't whether this will be used. It's who gets there first.

### Key Story Beats

**The Pain (Status Quo):**
- Government officials need to assess policy impact but they're not data scientists -- they master Excel, not R or Python
- Finding the right OpenData source, downloading it (often too heavy for Excel), doing jointures, interpolation, synthetic data, reweighting -- it's overwhelming
- They either give up, produce shaky results they don't trust, or outsource to researchers
- Outsourcing means: meetings, conventions, money transfers, months of waiting
- Result: policies affecting millions are assessed poorly or not at all

**The Broken Ecosystem:**
- Researchers use R with no functions, no structure, no software engineering best practices
- No end-to-end solution exists that targets the actual decision-makers (authorities)
- OpenFisca exists as a great academic engine, but there's no user-friendly software layer on top

**The Insight:**
- Build an end-to-end platform on top of OpenFisca, targeting non-technical users in government
- No-code, clear GUI, fully customizable, powered by OpenData

**The Transformation:**
- A government official can assess a policy themselves, directly
- They select the data they want, the policies they want to model, and get results
- Speed matters: sometimes the difference between "we assessed it" and "we didn't bother"

**Concrete Examples:**
- Energy renovation subsidies: Who benefits? Who loses? Which income brackets are affected?
- Social electric vehicle leasing policy: Who are the winners and losers? What's the real targeting?
- Today: build from scratch, ask operators or researchers, wait. With the platform: select, model, get results.

### Emotional Arc

**Tone Philosophy:** Pragmatic optimism. Don't oversell. Don't claim to save the world. Claim to make one specific thing work better. The bigger picture (better policies, distributive justice, informed voting) is a *consequence*, not a pitch.

**Family Arc:**
- Start: Curiosity + "I don't really get what you do"
- Middle: "Oh, that makes sense -- so right now they just... can't check?"
- End: "That's actually clever. I get why you're building this." (Pride, not awe)

**Expert Arc:**
- Start: Frustration + enthusiasm about building their own tools (even if messy)
- Middle: "Wait -- this handles the data pipeline AND the modeling?" + discovery of what AI makes possible
- End: Excitement about using it, contributing to it, being part of something that works

**Investor Arc (for later):**
- Start: "Interesting space, but is there a real product?"
- Middle: "One developer, AI-enabled, already building -- and nobody else serves this customer in Europe"
- End: Quiet urgency. "This is happening. It's going to be used. You can be part of it."

**Emotional Low Point:** Not dramatic -- mundane. Most policy assessments simply don't happen. Nobody screams about it. The analysis just doesn't get done, and nobody notices.

**Emotional High Point:** Not revolutionary -- practical. Someone does their job better. A policy gets assessed that wouldn't have been. That's enough. That's real.

**What this is NOT:** A world-changing manifesto. It's a tool that helps people do their jobs. Better policies are a consequence, not a promise.

### Resolution/Call to Action

**For experts/collaborators:** "I'd love to show you what we're building and get your feedback. If this resonates with challenges you've seen, let's talk."

**For potential customers (administration contacts):** "We're building this with real use cases in mind. If your team has ever struggled with policy impact assessment tooling, I'd like to understand your workflow and show you what's possible."

**For investors (later):** "This is happening. The question is who moves first in continental Europe."

## Story Elements Analysis

### Character/Voice

- **Expert version:** Peer-to-peer, technically credible, visionary. "You know this problem. Here's what's finally possible."
- **Public version:** Personal, warm, concrete. Lucas explaining to family why this matters. "Let me show you what I'm building and why."
- **Investor version:** Confident, opportunity-focused, backed by evidence. "Here's a gap no one has filled in Europe."

### Conflict/Tension

- The people who need to assess policies (government officials) don't have the tools to do it
- The tools that exist (R scripts, Excel) are not built for them
- The data is open but practically inaccessible -- too heavy, too fragmented, requiring skills they don't have
- The alternative (outsourcing to researchers) is slow, expensive, and creates dependency
- The ultimate tension: policies affecting millions of lives go unassessed because the tooling gap is too wide

### Transformation/Change

- FROM: "We need to ask someone else, wait months, spend budget on conventions, and hope we get an answer"
- TO: "We select the data, choose the policy, and see the results ourselves"
- The official becomes autonomous -- they can iterate, explore scenarios, and make evidence-based decisions directly
- Speed unlocks action: assessments that were "not worth the effort" become routine

### Emotional Touchpoints

- **The absurdity moment:** "You know what stands between a government official and knowing who a policy helps? Excel."
- **The systems failure:** Brilliant researchers who've published papers, trapped in tools with no functions, no structure -- not their failure, a systems failure
- **The "why now" moment:** AI changed the math -- one developer with domain expertise can build what used to need an entire team
- **The clarity moment (product climax):** Official opens the web app, selects a policy, clicks run -- clean executive summary with figures appears. The fog lifts. "I can see it now."
- **The power moment (advanced climax):** They're not just reading results -- they're testing multiple simulations, running optimizations, asking "what would the *best* targeting look like?"
- **The trust moment:** Clean design, no clutter, figures that tell the story visually before they read a word

### Key Messages

- **Core:** The people who make decisions about millions of lives don't have the tools to assess their own policies
- **Differentiator:** No-code, clear GUI, fully customizable, built on OpenData, France/Europe-focused
- **Why now:** AI enables one person with domain expertise to build what previously required a full team
- **Two-act product:** Simple mode (clear reports, exec summaries) + Advanced mode (multi-simulation, optimization)
- **Land-and-expand:** Simple reports get you in the door; optimization mode creates lock-in

### Party Mode Insights

**Story Map (from John/PM):**

| | Opening | Middle | Climax |
|---|---|---|---|
| **Family** | "You know how the government makes policies? They can't actually check who they help." | "Excel, months of waiting, or giving up entirely" | "Now: open a web app, pick the policy, get a clear report in minutes" |
| **Expert** | "You know the R scripts. You know the data nightmares." | "No end-to-end tool exists for the actual decision-makers" | "Simple mode for reports + advanced mode for multi-simulation optimization" |
| **Investor** | "European public policy has no tooling for decision-makers" | "AI enables one developer to build what used to need a team" | "Land-and-expand: simple reports get you in, optimization mode locks them in" |

**Victor's Investor Framing:** Classic disruption -- incumbents (research labs, consultancies) serve the wrong customer. You're serving a customer nobody is serving. Blue ocean.

**Sophia's Public Story Opener:** Don't start with "microsimulation platform." Start with: "Imagine someone in the government wants to know if a new policy will help poor families or rich ones. You know what they have? Excel."

## Variations AND Adaptations

### Short Version (Email subject line / opener)

**For expert collaborators:**
> I'm building an end-to-end policy impact modeling platform for European administrations -- no code, built on open data. I think you'd find it interesting. Can I show you?

**For potential customers:**
> We're developing a tool that lets policy teams assess distributional impact directly -- no external researchers, no months of waiting. Would you have 20 minutes to see a demo and share your perspective?

### Medium Version (Email body)

**For expert collaborators / researchers:**

> Hi [Name],
>
> I hope you're doing well. I wanted to reach out because I'm building something I think connects to challenges you know well.
>
> You know how difficult it is for administrations to assess the distributional impact of policies -- energy subsidies, social programs, fiscal reforms. The data is publicly available, but connecting it, cleaning it, running models on it requires technical skills most policy teams don't have. They either outsource to researchers (months of lead time), hire consultants (expensive, black-box), coordinate across ministries (overhead), or try it themselves in Excel or ad hoc scripts.
>
> I'm building an end-to-end platform that handles the full pipeline: open data ingestion, population synthesis, microsimulation, and clear reporting -- executive summaries, distributional charts, targeting analysis. No coding required. A policy analyst can select their data, define a scenario, and get results they can trust. There's also an advanced mode for multi-scenario comparison and budget-constrained optimization.
>
> It's built on proven modeling engines, starting with France and designed for European expansion. The platform is fully customizable -- teams can bring their own models and data sources.
>
> I'd love to show you where things stand and get your perspective. Would you have time for a short call or demo in the coming weeks?
>
> Best,
> Lucas

**For potential customers (administration contacts):**

> Hi [Name],
>
> I hope you're well. I'm reaching out because I'm working on something that I believe could help teams like yours.
>
> Assessing the real impact of policies -- who benefits, who loses, whether the targeting works -- is difficult and time-consuming. The data exists publicly, but it's scattered, heavy, and hard to use without specialized technical skills. Most teams either rely on external researchers or consulting firms, or work with limited tools that don't give the full picture.
>
> I'm developing a web platform where policy teams can do this themselves: select the data they need, pick a policy scenario, and get a clear report with figures and an executive summary. No coding, no waiting for external teams. For more advanced needs, there's a mode for comparing multiple scenarios side by side or optimizing targeting given budget constraints.
>
> We're starting with France and French open data, with European expansion planned.
>
> I'd really value your perspective on this -- both to understand your current workflow better and to show you what we're building. Would you have 20 minutes for a call?
>
> Best,
> Lucas

### Ready-to-send emails (French, familiar tone)

See separate deliverable: **email-outreach-french-2026-02-25.md**

- Email 1: Expert collaborators / researchers
- Email 2: Administration contacts / future customers
- Includes adaptation notes and alternative subject lines

### Extended Version (Full narratives)

See Core Narrative section above -- the three audience-specific stories serve as extended versions for articles, presentations, and grant applications when needed.

## Usage Guidelines

### Best Channels (current focus)

- **Direct email** to known collaborators and potential customers -- personalized, referencing shared context
- **Casual conversation** with family/friends using the public version as a mental script

### Audience Considerations

- **Expert collaborators:** They know the domain. Don't over-explain the problem -- spend more time on the solution and what makes it different. Ask for their input; they'll engage more as co-creators than as an audience.
- **Potential customers (administration):** They may not think of themselves as "underserved." Frame it as making their existing work easier, not as fixing something broken. Respect their competence.
- **Tone across all:** Pragmatic, not grandiose. "This helps" not "this changes everything."

### Tone AND Voice Notes

- First person (Lucas speaking) for all email versions
- Warm but professional -- you know these people or have a connection
- No jargon in public version; technical terms welcome in expert version
- Avoid "microsimulation" in subject lines and openers -- use "policy impact modeling" or describe concretely
- Never give time estimates for delivery or development

### Adaptation Suggestions

- When emailing someone specific, reference a concrete policy or challenge relevant to their work
- For French-speaking contacts, these stories should be translated/adapted to French (future task)
- LinkedIn versions, conference slides, grant narratives, and website copy can be derived from the extended versions when needed

## Next Steps

### Refinement Opportunities

- Test the email versions with 2-3 contacts and note which phrases generate the most engagement
- The opening hooks could be A/B tested (the "absurdity" angle vs. the "nuanced/challenging" angle)
- The investor version needs refinement once market sizing data is available
- French-language adaptations for French contacts

### Additional Versions Needed (future)

- LinkedIn post versions (short, punchy, with a hook)
- Conference presentation narrative (5-minute pitch structure)
- Grant application narrative (academic framing)
- Website landing page copy
- French-language versions of all stories

### Testing/Feedback Plan

- Send expert email to 2-3 trusted collaborators first -- note their reactions and questions
- Send customer email to 1-2 administration contacts you know best -- see if they take the call
- Use family conversations as a litmus test: if they can explain it back to you, the public version works
- Iterate based on what questions people ask -- those gaps become the next version's improvements

---

_Story crafted using the BMAD CIS storytelling framework_
