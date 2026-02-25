---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'Entity-graph data modeling and vectorized simulation engines in microsimulation'
research_goals: 'Analyze entity and relationship modeling in microsimulation, survey Python libraries, compare OpenFisca and EUROMOD approaches, and identify design patterns that reconcile graph traversal with vectorized computation.'
user_name: 'Lucas'
date: '2026-02-23'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-02-23
**Author:** Lucas
**Research Type:** technical

---

## Research Overview

[Research overview and methodology will be appended here]

## Project Strategy Interpretation Update (2026-02-24)

Technical findings in this report remain useful, but implementation scope is updated:

- OpenFisca is retained as the policy-calculation core.
- Entity-graph and vectorized-engine findings are treated as reference architecture patterns, not mandatory MVP rebuild targets.
- MVP engineering priority is adapter quality, dynamic orchestration, vintage tracking, and reproducible workflow operations.

Project implication: apply technical recommendations selectively to orchestration and data-contract layers, and avoid duplicating mature OpenFisca internals.

---

<!-- Content will be appended sequentially through research workflow steps -->

## Technical Research Scope Confirmation

**Research Topic:** Entity-graph data modeling and vectorized simulation engines in microsimulation
**Research Goals:** Analyze entity and relationship modeling in microsimulation, survey Python libraries, compare OpenFisca and EUROMOD approaches, and identify design patterns that reconcile graph traversal with vectorized computation.

**Technical Research Scope:**

- Architecture Analysis - design patterns, frameworks, system architecture
- Implementation Approaches - development methodologies, coding patterns
- Technology Stack - languages, frameworks, tools, platforms
- Integration Patterns - APIs, protocols, interoperability
- Performance Considerations - scalability, optimization, patterns

**Research Methodology:**

- Current web data with rigorous source verification
- Multi-source validation for critical technical claims
- Confidence level framework for uncertain information
- Comprehensive technical coverage with architecture-specific insights

**Scope Confirmed:** 2026-02-23

## Technology Stack Analysis

### Programming Languages

Microsimulation stacks in this area are strongly Python-centric at the modeling interface, with specialized lower-level execution components where needed.

- OpenFisca formulas are authored in Python but executed as NumPy-backed vector operations over entity arrays. This keeps policy code readable while preserving population-scale execution characteristics.
- EUROMOD exposes a Python connector with an object model (`Model` -> `Country` -> `System`) and simulation execution via pandas DataFrames, which positions Python as an orchestration and experimentation layer over the underlying EUROMOD model assets.
- EUROMOD model assets are stored as XML policy-rule files, reinforcing a separation between declarative rule encoding and runtime execution.
- For graph-heavy workloads, performance-oriented options in Python now commonly include Rust/C-backed libraries (e.g., rustworkx, igraph, GraphBLAS bindings) while preserving Python ergonomics.

_Popular Languages:_ Python dominates policy modeling and workflow automation in this domain.
_Emerging Languages:_ Rust-backed graph/data tooling is increasingly used for compute-critical sections.
_Language Evolution:_ The trend is Python-first APIs with optimized native kernels under the hood.
_Performance Characteristics:_ Python improves modeling velocity; compiled backends improve throughput for large graph/array kernels.
_Source:_ https://openfisca.org/doc/coding-the-legislation/25_vectorial_computing.html ; https://openfisca.org/doc/simulate/index.html ; https://pythonconnectoreuromod.readthedocs.io/en/latest/notebooks/getstarted.html ; https://euromod-web.jrc.ec.europa.eu/resources/glossary ; https://www.rustworkx.org/dev/ ; https://python.igraph.org/en/main/

### Development Frameworks and Libraries

The current Python ecosystem for this problem space splits into three complementary layers: policy engines, graph libraries, and columnar/vectorized compute libraries.

- **Policy engines:** OpenFisca provides entities/roles, variable formulas, period semantics, and dependency-driven calculation with caching/tracing.
- **Graph modeling/traversal libraries:** NetworkX (flexible typed graph classes and broad algorithms), rustworkx (high-performance graph data structures/algorithms), igraph (C-backed graph analytics), and GraphBLAS bindings for sparse-matrix graph execution.
- **Vectorized/columnar execution libraries:** NumPy ufunc/broadcast model for vectorized math; Apache Arrow for columnar memory layout and zero-copy interoperability; Polars lazy optimization pipeline (predicate/projection pushdown) as an increasingly relevant dataframe engine.

_Major Frameworks:_ OpenFisca, NetworkX, rustworkx, igraph, python-graphblas, NumPy, Arrow, Polars.
_Micro-frameworks:_ Specialized graph or sparse-matrix bindings (e.g., GraphBLAS wrappers) for targeted acceleration.
_Evolution Trends:_ Movement toward hybrid stacks that combine graph semantics with columnar/vectorized execution.
_Ecosystem Maturity:_ High for NumPy/NetworkX/OpenFisca core usage; medium and fast-growing for GraphBLAS-driven Python workflows.
_Source:_ https://openfisca.org/doc/architecture.html ; https://openfisca.org/doc/_modules/openfisca_core/simulations/simulation.html ; https://networkx.org/documentation/stable/reference/index.html ; https://www.rustworkx.org/dev/ ; https://python.igraph.org/en/main/ ; https://github.com/python-graphblas/python-graphblas ; https://numpy.org/doc/2.4/reference/ufuncs.html ; https://arrow.apache.org/docs/format/Columnar.html ; https://docs.pola.rs/user-guide/lazy/optimizations/

### Database and Storage Technologies

Microsimulation workloads here are primarily file- and array-oriented rather than transactional-DB-oriented.

- OpenFisca supports test-case and bulk-data workflows (including CSV-based inputs), then computes outputs in vectorized arrays.
- EUROMOD input datasets are standardized row-wise microdata (one row per individual, household identifiers, strict naming conventions) with output produced at individual or household level.
- For large workloads, storage and memory behavior matter: OpenFisca includes mechanisms for temporary on-disk storage when memory pressure occurs; Arrow defines columnar in-memory layout optimized for scans/SIMD/zero-copy movement.

_Relational Databases:_ Usually peripheral to core simulation loops; often used upstream/downstream.
_NoSQL Databases:_ Not central in source workflows; typically optional for metadata/pipeline needs.
_In-Memory Databases:_ Equivalent role often played by in-memory arrays/dataframes in simulation runtime.
_Data Warehousing:_ Common as an analytics sink, but simulation kernels remain array-centric.
_Source:_ https://openfisca.org/doc/simulate/index.html ; https://openfisca.org/doc/_modules/openfisca_core/simulations/simulation.html ; https://euromod-web.jrc.ec.europa.eu/resources/glossary ; https://arrow.apache.org/docs/format/Columnar.html

### Development Tools and Platforms

Tooling emphasizes reproducible policy modeling, traceability, and connector-based interoperability.

- OpenFisca provides both Python API and optional web API for HTTP/JSON integration into broader systems.
- OpenFisca tracing facilities expose calculation steps and dependency chains for debugging and validation.
- EUROMOD provides a software platform plus connectors (Python/Stata/R/Matlab terminology in official glossary), enabling integration with statistical and research workflows.
- EUROMOD Python connector mirrors EUROMOD hierarchy and supports model navigation, system selection, and DataFrame-based runs.

_IDE and Editors:_ Standard Python tooling ecosystem applies.
_Version Control:_ Git-based workflows are common for policy-rule repositories and experiments.
_Build Systems:_ Python packaging/virtual environments dominate.
_Testing Frameworks:_ OpenFisca documentation emphasizes simulation tests and trace-based inspection.
_Source:_ https://openfisca.org/doc/architecture.html ; https://openfisca.org/doc/simulate/analyse-simulation.html ; https://pythonconnectoreuromod.readthedocs.io/en/latest/notebooks/getstarted.html ; https://euromod-web.jrc.ec.europa.eu/resources/glossary

### Cloud Infrastructure and Deployment

For this domain, cloud concerns center on API exposure, memory locality, and scale-out processing patterns rather than pure infrastructure branding.

- OpenFisca can be exposed via web APIs for remote calls and integration into policy services.
- Arrow’s columnar format is designed for efficient inter-process/system interchange with zero-copy potential, which is useful in distributed analytics pipelines.
- Dask array chunking patterns are relevant for out-of-core and distributed array computation when population-scale runs exceed single-node memory.

_Major Cloud Providers:_ Provider-agnostic patterns dominate in sources.
_Container Technologies:_ Common in practice, though not the core focus of referenced docs.
_Serverless Platforms:_ Possible for API wrappers but less suitable for long-running heavy simulations.
_CDN and Edge Computing:_ Usually low relevance for core simulation kernels.
_Source:_ https://openfisca.org/doc/architecture.html ; https://arrow.apache.org/docs/format/Columnar.html ; https://docs.dask.org/en/latest/array-chunks.html

### Technology Adoption Trends

Observed trend: policy microsimulation is converging toward a **hybrid architecture** where semantic policy graphs and entity relations coexist with vectorized array execution.

- OpenFisca’s established vector-first formula model remains a reference approach for Python policy engines.
- EUROMOD’s continued releases and connector strategy indicate sustained investment in interoperable research workflows and model portability.
- Graph and sparse-linear-algebra ecosystems (NetworkX/rustworkx/igraph/GraphBLAS) are increasingly used to represent entity relations, dependency structures, and high-performance traversal workloads.
- Columnar/lazy execution trends (Arrow + modern dataframe engines) are tightening the loop between simulation and downstream analytics.

_Migration Patterns:_ From monolithic scalar logic to vectorized plus graph-aware modular designs.
_Emerging Technologies:_ GraphBLAS-based sparse graph computation and Arrow-native pipelines.
_Legacy Technology:_ Spreadsheet-centric or purely scalar implementations are increasingly constrained at scale.
_Community Trends:_ Strong growth in Python-native connectors, reproducibility, and open-source model assets.
_Source:_ https://openfisca.org/doc/simulate/index.html ; https://euromod-web.jrc.ec.europa.eu/download-euromod ; https://euromod-web.jrc.ec.europa.eu/resources/glossary ; https://networkx.org/documentation/stable/reference/index.html ; https://github.com/python-graphblas/python-graphblas ; https://arrow.apache.org/docs/format/Columnar.html ; https://docs.pola.rs/user-guide/lazy/optimizations/

## Integration Patterns Analysis

In this domain, the most robust interoperability pattern is a dual representation: maintain relationship semantics in a graph layer (entities, roles, dependencies), while executing formulas on index-aligned vectorized columns. The bridge is deterministic index mapping and sparse gather/scatter transforms.
_Source:_ https://openfisca.org/doc/coding-the-legislation/50_entities.html ; https://openfisca.org/doc/coding-the-legislation/25_vectorial_computing.html ; https://graphblas.org ; https://arrow.apache.org/docs/format/Columnar.html

### API Design Patterns

OpenFisca exposes API-first integration options and JSON-oriented simulation flows, which align naturally with REST request/response usage and traceable calculations. EUROMOD integration is commonly connector-driven (Python connector object model) rather than REST-first, but can be wrapped behind service interfaces when used in larger distributed systems.

_RESTful APIs:_ Best fit for external clients requesting simulation outputs by period/entity with predictable idempotent read patterns where possible.
_GraphQL APIs:_ Useful when clients require selective nested retrieval over entity graphs, but adds resolver complexity and can obscure cost unless query controls are enforced.
_RPC and gRPC:_ Effective for internal low-latency services where binary Protocol Buffers and strict interface contracts reduce payload/serialization overhead.
_Webhook Patterns:_ Useful for long-running batch simulations, with asynchronous completion notifications rather than blocking request cycles.
_Source:_ https://openfisca.org/doc/architecture.html ; https://openfisca.org/doc/openfisca-web-api/index.html ; https://pythonconnectoreuromod.readthedocs.io/en/latest/notebooks/getstarted.html ; https://spec.graphql.org/ ; https://grpc.io/docs/what-is-grpc/

### Communication Protocols

Transport/protocol choices should be split by interaction type: synchronous policy evaluation, streaming state updates, and asynchronous batch orchestration.

_HTTP/HTTPS Protocols:_ Default for interoperable synchronous simulation APIs, with broad tooling and observability support.
_WebSocket Protocols:_ Appropriate when clients need persistent channels for progressive simulation status/results.
_Message Queue Protocols:_ AMQP and MQTT are useful for decoupled job dispatch, event fanout, and resilient retry handling.
_gRPC and Protocol Buffers:_ Preferred for high-throughput internal calls and strongly typed contracts between compute services.
_Source:_ https://www.rfc-editor.org/rfc/rfc9110 ; https://www.rfc-editor.org/rfc/rfc6455 ; https://docs.oasis-open.org/amqp/core/v1.0/amqp-core-overview-v1.0.html ; https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html ; https://grpc.io/docs/what-is-grpc/ ; https://protobuf.dev/

### Data Formats and Standards

Microsimulation integration usually combines human-readable exchange formats for interoperability with compact binary formats for high-throughput service boundaries.

_JSON and XML:_ JSON dominates API payloads; XML remains important where rule systems are declarative (EUROMOD policy/model assets).
_Protobuf and MessagePack:_ Strong options for compact binary transport and reduced serialization overhead at scale.
_CSV and Flat Files:_ Still central for microdata interchange and batch ingestion in public-policy pipelines.
_Custom Data Formats:_ A practical pattern is explicit entity-index maps plus relationship adjacency/sparse structures to reconcile graph traversal and vectorized kernels.
_Source:_ https://www.rfc-editor.org/rfc/rfc8259 ; https://www.w3.org/TR/xml/ ; https://protobuf.dev/ ; https://github.com/msgpack/msgpack/blob/master/spec.md ; https://www.rfc-editor.org/rfc/rfc4180 ; https://euromod-web.jrc.ec.europa.eu/resources/glossary

### System Interoperability Approaches

Interoperability architecture should isolate model semantics from execution concerns: policy models, entity graph semantics, and vector engine runtime each evolve at different speeds.

_Point-to-Point Integration:_ Fast to implement for research workflows (e.g., notebook -> connector -> engine) but scales poorly in operational complexity.
_API Gateway Patterns:_ Useful for stable contracts, auth, routing, and version mediation across multiple simulation services.
_Service Mesh:_ Valuable for service-to-service security, traffic policy, retries, and telemetry in distributed simulation platforms.
_Enterprise Service Bus:_ Still relevant in legacy institutions integrating microsimulation engines with established enterprise middleware.
_Source:_ https://pythonconnectoreuromod.readthedocs.io/en/latest/notebooks/getstarted.html ; https://microservices.io/patterns/apigateway ; https://istio.io/latest/docs/concepts/what-is-istio/ ; https://www.enterpriseintegrationpatterns.com/

### Microservices Integration Patterns

When simulation capabilities are decomposed into services (data prep, rule evaluation, aggregation, reporting), classic resilience and consistency patterns become essential.

_API Gateway Pattern:_ Centralizes external access while hiding internal service topology and version churn.
_Service Discovery:_ Enables dynamic endpoint resolution and autoscaled worker pools in orchestration platforms.
_Circuit Breaker Pattern:_ Prevents cascading failures when dependency services degrade.
_Saga Pattern:_ Coordinates multi-step distributed operations where strict ACID transactions are not feasible.
_Source:_ https://microservices.io/patterns/apigateway ; https://kubernetes.io/docs/concepts/services-networking/service/ ; https://martinfowler.com/bliki/CircuitBreaker.html ; https://microservices.io/patterns/data/saga.html

### Event-Driven Integration

Event-driven patterns fit high-volume microsimulation pipelines where ingestion, recalculation, and publication are decoupled.

_Publish-Subscribe Patterns:_ Support independent producers/consumers for simulation triggers and downstream analytics.
_Event Sourcing:_ Useful when reproducibility/auditability requires capturing state transitions as immutable events.
_Message Broker Patterns:_ Kafka-class brokers are common for durable streaming and replay.
_CQRS Patterns:_ Separating write/recompute flows from read/reporting models can reduce contention and improve query performance.
_Source:_ https://kafka.apache.org/documentation/ ; https://www.enterpriseintegrationpatterns.com/ ; https://martinfowler.com/eaaDev/EventSourcing.html ; https://martinfowler.com/bliki/CQRS.html ; https://cloudevents.io/

### Integration Security Patterns

Because policy systems can involve sensitive household/person-level attributes, integration security architecture must be explicit and layered.

_OAuth 2.0 and JWT:_ Standard approach for delegated authorization and token-based API access.
_API Key Management:_ Suitable for service or application-level identity where scoped and rotated under strict governance.
_Mutual TLS:_ Strong service-to-service authentication for internal platform traffic.
_Data Encryption:_ TLS 1.3 (in transit) plus encrypted storage/key management for dataset at rest.
_Source:_ https://www.rfc-editor.org/rfc/rfc6749 ; https://www.rfc-editor.org/rfc/rfc7519 ; https://www.rfc-editor.org/rfc/rfc8705 ; https://www.rfc-editor.org/rfc/rfc8446 ; https://owasp.org/API-Security/editions/2023/en/0x11-t10/

## Architectural Patterns and Design

### System Architecture Patterns

For microsimulation engines with entity relationships and population-scale execution, the most robust baseline is a dual-plane architecture:

- A semantic graph plane for entities, roles, and dependency relationships.
- A vectorized execution plane for period-indexed array computation.

OpenFisca demonstrates this approach through explicit entity/role modeling and vectorized variable formulas. EUROMOD demonstrates clear layering between software engine, model rules, and input datasets, reinforcing separation between policy semantics and runtime execution.
_Source:_ https://openfisca.org/doc/architecture.html ; https://openfisca.org/doc/coding-the-legislation/50_entities.html ; https://openfisca.org/doc/simulate/index.html ; https://euromod-web.jrc.ec.europa.eu/download-euromod ; https://euromod-web.jrc.ec.europa.eu/resources/glossary

### Design Principles and Best Practices

- Separate policy semantics, graph relationships, and compute kernels into explicit bounded layers.
- Preserve deterministic period semantics and dependency ordering.
- Use traceability as a first-class concern for auditability and debugging.
- Add explicit graph-to-array projection boundaries (stable index maps and validation checks).
- Detect and mitigate dependency cycles early in formula planning.

_Source:_ https://openfisca.org/doc/_modules/openfisca_core/simulations/simulation.html ; https://openfisca.org/doc/simulate/analyse-simulation.html ; https://learn.microsoft.com/en-us/azure/architecture/patterns/

### Scalability and Performance Patterns

- Vectorized kernels and broadcasting for population-scale throughput.
- Variable-period caching with invalidation strategies for repeated computation paths.
- Spill-to-disk fallback under memory pressure for large scenarios.
- Horizontal scaling for API-facing simulation services.
- Chunk-aware execution and data locality optimization for out-of-core workloads.

_Source:_ https://openfisca.org/doc/coding-the-legislation/25_vectorial_computing.html ; https://openfisca.org/doc/_modules/openfisca_core/simulations/simulation.html ; https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/ ; https://docs.dask.org/en/stable/array-best-practices.html

### Integration and Communication Patterns

- Expose stable API contracts at platform boundaries.
- Maintain connector-based interoperability for research/statistical workflows.
- Prefer asynchronous orchestration for long-running simulation batches.
- Use gateway patterns to isolate external contracts from internal engine evolution.

_Source:_ https://openfisca.org/doc/openfisca-web-api/index.html ; https://pythonconnectoreuromod.readthedocs.io/en/latest/notebooks/getstarted.html ; https://euromod-web.jrc.ec.europa.eu/resources/glossary ; https://learn.microsoft.com/en-us/azure/architecture/patterns/

### Security Architecture Patterns

- Apply zero-trust assumptions to all service/service and user/service interactions.
- Use OAuth2/JWT for delegated and tokenized authorization.
- Use mutual TLS for service identity and encrypted inter-service traffic.
- Validate API exposures against OWASP API security threat models.

_Source:_ https://csrc.nist.gov/pubs/sp/800/207/final ; https://www.rfc-editor.org/rfc/rfc6749 ; https://www.rfc-editor.org/rfc/rfc7519 ; https://www.rfc-editor.org/rfc/rfc8705 ; https://owasp.org/API-Security/editions/2023/en/0x11-t10/

### Data Architecture Patterns

- Use columnar in-memory structures for efficient vectorized scans and aggregations.
- Use columnar persistence for compressed analytical workloads.
- Map relationship graphs to sparse matrix/vector representations for graph-plus-vector workloads.
- Keep stable entity-ID to array-index projections to avoid semantic drift.

_Source:_ https://arrow.apache.org/docs/format/Columnar.html ; https://parquet.apache.org/docs/overview/ ; https://graphblas.org/graphblas-api-cpp/ ; https://github.com/python-graphblas/python-graphblas

### Deployment and Operations Architecture

- Version model artifacts and data snapshots for reproducibility.
- Treat observability (trace, metrics, diagnostics) as core runtime capability.
- Include reliability controls for long batch runs and degraded dependencies.

_Source:_ https://euromod-web.jrc.ec.europa.eu/news-and-events/news/new-euromod-stable-release-2025q1 ; https://openfisca.org/doc/simulate/analyse-simulation.html ; https://cloud.google.com/architecture/framework/reliability

## Implementation Approaches and Technology Adoption

### Technology Adoption Strategies

For a microsimulation engine that combines entity graphs and vectorized arrays, phased migration is consistently lower risk than big-bang replacement.

- Apply strangler-style replacement around current simulation pathways, then replace by bounded capability slices.
- Run old/new pathways in parallel for selected cohorts and periods with explicit delta thresholds.
- Treat policy model artifacts (rules, parameters, schemas, input datasets) as versioned assets with compatibility checks.
- Pilot in limited policy domains before broad rollout.

_Source:_ https://martinfowler.com/bliki/OriginalStranglerFigApplication.html ; https://martinfowler.com/articles/strangler-fig-mobile-apps.html ; https://openfisca.org/doc/architecture.html ; https://openfisca.org/doc/coding-the-legislation/bootstrapping_a_new_country_package.html ; https://openfisca.org/en/packages/

### Development Workflows and Tooling

- Build CI pipelines that run linting, schema validation, simulation regression tests, and benchmark smoke tests.
- Track delivery quality and speed with DORA metrics for throughput and stability.
- Use staged or DAG-based pipelines so heavy simulation suites do not block fast quality signals.
- Keep model/package release workflows separate from runtime release workflows, linked by compatibility gates.

_Source:_ https://dora.dev/guides/dora-metrics/ ; https://dora.dev/guides/dora-metrics/history ; https://docs.gitlab.com/ee/ci/pipelines/ ; https://docs.github.com/de/actions/get-started/continuous-integration ; https://openfisca.org/doc/architecture.html

### Testing and Quality Assurance

- Use deterministic rule tests as baseline (OpenFisca-style YAML formula testing).
- Add differential testing between legacy and target engines by entity, period, and aggregate distribution.
- Keep pytest-based unit and integration suites with explicit numeric tolerances.
- Maintain golden datasets and expected outputs for non-regression across model/runtime changes.

_Source:_ https://openfisca.org/doc/coding-the-legislation/writing_yaml_tests.html ; https://openfisca.org/doc/coding-the-legislation/10_basic_example.html ; https://docs.pytest.org/en/stable/how-to/usage.html ; https://openfisca.org/doc/simulate/run-simulation.html

### Deployment and Operations Practices

- Use controlled rollout strategies with bounded surge/unavailable settings.
- Autoscale compute workers for traffic and batch variability.
- Instrument traces, metrics, and logs with consistent telemetry semantics.
- Operate with SLO/error-budget governance to balance reliability and release velocity.

_Source:_ https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ ; https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/ ; https://opentelemetry.io/docs/ ; https://opentelemetry.io/docs/concepts/signals/ ; https://sre.google/sre-book/embracing-risk/ ; https://sre.google/workbook/error-budget-policy/

### Team Organization and Skills

- Align team boundaries with architecture boundaries (policy modeling, graph semantics, vector runtime, platform operations).
- Use platform/enabling patterns to reduce cognitive load for policy specialists.
- Build combined competency in policy-as-code, numerical/vector computing, data engineering, and reliability operations.

_Source:_ https://martinfowler.com/bliki/ConwaysLaw.html ; https://teamtopologies.com/news-blogs-newsletters/2024/11/24/revisiting-team-topologies-misuses-of-platform-teams ; https://openfisca.org/doc/architecture.html

### Cost Optimization and Resource Management

- Treat cost as an engineering signal with team ownership and clear allocation.
- Optimize for right-sizing, autoscaling behavior, and commitment strategy where stable.
- Evaluate architecture options with explicit unit-cost impact (per run/per cohort/per period).

_Source:_ https://www.finops.org/framework/principles/ ; https://www.finops.org/framework/capabilities/rate-optimization/ ; https://www.finops.org/wg/cloud-cost-allocation/ ; https://docs.cloud.google.com/architecture/framework/cost-optimization

### Risk Assessment and Mitigation

- Main risks: policy-correctness drift, schema mismatch, runtime instability, and security/compliance gaps.
- Apply secure development and supply-chain controls.
- Enforce API security controls (authorization scope, validation, rate limits, token hygiene).
- Maintain migration risk register with trigger-based mitigations and rollback paths.

_Source:_ https://csrc.nist.gov/pubs/sp/800/218/final ; https://owasp.org/API-Security/editions/2023/en/0x11-t10/ ; https://sre.google/sre-book/embracing-risk/

## Technical Research Recommendations

### Implementation Roadmap

1. Define target hybrid architecture (semantic graph + vector execution).
2. Formalize entity-index mapping contracts and differential test harness.
3. Execute phased migration with parallel-run validation.
4. Harden CI/CD, observability, and SLO governance.
5. Expand rollout with cost and team-topology optimization.

### Technology Stack Recommendations

- Policy semantics: OpenFisca-style entities, variables, parameters, periods.
- Graph layer: NetworkX/rustworkx/igraph with optional GraphBLAS route for sparse acceleration.
- Vector layer: NumPy with Arrow-compatible columnar boundaries; distributed chunking where required.
- Platform layer: stable APIs, async orchestration for batch workloads, observability-first runtime.

### Skill Development Requirements

- Policy-as-code and legislative test design
- Vectorized numerical computing and sparse graph techniques
- CI/CD and reliability engineering practices
- API and data security engineering

### Success Metrics and KPIs

- Correctness: differential output error rate within defined tolerance.
- Delivery: DORA throughput/stability trend.
- Runtime: throughput/latency/memory versus population size.
- Reliability: SLO attainment and error-budget burn rate.
- Cost: unit cost per simulation run and allocation coverage.
