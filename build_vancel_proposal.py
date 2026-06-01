from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


OUT = "Vancel_Enterprise_Lead_Management_AI_Transformation_Proposal.docx"

NAVY = RGBColor(11, 37, 69)
BLUE = RGBColor(46, 116, 181)
DARK_BLUE = RGBColor(31, 77, 120)
LIGHT_BLUE = "EAF2FB"
MID_BLUE = "D9EAF7"
PALE = "F4F7FB"
WHITE = "FFFFFF"
GRAY = RGBColor(86, 96, 112)
BLACK = RGBColor(25, 31, 38)
BORDER = "C8D3E0"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=120, start=140, bottom=120, end=140):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for m, v in [("top", top), ("start", start), ("bottom", bottom), ("end", end)]:
        node = tc_mar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(v))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table, color=BORDER, size="6"):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = f"w:{edge}"
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def set_table_width(table, widths):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:type"), "dxa")
    tbl_w.set(qn("w:w"), str(sum(widths)))

    tbl_ind = tbl_pr.find(qn("w:tblInd"))
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:type"), "dxa")
    tbl_ind.set(qn("w:w"), "120")

    grid = tbl.tblGrid
    if grid is None:
        grid = OxmlElement("w:tblGrid")
        tbl.insert(0, grid)
    for child in list(grid):
        grid.remove(child)
    for width in widths:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(width))
        grid.append(col)

    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            cell.width = Pt(widths[idx] / 20)
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:type"), "dxa")
            tc_w.set(qn("w:w"), str(widths[idx]))
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)


def mark_header_row(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = tr_pr.find(qn("w:tblHeader"))
    if tbl_header is None:
        tbl_header = OxmlElement("w:tblHeader")
        tr_pr.append(tbl_header)
    tbl_header.set(qn("w:val"), "true")


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("Page ")
    field_begin = OxmlElement("w:fldChar")
    field_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    field_end = OxmlElement("w:fldChar")
    field_end.set(qn("w:fldCharType"), "end")
    run._r.append(field_begin)
    run._r.append(instr)
    run._r.append(field_end)
    for r in paragraph.runs:
        r.font.name = "Calibri"
        r.font.size = Pt(9)
        r.font.color.rgb = GRAY


def add_hyperlink(paragraph, text, url):
    part = paragraph.part
    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    new_run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "2E74B5")
    r_pr.append(color)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    r_pr.append(underline)
    new_run.append(r_pr)
    text_node = OxmlElement("w:t")
    text_node.text = text
    new_run.append(text_node)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)


def set_run(run, size=None, color=None, bold=None, italic=None):
    run.font.name = "Calibri"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    if size is not None:
        run.font.size = Pt(size)
    if color is not None:
        run.font.color.rgb = color
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def paragraph(text="", style=None, bold=False, color=None, size=None, align=None, before=0, after=8):
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    if align is not None:
        p.alignment = align
    if text:
        r = p.add_run(text)
        set_run(r, size=size, color=color or BLACK, bold=bold)
    return p


def h1(text):
    return paragraph(text, "Heading 1")


def h2(text):
    return paragraph(text, "Heading 2")


def h3(text):
    return paragraph(text, "Heading 3")


def bullet(text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(4)
    for run in p.runs:
        set_run(run)
    r = p.add_run(text)
    set_run(r, size=10.5, color=BLACK)
    return p


def numbered(text):
    p = doc.add_paragraph(style="List Number")
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    set_run(r, size=10.5, color=BLACK)
    return p


def make_table(headers, rows, widths, header_fill=LIGHT_BLUE, font_size=9.2):
    table = doc.add_table(rows=1, cols=len(headers))
    set_table_width(table, widths)
    set_table_borders(table)
    mark_header_row(table.rows[0])
    hdr = table.rows[0].cells
    for i, text in enumerate(headers):
        set_cell_shading(hdr[i], header_fill)
        p = hdr[i].paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(text)
        set_run(r, size=9.2, bold=True, color=NAVY)
    for row in rows:
        cells = table.add_row().cells
        for i, text in enumerate(row):
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(text))
            set_run(r, size=font_size, color=BLACK)
    paragraph("", after=6)
    return table


def callout(label, body, fill=PALE):
    table = doc.add_table(rows=1, cols=1)
    set_table_width(table, [9360])
    set_table_borders(table, color="D5E0EA")
    mark_header_row(table.rows[0])
    cell = table.cell(0, 0)
    set_cell_shading(cell, fill)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(label)
    set_run(r, size=10.5, bold=True, color=NAVY)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    r2 = p2.add_run(body)
    set_run(r2, size=10.2, color=BLACK)
    paragraph("", after=6)


def set_document_styles(doc):
    sec = doc.sections[0]
    sec.page_width = Inches(8.5)
    sec.page_height = Inches(11)
    sec.top_margin = Inches(1)
    sec.bottom_margin = Inches(1)
    sec.left_margin = Inches(1)
    sec.right_margin = Inches(1)
    sec.header_distance = Inches(0.492)
    sec.footer_distance = Inches(0.492)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Calibri"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    normal.font.size = Pt(11)
    normal.font.color.rgb = BLACK
    normal.paragraph_format.space_after = Pt(8)
    normal.paragraph_format.line_spacing = 1.333

    for name, size, color, before, after in [
        ("Heading 1", 16, BLUE, 18, 10),
        ("Heading 2", 13, BLUE, 12, 6),
        ("Heading 3", 12, DARK_BLUE, 8, 4),
    ]:
        st = styles[name]
        st.font.name = "Calibri"
        st._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
        st._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = color
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True

    for name in ["List Bullet", "List Number"]:
        st = styles[name]
        st.font.name = "Calibri"
        st.font.size = Pt(10.5)
        st.paragraph_format.left_indent = Inches(0.375)
        st.paragraph_format.first_line_indent = Inches(-0.194)
        st.paragraph_format.space_after = Pt(4)
        st.paragraph_format.line_spacing = 1.208


def setup_footer(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.text = ""
    r = p.add_run("Vancel Technologies Pvt. Ltd. | Confidential Proposal")
    set_run(r, size=8.5, color=GRAY)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p2 = footer.add_paragraph()
    add_page_number(p2)


doc = Document()
set_document_styles(doc)
setup_footer(doc.sections[0])

# Cover page
paragraph("VANCEL TECHNOLOGIES PVT. LTD.", bold=True, size=12, color=BLUE, align=WD_ALIGN_PARAGRAPH.CENTER, after=20)
paragraph(
    "Enterprise Lead Management, Calling Automation, WhatsApp Automation & AI Transformation Platform",
    bold=True,
    size=25,
    color=NAVY,
    align=WD_ALIGN_PARAGRAPH.CENTER,
    after=10,
)
paragraph(
    "A consulting-led proposal for CRM foundation, communication automation, and practical AI transformation.",
    size=13,
    color=GRAY,
    align=WD_ALIGN_PARAGRAPH.CENTER,
    after=24,
)
make_table(
    ["Prepared By", "Organization"],
    [
        ["Vetri Murugan\nChief Solutions Architect", "Vancel Technologies Pvt. Ltd."],
        ["Company Website", "www.vanceltech.com"],
        ["Document Purpose", "Client submission proposal for enterprise lead management and AI-enabled growth systems"],
        ["Date", "June 2026"],
    ],
    [3300, 6060],
    header_fill=MID_BLUE,
    font_size=10,
)
callout(
    "Proposal Intent",
    "This proposal is designed as a business transformation engagement, not a software implementation exercise. The program is structured to improve lead conversion, reduce manual effort, create reliable management visibility, and establish a scalable foundation for future AI agents.",
    fill=LIGHT_BLUE,
)
paragraph("Prepared for client review and PDF generation.", size=10, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, after=0)
doc.add_page_break()

# TOC
h1("Table of Contents")
toc_items = [
    "Executive Summary",
    "Understanding of Business Requirements",
    "Recommended Solution Approach",
    "Proposed Technology Stack",
    "Solution Architecture",
    "Phase-wise Implementation Approach",
    "Project Timeline",
    "Commercial Proposal",
    "Software & Platform Costs",
    "Data & CRM Structure Required",
    "Support & Handover Approach",
    "Training & Documentation",
    "Relevant Experience & Case Studies",
    "Why Vancel Technologies",
    "Assumptions & Dependencies",
    "Recommended Next Steps",
]
for idx, item in enumerate(toc_items, 1):
    paragraph(f"{idx}. {item}", size=10.5, color=BLACK, after=3)
doc.add_page_break()

h1("Executive Summary")
paragraph(
    "Vancel Technologies proposes to design and implement a scalable enterprise lead management ecosystem that integrates CRM, telecalling workflows, WhatsApp engagement, automation, reporting, and practical AI capabilities. The objective is to create a high-visibility operating system for sales, telecalling, operations, and management stakeholders.",
)
callout(
    "Executive Recommendation",
    "The engagement should be executed as a phased transformation program: first stabilizing the CRM foundation, then automating communication workflows, and finally introducing AI-enabled productivity and intelligence layers.",
)
paragraph("The platform will enable:")
for item in [
    "Lead capture and structured lead management",
    "Lead qualification, scoring, and ownership governance",
    "Duplicate lead prevention and bad lead identification",
    "Telecalling workflows with call logging and disposition tracking",
    "WhatsApp automation for engagement, reminders, and nurturing",
    "Sales process automation, reporting, dashboards, and management controls",
    "AI-assisted lead management with a roadmap toward future agentic workflows",
]:
    bullet(item)
paragraph(
    "The focus is not software configuration alone. The broader objective is business transformation: increased lead conversion, reduced manual effort, stronger operational discipline, better customer response quality, and a scalable growth system that can expand with the organization.",
)

h1("Understanding of Business Requirements")
paragraph(
    "Based on the stated requirements, the business requires an integrated lead operating model that can manage high-volume lead flow, reduce leakage, enforce follow-up discipline, and create reliable visibility across the full revenue pipeline."
)
make_table(
    ["Business Need", "Observed Requirement", "Transformation Outcome"],
    [
        ["Lead lifecycle control", "Structured stages, status mapping, source tracking, ownership, and follow-ups", "Clear pipeline governance and reduced lead leakage"],
        ["Lead quality management", "Qualification rules, bad lead identification, duplicate checks, and DNC handling", "Improved sales focus and cleaner CRM data"],
        ["Telecalling productivity", "Call logging, call disposition, callback scheduling, and escalation workflows", "Higher agent productivity and measurable calling outcomes"],
        ["WhatsApp engagement", "Consent management, reminders, nurturing workflows, and communication tracking", "Consistent engagement with reduced manual messaging"],
        ["Management visibility", "Dashboards, reports, conversion analytics, and operational KPIs", "Data-led decision-making and predictable review cadence"],
        ["AI readiness", "AI lead classification, call summaries, recommendations, and productivity automation", "Practical AI adoption with a path toward agentic applications"],
    ],
    [1900, 3940, 3520],
)

h1("Recommended Solution Approach")
paragraph(
    "Vancel recommends a three-layer enterprise architecture. This creates rapid go-live value while ensuring that future automation and AI investments are built on clean data, governed processes, and measurable business outcomes."
)
make_table(
    ["Strategic Layer", "Core Capabilities", "Business Value"],
    [
        ["Layer 1: CRM Foundation", "Lead lifecycle management, lead qualification, lead ownership, follow-up automation, reporting", "Creates process discipline and establishes one source of truth"],
        ["Layer 2: Communication Layer", "Telephony integration, call tracking, callback scheduling, WhatsApp automation, lead nurturing", "Improves speed-to-lead, follow-up consistency, and engagement visibility"],
        ["Layer 3: Intelligence Layer", "AI lead qualification, AI call summaries, AI recommendations, AI CRM updates, agentic workflows, future AI voice automation", "Reduces manual work and enables intelligent revenue operations"],
    ],
    [2100, 3800, 3460],
)
callout(
    "Implementation Principle",
    "The program will be phased to allow rapid go-live while creating a scalable enterprise foundation. Phase 2 planning and requirement workshops will begin during Phase 1 to reduce implementation delays.",
)

h1("Proposed Technology Stack")
paragraph(
    "The final technology stack should be confirmed after discovery, user analysis, and integration feasibility review. The following stack is recommended as the working baseline."
)
make_table(
    ["Domain", "Recommended Platforms", "Role in Solution"],
    [
        ["CRM & Business Process", "Zoho CRM, Zoho Flow, Zoho Analytics, Zoho Desk (optional)", "CRM foundation, workflow orchestration, reporting, and optional support/service desk capabilities"],
        ["Telephony", "Exotel or Tata Tele Business Services", "Calling, call logs, call dispositions, recordings where applicable, and callback workflows"],
        ["WhatsApp", "Interakt, Gallabox, or Gupshup", "WhatsApp Business API messaging, templates, journeys, consent, and engagement tracking"],
        ["AI Layer", "Zoho AI, Zoho AI Agents, OpenAI models if required, custom agentic applications", "AI-assisted classification, summaries, recommendations, productivity automation, and future agents"],
    ],
    [1900, 3100, 4360],
)

h1("Solution Architecture")
paragraph(
    "The proposed architecture connects lead capture channels, CRM governance, communication systems, automation workflows, analytics, and AI productivity services into a single operating model."
)
make_table(
    ["Architecture Layer", "Representative Components", "Key Controls"],
    [
        ["Lead Capture & Intake", "Website forms, landing pages, campaigns, imports, partner lists, offline sources", "Source attribution, deduplication, validation, consent capture"],
        ["CRM Core", "Zoho CRM leads, contacts, deals, activities, tasks, ownership rules", "Lifecycle stages, status mapping, assignment rules, mandatory fields"],
        ["Communication Automation", "Telephony connector, WhatsApp API, callbacks, reminders, escalation journeys", "Disposition governance, communication logs, opt-in/opt-out controls"],
        ["Analytics & Management", "Zoho Analytics dashboards, CRM reports, conversion funnels, team performance views", "KPI definitions, access control, management cadence"],
        ["AI & Agentic Layer", "AI classification, call summaries, next-action recommendations, future agents", "Human oversight, prompt governance, outcome measurement, usage monitoring"],
    ],
    [2100, 4020, 3240],
)

h1("Phase-wise Implementation Approach")
h2("Phase 1: CRM Foundation")
make_table(
    ["Timeline", "Investment", "Scope", "Outcome"],
    [[
        "2 Months",
        "INR 4,20,000",
        "CRM architecture design; lead stage creation; lead status mapping; lead disposition framework; lead qualification process; duplicate lead detection; bad lead identification; DNC management; lead assignment rules; follow-up automation; lead source tracking; dashboard creation; reporting framework; sales process mapping; documentation; user training; data migration.",
        "Fully operational CRM ecosystem.",
    ]],
    [1300, 1500, 5160, 1400],
    font_size=8.7,
)
h2("Phase 2: Communication Automation Layer")
make_table(
    ["Timeline", "Investment", "Scope", "Outcome"],
    [[
        "1.5 Months",
        "INR 2,50,000",
        "Telephony integration; call logging; call disposition workflows; callback scheduling; escalation workflows; WhatsApp integration; consent management; lead nurturing workflows; reminder automation; follow-up journeys; communication tracking.",
        "Complete communication automation layer.",
    ]],
    [1300, 1500, 5160, 1400],
    font_size=8.7,
)
callout(
    "Parallel Planning",
    "Planning and requirement workshops for Phase 2 will begin during Phase 1 itself. This will help accelerate implementation, reduce handoff delays, and keep the overall program timeline efficient.",
)
h2("Phase 3: AI Transformation Layer")
make_table(
    ["Timeline", "Investment", "Scope", "Outcome"],
    [[
        "2 Months",
        "INR 1,00,000",
        "AI lead classification; AI call summaries; AI CRM updates; AI next action recommendations; AI productivity automation; AI reporting enhancements.",
        "Initial practical AI implementation layer using Zoho AI capabilities.",
    ]],
    [1300, 1500, 5160, 1400],
    font_size=8.7,
)
paragraph(
    "Phase 3 focuses on practical AI implementation using Zoho AI capabilities. The investment above includes only the initial AI implementation layer. Additional AI agents and custom agentic applications can be introduced after a deeper understanding of business processes, user behavior, data quality, and operating metrics."
)
make_table(
    ["Potential Future AI Agents", "Indicative Purpose"],
    [
        ["AI Sales Agents", "Assist sales users with next best actions, follow-up drafting, and opportunity prioritization"],
        ["AI Lead Qualification Agents", "Assess inbound lead quality using defined business rules and contextual signals"],
        ["AI Lead Nurturing Agents", "Recommend or execute personalized engagement journeys under approved governance"],
        ["AI Operations Agents", "Monitor process exceptions, missing updates, delayed tasks, and data quality issues"],
        ["AI Management Agents", "Summarize performance trends and surface management-level insights"],
        ["AI Revenue Optimization Agents", "Identify conversion bottlenecks, source performance trends, and revenue opportunities"],
        ["AI Voice Agents", "Enable future AI voice automation where commercially and operationally viable"],
    ],
    [3000, 6360],
)
paragraph(
    "Vancel has already designed and implemented agentic applications and AI-driven business solutions across multiple industries, giving the team practical experience in turning AI concepts into business workflows."
)

h1("Project Timeline")
make_table(
    ["Phase", "Duration", "Primary Focus", "Notes"],
    [
        ["Phase 1", "2 Months", "CRM foundation and reporting", "Foundation design, configuration, migration, training, and go-live"],
        ["Phase 2", "1.5 Months", "Telephony and WhatsApp automation", "Requirement planning starts during Phase 1 to reduce delays"],
        ["Phase 3", "2 Months", "Initial AI implementation layer", "Practical AI capabilities with roadmap for future agents"],
        ["Total Program Duration", "Approximately 5-6 Months", "CRM + communication + AI transformation", "Parallel planning activities will be used to reduce overall timelines wherever feasible"],
    ],
    [1800, 1800, 3000, 2760],
)

h1("Commercial Proposal")
make_table(
    ["Phase", "Investment", "Commercial Description"],
    [
        ["Phase 1: CRM Foundation", "INR 4,20,000", "Enterprise CRM architecture, lead governance, automation, reporting, migration, documentation, and training"],
        ["Phase 2: Communication Automation", "INR 2,50,000", "Telephony, call workflows, WhatsApp automation, consent, reminders, nurturing, and communication tracking"],
        ["Phase 3: AI Transformation Layer", "INR 1,00,000", "Initial AI lead classification, summaries, CRM updates, recommendations, and reporting enhancements"],
        ["Total Investment", "INR 7,50,000", "Total professional services investment for the proposed phased program"],
    ],
    [2600, 1900, 4860],
)
h2("Payment Milestones")
make_table(
    ["Milestone", "Payment", "Trigger"],
    [
        ["Engagement Kickoff", "30%", "On project confirmation and kickoff"],
        ["Phase 1 Configuration Review", "25%", "On completion of CRM architecture, lead structure, and core workflow review"],
        ["Phase 2 Communication Layer Review", "25%", "On completion of telephony and WhatsApp automation review"],
        ["Final Go-live and Handover", "20%", "On completion of Phase 3, documentation, training, and handover"],
    ],
    [2900, 1800, 4660],
)

h1("Software & Platform Costs")
paragraph(
    "Software subscriptions, usage charges, licenses, telephony charges, WhatsApp API fees, AI consumption, SMS charges if applicable, and third-party integration costs are separate from the professional services investment."
)
make_table(
    ["Cost Category", "Indicative Cost / Basis", "Notes"],
    [
        ["Zoho One - Monthly", "Approx. INR 2,500 per user/month", "Exact pricing depends on plan, billing model, taxes, and Zoho commercial terms"],
        ["Zoho One - Annual", "Approx. INR 1,200-1,300 per user/month effective cost", "Subject to plan, commitment, and current licensing terms"],
        ["Telephony", "As per Exotel or Tata Tele Business Services pricing", "Includes calling usage, numbers, recordings, and platform-specific charges where applicable"],
        ["WhatsApp API", "As per Interakt, Gallabox, Gupshup, and Meta conversation charges", "Depends on message category, templates, conversation volume, and provider plan"],
        ["AI Consumption", "As per Zoho AI / OpenAI / provider usage", "Depends on model, usage volume, token consumption, and automation design"],
        ["Third-party Integrations", "As applicable", "Any connector, API, custom middleware, or platform-specific charges will be confirmed after discovery"],
    ],
    [2200, 2700, 4460],
)
callout("Licensing Recommendation", "Final licensing recommendation will be provided after discovery, user count confirmation, integration review, and commercial validation.")

h1("Data & CRM Structure Required")
make_table(
    ["Data / Input Required", "Details Needed from Client", "Purpose"],
    [
        ["Lead database", "Existing lead lists, field structure, source data, status values, and historical conversion information", "Migration, deduplication, and lead structure design"],
        ["Existing CRM", "Current CRM access, module structure, users, workflows, reports, and export files if available", "Current-state assessment and migration planning"],
        ["Team structure", "Sales, telecalling, operations, management, roles, and reporting lines", "User hierarchy, access control, and ownership rules"],
        ["User hierarchy", "Manager-agent mapping, territories, teams, branches, or business units", "Assignment, escalation, and visibility design"],
        ["Lead sources", "Campaigns, website forms, channels, partners, referrals, imports, events, and offline sources", "Source tracking and ROI reporting"],
        ["Telecalling process", "Call scripts, dispositions, callback rules, escalation paths, and productivity metrics", "Telephony workflow design"],
        ["WhatsApp process", "Templates, consent logic, opt-out handling, journey rules, and communication expectations", "WhatsApp automation and compliance design"],
        ["Reporting requirements", "Management KPIs, operational dashboards, conversion metrics, team metrics, and review cadence", "Dashboard and analytics design"],
        ["Existing tools", "Current software, spreadsheets, forms, telephony, WhatsApp providers, and campaign platforms", "Integration feasibility and migration planning"],
        ["Qualification criteria", "Good lead criteria, bad lead criteria, scoring rules, DNC logic, and disqualification reasons", "Lead scoring, classification, and quality controls"],
    ],
    [2300, 4200, 2860],
    font_size=8.9,
)

h1("Support & Handover Approach")
paragraph(
    "Vancel will ensure that the client team can operate, administer, and continuously improve the implemented system after go-live. Handover will include process walkthroughs, documentation, admin knowledge transfer, and stabilization support."
)
h2("Monthly Retainer Plans")
make_table(
    ["Plan", "Included Hours", "Monthly Retainer", "Best Fit"],
    [
        ["Essential Support", "20 Hours", "INR 35,000", "Light post-go-live support, minor changes, issue handling, and advisory assistance"],
        ["Growth Support", "40 Hours", "INR 75,000", "Ongoing optimization, dashboards, workflow improvements, integrations, and user support"],
        ["Transformation Support", "60 Hours", "INR 1,10,000", "High-touch support for continuous automation, AI workflow refinement, analytics, and process improvements"],
    ],
    [1900, 1600, 1900, 3960],
)

h1("Training & Documentation")
paragraph("The implementation will be supported by structured enablement for users, administrators, and management stakeholders.")
for item in [
    "User manuals for CRM usage, lead updates, follow-ups, call dispositions, and WhatsApp workflows",
    "Admin manuals covering configuration logic, key workflows, user roles, and governance controls",
    "Workflow documentation for lead stages, qualification rules, automation triggers, and escalation paths",
    "Recorded training sessions for sales, telecalling, operations, and management users",
    "Knowledge transfer sessions for client administrators and internal champions",
    "Go-live support to assist users during transition and early adoption",
]:
    bullet(item)

h1("Relevant Experience & Case Studies")
paragraph(
    "Vancel Technologies brings cross-industry experience in CRM transformation, automation, and AI-enabled business systems. The leadership team has delivered 15+ business transformation projects across business process redesign, CRM implementation, workflow automation, and AI-powered productivity systems."
)
make_table(
    ["Industry Experience", "Relevant Capabilities Delivered"],
    [
        ["Staffing & Recruitment", "Lead automation, candidate pipeline tracking, calling workflows, CRM dashboards"],
        ["Travel", "Inquiry management, WhatsApp engagement, follow-up automation, conversion reporting"],
        ["Healthcare", "Patient lead workflows, appointment follow-ups, operational dashboards, process automation"],
        ["Logistics", "Operational tracking, customer communication automation, exception reporting"],
        ["Real Estate", "Lead nurturing, telecalling automation, source tracking, sales dashboards"],
        ["SaaS", "CRM transformation, onboarding workflows, lifecycle reporting, automation design"],
        ["Professional Services", "Pipeline management, client communication workflows, management reporting"],
    ],
    [3000, 6360],
)
paragraph(
    "Relevant solution themes include lead automation, call automation, WhatsApp automation, lead nurturing, CRM transformation, AI-powered workflows, and agentic applications."
)

h1("Why Vancel Technologies")
callout(
    "Positioning",
    "Vancel Technologies is not a software implementation agency. Vancel helps organizations increase revenue, improve lead conversion, reduce manual effort, optimize operations, and build scalable business systems using CRM, AI, automation, ERP systems, and agentic applications.",
    fill=LIGHT_BLUE,
)
paragraph(
    "Every engagement is approached as a long-term business transformation initiative. Vancel treats clients' businesses as its own and continuously identifies opportunities where technology can create measurable business value."
)
make_table(
    ["Differentiator", "Client Value"],
    [
        ["Consulting-led delivery", "Business process, governance, and adoption are designed alongside software configuration"],
        ["CRM + automation depth", "Ability to connect lead operations, calling, WhatsApp, analytics, and workflow automation"],
        ["AI transformation capability", "Practical AI implementation with a roadmap toward agentic applications and future voice automation"],
        ["Industry-relevant experience", "Experience across staffing, travel, healthcare, logistics, real estate, SaaS, and professional services"],
        ["Long-term partnership mindset", "Focus on measurable improvement, continuous optimization, and business outcomes"],
    ],
    [2700, 6660],
)

h1("Assumptions & Dependencies")
for item in [
    "Client will provide timely access to Zoho, telephony, WhatsApp provider accounts, existing data, and relevant business users.",
    "Client will nominate process owners and decision makers for requirement validation, user acceptance, and go-live approvals.",
    "Data quality, source availability, and current system export formats may affect migration effort and timeline.",
    "Third-party platform limitations, API availability, provider commercials, and approval timelines may affect delivery sequencing.",
    "WhatsApp templates, consent management, and communication use cases must comply with applicable provider and regulatory policies.",
    "AI outputs will be deployed with appropriate human oversight, especially for recommendations, classification, and customer-facing workflows.",
    "Any scope beyond the listed deliverables, including advanced custom applications or additional AI agents, will be estimated separately.",
]:
    bullet(item)

h1("Recommended Next Steps")
paragraph("Vancel recommends the following immediate next steps to move from proposal to execution.")
for item in [
    "Confirm commercial approval and engagement start date.",
    "Conduct discovery workshop with sales, telecalling, operations, and management stakeholders.",
    "Finalize platform stack, user count, licensing model, and integration priorities.",
    "Collect data samples, lead source details, CRM exports, call dispositions, and reporting requirements.",
    "Sign off Phase 1 solution blueprint, implementation plan, and governance cadence.",
    "Begin Phase 1 CRM foundation implementation while initiating Phase 2 planning workshops in parallel.",
]:
    numbered(item)
callout(
    "Closing Note",
    "Vancel Technologies is prepared to partner with the client team to build a scalable lead management, communication automation, and AI transformation platform that supports immediate operational needs and long-term growth.",
)

p = paragraph("", after=0)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("www.vanceltech.com")
set_run(r, size=10.5, color=BLUE, bold=True)
paragraph("Prepared By: Vetri Murugan, Chief Solutions Architect, Vancel Technologies Pvt. Ltd.", size=9.5, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, after=0)

doc.save(OUT)
print(OUT)
