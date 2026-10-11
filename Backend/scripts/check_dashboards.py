import os

ROOT = r"c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co"

dashboards = [
    os.path.join(ROOT, 'Frontend/src/pages/admin/AdminDashboard.jsx'),
    os.path.join(ROOT, 'Frontend/src/pages/manager/ManagerDashboard.jsx'),
    os.path.join(ROOT, 'Frontend/src/pages/location/LocationDashboard.jsx'),
    os.path.join(ROOT, 'Frontend/src/pages/coordinator/CoordinatorDashboard.jsx'),
    os.path.join(ROOT, 'Frontend/src/pages/student/StudentDashboard.jsx'),
]

for d in dashboards:
    if os.path.exists(d):
        with open(d, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"\n=== {os.path.basename(d)} ===")
        for i, line in enumerate(lines):
            if any(k in line.lower() for k in ['announcement', 'notice', 'compose', 'megaphone']):
                print(f"  {i+1}: {line.strip()[:100]}")
