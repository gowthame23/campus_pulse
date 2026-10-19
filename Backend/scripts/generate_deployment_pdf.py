import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

PDF_OUTPUT_PATH = r"C:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\Campus_Pulse_Production_Deployment_and_Platform_Guide.pdf"


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "CampusPulse — Production VPS Deployment & Operations Manual")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Running Footer
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 36, "Confidential & Proprietary — CampusPulse Engineering Handover")
        self.drawRightString(558, 36, f"Page {self._pageNumber} of {page_count}")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 46, 558, 46)

        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        PDF_OUTPUT_PATH,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "CoverSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2563EB"),
        spaceAfter=14,
    )
    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )
    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=4,
    )
    code_style = ParagraphStyle(
        "Code_Custom",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=6,
    )
    callout_style = ParagraphStyle(
        "Callout_Custom",
        parent=body_style,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E3A8A"),
    )

    story = []

    # Title Banner
    story.append(Paragraph("CampusPulse", title_style))
    story.append(Paragraph("Production VPS Deployment, Architecture & Operations Manual", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=12))

    # Metadata Summary Box
    meta_data = [
        [
            Paragraph("<b>Target Environment:</b> Linux Cloud VPS (Ubuntu 22.04 / 24.04)", body_style),
            Paragraph("<b>Status:</b> Production Ready (100% Passed)", body_style),
        ],
        [
            Paragraph("<b>Stack:</b> FastAPI + React 19 PWA + Nginx + Gunicorn", body_style),
            Paragraph("<b>Test Suite:</b> 241/241 Backend + 35/35 Frontend", body_style),
        ],
        [
            Paragraph("<b>Deployment Mode:</b> Turnkey 1-Command Script (deploy.sh)", body_style),
            Paragraph("<b>Security:</b> SSL Ready, Rate-Limited, RBAC Hardened", body_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # SECTION 1: SYSTEM OVERVIEW
    story.append(Paragraph("1. Executive Platform & Feature Overview", h1_style))
    story.append(Paragraph(
        "<b>CampusPulse</b> is an enterprise-grade campus operations, grievance tracking, and emergency response "
        "platform engineered to eliminate unassigned tickets, enforce accountable repairs with cryptographic proof, "
        "and provide safe, anonymous channels for sensitive student safety concerns.",
        body_style,
    ))

    features = [
        "<b>Multi-Department Coordinator Engine:</b> Intelligent routing based on active location-department teams. Includes automatic backup coordinator failover when primary coordinators are on leave.",
        "<b>'Other / Not Sure' Informational Triage:</b> Unlisted or ambiguous location issues bypass rigid SLA countdowns and route straight to Administration for review with zero artificial timers.",
        "<b>Anti-Tamper Repair Verification:</b> Technicians submit before/after photo proof. SHA-256 perceptual hashing blocks stock photo reuse; tickets require Location Warden inspection and Student sign-off.",
        "<b>Privacy-First Anonymous Safety Reporting:</b> Encrypted reporter identity isolation. Ordinary staff/admins cannot retrieve identity. Strict Admin-only disclosure requires re-authentication password entry and generates an immutable audit log.",
        "<b>Emergency SOS & Rapid Response:</b> Instant one-tap SOS broadcasting location to security and medical responders, backed by a 10-minute unacknowledged background escalation daemon.",
        "<b>Campus Community Hub:</b> Peer-to-peer Lost & Found with strict creator deletion ownership, public complaint endorsements to prevent ticket spam, and real-time personal/department chat.",
    ]
    for feat in features:
        story.append(Paragraph(f"• {feat}", bullet_style))

    story.append(Spacer(1, 12))

    # SECTION 2: PRODUCTION VPS DEPLOYMENT
    story.append(Paragraph("2. Turnkey Linux VPS Deployment (5-Minute Setup)", h1_style))
    story.append(Paragraph(
        "CampusPulse includes a turnkey automated deployment script (<code>deploy.sh</code>) configured for "
        "Ubuntu 22.04 LTS / 24.04 LTS servers (DigitalOcean, AWS EC2, Hetzner, Linode, Hostinger, or GCP).",
        body_style,
    ))

    story.append(Paragraph("Step 1 — Transfer Repository to Server", h2_style))
    story.append(Paragraph("SSH into your server and clone your repository (or copy via SCP):", body_style))
    code_block_1 = [
        [Paragraph("<b># On your Linux VPS terminal:</b><br/>"
                   "ssh root@&lt;YOUR_SERVER_IP&gt;<br/>"
                   "git clone &lt;YOUR_REPO_URL&gt; /var/www/campuspulse<br/>"
                   "cd /var/www/campuspulse", code_style)]
    ]
    t1 = Table(code_block_1, colWidths=[504])
    t1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t1)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Step 2 — Run the 1-Command Automated Deploy Script", h2_style))
    story.append(Paragraph("Execute the deploy script with your server IP address or domain name:", body_style))
    code_block_2 = [
        [Paragraph("<b># Make scripts executable and run:</b><br/>"
                   "chmod +x deploy.sh enable-ssl.sh<br/>"
                   "sudo ./deploy.sh &lt;YOUR_SERVER_IP_OR_DOMAIN&gt;<br/><br/>"
                   "<i># Example using Server IP:</i><br/>"
                   "sudo ./deploy.sh 159.65.120.45<br/><br/>"
                   "<i># Example using Domain Name:</i><br/>"
                   "sudo ./deploy.sh campuspulse.edu", code_style)]
    ]
    t2 = Table(code_block_2, colWidths=[504])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t2)
    story.append(Spacer(1, 10))

    story.append(Paragraph("What the Automated Script Configures:", h2_style))
    deploy_steps = [
        "<b>Dependency Provisioning:</b> Installs Python 3, Node.js 20 LTS, Nginx, Gunicorn, Uvicorn, and build tools.",
        "<b>Virtual Environment:</b> Isolates all Python backend packages inside <code>Backend/venv</code>.",
        "<b>PWA Compilation:</b> Builds the React 19 frontend into optimized production assets inside <code>Frontend/dist</code>.",
        "<b>Systemd Service:</b> Generates and activates <code>campuspulse-backend.service</code> managed by Gunicorn with 4 async Uvicorn workers and automatic reboot persistence.",
        "<b>Nginx Reverse Proxy:</b> Routes traffic, enables gzip, serves static assets with 6-month caching, manages SPA URL fallbacks, and upgrades WebSocket connections for real-time notifications.",
        "<b>Firewall Security:</b> Automatically enables UFW allowing ports 22 (SSH), 80 (HTTP), and 443 (HTTPS).",
    ]
    for ds in deploy_steps:
        story.append(Paragraph(f"• {ds}", bullet_style))

    story.append(PageBreak())

    # SECTION 3: SSL & PRODUCTION OPERATIONS
    story.append(Paragraph("3. Free SSL / HTTPS & Production Operations", h1_style))
    story.append(Paragraph(
        "If you have pointed a custom domain name (e.g. <code>campuspulse.edu</code>) to your server's public IP address, "
        "you can enable trusted Let's Encrypt SSL certificates with automated background renewal in one step:",
        body_style,
    ))

    code_block_3 = [
        [Paragraph("<b># Activate free Let's Encrypt SSL:</b><br/>"
                   "sudo ./enable-ssl.sh yourdomain.com admin_email@yourdomain.com", code_style)]
    ]
    t3 = Table(code_block_3, colWidths=[504])
    t3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t3)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Production Service Management Commands", h2_style))
    mgmt_data = [
        [Paragraph("<b>Operation</b>", body_style), Paragraph("<b>Terminal Command</b>", body_style)],
        [Paragraph("Check Backend Status", body_style), Paragraph("<code>sudo systemctl status campuspulse-backend</code>", code_style)],
        [Paragraph("Restart Backend API", body_style), Paragraph("<code>sudo systemctl restart campuspulse-backend</code>", code_style)],
        [Paragraph("Stream Live Backend Logs", body_style), Paragraph("<code>sudo journalctl -u campuspulse-backend -f</code>", code_style)],
        [Paragraph("Check Nginx Status", body_style), Paragraph("<code>sudo systemctl status nginx</code>", code_style)],
        [Paragraph("Test Nginx Configuration", body_style), Paragraph("<code>sudo nginx -t</code>", code_style)],
        [Paragraph("Reload Nginx Config", body_style), Paragraph("<code>sudo systemctl reload nginx</code>", code_style)],
    ]
    t_mgmt = Table(mgmt_data, colWidths=[180, 324])
    t_mgmt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_mgmt)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Zero-Downtime Code Updates", h2_style))
    story.append(Paragraph(
        "When making updates to your application code in the future, simply run:",
        body_style,
    ))
    code_block_4 = [
        [Paragraph("cd /var/www/campuspulse<br/>"
                   "git pull origin main<br/>"
                   "sudo ./deploy.sh &lt;YOUR_SERVER_IP_OR_DOMAIN&gt;", code_style)]
    ]
    t4 = Table(code_block_4, colWidths=[504])
    t4.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t4)
    story.append(Spacer(1, 14))

    # SECTION 4: REDDIT & COMMUNITY LAUNCH STRATEGY
    story.append(Paragraph("4. Reddit & Developer Community Showcase Copy", h1_style))
    story.append(Paragraph(
        "When sharing CampusPulse on <b>r/webdev</b>, <b>r/Python</b>, <b>r/reactjs</b>, or <b>r/SideProject</b>, "
        "highlight the production engineering depth rather than pitching it as a generic school project:",
        body_style,
    ))

    reddit_callout = [
        [Paragraph(
            "<b>Recommended Reddit Hook:</b><br/>"
            "<i>'Most college complaint portals look like 2004 legacy web apps where tickets disappear into a void. "
            "I spent the last several months building <b>CampusPulse</b> — an enterprise-grade campus operations & "
            "emergency response ecosystem built on FastAPI and React 19.'</i><br/><br/>"
            "<b>Key Technical Talking Points:</b><br/>"
            "• <b>241 Automated Tests (100% Pass Rate):</b> Complete regression coverage verifying RBAC, OTP brute-force capping, sliding session cap, and N+1 aggregation query elimination.<br/>"
            "• <b>Multi-Department Dynamic Routing:</b> Coordinator delegation engine with leave failovers.<br/>"
            "• <b>Step-Up Identity Protection:</b> Anonymous safety reporting with password-gated Admin investigation disclosures.<br/>"
            "• <b>Zero-Lag Real-Time Pipeline:</b> WebSocket push messaging with ping/pong suppression.",
            callout_style,
        )]
    ]
    t_red = Table(reddit_callout, colWidths=[504])
    t_red.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#3B82F6")),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t_red)

    doc.build(story, canvasmaker=NumberedCanvas)
    print("SUCCESS: PDF generated successfully at:", PDF_OUTPUT_PATH)


if __name__ == "__main__":
    build_pdf()
