// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Tests for RunManifestViewer — Story 26.4, AC-2, AC-4, AC-6. */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { RunManifestViewer } from "@/components/results/RunManifestViewer";
import type { ManifestResponse } from "@/api/types";

// ============================================================================
// Mock Helpers
// ============================================================================

const mockManifest = (overrides: Partial<ManifestResponse> = {}): ManifestResponse => ({
  run_id: "550e8400-e29b-41d4-a716-446655440001",
  manifest_id: "550e8400-e29b-41d4-a716-446655440001",
  created_at: "2026-03-07T22:00:00+00:00",
  started_at: "2026-03-07T22:00:00+00:00",
  finished_at: "2026-03-07T22:00:05+00:00",
  status: "completed",
  engine_version: "1.0.0",
  openfisca_version: "44.0.0",
  adapter_version: "1.0.0",
  scenario_version: "1.0.0",
  data_hashes: { "population.csv": "a".repeat(64) },
  output_hashes: { "panel.parquet": "b".repeat(64) },
  integrity_hash: "c".repeat(64),
  seeds: { master: 42, "2025": 42, "2026": 43 },
  policy: { carbon_tax_rate: 100 },
  assumptions: [
    { key: "carbon_tax_rate", value: 100, source: "user", is_default: false },
  ],
  mappings: [
    { openfisca_name: "carbon_tax", project_name: "carbon_tax_rate", direction: "input" },
  ],
  warnings: ["Warning message"],
  step_pipeline: ["preprocess", "compute", "aggregate"],
  parent_manifest_id: "",
  child_manifests: { "2026": "660e8400-e29b-41d4-a716-446655440002" },
  exogenous_series: ["co2_price"],
  taste_parameters: { price_sensitivity: -1.5 },
  evidence_assets: [{ type: "official", source: "INSEE" }],
  calibration_assets: [],
  validation_assets: [],
  evidence_summary: { trust_level: "high" },
  runtime_mode: "live",
  population_id: "fr-synthetic-2024",
  population_source: "bundled",
  metadata_only: false,
  ...overrides,
});

const partialManifest = (): ManifestResponse => ({
  ...mockManifest(),
  assumptions: [],
  mappings: [],
  warnings: [],
  data_hashes: {},
  output_hashes: {},
  integrity_hash: "",
  parent_manifest_id: "",
  child_manifests: {},
  exogenous_series: [],
  taste_parameters: {},
  evidence_assets: [],
  calibration_assets: [],
  validation_assets: [],
  evidence_summary: {},
  step_pipeline: [],
});

// ============================================================================
// Tests
// ============================================================================

describe("RunManifestViewer", () => {
  describe("loading state", () => {
    it("renders skeleton loaders when loading is true", () => {
      render(<RunManifestViewer manifest={null} loading={true} />);
      expect(screen.getByLabelText("Loading manifest")).toBeInTheDocument();
      // Skeleton components should be present (they render div elements with specific styling)
      const container = screen.getByLabelText("Loading manifest");
      expect(container.children.length).toBeGreaterThan(0);
    });
  });

  describe("error state", () => {
    it("renders error message when error is provided", () => {
      render(<RunManifestViewer manifest={null} error="Manifest not found" />);
      expect(screen.getByLabelText("Manifest error")).toBeInTheDocument();
      expect(screen.getByText("No manifest data available")).toBeInTheDocument();
      expect(screen.getByText("Manifest not found")).toBeInTheDocument();
    });

    it("renders default error message when manifest is null and no error provided", () => {
      render(<RunManifestViewer manifest={null} />);
      expect(screen.getByLabelText("Manifest error")).toBeInTheDocument();
      expect(screen.getByText(/The full manifest could not be loaded/i)).toBeInTheDocument();
    });

    it("shows close button when onClose is provided in error state", async () => {
      const handleClose = vi.fn();
      render(<RunManifestViewer manifest={null} error="Failed" onClose={handleClose} />);
      const closeBtn = screen.getByRole("button", { name: /Close/i });
      expect(closeBtn).toBeInTheDocument();
      await userEvent.click(closeBtn);
      expect(handleClose).toHaveBeenCalledTimes(1);
    });
  });

  describe("header", () => {
    it("shows manifest title", () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      expect(screen.getByText("Run Manifest")).toBeInTheDocument();
    });

    it("shows truncated manifest ID", () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      expect(screen.getByText("550e8400")).toBeInTheDocument();
    });

    it("shows close button when onClose is provided", async () => {
      const handleClose = vi.fn();
      render(<RunManifestViewer manifest={mockManifest()} onClose={handleClose} />);
      const closeBtn = screen.getByRole("button", { name: /Close/i });
      await userEvent.click(closeBtn);
      expect(handleClose).toHaveBeenCalledTimes(1);
    });
  });

  describe("Overview section", () => {
    it("renders all overview fields", () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      expect(screen.getByText("Run ID")).toBeInTheDocument();
      expect(screen.getByText("Manifest ID")).toBeInTheDocument();
      expect(screen.getByText("Status")).toBeInTheDocument();
      expect(screen.getByText("Created")).toBeInTheDocument();
      expect(screen.getByText("Started")).toBeInTheDocument();
      expect(screen.getByText("Finished")).toBeInTheDocument();
    });

    it("shows truncated run ID", () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      expect(screen.getAllByText(/550e8400-e29b/).length).toBeGreaterThan(0);
    });

    it("shows status badge", () => {
      render(<RunManifestViewer manifest={mockManifest({ status: "completed" })} />);
      expect(screen.getByText("completed")).toBeInTheDocument();
    });

    it("shows version fields", () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      expect(screen.getByText("Engine Version")).toBeInTheDocument();
      expect(screen.getAllByText("1.0.0").length).toBeGreaterThan(0);
      expect(screen.getByText("OpenFisca Version")).toBeInTheDocument();
      expect(screen.getByText("44.0.0")).toBeInTheDocument();
      expect(screen.getByText("Adapter Version")).toBeInTheDocument();
    });

    it("shows runtime mode badge", () => {
      render(<RunManifestViewer manifest={mockManifest({ runtime_mode: "live" })} />);
      expect(screen.getByText("Live OpenFisca")).toBeInTheDocument();
    });

    it("shows replay mode badge", () => {
      render(<RunManifestViewer manifest={mockManifest({ runtime_mode: "replay" })} />);
      expect(screen.getByText("Replay")).toBeInTheDocument();
    });

    it("shows population source badge", () => {
      render(<RunManifestViewer manifest={mockManifest({ population_source: "bundled" })} />);
      expect(screen.getByText("bundled")).toBeInTheDocument();
    });

    it("shows uploaded population source badge", () => {
      render(<RunManifestViewer manifest={mockManifest({ population_source: "uploaded" })} />);
      expect(screen.getByText("uploaded")).toBeInTheDocument();
    });

    it("shows generated population source badge", () => {
      render(<RunManifestViewer manifest={mockManifest({ population_source: "generated" })} />);
      expect(screen.getByText("generated")).toBeInTheDocument();
    });
  });

  describe("Execution section", () => {
    it("shows seeds when present", async () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      // Open the Execution section (it's collapsed by default)
      await userEvent.click(screen.getByText("Execution"));
      expect(screen.getByText("Seeds")).toBeInTheDocument();
      expect(screen.getByText("master")).toBeInTheDocument();
      expect(screen.getAllByText("42").length).toBeGreaterThan(0);
    });

    it("shows step pipeline when present", async () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      await userEvent.click(screen.getByText("Execution"));
      expect(screen.getByText("Step Pipeline")).toBeInTheDocument();
      expect(screen.getAllByText("preprocess").length).toBeGreaterThan(0);
      expect(screen.getAllByText("compute").length).toBeGreaterThan(0);
      expect(screen.getAllByText("aggregate").length).toBeGreaterThan(0);
    });

    it("shows population reference", async () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      await userEvent.click(screen.getByText("Execution"));
      expect(screen.getAllByText("Population").length).toBeGreaterThan(0);
      expect(screen.getByText("fr-synthetic-2024")).toBeInTheDocument();
    });

    it("handles empty step pipeline", () => {
      render(<RunManifestViewer manifest={mockManifest({ step_pipeline: [] })} />);
      // Should not crash, step pipeline section just won't render the list
      expect(screen.getByLabelText("Run manifest viewer")).toBeInTheDocument();
    });
  });

  describe("Policy section", () => {
    it("shows assumptions table", async () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      await userEvent.click(screen.getByText("Policy & Assumptions"));
      expect(screen.getByText("Policy")).toBeInTheDocument();
      expect(screen.getByText("Assumptions")).toBeInTheDocument();
      expect(screen.getAllByText("carbon_tax_rate").length).toBeGreaterThan(0);
      expect(screen.getByText("user")).toBeInTheDocument();
      expect(screen.getByText("No")).toBeInTheDocument();
    });

    it("shows mappings table", async () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      await userEvent.click(screen.getByText("Policy & Assumptions"));
      expect(screen.getByText("Variable Mappings")).toBeInTheDocument();
      expect(screen.getByText("carbon_tax")).toBeInTheDocument();
      expect(screen.getAllByText("carbon_tax_rate").length).toBeGreaterThan(0);
      expect(screen.getByText("input")).toBeInTheDocument();
    });

    it("handles empty assumptions", () => {
      render(<RunManifestViewer manifest={mockManifest({ assumptions: [] })} />);
      // Should not crash
      expect(screen.getByLabelText("Run manifest viewer")).toBeInTheDocument();
    });

    it("handles empty mappings", () => {
      render(<RunManifestViewer manifest={mockManifest({ mappings: [] })} />);
      // Should not crash
      expect(screen.getByLabelText("Run manifest viewer")).toBeInTheDocument();
    });
  });

  describe("Data Provenance section", () => {
    it("shows data hashes", async () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      await userEvent.click(screen.getByText("Data Provenance"));
      expect(screen.getByText("Input Hashes (SHA-256)")).toBeInTheDocument();
      expect(screen.getByText("population.csv")).toBeInTheDocument();
      // Hash should be truncated (8 chars...8 chars)
      expect(screen.getByText(/a{8}\.\.\./)).toBeInTheDocument();
    });

    it("shows output hashes", async () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      await userEvent.click(screen.getByText("Data Provenance"));
      expect(screen.getByText("Output Hashes (SHA-256)")).toBeInTheDocument();
      expect(screen.getByText("panel.parquet")).toBeInTheDocument();
    });

    it("shows integrity hash", async () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      await userEvent.click(screen.getByText("Data Provenance"));
      expect(screen.getByText("Integrity Hash")).toBeInTheDocument();
      expect(screen.getByText(/c{8}\.\.\./)).toBeInTheDocument();
    });

    it("truncates long hashes with tooltip", async () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      await userEvent.click(screen.getByText("Data Provenance"));
      const hashElement = screen.getByText(/a{8}\.\./);
      expect(hashElement).toHaveAttribute("title", "a".repeat(64));
    });
  });

  describe("Lineage section", () => {
    it("shows child manifests by year", async () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      await userEvent.click(screen.getByText("Lineage"));
      expect(screen.getByText("Child Manifests (by year)")).toBeInTheDocument();
      expect(screen.getByText("Year 2026")).toBeInTheDocument();
      expect(screen.getByText("660e8400-e29b-41d4-a716-446655440002")).toBeInTheDocument();
    });

    it("shows parent manifest when present", async () => {
      render(
        <RunManifestViewer
          manifest={mockManifest({ parent_manifest_id: "parent-manifest-123" })}
        />,
      );
      await userEvent.click(screen.getByText("Lineage"));
      expect(screen.getByText("Parent Manifest")).toBeInTheDocument();
      expect(screen.getByText("parent-manifest-123")).toBeInTheDocument();
    });

    it("shows no lineage message when both are empty", async () => {
      const emptyLineageManifest = mockManifest();
      emptyLineageManifest.parent_manifest_id = "";
      emptyLineageManifest.child_manifests = {};
      render(<RunManifestViewer manifest={emptyLineageManifest} />);
      await userEvent.click(screen.getByRole("button", { name: /Lineage/i }));
      expect(screen.getByText(/No lineage information available/)).toBeInTheDocument();
    });
  });

  describe("Evidence section", () => {
    it("shows evidence assets", async () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      await userEvent.click(screen.getByText("Evidence & Assets"));
      expect(screen.getByText("Evidence Summary")).toBeInTheDocument();
      expect(screen.getByText("trust_level")).toBeInTheDocument();
      expect(screen.getByText("Evidence Assets")).toBeInTheDocument();
    });

    it("does not show evidence section when all arrays are empty", () => {
      render(<RunManifestViewer manifest={partialManifest()} />);
      expect(screen.queryByText("Evidence & Assets")).not.toBeInTheDocument();
    });
  });

  describe("Warnings section", () => {
    it("shows warnings list", () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      expect(screen.getByText("Warnings")).toBeInTheDocument();
      expect(screen.getByText("Warning message")).toBeInTheDocument();
    });

    it("does not show warnings section when empty", () => {
      render(<RunManifestViewer manifest={mockManifest({ warnings: [] })} />);
      expect(screen.queryByText("Warnings")).not.toBeInTheDocument();
    });
  });

  describe("collapsible sections", () => {
    it("renders collapsible sections", () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      expect(screen.getByText("Overview")).toBeInTheDocument();
      expect(screen.getByText("Execution")).toBeInTheDocument();
      expect(screen.getByText("Policy & Assumptions")).toBeInTheDocument();
      expect(screen.getByText("Data Provenance")).toBeInTheDocument();
      expect(screen.getByText("Lineage")).toBeInTheDocument();
    });

    it("overview section is open by default", () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      // Check that Run ID is visible (inside Overview section)
      expect(screen.getByText("Run ID")).toBeInTheDocument();
    });

    it("warnings section is open by default when warnings exist", () => {
      render(<RunManifestViewer manifest={mockManifest()} />);
      expect(screen.getByText("Warning message")).toBeVisible();
    });
  });

  describe("metadata_only flag", () => {
    it("shows a metadata-only warning when metadata_only is true", () => {
      render(<RunManifestViewer manifest={mockManifest({ metadata_only: true })} />);
      expect(screen.getByText("Metadata-only manifest")).toBeInTheDocument();
      expect(screen.getByText(/Panel data was evicted/i)).toBeInTheDocument();
    });
  });
});
