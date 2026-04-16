#!/usr/bin/env python
"""Full-stack codebase audit using the Graph Intelligence Layer.

Scans the repository into an in-memory knowledge graph and runs 8
audit dimensions: dependency hotspots, clustering, circular deps,
orphan modules, test coverage gaps, MCP surface, import depth,
and skill generation candidates.

Usage:
    uv run python scripts/graph_full_stack_audit.py          # human-readable
    uv run python scripts/graph_full_stack_audit.py --json    # JSON output
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from src.knowledge_graph import GraphStore, NodeType, EdgeType, node_id
from src.knowledge_graph.parsers.repo_scanner import scan_repository
from src.knowledge_graph.analysis.impact_engine import compute_blast_radius, find_most_central
from src.knowledge_graph.analysis.cluster_engine import cluster_modules
from src.knowledge_graph.analysis.process_engine import trace_process, find_entry_points
from src.knowledge_graph.analysis.skill_generator import generate_all_skills
from src.knowledge_graph.mcp_metadata import extract_mcp_metadata


def _scan(store: GraphStore) -> dict:
    """Scan the repository and return counts."""
    counts = scan_repository(store, _REPO_ROOT)
    return counts


# ── Dimension 1: Dependency Hotspots ──────────────────────────────────────

def audit_dependency_hotspots(store: GraphStore, limit: int = 15) -> dict:
    """Find modules with the highest blast radius."""
    src_modules = [
        m for m in store.get_nodes_by_type(NodeType.MODULE)
        if m.label and m.label.startswith("src.") and not m.label.startswith("src.private")
    ]

    results = []
    for m in src_modules:
        impact = compute_blast_radius(store, m.node_id)
        results.append({
            "module": m.label,
            "node_id": m.node_id,
            "direct": len(impact.direct_dependents),
            "transitive": len(impact.transitive_dependents),
            "blast_radius": impact.blast_radius,
        })

    results.sort(key=lambda x: -x["blast_radius"])
    top = results[:limit]

    # Flag RED if any module has blast_radius > 50
    red_count = sum(1 for r in top if r["blast_radius"] > 50)
    return {
        "dimension": "Dependency Hotspots",
        "status": "RED" if red_count > 0 else "GREEN",
        "findings": top,
        "summary": f"{red_count} modules with blast radius > 50",
    }


# ── Dimension 2: Module Clustering ────────────────────────────────────────

def audit_clustering(store: GraphStore) -> dict:
    """Cluster modules and flag low-cohesion groups."""
    clusters = cluster_modules(store, n_clusters=0)

    findings = []
    low_cohesion = 0
    for c in clusters:
        entry = {
            "cluster_id": c.cluster_id,
            "label": c.label,
            "size": len(c.members),
            "cohesion": round(c.cohesion, 4),
            "sample_members": [
                store.get_node(m).label if store.get_node(m) else m
                for m in c.members[:5]
            ],
        }
        if c.cohesion < 0.05 and len(c.members) > 3:
            entry["flag"] = "LOW_COHESION"
            low_cohesion += 1
        findings.append(entry)

    return {
        "dimension": "Module Clustering",
        "status": "AMBER" if low_cohesion > 2 else "GREEN",
        "findings": findings,
        "summary": f"{len(clusters)} clusters, {low_cohesion} with low cohesion (<0.05)",
    }


# ── Dimension 3: Circular Dependencies ───────────────────────────────────

def audit_circular_deps(store: GraphStore) -> dict:
    """Detect import cycles using DFS with back-edge detection."""
    modules = store.get_nodes_by_type(NodeType.MODULE)
    module_ids = {m.node_id for m in modules}

    # Build adjacency list from IMPORTS edges
    adj: dict[str, list[str]] = defaultdict(list)
    for m in modules:
        for edge in store.get_edges_from(m.node_id):
            if edge.edge_type == EdgeType.IMPORTS and edge.target_id in module_ids:
                adj[m.node_id].append(edge.target_id)

    # DFS cycle detection
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {m.node_id: WHITE for m in modules}
    parent: dict[str, str | None] = {}
    cycles: list[list[str]] = []

    def dfs(u: str, path: list[str]) -> None:
        color[u] = GRAY
        for v in adj.get(u, []):
            if color.get(v) == GRAY:
                # Back edge — extract cycle
                cycle_start = path.index(v) if v in path else -1
                if cycle_start >= 0:
                    cycle = path[cycle_start:] + [v]
                    labels = []
                    for nid in cycle:
                        n = store.get_node(nid)
                        labels.append(n.label if n else nid)
                    cycles.append(labels)
            elif color.get(v, WHITE) == WHITE:
                dfs(v, path + [v])
        color[u] = BLACK

    for m in modules:
        if color.get(m.node_id, WHITE) == WHITE:
            dfs(m.node_id, [m.node_id])

    # Deduplicate cycles (normalize by rotating to smallest element)
    unique_cycles = []
    seen = set()
    for cycle in cycles:
        if len(cycle) < 2:
            continue
        # Normalize: rotate so smallest element is first
        path = cycle[:-1]  # remove duplicate end
        min_idx = path.index(min(path))
        normalized = tuple(path[min_idx:] + path[:min_idx])
        if normalized not in seen:
            seen.add(normalized)
            unique_cycles.append(list(normalized))

    return {
        "dimension": "Circular Dependencies",
        "status": "RED" if len(unique_cycles) > 0 else "GREEN",
        "findings": unique_cycles[:20],
        "summary": f"{len(unique_cycles)} import cycles detected",
    }


# ── Dimension 4: Orphan Modules ───────────────────────────────────────────

def audit_orphan_modules(store: GraphStore) -> dict:
    """Find source modules with zero incoming imports."""
    src_modules = [
        m for m in store.get_nodes_by_type(NodeType.MODULE)
        if m.label and m.label.startswith("src.") and not m.label.startswith("src.private")
    ]

    orphans = []
    for m in src_modules:
        edges_in = store.get_edges_to(m.node_id)
        imports_in = [e for e in edges_in if e.edge_type == EdgeType.IMPORTS]
        if not imports_in:
            # Check if it defines any symbols
            edges_out = store.get_edges_from(m.node_id)
            defines = [e for e in edges_out if e.edge_type == EdgeType.DEFINES]
            orphans.append({
                "module": m.label,
                "symbols_defined": len(defines),
            })

    orphans.sort(key=lambda x: x["module"])
    return {
        "dimension": "Orphan Modules",
        "status": "AMBER" if len(orphans) > 5 else "GREEN",
        "findings": orphans,
        "summary": f"{len(orphans)} source modules with zero importers",
    }


# ── Dimension 5: Test Coverage Gaps ───────────────────────────────────────

def audit_test_coverage(store: GraphStore) -> dict:
    """Cross-reference src modules against test modules."""
    src_modules = {
        m.label for m in store.get_nodes_by_type(NodeType.MODULE)
        if m.label and m.label.startswith("src.") and not m.label.startswith("src.private")
    }
    test_modules = {
        m.label for m in store.get_nodes_by_type(NodeType.MODULE)
        if m.label and m.label.startswith("tests.")
    }

    # Derive expected test module names
    # src.foo.bar → tests.test_foo_bar or tests.test_bar
    untested = []
    for src in sorted(src_modules):
        # Skip __init__ and internal modules
        if src.endswith(".__init__") or ".private" in src:
            continue
        # Generate possible test file names
        parts = src.replace("src.", "").replace(".", "_")
        candidates = [
            f"tests.test_{parts}",
            f"tests.test_{src.split('.')[-1]}",
        ]
        if not any(c in test_modules for c in candidates):
            untested.append(src)

    return {
        "dimension": "Test Coverage Gaps",
        "status": "RED" if len(untested) > 10 else "AMBER" if len(untested) > 5 else "GREEN",
        "findings": untested,
        "summary": f"{len(untested)} source modules without corresponding test files",
    }


# ── Dimension 6: MCP Surface Audit ───────────────────────────────────────

def audit_mcp_surface(store: GraphStore) -> dict:
    """Check MCP tools/resources/prompts for completeness."""
    meta = extract_mcp_metadata()

    missing_docstrings = []
    for name, tool in meta.tools.items():
        if not tool.docstring or len(tool.docstring.strip()) < 10:
            missing_docstrings.append({"type": "tool", "name": name})
    for uri, res in meta.resources.items():
        if not res.docstring or len(res.docstring.strip()) < 10:
            missing_docstrings.append({"type": "resource", "uri": uri})
    for name, prompt in meta.prompts.items():
        if not prompt.docstring or len(prompt.docstring.strip()) < 10:
            missing_docstrings.append({"type": "prompt", "name": name})

    return {
        "dimension": "MCP Surface",
        "status": "AMBER" if missing_docstrings else "GREEN",
        "findings": {
            "tools": len(meta.tools),
            "resources": len(meta.resources),
            "prompts": len(meta.prompts),
            "missing_docstrings": missing_docstrings,
        },
        "summary": f"{len(meta.tools)} tools, {len(meta.resources)} resources, {len(meta.prompts)} prompts; {len(missing_docstrings)} missing docstrings",
    }


# ── Dimension 7: Import Depth Analysis ────────────────────────────────────

def audit_import_depth(store: GraphStore) -> dict:
    """Find the deepest import chains from entry points."""
    entry_points = find_entry_points(store)

    # Filter to src modules only
    src_entries = [
        ep for ep in entry_points
        if ep.startswith("module:src.")
    ]

    deep_chains = []
    for ep in src_entries[:20]:  # limit to avoid long runs
        trace = trace_process(store, ep, max_depth=12)
        if trace.max_depth_reached > 5:
            deep_chains.append({
                "entry": store.get_node(ep).label if store.get_node(ep) else ep,
                "max_depth": trace.max_depth_reached,
                "step_count": len(trace.steps),
                "deepest_path": [
                    store.get_node(s.node_id).label if store.get_node(s.node_id) else s.node_id
                    for s in trace.steps
                    if s.depth <= trace.max_depth_reached
                ][:8],
            })

    deep_chains.sort(key=lambda x: -x["max_depth"])
    return {
        "dimension": "Import Depth",
        "status": "AMBER" if any(c["max_depth"] > 8 for c in deep_chains) else "GREEN",
        "findings": deep_chains[:10],
        "summary": f"{len(deep_chains)} entry points with import depth > 5",
    }


# ── Dimension 8: Skill Generation ─────────────────────────────────────────

def audit_skill_candidates(store: GraphStore) -> dict:
    """Generate skill suggestions from module clusters."""
    suggestions = generate_all_skills(store, min_cluster_size=3)

    findings = []
    for s in suggestions:
        findings.append({
            "name": s.name,
            "description": s.description,
            "safety_scope": s.safety_scope,
            "confidence": round(s.confidence, 2),
            "applicable_context": s.applicable_context[:80],
        })

    findings.sort(key=lambda x: -x["confidence"])
    return {
        "dimension": "Skill Candidates",
        "status": "GREEN",
        "findings": findings,
        "summary": f"{len(findings)} skill suggestions from module clusters",
    }


# ── Main ──────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Full-stack graph audit")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Initialize graph
    store = GraphStore(":memory:")
    store.initialize()

    if not args.json:
        print("Scanning repository...", flush=True)
    counts = _scan(store)
    if not args.json:
        print(f"  {counts.get('modules', 0)} modules, {counts.get('symbols', 0)} symbols, "
              f"{counts.get('nodes', 0)} nodes, {counts.get('edges', 0)} edges\n")

    # Run all dimensions
    dimensions = [
        audit_dependency_hotspots,
        audit_clustering,
        audit_circular_deps,
        audit_orphan_modules,
        audit_test_coverage,
        audit_mcp_surface,
        audit_import_depth,
        audit_skill_candidates,
    ]

    report = {"scan": counts, "dimensions": []}
    has_red = False

    for audit_fn in dimensions:
        if not args.json:
            print(f"Running: {audit_fn.__name__}...", flush=True)
        result = audit_fn(store)
        report["dimensions"].append(result)

        if result["status"] == "RED":
            has_red = True

        if not args.json:
            status_icon = {"GREEN": "[OK]", "AMBER": "[!!]", "RED": "[XX]"}[result["status"]]
            print(f"  {status_icon} {result['dimension']}: {result['summary']}")

            # Show top findings for non-GREEN
            if result["status"] != "GREEN":
                findings = result["findings"]
                if isinstance(findings, list):
                    for f in findings[:5]:
                        if isinstance(f, dict):
                            print(f"      - {f}")
                        elif isinstance(f, list):
                            print(f"      - {' -> '.join(str(x) for x in f)}")
                        else:
                            print(f"      - {f}")
                    if len(findings) > 5:
                        print(f"      ... +{len(findings) - 5} more")
                elif isinstance(findings, dict) and "missing_docstrings" in findings:
                    for f in findings["missing_docstrings"][:5]:
                        print(f"      - {f}")
            print()

    store.close()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        # Summary
        print("=" * 60)
        print("AUDIT SUMMARY")
        print("=" * 60)
        for d in report["dimensions"]:
            icon = {"GREEN": "GREEN ", "AMBER": "AMBER ", "RED": "RED   "}[d["status"]]
            print(f"  {icon}  {d['dimension']:30s}  {d['summary']}")
        print()
        if has_red:
            print("RESULT: RED findings detected — review required")
        else:
            print("RESULT: No RED findings — codebase is healthy")

    return 1 if has_red else 0


if __name__ == "__main__":
    sys.exit(main())
