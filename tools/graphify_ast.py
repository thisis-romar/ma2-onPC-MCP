"""Graphify Step 3A: AST extraction for code files. Run via: uv run python tools/graphify_ast.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from graphify.extract import collect_files, extract  # noqa: E402

detect = json.loads(Path(".graphify_detect.json").read_text())
code_files = []
for f in detect.get("files", {}).get("code", []):
    p = Path(f)
    code_files.extend(collect_files(p) if p.is_dir() else [p])

if code_files:
    result = extract(code_files, parallel=False)
    Path(".graphify_ast.json").write_text(json.dumps(result, indent=2))
    print(f"AST: {len(result['nodes'])} nodes, {len(result['edges'])} edges")
else:
    Path(".graphify_ast.json").write_text(
        json.dumps({"nodes": [], "edges": [], "input_tokens": 0, "output_tokens": 0})
    )
    print("No code files — skipping AST extraction")
