# How It Works

**Created:** 2026-02-25
**Author:** Paige (Tech Writer) for Lucas

---

## The Pipeline

ReformLab connects four stages into a single workflow. You interact with the parts you care about; the platform handles the plumbing.

```
Open Data Sources ──→ Population Builder ──→ Policy Engine ──→ Results & Indicators
   (INSEE, Eurostat,     (synthetic          (OpenFisca +       (charts, tables,
    EU-SILC)              population)          your scenarios)     manifests)
```

---

## Stage 1: Data

### What happens

The platform ingests data from European open data sources — household surveys, income distributions, energy consumption patterns, housing stock characteristics. It harmonizes these into a consistent analytical format: same identifiers, same units, same structure.

### What you do

Pick your data sources from a catalog, or use the defaults. The platform handles downloading, cleaning, joining, and validating. Every transformation is logged.

### What you don't do

Download raw files. Write jointure scripts. Debug encoding issues. Manually document your data pipeline.

---

## Stage 2: Population

### What happens

From public marginal distributions (published tables, not restricted microdata), the platform generates a synthetic population that matches known demographic and economic characteristics. This population is the input to your simulation.

### What you do

Choose a pre-built population (e.g., "French households 2024") or configure your own: select which marginals to match, set tolerances, choose generation method.

### Technical detail

Synthetic populations are generated using established statistical methods (IPF, combinatorial optimization) from published marginals. The generation process is fully documented in the run manifest: which source tables, which matching targets, what tolerances, what deviations from targets.

---

## Stage 3: Policy Simulation

### What happens

OpenFisca computes tax-benefit calculations for each household in the population. Your policy scenarios — defined as templates with parameter overrides — layer environmental policy logic on top: carbon tax rates, subsidy eligibility, redistribution formulas.

For multi-year projections, the dynamic orchestrator runs this computation year by year, updating household state between periods: income changes, asset aging, vintage transitions.

### What you do

**In the GUI:** Pick a template, adjust parameters, click Run.

**In code:**

```python
scenario = Scenario.from_template("carbon_tax", tax_rate=100)
results = run(scenario, population, years=range(2025, 2035))
```

### Architecture note

OpenFisca handles what it's good at: encoding tax-benefit legislation and computing individual/household-level effects. ReformLab handles everything above that: data preparation, scenario management, multi-year orchestration, vintage tracking, and output formatting.

```
┌──────────────────────────────────────────┐
│            ReformLab Platform            │
│                                          │
│  Data Layer ─→ Scenario Templates        │
│       │              │                   │
│       ▼              ▼                   │
│  Population ─→ Dynamic Orchestrator      │
│                      │                   │
│              ┌───────┴───────┐           │
│              │   OpenFisca   │           │
│              │  (per-year    │           │
│              │  computation) │           │
│              └───────────────┘           │
│                      │                   │
│              Indicators & Reports        │
│              Run Manifests               │
└──────────────────────────────────────────┘
```

---

## Stage 4: Results

### What happens

The platform computes standard indicators from simulation outputs: distributional impact by income group, welfare effects, fiscal cost, targeting efficiency. Results are formatted for both visual exploration and data export.

### What you get

- **Distributional charts** — Bar charts showing effects by income decile, region, or household type
- **Winners and losers tables** — Which groups gain, which lose, by how much
- **Fiscal summary** — Revenue, cost, net impact
- **Executive summary** — Key findings in plain language
- **Run manifest** — Complete provenance for reproducibility

### What you can do next

- Compare multiple scenarios side by side
- Sweep parameters to see sensitivity
- Drill down from any indicator to its source assumptions
- Export to CSV/Parquet for further analysis
- Share the manifest and notebook for replication

---

## The Two Modes

### Simple Mode (No-Code GUI)

For policy analysts who need fast answers:

1. Open the platform
2. Pick a pre-configured template and population
3. Adjust parameters if needed
4. Click Run
5. Read charts, tables, executive summary

**Best for:** Routine assessments, director briefings, quick comparisons.

### Advanced Mode (Python API + Notebooks)

For researchers who need full control:

1. Import the library in Jupyter
2. Configure population, scenarios, and orchestration programmatically
3. Run simulations with custom parameters
4. Access results as DataFrames
5. Export manifests for replication packages

**Best for:** Academic publications, custom analysis, pipeline integration.

**Both modes use the same engine.** A scenario configured in the GUI can be exported as a notebook. Code-based configurations can be loaded into the GUI. No separate systems, no translation layer.

---

_Technical documentation based on PRD architecture and UX design specification._
