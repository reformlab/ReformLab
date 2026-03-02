"""Governance subsystem for reproducibility, lineage, and auditability.

This module provides immutable run manifests for documenting all parameters,
data sources, and assumptions used in simulation runs. Manifests support
integrity verification, deterministic serialization, and tamper detection.

Public API:
    RunManifest: Immutable manifest schema with integrity hashing
    ManifestIntegrityError: Raised on tampering detection
    ManifestValidationError: Raised on schema validation failures
    LineageIntegrityError: Raised on lineage validation failures
    ReproducibilityValidationError: Raised on reproducibility input contract errors
    LineageGraph: Lineage graph query model
    get_lineage: Extract lineage graph from manifest
    validate_lineage: Validate bidirectional lineage integrity
    capture_assumptions: Capture structured assumption entries
    capture_mappings: Capture mapping configuration
    capture_policy: Capture policy snapshot
    capture_warnings: Capture warnings for manifest
    hash_file: Compute SHA-256 hash of a file
    hash_input_artifacts: Hash input data files
    hash_output_artifacts: Hash output artifacts
    verify_artifact_hashes: Verify stored hashes against current files
    ArtifactVerificationResult: Hash verification result
    check_reproducibility: Re-execute a run and verify outputs match
    ReproducibilityResult: Result of reproducibility check
    BenchmarkResult: Result of a single benchmark test
    BenchmarkSuiteResult: Result of running the complete benchmark suite
    run_benchmark_suite: Orchestrate benchmark checks
    MemoryEstimate: Memory usage estimate for simulation runs
    estimate_memory_usage: Estimate memory usage for a simulation
    get_available_memory: Get available system memory
"""

from reformlab.governance.benchmarking import (
    BenchmarkResult,
    BenchmarkSuiteResult,
    run_benchmark_suite,
)
from reformlab.governance.capture import (
    TESTED_MAX_HORIZON_YEARS,
    TESTED_MAX_POPULATION_SIZE,
    capture_assumptions,
    capture_mappings,
    capture_policy,
    capture_unsupported_config_warning,
    capture_unvalidated_mapping_warning,
    capture_unvalidated_template_warning,
    capture_warnings,
)
from reformlab.governance.errors import (
    LineageIntegrityError,
    ManifestIntegrityError,
    ManifestValidationError,
    ReproducibilityValidationError,
)
from reformlab.governance.hashing import (
    ArtifactVerificationResult,
    hash_file,
    hash_input_artifacts,
    hash_output_artifacts,
    verify_artifact_hashes,
)
from reformlab.governance.lineage import (
    LineageGraph,
    get_lineage,
    validate_lineage,
)
from reformlab.governance.manifest import RunManifest
from reformlab.governance.memory import (
    MemoryEstimate,
    estimate_memory_usage,
    get_available_memory,
)
from reformlab.governance.reproducibility import (
    ReproducibilityResult,
    check_reproducibility,
)

__all__ = [
    "RunManifest",
    "ManifestIntegrityError",
    "ManifestValidationError",
    "LineageIntegrityError",
    "ReproducibilityValidationError",
    "LineageGraph",
    "get_lineage",
    "validate_lineage",
    "TESTED_MAX_HORIZON_YEARS",
    "TESTED_MAX_POPULATION_SIZE",
    "capture_assumptions",
    "capture_mappings",
    "capture_policy",
    "capture_unsupported_config_warning",
    "capture_unvalidated_mapping_warning",
    "capture_unvalidated_template_warning",
    "capture_warnings",
    "hash_file",
    "hash_input_artifacts",
    "hash_output_artifacts",
    "verify_artifact_hashes",
    "ArtifactVerificationResult",
    "check_reproducibility",
    "ReproducibilityResult",
    "BenchmarkResult",
    "BenchmarkSuiteResult",
    "run_benchmark_suite",
    "MemoryEstimate",
    "estimate_memory_usage",
    "get_available_memory",
]
