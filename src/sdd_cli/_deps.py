"""User-owned, local cross-project dependency registry."""

from __future__ import annotations

import json
from pathlib import Path


def path_for(root: Path) -> Path:
    return root / ".sdd" / "dependencies.json"


def load(root: Path) -> dict:
    path = path_for(root)
    if not path.is_file():
        return {"version": 1, "dependencies": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "dependencies": [], "invalid": True}
    if not isinstance(data, dict) or not isinstance(data.get("dependencies", []), list):
        return {"version": 1, "dependencies": [], "invalid": True}
    return data


def save(root: Path, data: dict) -> Path:
    path = path_for(root)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")
    return path


def findings(root: Path) -> list[str]:
    data = load(root)
    if data.get("invalid"):
        return ["dependencies.json is invalid"]
    out: list[str] = []
    for edge in data["dependencies"]:
        target = Path(edge.get("path", ""))
        if not target.is_dir():
            out.append(f"dependency path missing: {target}")
        elif not (target / ".sdd").is_dir():
            out.append(f"dependency is not an SDD project: {target}")
        elif target.resolve() == root.resolve():
            out.append("dependency cycle: project depends on itself")
    if not out:
        seen: set[Path] = set()

        def visits(project: Path) -> bool:
            project = project.resolve()
            if project in seen:
                return project == root.resolve()
            seen.add(project)
            for edge in load(project).get("dependencies", []):
                target = Path(edge.get("path", ""))
                if target.is_dir() and visits(target):
                    return True
            seen.remove(project)
            return False

        if visits(root):
            out.append("dependency cycle reachable from this project")
    return out
