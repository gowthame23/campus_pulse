import time
import socket
import subprocess
import sys
from playwright.sync_api import sync_playwright

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0

def run():
    backend_proc = None
    frontend_proc = None

    if not is_port_open(8000):
        print("Starting Backend server...")
        backend_proc = subprocess.Popen([sys.executable, 'run_api.py'], cwd='Backend', stdin=subprocess.PIPE)
    if not is_port_open(5173):
        print("Starting Frontend server...")
        frontend_proc = subprocess.Popen(['npx.cmd', 'vite', '--host', '127.0.0.1', '--port', '5173'], cwd='Frontend', stdin=subprocess.PIPE)

    for _ in range(20):
        if is_port_open(8000) and is_port_open(5173):
            print("Both servers verified listening on 8000 & 5173.")
            break
        time.sleep(0.5)

    logs = []
    requests_log = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            context.add_init_script("""
                localStorage.setItem('campus_pulse_lang_chosen', 'true');
                localStorage.setItem('campus_pulse_lang', 'en');
            """)
            page = context.new_page()

            page.on("console", lambda msg: logs.append(f"[{msg.type}] {msg.text}"))
            page.on("pageerror", lambda err: logs.append(f"[PAGE_ERROR] {err}"))

            def on_req(req):
                requests_log.append({"url": req.url, "method": req.method, "start": time.time(), "id": id(req)})

            def on_res(res):
                req_id = id(res.request)
                for r in requests_log:
                    if r["id"] == req_id:
                        r["status"] = res.status
                        r["duration"] = time.time() - r["start"]
                        break

            page.on("request", on_req)
            page.on("response", on_res)

            print("\n=== SCENARIO 1: Fresh Login and Student Dashboard Load ===")
            page.goto("http://127.0.0.1:5173/login")
            page.wait_for_selector('input[name="email"]')
            page.fill('input[name="email"]', "student@example.com")
            page.fill('input[name="password"]', "Student@123")

            t_login_click = time.time()
            page.click('button[type="submit"]')

            page.wait_for_url("**/student", timeout=15000)
            t_nav_start = time.time()
            print(f"Navigated to /student in {t_nav_start - t_login_click:.2f}s after login click")

            # High-resolution polling for skeleton vs content
            load_time_1 = None
            for step in range(300):
                has_skeleton = page.locator("[aria-label='Loading student dashboard...']").count() > 0 or page.locator("text=Loading student dashboard").count() > 0
                has_content = page.locator("text=Good day").count() > 0
                if has_content and not has_skeleton:
                    load_time_1 = time.time() - t_nav_start
                    print(f"Scenario 1 COMPLETE: Content usable in {load_time_1:.3f}s")
                    break
                time.sleep(0.05)

            if load_time_1 is None:
                print("Scenario 1 TIMED OUT: Still showing skeleton after 15s!")

            page.screenshot(path="dashboard_load_before_fix.png")

            print("\n=== SCENARIO 2: Page Refresh on /student ===")
            t_refresh_start = time.time()
            page.reload()
            page.wait_for_url("**/student")
            load_time_2 = None
            for step in range(300):
                has_skeleton = page.locator("[aria-label='Loading student dashboard...']").count() > 0 or page.locator("text=Loading student dashboard").count() > 0
                has_content = page.locator("text=Good day").count() > 0
                if has_content and not has_skeleton:
                    load_time_2 = time.time() - t_refresh_start
                    print(f"Scenario 2 COMPLETE: Content usable in {load_time_2:.3f}s")
                    break
                time.sleep(0.05)

            if load_time_2 is None:
                print("Scenario 2 TIMED OUT: Still showing skeleton after 15s!")

            print("\n=== SCENARIO 3: Navigate to /complaints and Return to /student ===")
            page.goto("http://127.0.0.1:5173/complaints")
            page.wait_for_url("**/complaints")
            time.sleep(1)

            t_return_start = time.time()
            page.goto("http://127.0.0.1:5173/student")
            page.wait_for_url("**/student")
            load_time_3 = None
            for step in range(300):
                has_skeleton = page.locator("[aria-label='Loading student dashboard...']").count() > 0 or page.locator("text=Loading student dashboard").count() > 0
                has_content = page.locator("text=Good day").count() > 0
                if has_content and not has_skeleton:
                    load_time_3 = time.time() - t_return_start
                    print(f"Scenario 3 COMPLETE: Content usable in {load_time_3:.3f}s")
                    break
                time.sleep(0.05)

            if load_time_3 is None:
                print("Scenario 3 TIMED OUT: Still showing skeleton after 15s!")

            browser.close()

        print("\n=== RELEVANT API REQUEST TIMINGS ===")
        api_reqs = [r for r in requests_log if "127.0.0.1:8000" in r["url"]]
        for r in api_reqs:
            url_short = r["url"].replace("http://127.0.0.1:8000", "")
            print(f"  {r['method']} {url_short:<42} -> {r.get('status')} in {r.get('duration', -1):.3f}s")

        print("\n=== CONSOLE WARNINGS/ERRORS ===")
        for l in logs:
            if any(k in l.lower() for k in ["error", "warn", "fail"]):
                print("  " + l)

    finally:
        pass

if __name__ == "__main__":
    run()
