from pathlib import Path
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle,
    KeepTogether
)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output/booklet"
OUT.mkdir(parents=True, exist_ok=True)
IMG = ROOT / "static/assets/images/fpspa"
LOGO = ROOT / "static/assets/images/fpspa_logo.png"
NAVY = colors.HexColor("#0F2F5F")
BLUE = colors.HexColor("#1F5CA8")
GOLD = colors.HexColor("#FDE339")
INK = colors.HexColor("#24364B")
PALE = colors.HexColor("#EEF3F8")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Kicker", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.5, leading=9, textColor=BLUE, spaceAfter=4, uppercase=True))
styles.add(ParagraphStyle(name="BookTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=24, leading=26, textColor=NAVY, alignment=TA_CENTER, spaceAfter=8))
styles.add(ParagraphStyle(name="H1b", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=18, leading=20, textColor=NAVY, spaceAfter=7))
styles.add(ParagraphStyle(name="H2b", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=14, textColor=NAVY, spaceBefore=6, spaceAfter=4))
styles.add(ParagraphStyle(name="BodyB", parent=styles["BodyText"], fontName="Helvetica", fontSize=9, leading=11.2, textColor=INK, spaceAfter=6))
styles.add(ParagraphStyle(name="Lead", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=10.3, leading=13, textColor=INK, spaceAfter=8))
styles.add(ParagraphStyle(name="BulletB", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.8, leading=11, textColor=INK, leftIndent=10, firstLineIndent=-6, bulletIndent=0, spaceAfter=4))
styles.add(ParagraphStyle(name="CenterB", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.3, leading=12, textColor=INK, alignment=TA_CENTER, spaceAfter=6))

def picture(path, width=111*mm, max_h=58*mm):
    p = Path(path)
    if p.suffix.lower() == ".webp":
        conv = OUT / f"{p.stem}.png"
        if not conv.exists():
            PILImage.open(p).convert("RGB").save(conv)
        p = conv
    im = PILImage.open(p)
    ratio = min(width / im.width, max_h / im.height)
    return Image(str(p), im.width * ratio, im.height * ratio)

def page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 6.5)
    canvas.setFillColor(BLUE)
    canvas.drawCentredString(A5[0]/2, 7*mm, f"FIJI HEAD TEACHERS ASSOCIATION  |  {doc.page}")
    canvas.restoreState()

def p(text, style="BodyB"):
    return Paragraph(text, styles[style])

story = []
story += [Spacer(1, 8*mm), picture(LOGO, 34*mm, 34*mm), Spacer(1, 5*mm),
          p("FIJI HEAD TEACHERS ASSOCIATION", "CenterB"),
          p("Strengthening Primary<br/>School Leadership", "BookTitle"),
          p("<b>A briefing booklet for the Minister for Education</b>", "CenterB"),
          picture(IMG/"conference-leaders.jpg", 111*mm, 52*mm), Spacer(1, 4*mm),
          p("<b>Leadership &nbsp;&bull;&nbsp; Advocacy &nbsp;&bull;&nbsp; Excellence</b>", "CenterB"), PageBreak()]

stats = Table([
    [p("<font color='#FDE339' size='18'><b>735</b></font><br/><font color='white' size='7'><b>HEADS OF SCHOOLS</b></font>", "CenterB"),
     p("<font color='#FDE339' size='18'><b>12</b></font><br/><font color='white' size='7'><b>DISTRICT NETWORKS</b></font>", "CenterB"),
     p("<font color='#FDE339' size='18'><b>43</b></font><br/><font color='white' size='7'><b>YEARS ESTABLISHED</b></font>", "CenterB")]
], colWidths=[37*mm]*3)
stats.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),NAVY),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("BOX",(0,0),(-1,-1),0.3,colors.white),("INNERGRID",(0,0),(-1,-1),0.3,colors.white),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7)]))
story += [p("OUR NATIONAL LEADERSHIP NETWORK", "Kicker"), p("One association. A nationwide voice.", "H1b"),
          p("The Fiji Head Teachers Association (FHTA) connects primary school leaders across Fiji, representing their professional interests and strengthening the leadership that shapes schools, teachers and student outcomes.", "Lead"),
          stats, Spacer(1, 4*mm), p("What FHTA contributes", "H2b")]
for t in ["A trusted channel between Heads of Schools, communities, partners and the Ministry of Education.",
          "Professional learning and peer networks that translate policy into effective school-level practice.",
          "National, divisional and district representation on the issues affecting primary education.",
          "Practical member support, shared resources and timely communication."]:
    story.append(p("• " + t, "BulletB"))
story += [picture(IMG/"principals-audience.webp",111*mm,42*mm), PageBreak()]

story += [p("PURPOSE IN PRACTICE","Kicker"),p("Leading schools. Shaping futures.","H1b"),
          p("FHTA's work is grounded in the daily realities of school leadership. The Association helps Heads of Schools lead teaching and learning, manage people and resources, respond to community needs, and sustain improvement.","Lead"),
          p("Six areas of service","H2b")]
for a,b in [("Advocacy and representation","A coordinated voice at district, divisional and national levels."),
            ("Professional concerns","Support pathways for members facing workplace and leadership issues."),
            ("Professional learning","Workshops, online learning and capacity building."),
            ("Leadership practice","Approaches that strengthen teaching, learning and school operations."),
            ("Collaboration","Peer exchange through area, branch and national networks."),
            ("Ministry partnership","Constructive engagement in education initiatives and policy implementation.")]:
    story.append(p(f"<b><font color='#0F2F5F'>{a}.</font></b> {b}"))
story.append(PageBreak())

story += [p("DIGITAL ASSOCIATION PLATFORM","Kicker"),p("A connected website for public information and member service","H1b"),
          p("The FHTA website combines a public communications channel with secure member and staff services. It gives the Association one place to inform, support, train and connect school leaders.","Lead"),
          picture(IMG/"homepage.png",111*mm,57*mm),p("Three connected experiences","H2b")]
for a,b in [("Public website","Association information, news, events, services, resources, leadership and district coverage."),
            ("Member portal","Profiles, membership status, documents, helpdesk support, representatives and learning."),
            ("Staff operations","Member approvals, publishing, events, resources, support tickets, training, attendance and certificates.")]:
    story.append(p(f"<b><font color='#1F5CA8'>{a} -</font></b> {b}"))
story.append(PageBreak())

story += [p("PROFESSIONAL LEARNING","Kicker"),p("From enrolment to evidence of completion","H1b"),
          p("The training platform supports online, workshop and blended learning. Members move through a clear pathway while staff manage delivery and participation.","Lead"),
          picture(IMG/"district-symposium.webp",111*mm,48*mm)]
for i,t in enumerate(["Browse published courses and select an available schedule.","Enrol, access lessons, resources and learning outcomes.","Complete quizzes and track progress.","Check in at workshops using authenticated QR attendance.","Receive a printable certificate when requirements are met."],1):
    story.append(p(f"<font color='#1F5CA8'><b>{i:02d}</b></font>&nbsp;&nbsp; {t}"))
story.append(PageBreak())

story += [p("SCHOOL LEADERSHIP PRIORITIES","Kicker"),p("Practice for stronger schools","H1b"),
          p("FHTA promotes leadership approaches aligned with the changing needs of learners, teachers and communities.","Lead")]
for a,b in [("Instructional leadership","Keep teaching quality and learning outcomes at the centre."),
            ("Digital integration","Use appropriate technology to improve access, administration and learning."),
            ("Inclusive education","Advance equity, participation and support for every learner."),
            ("Community engagement","Build productive relationships with parents and stakeholders."),
            ("Data-informed decisions","Use evidence for planning, accountability and improvement."),
            ("Student wellbeing","Support learners' safety, belonging and holistic development.")]:
    box=Table([[p(f"<b><font color='#0F2F5F'>{a}</font></b><br/>{b}")]],colWidths=[111*mm])
    box.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PALE),("BOX",(0,0),(-1,-1),0.3,colors.HexColor("#D7E1EC")),("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    story += [box,Spacer(1,2.5*mm)]
story.append(PageBreak())

story += [p("OPPORTUNITY FOR PARTNERSHIP","Kicker"),p("A practical bridge between policy and schools","H1b"),
          p("FHTA is positioned to support effective dialogue and implementation by connecting national priorities with the experience of primary school leaders.","Lead"),p("Partnership opportunities","H2b")]
for t in ["Structured consultation with Heads of Schools before and during major policy initiatives.",
          "Joint professional learning on leadership, curriculum, inclusion, wellbeing and digital transformation.",
          "District-level feedback loops that identify implementation barriers and promising practice early.",
          "Coordinated communication of key notices, resources and opportunities through the FHTA network and portal.",
          "Collaborative recognition of school leadership excellence and innovation."]:
    story.append(p("• "+t,"BulletB"))
story += [Spacer(1,5*mm),p("<font color='#1F5CA8'><b>A SHARED GOAL</b></font>","CenterB"),
          p("<font color='#0F2F5F' size='16'><b>Confident school leaders, supported teachers, and better outcomes for Fiji's children.</b></font>","CenterB"),PageBreak()]

story += [Spacer(1,15*mm),picture(LOGO,38*mm,38*mm),Spacer(1,8*mm),p("FIJI HEAD TEACHERS ASSOCIATION","CenterB"),
          p("A national network for primary<br/>school leadership","BookTitle"),Spacer(1,8*mm),
          p("<b>Connect with FHTA</b><br/><font color='#1F5CA8'>fijiheadteachersassociation@gmail.com</font>","CenterB"),
          Spacer(1,7*mm),p("Website services include news, events, resources, member support, representatives and professional learning.","CenterB"),
          Spacer(1,12*mm),p("<font size='7' color='#6B7C8F'><i>Prepared from the current FHTA website and platform capabilities.</i></font>","CenterB")]

pdf = OUT / "FHTA_Minister_Briefing_Booklet.pdf"
doc = SimpleDocTemplate(str(pdf), pagesize=A5, rightMargin=12*mm,leftMargin=12*mm,topMargin=12*mm,bottomMargin=13*mm, title="FHTA Minister Briefing Booklet", author="Fiji Head Teachers Association")
doc.build(story,onFirstPage=page_number,onLaterPages=page_number)
print(pdf)
