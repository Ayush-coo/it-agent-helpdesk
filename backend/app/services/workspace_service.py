from pathlib import Path


class WorkspaceService:
    def __init__(self) -> None:
        self.root = Path(__file__).resolve().parents[3]
        self.max_output = 12000

    def _resolve(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError("Path must stay inside the project workspace")
        return candidate

    def read_file(self, relative_path: str) -> dict[str, object]:
        path = self._resolve(relative_path)
        if not path.is_file():
            raise ValueError("File was not found in the project workspace")
        content = path.read_text(encoding="utf-8", errors="replace")
        truncated = len(content) > self.max_output
        return {
            "operation": "read_file",
            "path": relative_path,
            "content": content[: self.max_output],
            "truncated": truncated,
        }

    def search(self, query: str, relative_path: str = ".") -> dict[str, object]:
        if not query.strip():
            raise ValueError("Search query is required")
        base = self._resolve(relative_path)
        if not base.is_dir():
            raise ValueError("Search directory was not found in the project workspace")

        results: list[dict[str, object]] = []
        ignored = {".git", "node_modules", ".pytest_cache", ".chroma", "dist"}
        for path in base.rglob("*"):
            if len(results) >= 50 or not path.is_file() or any(part in ignored for part in path.parts):
                continue
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for line_number, line in enumerate(lines, start=1):
                if query.casefold() in line.casefold():
                    results.append({
                        "path": str(path.relative_to(self.root)).replace("\\", "/"),
                        "line": line_number,
                        "text": line[:240],
                    })
                    if len(results) >= 50:
                        break

        return {"operation": "search", "query": query, "results": results, "truncated": len(results) >= 50}
