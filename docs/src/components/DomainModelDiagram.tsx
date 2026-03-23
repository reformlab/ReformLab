import { useState, useCallback, useEffect, useRef } from 'react';
import styles from './DomainModelDiagram.module.css';

interface NodeData {
  id: string;
  label: string;
  description: string;
  properties: string[];
  x: number;
  y: number;
}

interface EdgeData {
  from: string;
  to: string;
}

const NODE_W = 130;
const NODE_H = 44;

const nodes: NodeData[] = [
  {
    id: 'population',
    label: 'Population',
    description:
      'A dataset of representative households — income, housing, vehicles, energy use, and demographics.',
    properties: [
      'PyArrow Tables by entity',
      'INSEE / Eurostat / ADEME / SDES sources',
      'Data fusion pipeline',
      'Synthetic or custom',
    ],
    x: 20,
    y: 30,
  },
  {
    id: 'policy',
    label: 'Policy',
    description:
      'The reform being evaluated — tax rates, exemptions, thresholds, and redistribution rules.',
    properties: [
      '6 template types',
      'Year-indexed rate schedules',
      'Portfolio composition (2+ policies)',
      'Conflict detection',
    ],
    x: 20,
    y: 150,
  },
  {
    id: 'orchestrator',
    label: 'Orchestrator',
    description:
      'Runs your simulation year by year — feeding households through a pipeline of computation, behavioral response, and state transition steps.',
    properties: [
      'Pluggable step pipeline',
      'Multi-year projection (10+ years)',
      'Vintage tracking',
      'Deterministic seeds',
    ],
    x: 230,
    y: 90,
  },
  {
    id: 'engine',
    label: 'Engine',
    description:
      'The computation backend that calculates household-level taxes and benefits. Default: OpenFisca France.',
    properties: [
      'ComputationAdapter protocol',
      'Swappable backends',
      'Version-pinned',
      'Mock adapter for tests',
    ],
    x: 430,
    y: 90,
  },
  {
    id: 'results',
    label: 'Results',
    description:
      'Raw simulation output — a household-by-year panel dataset with every computed variable.',
    properties: [
      'Parquet storage on disk',
      'In-memory LRU cache',
      'Immutable run manifest',
      'Reproducible via seeds + hashes',
    ],
    x: 600,
    y: 90,
  },
  {
    id: 'indicators',
    label: 'Indicators',
    description:
      'Analytics computed from results — distributional, fiscal, geographic, and welfare metrics.',
    properties: [
      '7 indicator types',
      'Per-decile and per-region breakdowns',
      'Winner/loser analysis',
      'Cross-portfolio comparison',
    ],
    x: 770,
    y: 90,
  },
];

const edges: EdgeData[] = [
  { from: 'population', to: 'orchestrator' },
  { from: 'policy', to: 'orchestrator' },
  { from: 'orchestrator', to: 'engine' },
  { from: 'engine', to: 'results' },
  { from: 'results', to: 'indicators' },
];

function getNodeById(id: string): NodeData | undefined {
  return nodes.find((n) => n.id === id);
}

function getMidRight(node: NodeData): [number, number] {
  return [node.x + NODE_W, node.y + NODE_H / 2];
}

function getMidLeft(node: NodeData): [number, number] {
  return [node.x, node.y + NODE_H / 2];
}

interface EdgeLine {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

function computeEdgeLine(edge: EdgeData): EdgeLine {
  const fromNode = getNodeById(edge.from);
  const toNode = getNodeById(edge.to);
  if (!fromNode || !toNode) return { x1: 0, y1: 0, x2: 0, y2: 0 };
  const [x1, y1] = getMidRight(fromNode);
  const [x2, y2] = getMidLeft(toNode);
  return { x1, y1, x2, y2 };
}

export default function DomainModelDiagram() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleNodeClick = useCallback(
    (id: string) => {
      setSelectedId((prev) => (prev === id ? null : id));
    },
    []
  );

  const handleNodeKeyDown = useCallback(
    (e: React.KeyboardEvent, id: string) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleNodeClick(id);
      }
      if (e.key === 'Escape') {
        setSelectedId(null);
      }
    },
    [handleNodeClick]
  );

  const handleSvgClick = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    // Dismiss if clicking the SVG background (not a node)
    if (e.target === e.currentTarget) {
      setSelectedId(null);
    }
  }, []);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setSelectedId(null);
    }
  }, []);

  // Dismiss panel when clicking outside the diagram component
  useEffect(() => {
    if (!selectedId) return;
    const dismiss = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setSelectedId(null);
      }
    };
    document.addEventListener('mousedown', dismiss);
    return () => document.removeEventListener('mousedown', dismiss);
  }, [selectedId]);

  const selectedNode = selectedId ? getNodeById(selectedId) : null;

  return (
    <div ref={containerRef} onKeyDown={handleKeyDown}>
      <svg
        className={styles.diagram}
        viewBox="0 0 920 220"
        aria-labelledby="domain-diagram-title"
        onClick={handleSvgClick}
      >
        <title id="domain-diagram-title">
          Interactive domain model diagram — click a node to learn more
        </title>
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="10"
            refX="10"
            refY="5"
            orient="auto"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" className={styles.arrowMarker} />
          </marker>
        </defs>

        {/* Edges */}
        {edges.map((edge) => {
          const { x1, y1, x2, y2 } = computeEdgeLine(edge);
          // Shorten the line so the arrowhead doesn't overlap the node border
          const dx = x2 - x1;
          const dy = y2 - y1;
          const len = Math.sqrt(dx * dx + dy * dy);
          const offset = 8;
          const ex2 = len > 0 ? x2 - (dx / len) * offset : x2;
          const ey2 = len > 0 ? y2 - (dy / len) * offset : y2;
          return (
            <g key={`${edge.from}-${edge.to}`} className={styles.domainEdge}>
              <line
                x1={x1}
                y1={y1}
                x2={ex2}
                y2={ey2}
                markerEnd="url(#arrowhead)"
              />
            </g>
          );
        })}

        {/* Nodes */}
        {nodes.map((node) => {
          const isSelected = node.id === selectedId;
          const cx = node.x + NODE_W / 2;
          const cy = node.y + NODE_H / 2;
          return (
            <g
              key={node.id}
              className={`${styles.domainNode}${isSelected ? ` ${styles.selected}` : ''}`}
              onClick={(e) => {
                e.stopPropagation();
                handleNodeClick(node.id);
              }}
              onKeyDown={(e) => handleNodeKeyDown(e, node.id)}
              tabIndex={0}
              role="button"
              aria-label={`${node.label} — click to learn more`}
              aria-pressed={isSelected}
            >
              <rect
                x={node.x}
                y={node.y}
                width={NODE_W}
                height={NODE_H}
                rx={8}
                ry={8}
              />
              <text x={cx} y={cy} textAnchor="middle" dominantBaseline="middle">
                {node.label}
              </text>
            </g>
          );
        })}
      </svg>

      {selectedNode && (
        <div className={styles.detailPanel} role="region" aria-label={`Details for ${selectedNode.label}`} aria-live="polite">
          <div className={styles.detailHeader}>
            <h3 className={styles.detailTitle}>{selectedNode.label}</h3>
            <button
              type="button"
              className={styles.dismissButton}
              onClick={() => setSelectedId(null)}
              aria-label="Close detail panel"
            >
              ×
            </button>
          </div>
          <p className={styles.detailDescription}>{selectedNode.description}</p>
          <ul className={styles.detailProperties}>
            {selectedNode.properties.map((prop) => (
              <li key={prop}>{prop}</li>
            ))}
          </ul>
          <a
            className={styles.detailLink}
            href={`#${selectedNode.id}`}
          >
            Learn more about {selectedNode.label} ↓
          </a>
        </div>
      )}
    </div>
  );
}
