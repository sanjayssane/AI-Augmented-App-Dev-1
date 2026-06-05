"""Build a Postman Collection v2.1 JSON from FastAPI openapi-export.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

METHODS = ("get", "post", "put", "patch", "delete", "head", "options")

TEST_SCRIPT = """\
const ok = pm.collectionVariables.get("expectedStatus").split(",").map(s => parseInt(s.trim(), 10));
pm.test("Status code is expected", function () {
    pm.expect(ok).to.include(pm.response.code);
});
pm.test("Response time under 5s", function () {
    pm.expect(pm.response.responseTime).to.be.below(5000);
});
"""


def expected_statuses(operation: dict) -> list[int]:
    codes: list[int] = []
    for code, spec in operation.get("responses", {}).items():
        if code.isdigit():
            codes.append(int(code))
    return sorted(codes) if codes else [200]


def main() -> None:
    spec_path = Path(__file__).resolve().parents[1] / "openapi-export.json"
    out_path = Path(__file__).resolve().parents[1] / "mcq-postman-collection.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))

    folders: dict[str, list[dict]] = {}
    for path, path_item in spec.get("paths", {}).items():
        for method in METHODS:
            op = path_item.get(method)
            if not op:
                continue
            tag = (op.get("tags") or ["default"])[0]
            statuses = expected_statuses(op)
            url = "{{baseUrl}}" + path
            request = {
                "name": op.get("summary") or f"{method.upper()} {path}",
                "request": {
                    "method": method.upper(),
                    "header": [{"key": "Accept", "value": "application/json"}],
                    "url": url,
                    "description": op.get("description") or "",
                },
                "event": [
                    {
                        "listen": "prerequest",
                        "script": {
                            "type": "text/javascript",
                            "exec": [
                                f'pm.collectionVariables.set("expectedStatus", "{",".join(map(str, statuses))}");'
                            ],
                        },
                    },
                    {
                        "listen": "test",
                        "script": {"type": "text/javascript", "exec": TEST_SCRIPT.splitlines()},
                    },
                ],
            }
            if method in ("post", "put", "patch") and op.get("requestBody"):
                request["request"]["header"].append(
                    {"key": "Content-Type", "value": "application/json"}
                )
                request["request"]["body"] = {
                    "mode": "raw",
                    "raw": "{}",
                    "options": {"raw": {"language": "json"}},
                }
            folders.setdefault(tag, []).append(request)

    collection = {
        "info": {
            "name": "MCQ Online Test Platform API",
            "description": spec.get("info", {}).get("description", ""),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [
            {"key": "baseUrl", "value": "http://localhost:8000"},
            {"key": "expectedStatus", "value": "200"},
        ],
        "item": [
            {"name": tag, "item": items} for tag, items in sorted(folders.items())
        ],
    }
    out_path.write_text(json.dumps(collection, indent=2), encoding="utf-8")
    total = sum(len(v) for v in folders.values())
    print(json.dumps({"output": str(out_path), "folders": len(folders), "requests": total}))


if __name__ == "__main__":
    main()
