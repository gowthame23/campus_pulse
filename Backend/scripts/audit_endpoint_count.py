#!/usr/bin/env python3
"""
Campus Pulse — API Endpoint Count and Route Audit Script
Inspects FastAPI app.routes to calculate the verified endpoint count and route distribution.
"""
import sys
import os
from collections import defaultdict
from pathlib import Path

# Add Backend root to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from api.main import app


def audit_routes():
    endpoints = []
    routes_by_prefix = defaultdict(list)
    methods_count = defaultdict(int)

    for r in app.routes:
        methods = getattr(r, "methods", None)
        path = getattr(r, "path", None)
        name = getattr(r, "name", None)

        if not path:
            continue

        if methods:
            # Filter out implicit HEAD and OPTIONS
            active_methods = [m for m in methods if m not in ("HEAD", "OPTIONS")]
            for m in active_methods:
                endpoints.append((m, path, name))
                methods_count[m] += 1
                prefix = "/" + path.strip("/").split("/")[0] if path.strip("/") else "/"
                routes_by_prefix[prefix].append((m, path, name))
        else:
            # WebSocket or mount route
            route_type = r.__class__.__name__
            endpoints.append((route_type, path, name))
            methods_count[route_type] += 1
            prefix = "/" + path.strip("/").split("/")[0] if path.strip("/") else "/"
            routes_by_prefix[prefix].append((route_type, path, name))

    print("=" * 70)
    print("CAMPUS PULSE — VERIFIED API ROUTE AUDIT")
    print("=" * 70)
    print(f"Total Routes / Endpoints: {len(endpoints)}")
    print("-" * 70)
    print("HTTP / Protocol Distribution:")
    for m, c in sorted(methods_count.items(), key=lambda x: -x[1]):
        print(f"  {m:15}: {c}")

    print("-" * 70)
    print("Endpoints by URL Prefix / Router Module:")
    for prefix, r_list in sorted(routes_by_prefix.items(), key=lambda x: -len(x[1])):
        print(f"  {prefix:22}: {len(r_list):3d} endpoints")

    print("=" * 70)
    return len(endpoints)


if __name__ == "__main__":
    audit_routes()
