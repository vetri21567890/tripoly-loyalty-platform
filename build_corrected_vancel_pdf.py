from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    NextPageTemplate,
    Spacer,
    Table,
    TableStyle,
)


OUT = Path("Vancel_ZohoPeople_Proposal_corrected.pdf").resolve()

PAGE_W, PAGE_H = A4
LEFT = 22 * mm
RIGHT = 22 * mm
TOP = 24 * mm
BOTTOM = 22 * mm
CONTENT_W = PAGE_W - LEFT - RIGHT

NAVY = colors.HexColor("#163B5C")
TEAL = colors.HexColor("#0E8A94")
LIGHT_TEAL = colors.HexColor("#EAF6F7")
LIGHT_BLUE = colors.HexColor("#EEF4FA")
GRID = colors.HexColor("#B8CAD8")
TEXT = colors.HexColor("#25313B")
MUTED = colors.HexColor("#5E6B75")


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        "CoverKicker",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=TEAL,
        alignment=TA_CENTER,
        spaceAfter=18,
    )
)
styles.add(
    ParagraphStyle(
        "CoverTitle",
        fontName="Helvetica-Bold",
        fontSize=30,
        leading=36,
        textColor=NAVY,
        alignment=TA_CENTER,
        spaceAfter=8,
    )
)
styles.add(
    ParagraphStyle(
        "CoverSub",
        fontName="Helvetica",
        fontSize=15,
        leading=20,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=24,
    )
)
styles.add(
    ParagraphStyle(
        "Meta",
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=TEXT,
        alignment=TA_CENTER,
    )
)
styles.add(
    ParagraphStyle(
        "FooterNote",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=MUTED,
        alignment=TA_CENTER,
    )
)
styles.add(
    ParagraphStyle(
        "SectionTag",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=TEAL,
        spaceAfter=2,
    )
)
styles.add(
    ParagraphStyle(
        "H1",
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=23,
        textColor=NAVY,
        spaceAfter=11,
    )
)
styles.add(
    ParagraphStyle(
        "H2",
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=16,
        textColor=NAVY,
        spaceBefore=8,
        spaceAfter=6,
    )
)
styles.add(
    ParagraphStyle(
        "Body",
        fontName="Helvetica",
        fontSize=9.8,
        leading=14.2,
        textColor=TEXT,
        spaceAfter=7,
    )
)
styles.add(
    ParagraphStyle(
        "Small",
        fontName="Helvetica",
        fontSize=8.4,
        leading=11.5,
        textColor=TEXT,
    )
)
styles.add(
    ParagraphStyle(
        "SmallCenter",
        parent=styles["Small"],
        alignment=TA_CENTER,
    )
)
styles.add(
    ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=8.2,
        leading=10.5,
        textColor=colors.white,
        alignment=TA_CENTER,
    )
)
styles.add(
    ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=8.2,
        leading=10.8,
        textColor=TEXT,
    )
)
styles.add(
    ParagraphStyle(
        "TableCellCenter",
        parent=styles["TableCell"],
        alignment=TA_CENTER,
    )
)
styles.add(
    ParagraphStyle(
        "Note",
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=10.5,
        textColor=MUTED,
    )
)
styles.add(
    ParagraphStyle(
        "Disclaimer",
        fontName="Helvetica",
        fontSize=7.4,
        leading=9.2,
        textColor=MUTED,
    )
)


def p(text, style="Body"):
    return Paragraph(text.replace("\n", "<br/>"), styles[style])


def bullet(text):
    return Paragraph(f"&bull;&nbsp;&nbsp;{text}", styles["Body"])


def table(data, col_widths, header=True, center_cols=()):
    rows = []
    for r_idx, row in enumerate(data):
        out = []
        for c_idx, val in enumerate(row):
            if isinstance(val, Paragraph):
                out.append(val)
            elif r_idx == 0 and header:
                out.append(p(str(val), "TableHeader"))
            elif c_idx in center_cols:
                out.append(p(str(val), "TableCellCenter"))
            else:
                out.append(p(str(val), "TableCell"))
        rows.append(out)
    t = Table(rows, colWidths=col_widths, repeatRows=1 if header else 0, hAlign="LEFT")
    cmd = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY if header else colors.white),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white if header else TEXT),
        ("GRID", (0, 0), (-1, -1), 0.45, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, LIGHT_BLUE]),
    ]
    t.setStyle(TableStyle(cmd))
    return t


def header_footer(canvas, doc):
    canvas.saveState()
    page_no = canvas.getPageNumber() - 1
    canvas.setFillColor(NAVY)
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.drawString(LEFT, PAGE_H - 13 * mm, "VANCEL TECHNOLOGIES PVT. LTD.")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(PAGE_W - RIGHT, PAGE_H - 13 * mm, "Zoho People Implementation Proposal  |  CONFIDENTIAL")
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.5)
    canvas.line(LEFT, PAGE_H - 17 * mm, PAGE_W - RIGHT, PAGE_H - 17 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(LEFT, 10 * mm, "© 2025 Vancel Technologies Pvt. Ltd. | Confidential & Proprietary")
    canvas.drawRightString(PAGE_W - RIGHT, 10 * mm, f"Page {page_no}")
    canvas.restoreState()


def cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(LIGHT_TEAL)
    canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.roundRect(20 * mm, 34 * mm, PAGE_W - 40 * mm, PAGE_H - 68 * mm, 8, stroke=0, fill=1)
    canvas.setStrokeColor(TEAL)
    canvas.setLineWidth(2)
    canvas.line(58 * mm, PAGE_H - 128 * mm, PAGE_W - 58 * mm, PAGE_H - 128 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8.5)
    canvas.drawCentredString(
        PAGE_W / 2,
        45 * mm,
        "This document is prepared for executive review and contains proprietary information.",
    )
    canvas.drawCentredString(
        PAGE_W / 2,
        40 * mm,
        "Unauthorised distribution is strictly prohibited.",
    )
    canvas.restoreState()


def section(num, title):
    return [p(f"SECTION {num:02d}", "SectionTag"), p(title, "H1")]


story = []
story.extend(
    [
        Spacer(1, 117 * mm),
        p("CONFIDENTIAL", "CoverKicker"),
        p("SOLUTION PROPOSAL", "CoverTitle"),
        p("Zoho People HRMS<br/>Implementation & Configuration", "CoverSub"),
        p("Prepared exclusively for<br/><b>Client Organisation</b>", "Meta"),
        Spacer(1, 10 * mm),
        p(
            "Prepared by: <b>Vancel Technologies Pvt. Ltd.</b><br/>"
            "Scope: Zoho People - 50 Users (Scalable)<br/>"
            "Version: 1.0 - Final<br/>"
            "Classification: Confidential<br/>"
            "Date: May 2025",
            "Meta",
        ),
        NextPageTemplate("normal"),
        PageBreak(),
    ]
)

story.extend(
    [
        p("TABLE OF CONTENTS", "H1"),
        p("Document Navigation", "H2"),
        table(
            [
                ["Section", "Title"],
                ["01", "Executive Summary"],
                ["02", "Client Requirements Understanding"],
                ["03", "Proposed Solution Overview"],
                ["04", "Implementation Methodology"],
                ["05", "Deliverables"],
                ["06", "Assumptions & Dependencies"],
                ["07", "Commercial Proposal"],
                ["08", "Annual Maintenance Contract (AMC)"],
                ["09", "Why Vancel Technologies"],
            ],
            [30 * mm, CONTENT_W - 30 * mm],
            center_cols=(0,),
        ),
        PageBreak(),
    ]
)

story.extend(section(1, "Executive Summary"))
story += [
    p(
        "Vancel Technologies Pvt. Ltd. is pleased to present this Solution Proposal for the end-to-end "
        "implementation and configuration of Zoho People, a cloud-based Human Resource Management System "
        "(HRMS), tailored to the operational requirements of your organisation. This proposal addresses the full "
        "scope of HR digitalisation across Employee Profile Management, Onboarding, Leave, Attendance, and "
        "Performance Management functions."
    ),
    p(
        "The proposed solution is architected for an initial deployment of 50 users, with a scalable design that "
        "accommodates future workforce growth without architectural rework. This flexibility ensures that your "
        "investment is protected as your organisation expands. Additional users can be onboarded seamlessly, and "
        "any change in scope, user count, or module requirements will be assessed and proposed transparently with "
        "revised timelines and investment."
    ),
    table(
        [
            ["Parameter", "Details"],
            ["Platform", "Zoho People - Cloud HRMS"],
            ["Initial User Scope", "50 Users (Scalable architecture)"],
            ["Industry Vertical", "Construction - Multi-site Workforce"],
            ["Implementation Duration", "7 Weeks"],
            ["Engagement Model", "Fixed-Scope Implementation"],
            ["Implementation Investment", "USD 3,000"],
            ["Post-Go-Live Support", "Annual Maintenance Contract (AMC)"],
            ["Delivery Methodology", "Phased Implementation"],
        ],
        [56 * mm, CONTENT_W - 56 * mm],
    ),
    Spacer(1, 7),
    p(
        "This engagement is positioned as a strategic technology partnership. Vancel Technologies serves as your "
        "long-term Zoho implementation advisor, ensuring the platform evolves in alignment with your business "
        "growth and operational maturity. Any additional requirements beyond this scope will be scoped, priced, "
        "and delivered as separate engagements."
    ),
    PageBreak(),
]

story.extend(section(2, "Client Requirements Understanding"))
story += [
    p(
        "Vancel Technologies has conducted a detailed review of the client's stated requirements and operational "
        "context. The following summarises our understanding of the business objectives driving this HRMS "
        "implementation initiative."
    ),
    p("2.1 Organisational Context", "H2"),
    p(
        "The client operates within the construction sector, managing a diverse workforce that includes corporate "
        "office personnel, project site employees, and non-desk field workers. This workforce composition demands "
        "an HRMS platform capable of supporting varied attendance models, compliance obligations, and certification "
        "management across geographically dispersed locations."
    ),
    p("2.2 Key Business Drivers", "H2"),
    bullet("Consolidation of fragmented HR data into a unified, auditable digital repository"),
    bullet("Automation of employee lifecycle processes from onboarding through offboarding"),
    bullet("Real-time visibility into leave balances, attendance patterns, and performance metrics"),
    bullet("Compliance with employment regulations and certification renewal requirements"),
    bullet("Mobile-enabled workforce management for site and field-based employees"),
    bullet("Reduction of administrative overhead through employee self-service capabilities"),
    bullet("Scalable HR infrastructure aligned with projected organisational growth"),
    p("2.3 Scope Summary", "H2"),
    table(
        [
            ["#", "Module", "Key Functional Areas"],
            ["1", "Employee Profile Management", "Master records, contracts, documents, IDs, certifications"],
            ["2", "Employee Onboarding", "Workflows, document collection, task checklists, approvals"],
            ["3", "Leave Management", "Policies, types, accruals, calendars, self-service"],
            ["4", "Attendance Management", "Shift management, mobile attendance, field tracking, reports"],
            ["5", "Performance Management", "Goals, review cycles, evaluations, dashboards"],
        ],
        [14 * mm, 58 * mm, CONTENT_W - 72 * mm],
        center_cols=(0,),
    ),
    PageBreak(),
]

story.extend(section(3, "Proposed Solution Overview"))
story += [
    p(
        "The proposed solution leverages Zoho People as the core HRMS platform, deployed on Zoho's enterprise-grade "
        "cloud infrastructure. The architecture is designed around four foundational pillars: Data Centralisation, "
        "Process Automation, Compliance Readiness, and Scalability."
    ),
    p("3.1 Architecture Pillars", "H2"),
    bullet("Data Centralisation: A single source of truth for all employee data, documents, and HR transactions."),
    bullet("Process Automation: Workflow-driven automation for onboarding, approvals, leave, and performance cycles."),
    bullet("Compliance Readiness: Structured tracking for work permits, certifications, and government-issued documents."),
    bullet("Scalability: Platform configured to seamlessly accommodate user growth beyond the initial 50-user base."),
    bullet("Mobile Accessibility: Native mobile app support enabling geo-tagged attendance and self-service for field employees."),
    p("3.2 Scalability Design", "H2"),
    p(
        "The initial implementation is scoped for 50 users. As the workforce grows, additional user licences can be "
        "activated through Zoho's subscription model. Any expansion in scope, whether additional users, new modules, "
        "or enhanced configurations, will be formally assessed and presented with a revised proposal outlining the "
        "revised timeline and investment. This ensures complete commercial transparency at every stage of your "
        "organisation's growth."
    ),
    PageBreak(),
]

story.extend(section(4, "Implementation Methodology"))
story += [
    p(
        "Vancel Technologies employs a structured, phased implementation methodology ensuring predictable delivery, "
        "stakeholder alignment, and knowledge transfer throughout the engagement lifecycle. The total implementation "
        "duration is 7 weeks."
    ),
    table(
        [
            ["Phase", "Activity", "Timeline", "Key Activities"],
            [
                "Phase 1",
                "Discovery & Requirement Validation",
                "Week 1",
                "Stakeholder workshops, HR process documentation, configuration blueprint finalisation, and user access matrix definition.",
            ],
            [
                "Phase 2",
                "Platform Setup & Core Configuration",
                "Weeks 2-3",
                "Organisational hierarchy setup, employee module configuration, leave and attendance policy configuration, role-based access implementation.",
            ],
            [
                "Phase 3",
                "Workflow & Automation Build",
                "Weeks 4-5",
                "Onboarding workflow configuration, approval chain setup, automated notification rules, performance management cycle configuration.",
            ],
            [
                "Phase 4",
                "Testing & UAT",
                "Week 6",
                "User acceptance testing facilitation, issue resolution, report configuration, and dashboard finalisation.",
            ],
            [
                "Phase 5",
                "Training & Go-Live",
                "Week 7",
                "Administrator and end-user training delivery, go-live checklist sign-off, hypercare support, and handover documentation.",
            ],
        ],
        [22 * mm, 46 * mm, 26 * mm, CONTENT_W - 94 * mm],
        center_cols=(0, 2),
    ),
    Spacer(1, 7),
    p(
        "Note: The above timeline is based on the current scope of 50 users across 5 modules. Additional requirements, "
        "expanded scope, or increases in user count will be assessed separately, with revised timelines and investment "
        "communicated transparently.",
        "Note",
    ),
    PageBreak(),
]

story.extend(section(5, "Deliverables"))
story += [
    p("The following deliverables are included within the fixed-scope implementation engagement."),
    table(
        [
            ["#", "Deliverable", "Description"],
            ["1", "Configuration Blueprint", "Documented configuration design covering all modules, workflows, and access controls"],
            ["2", "Configured Zoho People Instance", "Fully configured platform per agreed scope across all 5 modules"],
            ["3", "Workflow Documentation", "Approved workflow diagrams for onboarding, leave, and attendance processes"],
            ["4", "User Acceptance Test Report", "Signed-off UAT report confirming all configured features"],
            ["5", "Administrator Training", "Training session for HR administrators covering system management"],
            ["6", "End-User Training", "Training materials and session for employee self-service capabilities"],
            ["7", "Go-Live Sign-Off Report", "Formal go-live confirmation document with post-launch checklist"],
            ["8", "Knowledge Transfer Document", "Post-implementation operations guide for the internal HR team"],
        ],
        [13 * mm, 57 * mm, CONTENT_W - 70 * mm],
        center_cols=(0,),
    ),
    PageBreak(),
]

story.extend(section(6, "Assumptions & Dependencies"))
story += [
    p(
        "The following assumptions underpin the commercial and timeline commitments in this proposal. Vancel "
        "Technologies reserves the right to review scope and commercial terms in the event of material deviations."
    ),
    bullet("The implementation scope is based on an initial deployment of 50 users. Any increase in user count or scope will be separately assessed with revised timelines and investment."),
    bullet("The client will provide a designated Project Coordinator with authority to provide timely sign-offs, approvals, and stakeholder access throughout the engagement."),
    bullet("Zoho People SaaS licences are procured separately by the client or through Vancel Technologies as a Zoho Partner. Licence costs are not included in the implementation fee."),
    bullet("Employee data for import will be provided by the client in Zoho-standard Excel templates within agreed timelines. Data preparation and cleansing responsibilities rest with the client."),
    bullet("Any additional requirements identified post-commencement that fall outside this defined scope will be subject to a separate change request and revised commercial proposal."),
    bullet("A stable internet connection and compatible hardware (desktop/mobile) are available to all users prior to go-live."),
    bullet("Client sign-offs and feedback will be provided within 2 business days at each phase milestone."),
    bullet("This proposal is valid for a period of 30 days from the date of issuance."),
    PageBreak(),
]

story.extend(section(7, "Commercial Proposal"))
story += [
    p("7.1 Implementation Investment", "H2"),
    p(
        "The following represents the fixed-price investment for the complete Zoho People implementation as defined "
        "within this proposal for 50 users. This is an all-inclusive, fixed-scope engagement fee. Any additional "
        "scope, modules, or user count beyond 50 will be assessed and presented as a revised proposal."
    ),
    table(
        [
            ["Description", "Scope", "Investment"],
            ["Zoho People Implementation & Configuration", "All 5 modules - 50 users (scalable architecture)", "USD 3,000"],
            ["Total Implementation Fee", "", "USD 3,000"],
        ],
        [62 * mm, 75 * mm, CONTENT_W - 137 * mm],
        center_cols=(2,),
    ),
    p("7.2 Payment Schedule", "H2"),
    table(
        [
            ["Milestone", "Trigger Condition", "%", "Amount (USD)"],
            ["Advance Payment", "Upon contract execution", "50%", "USD 1,500"],
            ["Configuration Milestone", "Completion of all module configurations and client sign-off", "30%", "USD 900"],
            ["Go-Live Milestone", "Successful platform go-live and UAT sign-off", "20%", "USD 600"],
            ["Total", "", "100%", "USD 3,000"],
        ],
        [44 * mm, 78 * mm, 22 * mm, CONTENT_W - 144 * mm],
        center_cols=(2, 3),
    ),
    Spacer(1, 7),
    p(
        "Note: All payments are due within 5 business days of the respective milestone trigger. Zoho People SaaS "
        "subscription costs are billed separately by Zoho and are not included herein. All pricing is exclusive of "
        "applicable taxes.",
        "Note",
    ),
    PageBreak(),
]

story.extend(section(8, "Annual Maintenance Contract (AMC)"))
story += [
    p(
        "Following successful go-live, Vancel Technologies offers structured Annual Maintenance Contract plans to "
        "ensure continued platform optimisation, HR process enhancement, and proactive support. AMC engagement "
        "ensures your Zoho People instance evolves in step with your organisational requirements."
    ),
    p("8.1 AMC Plan Comparison", "H2"),
    table(
        [
            ["Feature", "Standard Plan", "Enhanced Plan", "Premium Plan"],
            ["Monthly Support Allocation", "20 Hours/Month", "40 Hours/Month", "60 Hours/Month"],
            ["Monthly Investment", "INR 40,000", "INR 80,000", "INR 1,20,000"],
            ["Configuration Updates", "Yes", "Yes", "Yes"],
            ["Workflow Enhancements", "Yes", "Yes", "Yes"],
            ["Report Modifications", "Yes", "Yes", "Yes"],
            ["Training Assistance", "Yes", "Yes", "Yes"],
            ["Best-Practice Guidance", "Yes", "Yes", "Yes"],
            ["New Module Onboarding", "Advisory", "Included", "Included"],
            ["Support Response Time", "Within 5 Business Hours", "Within 5 Business Hours", "Within 5 Business Hours"],
            ["Add-On Hours Available", "Yes", "Yes", "Yes"],
            ["Recommended For", "Stable, steady-state operations", "Growing or evolving teams", "High-growth or complex environments"],
        ],
        [49 * mm, 38 * mm, 38 * mm, CONTENT_W - 125 * mm],
        center_cols=(1, 2, 3),
    ),
    p("8.2 AMC Terms & Conditions", "H2"),
    bullet("AMC covers support, configuration updates, workflow enhancements, report modifications, training assistance, and best-practice advisory."),
    bullet("Monthly support allocations are non-cumulative and expire at month-end if unused."),
    bullet("Should monthly support requirements exceed the subscribed plan allocation, additional support may be arranged through mutually agreed add-on hours."),
    bullet("All add-on work must be formally approved by the client prior to execution."),
    bullet("All support requests will receive an initial response within 5 business hours of logging."),
    bullet("AMC is invoiced monthly in advance and commences from the go-live date."),
    bullet("AMC plans may be upgraded at any time with 30 days written notice. Downgrade requires 60 days notice."),
    PageBreak(),
]

story.extend(section(9, "Why Vancel Technologies"))
story += [
    p(
        "Vancel Technologies is a specialised enterprise technology solutions firm with deep expertise in Zoho "
        "ecosystem implementations across industry verticals including construction, manufacturing, logistics, and "
        "professional services. We are positioned not merely as a technology vendor, but as a strategic HR "
        "transformation partner."
    ),
    table(
        [
            ["Differentiator", "What This Means for You"],
            ["Zoho Implementation Expertise", "Certified team with deep functional knowledge of Zoho People and the broader Zoho One suite."],
            ["Construction Industry Context", "Proven experience configuring HRMS for blended workforces including site, office, and field personnel."],
            ["Fixed-Price Delivery Model", "Full implementation transparency - fixed scope, fixed price, no billing surprises."],
            ["Scalable Architecture Thinking", "Every configuration decision is made with future growth in mind."],
            ["Post-Implementation Partnership", "Structured AMC options ensure continuous optimisation and platform evolution."],
            ["End-to-End Accountability", "Single point of accountability from discovery through go-live and beyond."],
        ],
        [58 * mm, CONTENT_W - 58 * mm],
    ),
    Spacer(1, 12),
    p(
        "<b>DISCLAIMER:</b> This proposal document and its contents are confidential and intended solely for the named "
        "recipient organisation. The commercial terms, implementation approach, and technical specifications contained "
        "herein are proprietary to Vancel Technologies Pvt. Ltd. and may not be reproduced, distributed, or disclosed "
        "to any third party without prior written consent. All pricing is exclusive of applicable taxes. Zoho People "
        "software licencing costs are separate and subject to Zoho's current pricing schedule.",
        "Disclaimer",
    ),
    Spacer(1, 8),
    p("© 2025 Vancel Technologies Pvt. Ltd. All rights reserved.", "Disclaimer"),
]


doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=LEFT, rightMargin=RIGHT, topMargin=TOP, bottomMargin=BOTTOM)
main_frame = Frame(LEFT, BOTTOM + 6 * mm, CONTENT_W, PAGE_H - TOP - BOTTOM - 11 * mm, id="main")
cover_frame = Frame(LEFT, BOTTOM, CONTENT_W, PAGE_H - TOP - BOTTOM, id="cover")
doc.addPageTemplates(
    [
        PageTemplate(id="cover", frames=[cover_frame], onPage=cover),
        PageTemplate(id="normal", frames=[main_frame], onPage=header_footer),
    ]
)

doc.build(story)
print(OUT)
