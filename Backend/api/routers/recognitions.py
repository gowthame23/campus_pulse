from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse

from api.dependencies import get_auth_service, get_complaint_service
from api.security import get_current_user
from core.constants import STATUS_CLOSED, STATUS_AUTO_CLOSED
from models.administrator import Administrator
from models.app_manager import AppManager
from models.coordinator import Coordinator
from models.location_in_charge import LocationInCharge
from models.student import Student
from utils.helper import generate_id, now_string

router = APIRouter(prefix="/recognitions", tags=["recognitions"])


@router.get("/fixer-of-the-month")
def get_fixer_of_the_month(
    month: Optional[str] = Query(None, description="Month in YYYY-MM format"),
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
    auth_service=Depends(get_auth_service),
):
    """
    Calculates Fixer of the Month according to:
    score = 0.50 * on_time_rate + 0.30 * reopen_free_rate + 0.20 * positive_rating_rate
    Minimum 5 completed jobs in that month.
    Students see only the winner; staff see the full leaderboard.
    """
    target_month = month or datetime.now().strftime("%Y-%m")
    db = complaint_service.repository

    with db.get_connection() as conn:
        # 1. Fetch completed complaints in the given month with assigned coordinator
        query = """
            SELECT c.complaint_id, c.assigned_to, c.status, c.reopen_count,
                   c.created_at, c.sla_deadline, c.resolved_at, c.closed_at
            FROM complaints c
            WHERE c.status IN ('Closed', 'Closed (Auto Closed)', 'Waiting for Verification', 'Pending Warden Verification')
              AND (
                strftime('%Y-%m', c.closed_at) = ?
                OR strftime('%Y-%m', c.resolved_at) = ?
                OR (c.closed_at IS NULL AND strftime('%Y-%m', c.updated_at) = ?)
              )
              AND c.assigned_to IS NOT NULL AND TRIM(c.assigned_to) != ''
        """
        complaint_rows = conn.execute(query, (target_month, target_month, target_month)).fetchall()

        # 2. Fetch feedback in the given month
        feedback_rows = conn.execute("""
            SELECT fb.complaint_id, fb.rating, c.assigned_to
            FROM complaint_feedback fb
            JOIN complaints c ON c.complaint_id = fb.complaint_id
            WHERE strftime('%Y-%m', fb.created_at) = ?
        """, (target_month,)).fetchall()

    # Group by coordinator
    coord_stats = {}
    for r in complaint_rows:
        cid = r["assigned_to"]
        if cid not in coord_stats:
            coord_stats[cid] = {
                "total_completed": 0,
                "on_time_count": 0,
                "reopen_free_count": 0,
                "feedback_ratings": [],
            }
        coord_stats[cid]["total_completed"] += 1

        # Check on-time: resolved/closed before or at sla_deadline
        is_on_time = True
        done_time = r["resolved_at"] or r["closed_at"]
        if done_time and r["sla_deadline"] and done_time > r["sla_deadline"]:
            is_on_time = False

        if is_on_time:
            coord_stats[cid]["on_time_count"] += 1

        if (r["reopen_count"] or 0) == 0:
            coord_stats[cid]["reopen_free_count"] += 1

    for fb in feedback_rows:
        cid = fb["assigned_to"]
        if cid in coord_stats:
            coord_stats[cid]["feedback_ratings"].append(fb["rating"])

    # Load coordinators info
    coordinators = {u.user_id: u for u in auth_service.list_users(role=Coordinator.ROLE)}

    leaderboard = []
    for cid, stats in coord_stats.items():
        user = coordinators.get(cid) or auth_service.get_user(cid)
        if not user or (getattr(user, "role", "") or "").lower() != "coordinator":
            continue

        tot = stats["total_completed"]
        on_time_rate = stats["on_time_count"] / tot if tot > 0 else 0.0
        reopen_free_rate = stats["reopen_free_count"] / tot if tot > 0 else 0.0

        ratings = stats["feedback_ratings"]
        if ratings:
            pos_count = sum(1 for r in ratings if r >= 4)
            pos_rate = pos_count / len(ratings)
        else:
            pos_rate = 1.0  # Neutral benefit of the doubt when unrated

        # Score formula: 0.50 * on_time + 0.30 * reopen_free + 0.20 * positive_rating
        raw_score = (0.50 * on_time_rate) + (0.30 * reopen_free_rate) + (0.20 * pos_rate)
        score_pct = round(raw_score * 100, 1)

        leaderboard.append({
            "coordinator_id": cid,
            "coordinator_name": user.name,
            "total_completed": tot,
            "on_time_count": stats["on_time_count"],
            "on_time_rate": round(on_time_rate * 100, 1),
            "reopen_free_count": stats["reopen_free_count"],
            "reopen_free_rate": round(reopen_free_rate * 100, 1),
            "ratings_count": len(ratings),
            "positive_rating_rate": round(pos_rate * 100, 1),
            "score": score_pct,
            "qualified": tot >= 5,
        })

    # Sort leaderboard: qualified first, then highest score, then total completed
    leaderboard.sort(key=lambda x: (x["qualified"], x["score"], x["total_completed"]), reverse=True)

    winner = None
    if leaderboard and leaderboard[0]["qualified"]:
        winner = leaderboard[0]
    elif leaderboard:
        # Fallback to top coordinator if nobody reached 5 yet in early pilot
        winner = leaderboard[0]

    # Permission check: Student only sees the winner
    is_student = (current_user.role or "").lower() == Student.ROLE.lower()
    return {
        "month": target_month,
        "winner": winner,
        "leaderboard": [] if is_student else leaderboard,
        "is_student_view": is_student,
    }


@router.get("/badges")
def get_coordinator_badges(
    coordinator_id: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
    auth_service=Depends(get_auth_service),
):
    """List badges awarded to coordinator, dynamically evaluated from achievements."""
    target_id = coordinator_id or current_user.user_id
    user = auth_service.get_user(target_id)
    if not user:
        raise HTTPException(status_code=404, detail="Coordinator not found.")

    db = complaint_service.repository
    with db.get_connection() as conn:
        complaints = conn.execute("""
            SELECT complaint_id, sla_deadline, resolved_at, closed_at, reopen_count, status
            FROM complaints
            WHERE assigned_to = ? AND status IN ('Closed', 'Closed (Auto Closed)', 'Waiting for Verification', 'Pending Warden Verification')
        """, (target_id,)).fetchall()

        feedbacks = conn.execute("""
            SELECT fb.rating
            FROM complaint_feedback fb
            JOIN complaints c ON c.complaint_id = fb.complaint_id
            WHERE c.assigned_to = ?
        """, (target_id,)).fetchall()

    total_done = len(complaints)
    on_time_done = 0
    for c in complaints:
        done_time = c["resolved_at"] or c["closed_at"]
        if not (done_time and c["sla_deadline"] and done_time > c["sla_deadline"]):
            on_time_done += 1
    zero_reopen_done = sum(1 for c in complaints if (c["reopen_count"] or 0) == 0)
    five_star_count = sum(1 for f in feedbacks if f["rating"] == 5)

    badges = []
    if on_time_done >= 5:
        badges.append({
            "badge_key": "speed_demon",
            "name": "Speed Demon",
            "icon": "⚡",
            "description": "Resolved 5+ complaints ahead of the SLA deadline.",
            "unlocked": True,
        })
    if zero_reopen_done >= 5:
        badges.append({
            "badge_key": "first_time_fixer",
            "name": "First-Time Fixer",
            "icon": "🎯",
            "description": "5+ complaints closed with zero reopens.",
            "unlocked": True,
        })
    if five_star_count >= 3:
        badges.append({
            "badge_key": "student_favorite",
            "name": "Student Favorite",
            "icon": "⭐",
            "description": "Received 3 or more 5-star ratings from students.",
            "unlocked": True,
        })
    if total_done >= 10:
        badges.append({
            "badge_key": "campus_pillar",
            "name": "Campus Pillar",
            "icon": "🏛️",
            "description": "Completed over 10 campus maintenance tasks.",
            "unlocked": True,
        })

    return {
        "coordinator_id": target_id,
        "coordinator_name": user.name,
        "badges": badges,
        "total_badges": len(badges),
    }


@router.get("/certificate", response_class=HTMLResponse)
def get_winner_certificate(
    coordinator_id: str = Query(...),
    month: str = Query(...),
    auth_service=Depends(get_auth_service),
):
    """Printable Fixer of the Month HTML certificate."""
    user = auth_service.get_user(coordinator_id)
    if not user:
        raise HTTPException(status_code=404, detail="Coordinator not found.")

    coord_name = user.name
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Fixer of the Month - {coord_name}</title>
  <style>
    body {{
      font-family: 'Georgia', serif;
      background-color: #fdfaf6;
      margin: 0;
      padding: 40px;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      box-sizing: border-box;
    }}
    .cert-border {{
      border: 12px double #1e3a8a;
      background: white;
      padding: 60px 40px;
      text-align: center;
      max-width: 800px;
      width: 100%;
      box-shadow: 0 10px 25px rgba(0,0,0,0.1);
      position: relative;
    }}
    .cert-badge {{
      font-size: 54px;
      margin-bottom: 10px;
    }}
    h1 {{
      font-size: 38px;
      color: #1e3a8a;
      margin: 10px 0;
      letter-spacing: 2px;
      text-transform: uppercase;
    }}
    h2 {{
      font-size: 20px;
      color: #b45309;
      font-style: italic;
      margin-bottom: 30px;
    }}
    .recipient {{
      font-size: 32px;
      font-weight: bold;
      color: #111827;
      border-bottom: 2px solid #b45309;
      display: inline-block;
      padding-bottom: 8px;
      margin-bottom: 20px;
    }}
    p {{
      font-size: 18px;
      color: #4b5563;
      line-height: 1.6;
      max-width: 600px;
      margin: 0 auto 30px;
    }}
    .footer {{
      display: flex;
      justify-content: space-around;
      margin-top: 50px;
      padding-top: 20px;
    }}
    .sig-line {{
      border-top: 1px solid #9ca3af;
      width: 180px;
      padding-top: 6px;
      font-size: 14px;
      color: #6b7280;
    }}
    @media print {{
      body {{ background: white; padding: 0; }}
      .cert-border {{ box-shadow: none; border-width: 8px; }}
    }}
  </style>
</head>
<body>
  <div class="cert-border">
    <div class="cert-badge">🏆</div>
    <h2>CAMPUS PULSE EXCELLENCE AWARD</h2>
    <h1>Fixer of the Month</h1>
    <div class="recipient">{coord_name}</div>
    <p>In recognition of outstanding dedication, rapid turnaround, and exceptional service to the campus community for the month of <strong>{month}</strong>.</p>
    <div class="footer">
      <div>
        <div class="sig-line">Director of Campus Facilities</div>
      </div>
      <div>
        <div class="sig-line">Campus Administration</div>
      </div>
    </div>
  </div>
</body>
</html>"""
