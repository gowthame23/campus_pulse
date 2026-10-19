import requests
import time
import json
import statistics

BASE_URL = "http://127.0.0.1:8000"

def login(email, password):
    res = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if res.status_code != 200:
        raise Exception(f"Login failed for {email}: {res.status_code} {res.text}")
    return res.json().get("access_token")

def time_request(session, method, url, **kwargs):
    times = []
    for _ in range(5):
        t0 = time.perf_counter()
        res = session.request(method, url, **kwargs)
        t1 = time.perf_counter()
        if res.status_code not in (200, 201):
            raise Exception(f"Request failed: {method} {url} -> {res.status_code} {res.text}")
        times.append((t1 - t0) * 1000)
    return {
        "min_ms": round(min(times), 2),
        "avg_ms": round(statistics.mean(times), 2),
        "median_ms": round(statistics.median(times), 2),
        "max_ms": round(max(times), 2),
        "p95_ms": round(statistics.quantiles(times, n=10)[8] if len(times) >= 10 else max(times), 2)
    }

def run_benchmarks():
    print("=== CAMPUS PULSE PERFORMANCE BENCHMARK ===")
    
    # 1. Admin login
    admin_token = login("gowthamejjurothu@gmail.com", "Admin@123")
    admin_session = requests.Session()
    admin_session.headers.update({"Authorization": f"Bearer {admin_token}"})

    # 2. Coordinator login
    coord_token = login("gowthamejjurothu15@gmail.com", "Coord@123")
    coord_session = requests.Session()
    coord_session.headers.update({"Authorization": f"Bearer {coord_token}"})

    # 3. Student login
    student_token = login("gowtham.e23@iiits.in", "Student@123")
    student_session = requests.Session()
    student_session.headers.update({"Authorization": f"Bearer {student_token}"})

    results = {}

    print("\nBenchmarking Admin GET /complaints (list all)...")
    results["admin_get_complaints"] = time_request(admin_session, "GET", f"{BASE_URL}/complaints")
    print(f"  Result: {results['admin_get_complaints']}")

    print("\nBenchmarking Coordinator GET /complaints...")
    results["coord_get_complaints"] = time_request(coord_session, "GET", f"{BASE_URL}/complaints")
    print(f"  Result: {results['coord_get_complaints']}")

    print("\nBenchmarking Student GET /complaints...")
    results["student_get_complaints"] = time_request(student_session, "GET", f"{BASE_URL}/complaints")
    print(f"  Result: {results['student_get_complaints']}")

    # Pick a complaint ID for detail test
    comp_list = admin_session.get(f"{BASE_URL}/complaints").json()
    first_id = comp_list[0]["complaint_id"] if comp_list else "CMP-20261011-0001"

    print(f"\nBenchmarking GET /complaints/{first_id} (detail)...")
    results["get_complaint_detail"] = time_request(admin_session, "GET", f"{BASE_URL}/complaints/{first_id}")
    print(f"  Result: {results['get_complaint_detail']}")

    print("\nBenchmarking GET /coordinators/stats...")
    results["get_coordinator_stats"] = time_request(admin_session, "GET", f"{BASE_URL}/coordinators/stats")
    print(f"  Result: {results['get_coordinator_stats']}")

    print("\nBenchmarking GET /dashboard/stats...")
    results["get_dashboard_stats"] = time_request(admin_session, "GET", f"{BASE_URL}/dashboard/stats")
    print(f"  Result: {results['get_dashboard_stats']}")

    print("\nBenchmarking GET /departments/coverage-gaps...")
    results["get_coverage_gaps"] = time_request(admin_session, "GET", f"{BASE_URL}/departments/coverage-gaps")
    print(f"  Result: {results['get_coverage_gaps']}")

    print("\nBenchmarking GET /notifications...")
    results["get_notifications"] = time_request(student_session, "GET", f"{BASE_URL}/notifications")
    print(f"  Result: {results['get_notifications']}")

    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to benchmark_results.json")
    return results

if __name__ == "__main__":
    run_benchmarks()
