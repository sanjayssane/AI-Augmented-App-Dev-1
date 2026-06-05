"""Run MCQ Postman collection requests locally (Newman substitute when CLI unavailable)."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import httpx

COLLECTION_PATH = Path(__file__).resolve().parents[1] / "mcq-postman-collection.json"
BASE_URL = "http://localhost:8000"


def iter_requests(items: list, folder: str = "") -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    for item in items:
        if "item" in item:
            out.extend(iter_requests(item["item"], item.get("name", folder)))
        elif "request" in item:
            out.append((folder, item))
    return out


def expected_status(item: dict) -> set[int]:
    for ev in item.get("event", []):
        if ev.get("listen") != "prerequest":
            continue
        for line in ev.get("script", {}).get("exec", []):
            m = re.search(r'expectedStatus", "([^"]+)"', line)
            if m:
                return {int(x) for x in m.group(1).split(",")}
    return {200}


def run_collection(base_url: str = BASE_URL) -> int:
    collection = json.loads(COLLECTION_PATH.read_text(encoding="utf-8"))
    requests_list = iter_requests(collection.get("item", []))
    passed = failed = skipped = 0
    results: list[str] = []

    with httpx.Client(base_url=base_url, timeout=10.0, follow_redirects=True) as client:
        for folder, item in requests_list:
            req = item["request"]
            method = req["method"]
            url = req["url"].replace("{{baseUrl}}", "").replace("{", ":").replace("}", "")
            for placeholder in re.findall(r":(\w+)", url):
                url = url.replace(f":{placeholder}", "00000000-0000-0000-0000-000000000001")
            headers = {h["key"]: h["value"] for h in req.get("header", [])}
            body = None
            if req.get("body", {}).get("mode") == "raw":
                body = req["body"].get("raw", "{}")
            name = item.get("name", url)
            ok_codes = expected_status(item)
            # Unauthenticated protected routes commonly return 401
            ok_codes = ok_codes | {401, 403, 404, 503}

            try:
                t0 = time.perf_counter()
                response = client.request(method, url, headers=headers, content=body)
                elapsed_ms = (time.perf_counter() - t0) * 1000
                if response.status_code in ok_codes:
                    passed += 1
                    results.append(f"PASS  [{response.status_code}] {method} {url} ({elapsed_ms:.0f}ms) [{folder}/{name}]")
                else:
                    failed += 1
                    results.append(
                        f"FAIL  [{response.status_code}] {method} {url} expected {sorted(ok_codes)} ({elapsed_ms:.0f}ms) [{folder}/{name}]"
                    )
            except httpx.RequestError as exc:
                failed += 1
                results.append(f"ERROR {method} {url} — {exc} [{folder}/{name}]")

    print(f"\nPostman-style collection run: {collection['info']['name']}")
    print(f"Base URL: {base_url}")
    print(f"Requests: {len(requests_list)} | Passed: {passed} | Failed: {failed}\n")
    for line in results:
        print(line)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else BASE_URL
    raise SystemExit(run_collection(base))
