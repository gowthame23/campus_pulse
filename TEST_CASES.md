# Campus Pulse — Manual Test Cases

This is a checklist to click through the real app yourself. Items marked **✅ Verified** were already exercised live against a running backend+frontend this session (not just read from code) — I'm telling you the result, not asking you to re-prove it, though you're welcome to. Everything else is `☐` for you to check off.

Demo accounts: Admin `gowthamejjurothu@gmail.com` / `Admin@123` · App Manager `ejjurothugowtham@gmail.com` / `Manager@123` · Warden `naveen@campus.edu` / `warden@123` · Coordinator `gowthamejjurothu15@gmail.com` / `Coordinator@123` · Student `gowtham.e23@iiits.in` / `Student@123` · Super Admin `superadmin@campuspulse.edu` / `Superadmin@123`

---

## 1. Login & redirect per role

| # | Step | Expected | Status |
|---|---|---|---|
| 1.1 | Log in as Student | Lands on `/student` | ✅ Verified |
| 1.2 | Log in as Coordinator | Lands on `/coordinator` | ✅ Verified |
| 1.3 | Log in as Warden | Lands on `/location` | ✅ Verified |
| 1.4 | Log in as App Manager | Lands on `/manager` | ✅ Verified |
| 1.5 | Log in as Administrator | Lands on `/admin` | ✅ Verified |
| 1.6 | Log in as Super Admin | Lands on `/superadmin` | ✅ Verified |
| 1.7 | Log in with wrong password | Generic "Invalid credentials", no hint whether the email exists | ☐ |
| 1.8 | Visit a page for a role you're not logged in as (e.g. student visiting `/admin`) by typing the URL | Redirected to `/403` or your own dashboard, not the admin page | ☐ |
| 1.9 | Log out, then press the browser Back button | Does not land on a logged-in page | ☐ |

## 2. "Reflection" — admin creates X, it shows up elsewhere

| # | Step | Expected | Status |
|---|---|---|---|
| 2.1 | Admin creates a new Location | Immediately appears in the Student's "File Complaint" location dropdown, with no refresh needed beyond navigating to the page | ✅ Verified |
| 2.2 | Admin/Coordinator publishes an Announcement (status Published) | Shows on the Student's `/announcements` page **and** on the Student dashboard | ✅ Verified |
| 2.3 | Admin creates a new User | Appears in Admin's `/admin/users` list immediately; the new user can log in right away with the temp password, and is forced into "change password" (`first_login`) | ✅ Verified |
| 2.4 | Admin creates a Department for a Location | Department appears in that Location's complaint-form dropdown | ☐ |
| 2.5 | Admin adds an Issue type under a Department | New issue appears in the complaint form's issue dropdown for that department | ☐ |
| 2.6 | Admin assigns a Warden to a Location | That location shows the warden's name on the Admin's location list and the Warden dashboard shows that location | ☐ |
| 2.7 | Admin assigns a Coordinator to a Department+Location | New complaints in that dept/location appear in the coordinator's queue | ☐ |
| 2.8 | A student files a complaint | Appears in the responsible Coordinator's queue, the Warden's location view, and the Admin's "All Complaints" list | ☐ |
| 2.9 | Admin archives a Department | Confirm it disappears from the complaint-creation dropdown — **and separately check:** does any Coordinator still actively assigned to it keep a "ghost" assignment to a department they can no longer receive new complaints in? (see Finding #1 below — I found a real case of this) | ☐ |

## 3. Real-time notifications (no page refresh)

| # | Step | Expected | Status |
|---|---|---|---|
| 3.1 | Open the app as a Coordinator, leave the tab open. From another session, assign a complaint to them. | The notification bell updates and the browser's console shows a `campus-pulse-notification` event — all without reloading the tab | ✅ Verified — arrived in under half a second |
| 3.2 | Same as above, but reload the page right after the push instead of leaving it live | The "offline" delivery still shows it in the notification list | ☐ |
| 3.3 | Close the browser entirely for a coordinator, create and assign a complaint to them, then log back in | The notification appears in their list (delivered-while-offline path) | ☐ |
| 3.4 | Mark a notification read; log in from a second browser/device as the same user | Read state matches across sessions (it's server-stored, not per-device) | ☐ |
| 3.5 | As a student, delete (clear) your own notifications | Only your notifications are removed, not a broadcast announcement notification meant for everyone | ☐ |
| 3.6 | Note for your own testing: a hard page **reload** right after login can cause a brief (1–2s) window where the live socket is reconnecting — a push that lands in that exact window may be missed until the next navigation. This is a real, if narrow, gap — see Finding #2. | — | — |

## 4. Complaint lifecycle, end to end

| # | Step | Expected | Status |
|---|---|---|---|
| 4.1 | Student files a complaint | Status `Submitted`, visible only to the student and the responsible coordinator/warden/admin | ☐ |
| 4.2 | Coordinator accepts it | Status `Assigned`, assigned_to = that coordinator | ☐ |
| 4.3 | Coordinator starts work | Status `In Progress` | ☐ |
| 4.4 | Coordinator marks it resolved with notes | Status `Waiting for Verification` | ☐ |
| 4.5 | Student confirms the fix | Status `Closed` | ☐ |
| 4.6 | Student instead says "not fixed" with a reason | Status `Reopened`, reopen count increments | ☐ |
| 4.7 | Reopen the same complaint 3 times total | 4th reopen attempt is refused (limit reached) | ☐ |
| 4.8 | Leave a resolved complaint unconfirmed for the configured auto-close window | Auto-closes itself (check System Settings for the current `auto_close_days` value — don't wait the real number of days, just confirm the setting exists and is editable) | ☐ |
| 4.9 | Coordinator escalates a stuck complaint | Goes to the Warden (or App Manager if no warden) with the reason recorded in history | ☐ |
| 4.10 | Try escalating an already-Closed complaint | Rejected | ☐ |
| 4.11 | Student A tries to open Student B's private complaint by guessing/editing the URL's complaint ID | 403/404, not the complaint content | ☐ |

## 5. Lost & Found

| # | Step | Expected | Status |
|---|---|---|---|
| 5.1 | Student reports a lost item | Appears in their own list and in the public Lost & Found board (if Public visibility) | ☐ |
| 5.2 | Another student submits a claim with proof | Claim appears for the item owner/staff to approve or reject | ☐ |
| 5.3 | Claim is approved | A chat opens between finder and claimant | ☐ |
| 5.4 | Item marked Returned | Chat becomes read-only | ☐ |
| 5.5 | Student tries to delete another student's lost item (via API or devtools) | Rejected — only the reporter can delete their own item | ☐ |
| 5.6 | Admin marks an item "Private" | Other students can no longer open it directly by ID | ☐ |

## 6. RBAC — spot checks (try these as the "wrong" role; all should be blocked both by hidden buttons *and* by the server if you hit the API directly)

| # | Step | Expected | Status |
|---|---|---|---|
| 6.1 | Student tries to create/edit a Location or Department | Blocked | ☐ |
| 6.2 | Coordinator tries to delete another coordinator's complaint | Blocked | ☐ |
| 6.3 | App Manager tries to manage an Administrator account | Blocked | ☐ |
| 6.4 | Super Admin tries to open `/complaints`, `/lost-found`, `/announcements`, `/analytics`, `/reports`, `/feedback`, `/search` | Blocked (403) — Super Admin is platform-level only | ☐ |
| 6.5 | Administrator tries to view the Super Admin's own user profile or delete it | Not found / blocked — Super Admin is invisible to institution admins | ☐ |

## 7. Account security

| # | Step | Expected | Status |
|---|---|---|---|
| 7.1 | Enter the wrong password 5 times in a row for one account | 6th attempt is refused with a "try again in N seconds" message, even with the correct password | ☐ |
| 7.2 | Wait out the lockout window (starts at 1 minute) | Login works again with the correct password | ☐ |
| 7.3 | While locked out, use "Forgot password" instead | Reset flow still works and immediately clears the lockout | ☐ |
| 7.4 | Request "Forgot password" | Email/console shows a 6-digit OTP, expires in 15 minutes, limited attempts | ☐ |
| 7.5 | Admin bulk-imports students via CSV | New accounts get an activation email/link; link lets them set their own password and log in; link cannot be reused a second time | ☐ |
| 7.6 | Admin resets a user's password directly | That user's existing login session is immediately invalidated | ☐ |

## 8. Things I found while testing (not fixed — flagging for you to decide)

1. **A real coordinator assignment points to an archived department.** `USR_COORDINATOR` has an *Active* assignment to `DEPT_HOSTEL_ELECTRICAL` (Hostel Block A / Electrical), but that department is currently archived, so it no longer appears in the student complaint form — new Electrical complaints for that hostel can't reach this coordinator at all. Their other assignment (Plumbing) is fine. Worth checking Admin → Departments → Hostel Block A to confirm whether Electrical should be un-archived or the coordinator's assignment should be reassigned/removed.
2. **A brief WebSocket reconnect window right after a hard page reload.** In normal use (clicking around the app) the live notification socket connects once and stays open — confirmed, a push arrived in under 500ms. But a *manual browser reload* right after login causes the socket to briefly cycle (connect/disconnect a couple of times, React's dev-mode double-mount plus the reload itself) before settling, maybe 1–2 seconds. A notification created in that exact window could be missed until the next navigation (it's still saved server-side and will show up once you open the Notifications page or it reconnects — it's a live-push timing gap, not a lost notification).
3. **Housekeeping:** while testing, a leftover server process from an earlier session answered a few of my requests against the real database before I caught it. I removed every test record it created except two (a test Location and Department) that real role assignments (the Warden and Coordinator) had already been pointed at in the meantime — deleting them now would break those assignments, so I left them in place. If you see a Location called **"Reflect Test Hostel"** or a Department called **"Reflect Dept"** in Admin → Locations/Departments, that's them — safe to just rename to something real, or reassign the warden/coordinator elsewhere first if you'd rather delete them outright.
