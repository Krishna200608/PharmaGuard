"""
PharmaGuard Capstone Presentation Deck Builder
==============================================
Generates a publication-grade, 16:9 widescreen PowerPoint slide deck (.pptx)
for the 7th-Semester Capstone Defense before Dr. Nikhilanand Arya (IIIT Allahabad).

Follows strictly the presentation-deck-builder skill:
- 16:9 widescreen (13.333" x 7.5")
- Type-led hierarchy, disciplined color palette
- Dense, aligned multi-card layouts with metric hero numbers
- Covers all 20 slides from docs/presentation/End_Semester_Slide_Content.md

Output: docs/presentation/PharmaGuard_Defense_Deck.pptx
"""
import sys
from pathlib import Path
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ── Color Palette Definitions ──────────────────────────────────────────
NAVY_DARK = RGBColor(15, 23, 42)       # #0F172A (Primary Title Dark)
NAVY_HEADER = RGBColor(30, 41, 59)     # #1E293B (Cards / Headers)
BLUE_ACCENT = RGBColor(37, 99, 235)    # #2563EB (Hero numbers / Primary)
BLUE_LIGHT = RGBColor(239, 246, 255)   # #EFF6FF (Card subtle background)
GREEN_ACCENT = RGBColor(22, 101, 52)   # #166534 (Escalated signal / True Positive)
GREEN_BG = RGBColor(240, 253, 244)     # #F0FDF4
AMBER_ACCENT = RGBColor(180, 83, 9)    # #B45309 (Warning / Confounding)
AMBER_BG = RGBColor(254, 243, 199)     # #FEF3C7
SLATE_TEXT = RGBColor(51, 65, 85)      # #334155 (Body text)
MUTED_TEXT = RGBColor(100, 116, 139)   # #64748B (Subtitles / metadata)
WHITE = RGBColor(255, 255, 255)
BG_LIGHT = RGBColor(248, 250, 252)     # #F8FAFC (Slide canvas)
BORDER_GRAY = RGBColor(226, 232, 240)  # #E2E8F0 (Card outline)


def create_deck() -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def add_base_slide(prs: Presentation, category: str, title: str, slide_num: int, total_slides: int = 20) -> pptx.slide.Slide:
    """Add a standard light-canvas slide with consistent header and footer."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Canvas background
    bg_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = BG_LIGHT
    bg_shape.line.color.rgb = BG_LIGHT

    # Category Pill / Super-title
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.3))
    tf_cat = cat_box.text_frame
    tf_cat.word_wrap = True
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = category.upper()
    p_cat.font.name = "Arial"
    p_cat.font.size = Pt(10.5)
    p_cat.font.bold = True
    p_cat.font.color.rgb = BLUE_ACCENT

    # Slide Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.68), Inches(11.7), Inches(0.6))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = title
    p_t.font.name = "Arial"
    p_t.font.size = Pt(21)
    p_t.font.bold = True
    p_t.font.color.rgb = NAVY_DARK

    # Top hairline divider
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.32), Inches(11.733), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = BORDER_GRAY
    line.line.color.rgb = BORDER_GRAY

    # Footer
    foot_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.1), Inches(11.7), Inches(0.3))
    tf_f = foot_box.text_frame
    p_f = tf_f.paragraphs[0]
    p_f.text = f"PharmaGuard · Capstone Defense 2026–27 · Group 07 (IIIT Allahabad)                                              Slide {slide_num} of {total_slides}"
    p_f.font.name = "Arial"
    p_f.font.size = Pt(9.5)
    p_f.font.color.rgb = MUTED_TEXT

    return slide


def add_card(slide, left: float, top: float, width: float, height: float, bg_color=WHITE, border_color=BORDER_GRAY):
    """Add a card container rectangle."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1)
    return card


def build_slide_1(prs):
    """Slide 1: Title & Project Identity (Dark Navy Theme)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = NAVY_DARK
    bg.line.color.rgb = NAVY_DARK

    # Badge
    badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.0), Inches(4.8), Inches(0.38))
    badge.fill.solid()
    badge.fill.fore_color.rgb = RGBColor(30, 58, 138)
    badge.line.color.rgb = BLUE_ACCENT
    tb_b = badge.text_frame
    p_b = tb_b.paragraphs[0]
    p_b.text = "B.TECH 7TH-SEMESTER CAPSTONE DEFENSE (2026–27)"
    p_b.font.name = "Arial"
    p_b.font.size = Pt(10)
    p_b.font.bold = True
    p_b.font.color.rgb = RGBColor(191, 219, 254)
    p_b.alignment = PP_ALIGN.CENTER

    # Main Title
    tbox = slide.shapes.add_textbox(Inches(1.0), Inches(1.6), Inches(11.3), Inches(1.8))
    tf = tbox.text_frame
    tf.word_wrap = True
    p1 = tf.paragraphs[0]
    p1.text = "PharmaGuard: Intelligent Pharmacovigilance Signal Triage Orchestrator"
    p1.font.name = "Arial"
    p1.font.size = Pt(28)
    p1.font.bold = True
    p1.font.color.rgb = WHITE

    p2 = tf.add_paragraph()
    p2.text = "A Tool-Grounded, Tri-Source Evidence Fusion Agent for Postmarketing Adverse Drug Event Triage"
    p2.font.name = "Arial"
    p2.font.size = Pt(16)
    p2.font.color.rgb = RGBColor(148, 163, 184)
    p2.space_before = Pt(8)

    # 3 Cards for Team, Supervisor, Department
    c1 = add_card(slide, 1.0, 3.8, 3.6, 2.7, bg_color=NAVY_HEADER, border_color=RGBColor(51, 65, 85))
    tf1 = c1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "STUDENT INVESTIGATORS (GROUP 07)"
    p.font.name = "Arial"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT
    items = [
        ("Krishna Sikheriya", "IIT2023139 (Team Leader)"),
        ("Lokesh Bawariya", "IIT2023138"),
        ("Naitik Jain", "IIB2023036"),
    ]
    for name, roll in items:
        p_n = tf1.add_paragraph()
        p_n.text = f"• {name}"
        p_n.font.name = "Arial"
        p_n.font.size = Pt(12)
        p_n.font.bold = True
        p_n.font.color.rgb = WHITE
        p_n.space_before = Pt(4)
        p_r = tf1.add_paragraph()
        p_r.text = f"   Roll No: {roll}"
        p_r.font.name = "Arial"
        p_r.font.size = Pt(10)
        p_r.font.color.rgb = RGBColor(148, 163, 184)

    c2 = add_card(slide, 4.85, 3.8, 3.6, 2.7, bg_color=NAVY_HEADER, border_color=RGBColor(51, 65, 85))
    tf2 = c2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "FACULTY SUPERVISOR"
    p.font.name = "Arial"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT
    p_sup = tf2.add_paragraph()
    p_sup.text = "Dr. Nikhilanand Arya"
    p_sup.font.name = "Arial"
    p_sup.font.size = Pt(14)
    p_sup.font.bold = True
    p_sup.font.color.rgb = WHITE
    p_sup.space_before = Pt(8)
    p_des = tf2.add_paragraph()
    p_des.text = "Assistant Professor\nDepartment of Information Technology\nIndian Institute of Information Technology, Allahabad"
    p_des.font.name = "Arial"
    p_des.font.size = Pt(11)
    p_des.font.color.rgb = RGBColor(148, 163, 184)
    p_des.space_before = Pt(4)

    c3 = add_card(slide, 8.7, 3.8, 3.6, 2.7, bg_color=NAVY_HEADER, border_color=RGBColor(51, 65, 85))
    tf3 = c3.text_frame
    tf3.word_wrap = True
    p = tf3.paragraphs[0]
    p.text = "CORE VALIDATION STATS"
    p.font.name = "Arial"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT
    stats = [
        ("165 Pairs", "Across 3 Stratified Cohorts"),
        ("100% Precision", "Zero False Alarms in Strict Gating"),
        ("242 Tests", "Passing Automated Pytest Suite"),
    ]
    for top_t, sub_t in stats:
        p_s1 = tf3.add_paragraph()
        p_s1.text = top_t
        p_s1.font.name = "Arial"
        p_s1.font.size = Pt(13)
        p_s1.font.bold = True
        p_s1.font.color.rgb = RGBColor(52, 211, 153)
        p_s1.space_before = Pt(4)
        p_s2 = tf3.add_paragraph()
        p_s2.text = sub_t
        p_s2.font.name = "Arial"
        p_s2.font.size = Pt(10)
        p_s2.font.color.rgb = RGBColor(148, 163, 184)


def build_slide_2(prs):
    """Slide 2: Background & Clinical Motivation."""
    slide = add_base_slide(prs, "1. Background & Motivation", "The Pharmacovigilance Bottleneck & Clinician Alert Fatigue", 2)
    # Left Hero Card (The Clinical Reality)
    c1 = add_card(slide, 0.8, 1.5, 5.7, 5.3)
    tf1 = c1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "THE POSTMARKETING SURVEILLANCE DILEMMA"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT

    points = [
        ("Pre-Approval Trials are Blind to Rare Events:", "Randomized trials enroll small, homogeneous cohorts (thousands). Rare, delayed, or idiosyncratic adverse drug reactions (ADRs) only emerge when medications reach millions of real-world patients."),
        ("Spontaneous Reporting is Massive but Noisy:", "Postmarketing databases like US FDA FAERS receive millions of spontaneous reports annually. The data is noisy, heavily under-reported, and confounded by polypharmacy and baseline disease."),
        ("Severe Healthcare & Human Burden:", "Adverse drug events represent a leading cause of preventable patient morbidity, hospitalizations, and tens of billions in direct healthcare expenditures annually."),
    ]
    for h, b in points:
        p_h = tf1.add_paragraph()
        p_h.text = f"• {h}"
        p_h.font.size = Pt(12)
        p_h.font.bold = True
        p_h.font.color.rgb = NAVY_DARK
        p_h.space_before = Pt(12)
        p_b = tf1.add_paragraph()
        p_b.text = b
        p_b.font.size = Pt(11)
        p_b.font.color.rgb = SLATE_TEXT

    # Right Column: The Triage Crisis
    c2 = add_card(slide, 6.8, 1.5, 5.7, 5.3)
    tf2 = c2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "THE ACUTE COGNITIVE TRIAGE BOTTLENECK"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = AMBER_ACCENT

    triage_points = [
        ("Manual Review Cannot Scale:", "Safety teams face thousands of potential drug-event associations weekly. Manually cross-referencing FAERS, pharmacodynamics, and literature takes hours per candidate."),
        ("Clinician Alert Fatigue Hazard:", "Ungrounded automated systems trigger pervasive false alarms. Clinicians routinely override 49% to 96% of drug safety alerts, rendering warnings ineffective."),
        ("The Asymmetric Cost of Error:", "False Positives waste critical regulatory review resources; False Negatives leave severe, preventable patient harm unmonitored at national scale."),
        ("The Core Mission:", "Automate the triage funnel to classify signals into ESCALATE, MONITOR, or DO_NOT_ESCALATE with provable safety gating and zero false alarms."),
    ]
    for h, b in triage_points:
        p_h = tf2.add_paragraph()
        p_h.text = f"• {h}"
        p_h.font.size = Pt(12)
        p_h.font.bold = True
        p_h.font.color.rgb = NAVY_DARK
        p_h.space_before = Pt(10)
        p_b = tf2.add_paragraph()
        p_b.text = b
        p_b.font.size = Pt(11)
        p_b.font.color.rgb = SLATE_TEXT


def build_slide_3(prs):
    """Slide 3: Introduction: What PharmaGuard Is & What Makes It Different."""
    slide = add_base_slide(prs, "2. Introduction", "What PharmaGuard Is & What Distinguishes It", 3)
    # 3 Pillar Cards
    cards_data = [
        ("TRI-SOURCE EVIDENCE FUSION", BLUE_ACCENT, [
            ("FAERS Spontaneous Disproportionality:", "Calculates PRR, ROR, and Woolf 95% CI floors from live FDA postmarketing records (Weight: 0.40)."),
            ("ChEMBL Receptor Pharmacology:", "Examines molecular target mechanisms of action for biological plausibility (Weight: 0.20)."),
            ("PubMed Clinical Literature Grading:", "Automates E-utilities retrieval and epidemiological evidence grading (Weight: 0.40)."),
        ]),
        ("PUBLIC BIOMEDICAL APIS ONLY", GREEN_ACCENT, [
            ("Zero EHR Data Lock-In:", "Unlike recent causal AI frameworks (e.g., Toonsi 2026), PharmaGuard requires zero restricted Electronic Health Record data (e.g., MIMIC-IV or UK Biobank)."),
            ("100% Open-Access & Reproducible:", "Operates entirely over open FDA, ChEMBL, and PubMed APIs with zero licensing or institutional data governance barriers."),
            ("Auditable & Verifiable:", "Every decision is fully reproducible with pre-registered deterministic rules and persistent SHA-256 caching."),
        ]),
        ("OVERCOMING LLM FAILURE MODES", NAVY_DARK, [
            ("Eliminating Hallucinated Confidence:", "Replaces arbitrary LLM self-reported confidence with closed-form mathematical score calculation."),
            ("Resolving Regulatory Confusion:", "Prevents models from conflating past historical regulatory investigations with confirmed clinical harm (e.g., Liraglutide)."),
            ("Adversarial Mechanistic Critic:", "Detects and counterfactually penalizes LLM parametric memory leakage of regulatory warnings (MARCH pattern)."),
        ]),
    ]
    for i, (title, color, items) in enumerate(cards_data):
        c = add_card(slide, 0.8 + i * 3.95, 1.5, 3.8, 5.3)
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = color
        for h, b in items:
            ph = tf.add_paragraph()
            ph.text = f"• {h}"
            ph.font.size = Pt(11.5)
            ph.font.bold = True
            ph.font.color.rgb = NAVY_DARK
            ph.space_before = Pt(12)
            pb = tf.add_paragraph()
            pb.text = b
            pb.font.size = Pt(10.5)
            pb.font.color.rgb = SLATE_TEXT


def build_slide_4(prs):
    """Slide 4: Current Clinical & Regulatory Standard."""
    slide = add_base_slide(prs, "3. Clinical Baseline", "Current Regulatory Standards & Quantitative Disproportionality", 4)
    # Left Box: 2x2 Contingency Table
    c1 = add_card(slide, 0.8, 1.5, 5.7, 5.3)
    tf1 = c1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "THE 2 × 2 CONTINGENCY TABLE STANDARD"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT

    p_t = tf1.add_paragraph()
    p_t.text = "Classical quantitative signal detection compares adverse event counts against background reporting rates across all FDA FAERS submissions:"
    p_t.font.size = Pt(11)
    p_t.font.color.rgb = SLATE_TEXT
    p_t.space_before = Pt(8)

    formulas = [
        ("Proportional Reporting Ratio (PRR, Evans et al. 2001):",
         "PRR = [a / (a + b)] / [c / (c + d)]\nWhere a = reports with Drug X and Event Y; b = reports with Drug X and other events; c = reports with other drugs and Event Y; d = all other reports."),
        ("Reporting Odds Ratio (ROR, van Puijenbroek et al. 2002):",
         "ROR = (a / c) / (b / d) = (a · d) / (b · c)\nAsymptotic standard error: SE(ln ROR) = √(1/a + 1/b + 1/c + 1/d)."),
        ("Standard Regulatory Screening Gate:",
         "Standard criteria for candidate signal generation:\nPRR ≥ 2.0,  Report Count n ≥ 3,  χ² ≥ 4.0,  95% CI_lower > 1.0."),
    ]
    for h, b in formulas:
        ph = tf1.add_paragraph()
        ph.text = f"• {h}"
        ph.font.size = Pt(11.5)
        ph.font.bold = True
        ph.font.color.rgb = NAVY_DARK
        ph.space_before = Pt(10)
        pb = tf1.add_paragraph()
        pb.text = b
        pb.font.size = Pt(10.5)
        pb.font.color.rgb = SLATE_TEXT

    # Right Box: Core Limitations
    c2 = add_card(slide, 6.8, 1.5, 5.7, 5.3)
    tf2 = c2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "LIMITATIONS OF THE CLASSICAL STANDARD"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = AMBER_ACCENT

    lims = [
        ("Purely Correlational & Mechanistically Blind:", "A high PRR demonstrates mathematical co-occurrence, but cannot evaluate whether a drug's receptor pharmacology provides a plausible biological mechanism."),
        ("Vulnerable to Confounding by Indication:", "Symptoms of the underlying disease treated (e.g., kidney failure in diabetics, heart attacks in hypertensive patients) are falsely flagged as adverse drug effects."),
        ("Vulnerable to Polypharmacy Bias:", "Widely co-prescribed drugs (e.g., Metformin + Insulin) register severe false disproportionality signals due to companion drugs."),
        ("Denominator Dilution on Chronic Blockbusters (§31):", "Widely prescribed chronic therapies (e.g., Amlodipine, SSRIs) have massive reporting denominators, diluting true signals into the 1.1–1.9 range below static thresholds."),
    ]
    for h, b in lims:
        ph = tf2.add_paragraph()
        ph.text = f"• {h}"
        ph.font.size = Pt(11.5)
        ph.font.bold = True
        ph.font.color.rgb = NAVY_DARK
        ph.space_before = Pt(10)
        pb = tf2.add_paragraph()
        pb.text = b
        pb.font.size = Pt(10.5)
        pb.font.color.rgb = SLATE_TEXT


def build_slide_5(prs):
    """Slide 5: Problem Statement & Engineering Objectives."""
    slide = add_base_slide(prs, "4. Problem & Objectives", "Problem Statement & Four Core Engineering Objectives", 5)
    # Quote Card for Problem Statement
    c_q = add_card(slide, 0.8, 1.5, 11.7, 1.7, bg_color=BLUE_LIGHT, border_color=BLUE_ACCENT)
    tf_q = c_q.text_frame
    tf_q.word_wrap = True
    p = tf_q.paragraphs[0]
    p.text = "REVISED PROBLEM STATEMENT (DECISIONS.md §34.5)"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT
    p_body = tf_q.add_paragraph()
    p_body.text = '"PharmaGuard is a lightweight, publicly-reproducible multi-agent framework for postmarketing adverse drug event triage that fuses real-time FAERS disproportionality statistics, ChEMBL target pharmacology, and PubMed clinical literature grading through deterministic safety-gated escalation logic. The system incorporates disease/indication-context reasoning via public WHO ATC classification to stratify and evaluate signal interpretation across multiple therapeutic areas without requiring restricted EHR data."'
    p_body.font.size = Pt(11)
    p_body.font.color.rgb = NAVY_DARK
    p_body.space_before = Pt(4)

    # 4 Column Objectives
    objs = [
        ("1. Deterministic Multi-Source Fusion", "Combine FAERS disproportionality, ChEMBL pharmacology, and PubMed clinical grading via closed-form linear weighting (0.40 / 0.20 / 0.40) rather than uncalibrated generative language models."),
        ("2. Hard Safety Gating (Gate 1)", "Enforce an unyielding empirical safety rule: FAERS NO_SIGNAL strictly forces DO_NOT_ESCALATE, preventing literature speculation from ever generating false alarms."),
        ("3. Public Disease-Context Reasoning", "Characterize indication confounding and channeling bias using open WHO ATC ontologies resolved via ChEMBL, providing causal grounding without restricted clinical databases."),
        ("4. Multi-Scale Empirical Validation", "Validate across 3 standardized benchmark cohorts (15 Core + 50 Blockbusters + 100 OMOP = 165 pairs) with exact Wilson score 95% confidence intervals and dual strict/lenient validation."),
    ]
    for i, (h, b) in enumerate(objs):
        c = add_card(slide, 0.8 + i * 2.95, 3.4, 2.85, 3.4)
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = f"OBJECTIVE #{i+1}"
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = BLUE_ACCENT
        ph = tf.add_paragraph()
        ph.text = h
        ph.font.size = Pt(11.5)
        ph.font.bold = True
        ph.font.color.rgb = NAVY_DARK
        ph.space_before = Pt(6)
        pb = tf.add_paragraph()
        pb.text = b
        pb.font.size = Pt(10)
        pb.font.color.rgb = SLATE_TEXT
        pb.space_before = Pt(6)


def build_slide_6(prs):
    """Slide 6: Literature Review Evolution: 3 Generations of PV."""
    slide = add_base_slide(prs, "5. Related Literature", "Literature Evolution: Three Generations of Pharmacovigilance", 6)
    gens = [
        ("GENERATION 1 (1998–2009)", "Classical Statistical Disproportionality", BLUE_ACCENT, [
            ("Key Citations:", "Bate 1998 (BCPNN), Evans 2001 (PRR), van Puijenbroek 2002 (ROR), Bate & Evans 2009."),
            ("Core Methodology:", "2 × 2 contingency tables, Empirical Bayes shrinkage, frequentist odds ratios."),
            ("Boundary / Bottleneck:", "Fast and public, but blind to biology; highly susceptible to reporting biases and confounding."),
        ]),
        ("GENERATION 2 (2012–2023)", "Unimodal ML & NLP on Clinical Records", AMBER_ACCENT, [
            ("Key Citations:", "Harpaz 2012, Vilar 2014, Coste 2023 (systematic review of 101 studies)."),
            ("Core Methodology:", "Supervised classification, clinical note text mining, patient EHR feature engineering."),
            ("Boundary / Bottleneck:", "Improved feature extraction, but locked behind restricted hospital EHRs; opaque black-box models."),
        ]),
        ("GENERATION 3 (2023–2026)", "Multi-Agent & Foundation Model PV", GREEN_ACCENT, [
            ("Key Citations:", "Yao 2023 (ReAct), Omar 2025 (LLM vulnerabilities), DruGagent 2025, Toonsi 2026 (Bioinformatics)."),
            ("Core Methodology:", "Conversational LLMs, autonomous tool calling, causal knowledge graphs over UK Biobank."),
            ("Boundary / Bottleneck:", "Uncalibrated generative confidence (Omar 2025) or dependency on massive restricted cohorts (Toonsi 2026)."),
        ]),
    ]
    for i, (tag, title, color, items) in enumerate(gens):
        c = add_card(slide, 0.8 + i * 3.95, 1.5, 3.8, 3.8)
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = tag
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = color
        ph = tf.add_paragraph()
        ph.text = title
        ph.font.size = Pt(12)
        ph.font.bold = True
        ph.font.color.rgb = NAVY_DARK
        ph.space_before = Pt(4)
        for sub_h, sub_b in items:
            p_sh = tf.add_paragraph()
            p_sh.text = f"• {sub_h}"
            p_sh.font.size = Pt(10.5)
            p_sh.font.bold = True
            p_sh.font.color.rgb = NAVY_DARK
            p_sh.space_before = Pt(8)
            p_sb = tf.add_paragraph()
            p_sb.text = sub_b
            p_sb.font.size = Pt(10)
            p_sb.font.color.rgb = SLATE_TEXT

    # Bottom Full-Width Positioning Banner
    c_bot = add_card(slide, 0.8, 5.5, 11.7, 1.3, bg_color=NAVY_HEADER, border_color=BLUE_ACCENT)
    tf_b = c_bot.text_frame
    tf_b.word_wrap = True
    p = tf_b.paragraphs[0]
    p.text = "PHARMAGUARD'S STRATEGIC RESEARCH POSITIONING"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = RGBColor(147, 197, 253)
    p_desc = tf_b.add_paragraph()
    p_desc.text = "PharmaGuard occupies the vital missing intersection: a lightweight, disease-context-aware agent that delivers causal-grade auditability and epistemic defenses (Adversarial Critic, Indication Concordance) using strictly public open APIs (FAERS, ChEMBL, PubMed)—achieving regulatory safety guarantees without hospital EHR data lock-in."
    p_desc.font.size = Pt(11)
    p_desc.font.color.rgb = WHITE
    p_desc.space_before = Pt(4)


def build_slide_7(prs):
    """Slide 7: Identified Research Gaps."""
    slide = add_base_slide(prs, "6. Research Gaps", "Identified Research Gaps in Contemporary Pharmacovigilance", 7)
    gaps = [
        ("GAP 1: INDICATION CONFOUNDING IS NEGLECTED", AMBER_ACCENT, [
            ("Empirical Literature Evidence:", "A comprehensive systematic review of 101 signal detection studies (Coste et al. 2023, Pharmacoepidemiol Drug Saf) revealed that only 10 of 101 studies (9.9%) addressed confounding by indication or reported stratified performance."),
            ("Clinical Impact:", "Adverse events resulting from the treated disease are routinely misattributed to the therapy, distorting postmarketing risk evaluation."),
            ("PharmaGuard Solution:", "Pre-registered 7-rule IndicationConcordance cascade mapping WHO ATC classes to MedDRA events."),
        ]),
        ("GAP 2: STATIC DISPROPORTIONALITY THRESHOLDS FAIL (§31)", BLUE_ACCENT, [
            ("Empirical Discovery:", "PharmaGuard's OMOP pilot revealed that static PRR ≥ 2.0 thresholds systematically fail on widely-prescribed chronic medications (Amlodipine, SSRIs, Nifedipine)."),
            ("The Mathematical Mechanism:", "Massive prescribing volume inflates the reporting denominator, compressing true signals into the 1.1–1.9 range despite thousands of reports and significant lower 95% CIs."),
            ("PharmaGuard Solution:", "Formulated and evaluated alternative CI-based signal detection gates (Evans et al. 2001)."),
        ]),
        ("GAP 3: CAUSAL PV DEPENDS ON RESTRICTED EHRS", GREEN_ACCENT, [
            ("Data Accessibility Barrier:", "State-of-the-art causal knowledge graph frameworks (e.g., Toonsi et al. 2026, Bioinformatics) require patient-level Electronic Health Records (MIMIC-IV, UK Biobank)."),
            ("Regulatory & Reproducibility Impact:", "Restricted data prevents independent peer replication and deployment in resource-constrained environments."),
            ("PharmaGuard Solution:", "Grounded entirely on public biomedical APIs (openFDA, ChEMBL, NCBI E-utilities)."),
        ]),
    ]
    for i, (title, color, items) in enumerate(gaps):
        c = add_card(slide, 0.8 + i * 3.95, 1.5, 3.8, 5.3)
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = color
        for h, b in items:
            ph = tf.add_paragraph()
            ph.text = f"• {h}"
            ph.font.size = Pt(11.5)
            ph.font.bold = True
            ph.font.color.rgb = NAVY_DARK
            ph.space_before = Pt(12)
            pb = tf.add_paragraph()
            pb.text = b
            pb.font.size = Pt(10.5)
            pb.font.color.rgb = SLATE_TEXT


def build_slide_8(prs):
    """Slide 8: Datasets, Reference Sets & Benchmark Standards."""
    slide = add_base_slide(prs, "7. Benchmark Datasets", "Multi-Tiered Benchmark Cohorts (N = 165 Evaluated Pairs)", 8)
    cohorts = [
        ("CORE BENCHMARK (15 PAIRS)", "Primary Golden Reference Standard", BLUE_ACCENT, [
            ("7 Confirmed Positives:", "Established regulatory signals backed by FDA Boxed Warnings & clinical trials (Montelukast, Ciprofloxacin, Clozapine, Rosiglitazone)."),
            ("5 Genuine Negative Controls:", "Formally investigated and dismissed signals or monotherapy controls (Metformin, Liraglutide, Atorvastatin/Dementia)."),
            ("3 Zero-Report Edge Cases:", "Zero FAERS reports to verify hard safety gate short-circuiting (Albuterol, Amoxicillin, Adalimumab)."),
        ]),
        ("TOP PRESCRIBED BLOCKBUSTERS (50 PAIRS)", "Real-World Outpatient Safety Cohort", GREEN_ACCENT, [
            ("25 Boxed Warning Positives:", "Highest-mortality Boxed Warnings across Statins, ACEi/ARBs, Antibiotics, Antidepressants, Opioids, Anticonvulsants."),
            ("25 Balanced Negative Controls:", "Widely prescribed outpatient therapies paired with safe outcomes to test clinical specificity."),
            ("Real-World Practice Focus:", "Evaluates everyday outpatient prescribing safety with 100% offline Ollama inference."),
        ]),
        ("OMOP EXPANDED REFERENCE (100 PAIRS)", "OHDSI Gold-Standard Organ Toxicity Set", NAVY_DARK, [
            ("50 Positives + 50 Negatives:", "Established reference set from Ryan et al. 2013 (Drug Safety, Apache 2.0 license)."),
            ("4 Severe Organ-Failure Phenotypes:", "Acute Myocardial Infarction, Acute Liver Injury, Acute Kidney Injury, Upper GI Bleeding."),
            ("Chronic Dilution Testbed:", "Demonstrated the empirical PRR denominator dilution phenomenon across chronic therapies."),
        ]),
    ]
    for i, (tag, title, color, items) in enumerate(cohorts):
        c = add_card(slide, 0.8 + i * 3.95, 1.5, 3.8, 4.3)
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = tag
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = color
        ph = tf.add_paragraph()
        ph.text = title
        ph.font.size = Pt(12)
        ph.font.bold = True
        ph.font.color.rgb = NAVY_DARK
        ph.space_before = Pt(4)
        for sub_h, sub_b in items:
            p_sh = tf.add_paragraph()
            p_sh.text = f"• {sub_h}"
            p_sh.font.size = Pt(11)
            p_sh.font.bold = True
            p_sh.font.color.rgb = NAVY_DARK
            p_sh.space_before = Pt(8)
            p_sb = tf.add_paragraph()
            p_sb.text = sub_b
            p_sb.font.size = Pt(10)
            p_sb.font.color.rgb = SLATE_TEXT

    # Bottom Open-Science Banner
    c_bot = add_card(slide, 0.8, 6.0, 11.7, 0.85, bg_color=GREEN_BG, border_color=GREEN_ACCENT)
    tf_b = c_bot.text_frame
    tf_b.word_wrap = True
    p = tf_b.paragraphs[0]
    p.text = "100% PUBLIC DOMAIN & OPEN ACCESS LICENSING DISCIPLINE (NOTICE.md)"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = GREEN_ACCENT
    p_desc = tf_b.add_paragraph()
    p_desc.text = "All data derives from public FDA records, ChEMBL (CC BY-SA 3.0), and OHDSI (Apache 2.0). Zero MedDRA MSSO proprietary licensing dependencies; fully reproducible worldwide."
    p_desc.font.size = Pt(10.5)
    p_desc.font.color.rgb = NAVY_DARK


def build_slide_9(prs):
    """Slide 9: System Architecture: Tri-Source Evidence Fusion & Gating."""
    slide = add_base_slide(prs, "8. System Architecture", "Tri-Source Evidence Fusion & Deterministic Safety Gating", 9)
    # 3 Streams Cards
    streams = [
        ("STREAM 1: openFDA FAERS", "Weight: 0.40", BLUE_ACCENT, [
            ("2 × 2 Disproportionality:", "Calculates PRR, ROR, and Woolf 95% log-confidence interval floors."),
            ("Discrete Strength Tiers:", "STRONG (1.00), MODERATE (0.66), WEAK (0.33), NO_SIGNAL (0.00)."),
            ("Woolf Fallthrough Gate:", "Downgrades tier if lower 95% CI < 1.0/1.5/2.0 to guard against small-sample instability."),
        ]),
        ("STREAM 2: ChEMBL Target MoA", "Weight: 0.20", NAVY_HEADER, [
            ("Molecular Pharmacology:", "Queries receptor mechanism of action (MoA) via ChEMBL API v34."),
            ("Plausibility Scoring:", "HIGH (0.90), MODERATE (0.50), LOW (0.00) based on biological pathway connection."),
            ("Blinded MoA Authoring:", "MoA authoring strictly blind to adverse event to eliminate circular reasoning (§1.1)."),
        ]),
        ("STREAM 3: NCBI PubMed", "Weight: 0.40", GREEN_ACCENT, [
            ("Automated Abstract Fetch:", "NCBI E-utilities API fetches peer-reviewed clinical abstracts."),
            ("Standardized Rubric (v1.0):", "Grade A (1.00: RCT/OR/HR w/ 95% CI), Grade B (0.50: Case reports), Grade C (0.00: Negative)."),
            ("Zero String-Matching:", "Semantic LLM grading cached by rubric prompt version."),
        ]),
    ]
    for i, (tag, sub, color, items) in enumerate(streams):
        c = add_card(slide, 0.8 + i * 3.95, 1.5, 3.8, 3.6)
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = tag
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = color
        p_sub = tf.add_paragraph()
        p_sub.text = sub
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = MUTED_TEXT
        for h, b in items:
            ph = tf.add_paragraph()
            ph.text = f"• {h}"
            ph.font.size = Pt(10.5)
            ph.font.bold = True
            ph.font.color.rgb = NAVY_DARK
            ph.space_before = Pt(6)
            pb = tf.add_paragraph()
            pb.text = b
            pb.font.size = Pt(9.5)
            pb.font.color.rgb = SLATE_TEXT

    # Bottom Formula & Gating Card
    c_bot = add_card(slide, 0.8, 5.3, 11.7, 1.55, bg_color=WHITE, border_color=BLUE_ACCENT)
    tf_b = c_bot.text_frame
    tf_b.word_wrap = True
    p = tf_b.paragraphs[0]
    p.text = "CLOSED-FORM COMPOSITE CONFIDENCE & DETERMINISTIC DECISION RULES"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT

    p_f = tf_b.add_paragraph()
    p_f.text = "Confidence = 0.40 · S_FAERS + 0.40 · S_PubMed + 0.20 · S_ChEMBL"
    p_f.font.size = Pt(13)
    p_f.font.bold = True
    p_f.font.color.rgb = NAVY_DARK
    p_f.space_before = Pt(3)

    p_rules = tf_b.add_paragraph()
    p_rules.text = "• Gate 1 (Hard Empirical Stop): If FAERS == NO_SIGNAL ⇒ Immediately force DO_NOT_ESCALATE (overrides high literature or plausibility).\n• ESCALATE: Confidence ≥ 0.70 AND FAERS ≥ MODERATE   |   MONITOR: Confidence ≥ 0.35   |   DO_NOT_ESCALATE: Otherwise."
    p_rules.font.size = Pt(10.5)
    p_rules.font.color.rgb = SLATE_TEXT
    p_rules.space_before = Pt(3)


def build_slide_10(prs):
    """Slide 10: Deep-Dive #1: Disease-Context Reasoning Architecture."""
    slide = add_base_slide(prs, "9. Deep-Dive #1", "Disease-Context Reasoning Engine (DiseaseContextTool)", 10)
    # Left Card: Taxonomy Resolution
    c1 = add_card(slide, 0.8, 1.5, 5.7, 5.3)
    tf1 = c1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "WHO ATC ONTOLOGICAL TAXONOMY RESOLUTION"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT

    points = [
        ("The Biological Challenge:", "Spontaneous reporting confounded by indication: drugs prescribed for chronic illnesses (heart failure, hypertension) naturally co-occur with complications of that disease."),
        ("WHO ATC Hierarchical Classification:", "Queries World Health Organization ATC codes via ChEMBL API molecule endpoints with 95.7% corpus coverage and curated WHO fallbacks."),
        ("Taxonomic Depth Resolved:", "• Level 1: Main Anatomical Group (e.g., C - Cardiovascular, N - Nervous)\n• Level 2: Pharmacological Subgroup (e.g., C08 - Calcium Channel Blockers, N06A - Antidepressants)\n• Level 4/5: Generic chemical substance identifier."),
        ("Lightweight Public Alternative:", "Provides disease-level context comparable to complex EHR causal graphs (Toonsi 2026), but powered 100% by open biomedical ontologies."),
    ]
    for h, b in points:
        ph = tf1.add_paragraph()
        ph.text = f"• {h}"
        ph.font.size = Pt(11.5)
        ph.font.bold = True
        ph.font.color.rgb = NAVY_DARK
        ph.space_before = Pt(10)
        pb = tf1.add_paragraph()
        pb.text = b
        pb.font.size = Pt(10.5)
        pb.font.color.rgb = SLATE_TEXT

    # Right Card: Utilization Duration Derivation
    c2 = add_card(slide, 6.8, 1.5, 5.7, 5.3)
    tf2 = c2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "PHARMACOLOGICAL UTILIZATION DURATION DERIVATION"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = GREEN_ACCENT

    util_points = [
        ("CHRONIC Utilization (≥ 3 Months Continuous):", "Antihypertensives (C02, C09), Statins (C10), Antidiabetics (A10), Antiepileptics (N03). Tens of millions of patients exposed over decades; vulnerable to PRR denominator dilution."),
        ("ACUTE Utilization (< 4 Weeks Temporary):", "Systemic antibacterials (J01), antivirals (J05), antifungals (J02). Short treatment windows; high event concentration yields robust disproportionality."),
        ("MIXED Utilization (Variable Indication):", "NSAIDs (M01: acute headache vs. chronic osteoarthritis), bronchodilators (R03: acute rescue vs. maintenance)."),
        ("Live Name-Resolution & Retry Safeguards:", "Built-in exponential backoff (retries=3) and exact ChEMBL preferred-name query fallbacks ensure 96.3% holdout resolution stability."),
    ]
    for h, b in util_points:
        ph = tf2.add_paragraph()
        ph.text = f"• {h}"
        ph.font.size = Pt(11.5)
        ph.font.bold = True
        ph.font.color.rgb = NAVY_DARK
        ph.space_before = Pt(10)
        pb = tf2.add_paragraph()
        pb.text = b
        pb.font.size = Pt(10.5)
        pb.font.color.rgb = SLATE_TEXT


def build_slide_11(prs):
    """Slide 11: Deep-Dive #2: IndicationConcordance Clinical Heuristics."""
    slide = add_base_slide(prs, "10. Deep-Dive #2", "IndicationConcordance: 7 Pre-Registered Clinical Rules & Citation Audit", 11)
    # Left Card: The 7 Rules Table
    c1 = add_card(slide, 0.8, 1.5, 6.8, 5.3)
    tf1 = c1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "THE 7 PRE-REGISTERED CLINICAL HEURISTIC RULES (DECISIONS.md §35)"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT

    rules = [
        ("IND-CONF-01", "Cardiovascular / Ischemia", "ATC C, B01 × Myocardial Infarction, Stroke", "Psaty 1999, Salas 1999"),
        ("IND-CONF-02", "Neuropsychiatric / CNS", "ATC N × Suicidal Ideation, Depression, Seizures", "Schneeweiss 2005, Gibbons 2007"),
        ("IND-CONF-03", "Upper GI Ulcer / Bleeding", "ATC A02, M01 × GI Haemorrhage, Peptic Ulcer", "García Rodríguez 1994, Petri 1991"),
        ("IND-CONF-04", "Glycemic Dysregulation", "ATC A10 × Hypoglycaemia, Hyperglycaemia, DKA", "Cryer 2002, Schneeweiss 2007"),
        ("IND-CONF-05", "Hematologic Cytopenias", "ATC L × Neutropenia, Thrombocytopenia, DVT", "Lyman 2006, Groenwold 2011"),
        ("IND-CONF-06", "Renal Azotemia / AKI", "ATC C03, C09 × Acute Kidney Injury, Hyperkalaemia", "Schoolwerth 2001, Lapi 2013"),
        ("IND-CONF-07", "Airway Hyperresponsiveness", "ATC R03 × Bronchospasm, Asthma Exacerbation", "Suissa 2003, Ernst 1993"),
    ]
    for r_id, domain, overlap, cites in rules:
        p_r = tf1.add_paragraph()
        p_r.text = f"• {r_id} ({domain}): {overlap}"
        p_r.font.size = Pt(10)
        p_r.font.bold = True
        p_r.font.color.rgb = NAVY_DARK
        p_r.space_before = Pt(5)
        p_c = tf1.add_paragraph()
        p_c.text = f"   Verified Citations: {cites}"
        p_c.font.size = Pt(9)
        p_c.font.color.rgb = MUTED_TEXT

    # Right Card: Two-Round Independent Citation Audit
    c2 = add_card(slide, 7.8, 1.5, 4.7, 5.3)
    tf2 = c2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "TWO-ROUND CITATION AUDIT DISCIPLINE"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = GREEN_ACCENT

    audit_steps = [
        ("The Threat of Citation Drift in AI:", "Large language models frequently hallucinate or misattribute clinical citations. Research credibility requires strict verification of all grounding literature."),
        ("Round 1: Independent PubMed/NIH Audit (§35.8):", "Audited all 21 supporting citations against PubMed/NIH registries; uncovered 13 incorrect journals, volumes, or publication years and corrected them."),
        ("Round 2: Domain-Specific Grounding (§35.8.2):", "Removed over-extended general citations (e.g., generic Walker 1996), replacing them with domain-specific clinical trials (Lapi 2013 on triple-whammy AKI; Hernández-Díaz 2000 on NSAID GI bleeding)."),
        ("Gold-Standard Verification:", "100% of supporting rules are backed by real, verified, peer-reviewed clinical epidemiology."),
    ]
    for h, b in audit_steps:
        ph = tf2.add_paragraph()
        ph.text = f"• {h}"
        ph.font.size = Pt(11)
        ph.font.bold = True
        ph.font.color.rgb = NAVY_DARK
        ph.space_before = Pt(8)
        pb = tf2.add_paragraph()
        pb.text = b
        pb.font.size = Pt(10)
        pb.font.color.rgb = SLATE_TEXT


def build_slide_12(prs):
    """Slide 12: Deep-Dive #3: Scoring-Isolation Design."""
    slide = add_base_slide(prs, "11. Deep-Dive #3", "Scoring-Isolation Design: The Core Architectural Novelty", 12)
    # 2 Column Cards
    c1 = add_card(slide, 0.8, 1.5, 5.7, 5.3)
    tf1 = c1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "THE ARCHITECTURAL ISOLATION WALL"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT

    points = [
        ("The Design Choice:", "IndicationConcordance operates strictly as an informational surveillance annotation (DECISIONS.md §35)."),
        ("Scoring Impact = 0.000:", "In production, the concordance flag contributes exactly 0.000 to the composite confidence score and causes zero discrete escalation shifts."),
        ("High-Visibility Clinical Provenance:", "Flagged visibly on dashboard review cards and exported clinical dossiers to alert human safety reviewers to channeling bias without altering deterministic mathematics."),
        ("Verified Invariance Tests:", "Automated regression tests (test_indication_concordance_inertness.py) verify byte-identical output invariance across pipeline executions."),
    ]
    for h, b in points:
        ph = tf1.add_paragraph()
        ph.text = f"• {h}"
        ph.font.size = Pt(11.5)
        ph.font.bold = True
        ph.font.color.rgb = NAVY_DARK
        ph.space_before = Pt(10)
        pb = tf1.add_paragraph()
        pb.text = b
        pb.font.size = Pt(10.5)
        pb.font.color.rgb = SLATE_TEXT

    c2 = add_card(slide, 6.8, 1.5, 5.7, 5.3)
    tf2 = c2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "WHY SCORING-INERT? ANTI-OVERFITTING DISCIPLINE"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = AMBER_ACCENT

    why_points = [
        ("No Universal Confounding Constant Exists:", "Pharmacoepidemiology consensus (Walker 1996, Psaty 1999, CIOMS VIII) proves bias factors vary from 1.2 to 20-fold. Inventing a fixed scalar discount without patient clinical records is unscientific guesswork."),
        ("The Atorvastatin Regression Trap (§32):", "When we tested an automated chronic gate conditioning rule (Proposal B, §34), it caused an immediate false-positive regression on Atorvastatin + Dementia because Atorvastatin is also chronic."),
        ("Holdout Batch Empirical Result (§37):", "Testing an optional 0.85× discount on 40 held-out OMOP pairs attenuated continuous confidence downward in 4 concordant pairs, but shifted 0 discrete triage categories (a low-power null result)."),
        ("Anti-Overfitting Integrity (§15):", "We refuse to tune discount constants post-hoc to force benchmark fits. The isolation wall preserves pipeline truth."),
    ]
    for h, b in why_points:
        ph = tf2.add_paragraph()
        ph.text = f"• {h}"
        ph.font.size = Pt(11.5)
        ph.font.bold = True
        ph.font.color.rgb = NAVY_DARK
        ph.space_before = Pt(10)
        pb = tf2.add_paragraph()
        pb.text = b
        pb.font.size = Pt(10.5)
        pb.font.color.rgb = SLATE_TEXT


def build_slide_13(prs):
    """Slide 13: Key Experimental Finding #1: OMOP Reference Standard & Chronic Dilution."""
    slide = add_base_slide(prs, "12. Finding #1", "OMOP 100-Pair Evaluation & The Chronic PRR Dilution Paradox", 13)
    # Top 3 Hero Metric Cards
    m1 = add_card(slide, 0.8, 1.5, 3.6, 1.5, bg_color=GREEN_BG, border_color=GREEN_ACCENT)
    tf1 = m1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "STRICT SPECIFICITY"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = GREEN_ACCENT
    p_num = tf1.add_paragraph()
    p_num.text = "100.0%"
    p_num.font.size = Pt(28)
    p_num.font.bold = True
    p_num.font.color.rgb = GREEN_ACCENT
    p_sub = tf1.add_paragraph()
    p_sub.text = "50 / 50 Negative Controls Cleared (FP = 0)"
    p_sub.font.size = Pt(9.5)
    p_sub.font.color.rgb = NAVY_DARK

    m2 = add_card(slide, 4.85, 1.5, 3.6, 1.5, bg_color=WHITE, border_color=BORDER_GRAY)
    tf2 = m2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "LENIENT PRECISION"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT
    p_num = tf2.add_paragraph()
    p_num.text = "93.3%"
    p_num.font.size = Pt(28)
    p_num.font.bold = True
    p_num.font.color.rgb = BLUE_ACCENT
    p_sub = tf2.add_paragraph()
    p_sub.text = "14 / 15 Triaged Signals True Toxicities"
    p_sub.font.size = Pt(9.5)
    p_sub.font.color.rgb = SLATE_TEXT

    m3 = add_card(slide, 8.9, 1.5, 3.6, 1.5, bg_color=WHITE, border_color=BORDER_GRAY)
    tf3 = m3.text_frame
    tf3.word_wrap = True
    p = tf3.paragraphs[0]
    p.text = "OVER-CAUTION RATE"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK
    p_num = tf3.add_paragraph()
    p_num.text = "2.0%"
    p_num.font.size = Pt(28)
    p_num.font.bold = True
    p_num.font.color.rgb = NAVY_DARK
    p_sub = tf3.add_paragraph()
    p_sub.text = "Only 1 / 50 Negatives in MONITOR"
    p_sub.font.size = Pt(9.5)
    p_sub.font.color.rgb = SLATE_TEXT

    # Bottom Discovery Card
    c_bot = add_card(slide, 0.8, 3.2, 11.7, 3.6)
    tf_b = c_bot.text_frame
    tf_b.word_wrap = True
    p = tf_b.paragraphs[0]
    p.text = "THE CHRONIC PRR DENOMINATOR DILUTION PARADOX (DECISIONS.md §31)"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = AMBER_ACCENT

    dilution_points = [
        ("The Empirical Observation:", "While negative control rejection was flawless (100% specificity), Strict Recall on OMOP positives was 0.060 (3/50) and Lenient Recall was 0.280 (14/50). Why did known toxicities fail to escalate?"),
        ("Root-Cause Mathematical Analysis:", "Chronic blockbuster medications (e.g., Amlodipine, Sertraline, Citalopram, Nifedipine) are prescribed to tens of millions of patients over decades. Spontaneous reporting databases accumulate millions of background reports for these drugs."),
        ("Denominator Compression Below PRR 2.0 Gate:", "Because PRR divides a drug's specific event rate by its total reporting volume, the massive denominator compresses the PRR into the 1.1–1.9 range—falling just below the static PRR ≥ 2.0 gate—despite thousands of absolute reports (n up to 4,610), statistically significant Woolf CIs (lower CI > 1.0), and established biological plausibility."),
        ("Epidemiological Contribution:", "This empirically proves that static magnitude cutoffs (PRR ≥ 2.0) fail on high-utilization chronic therapies, highlighting the need for exposure-adjusted Bayesian shrinkage gates in future work."),
    ]
    for h, b in dilution_points:
        ph = tf_b.add_paragraph()
        ph.text = f"• {h}"
        ph.font.size = Pt(11)
        ph.font.bold = True
        ph.font.color.rgb = NAVY_DARK
        ph.space_before = Pt(8)
        pb = tf_b.add_paragraph()
        pb.text = b
        pb.font.size = Pt(10.5)
        pb.font.color.rgb = SLATE_TEXT


def build_slide_14(prs):
    """Slide 14: Key Experimental Finding #2: Top Prescribed Blockbuster Benchmark."""
    slide = add_base_slide(prs, "13. Finding #2", "Top Prescribed Blockbuster Benchmark (50 Pairs & Boxed Warnings)", 14)
    # Top 3 Hero Cards
    m1 = add_card(slide, 0.8, 1.5, 3.6, 1.5, bg_color=GREEN_BG, border_color=GREEN_ACCENT)
    tf1 = m1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "LENIENT F1-SCORE"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = GREEN_ACCENT
    p_num = tf1.add_paragraph()
    p_num.text = "0.9388"
    p_num.font.size = Pt(28)
    p_num.font.bold = True
    p_num.font.color.rgb = GREEN_ACCENT
    p_sub = tf1.add_paragraph()
    p_sub.text = "Wilson 95% CI: [0.850 – 0.978]"
    p_sub.font.size = Pt(9.5)
    p_sub.font.color.rgb = NAVY_DARK

    m2 = add_card(slide, 4.85, 1.5, 3.6, 1.5, bg_color=WHITE, border_color=BORDER_GRAY)
    tf2 = m2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "BOXED WARNING RECALL"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT
    p_num = tf2.add_paragraph()
    p_num.text = "92.0%"
    p_num.font.size = Pt(28)
    p_num.font.bold = True
    p_num.font.color.rgb = BLUE_ACCENT
    p_sub = tf2.add_paragraph()
    p_sub.text = "23 / 25 FDA Boxed Warnings Captured"
    p_sub.font.size = Pt(9.5)
    p_sub.font.color.rgb = SLATE_TEXT

    m3 = add_card(slide, 8.9, 1.5, 3.6, 1.5, bg_color=WHITE, border_color=BORDER_GRAY)
    tf3 = m3.text_frame
    tf3.word_wrap = True
    p = tf3.paragraphs[0]
    p.text = "STRICT PRECISION"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK
    p_num = tf3.add_paragraph()
    p_num.text = "1.0000"
    p_num.font.size = Pt(28)
    p_num.font.bold = True
    p_num.font.color.rgb = NAVY_DARK
    p_sub = tf3.add_paragraph()
    p_sub.text = "10 / 10 Strict Escalations Confirmed"
    p_sub.font.size = Pt(9.5)
    p_sub.font.color.rgb = SLATE_TEXT

    # Bottom Content Card
    c_bot = add_card(slide, 0.8, 3.2, 11.7, 3.6)
    tf_b = c_bot.text_frame
    tf_b.word_wrap = True
    p = tf_b.paragraphs[0]
    p.text = "REAL-WORLD CLINICAL VALIDATION ON HIGH-MORTALITY BLACK BOX TOXICITIES"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT

    points = [
        ("Everyday Outpatient Cohort Balance:", "Evaluated 25 high-mortality FDA Boxed Warnings vs. 25 balanced negative controls across 7 blockbuster therapeutic classes (Statins, ACEi/ARBs, Antibiotics, Antidepressants, Opioids, Anticonvulsants, Anticoagulants)."),
        ("Critical Toxicities Successfully Flagged:", "Metformin lactic acidosis, Lisinopril angioedema, Clozapine agranulocytosis, Amiodarone pulmonary fibrosis, Ciprofloxacin tendon rupture, and Bupropion seizures all correctly triaged for active clinician surveillance."),
        ("Conservative Clinician Alert Discipline:", "Out of 25 clean negative controls, 24 were completely cleared. Only a single benign diabetic pair (Glipizide lactic acidosis) entered MONITOR due to heavy diabetic polypharmacy confounding."),
        ("Offline Ollama Scalability:", "100% evaluated offline via local Ollama (qwen2.5:7b) with persistent disk caching—proving production readiness with zero external API fees or token throttles."),
    ]
    for h, b in points:
        ph = tf_b.add_paragraph()
        ph.text = f"• {h}"
        ph.font.size = Pt(11)
        ph.font.bold = True
        ph.font.color.rgb = NAVY_DARK
        ph.space_before = Pt(8)
        pb = tf_b.add_paragraph()
        pb.text = b
        pb.font.size = Pt(10.5)
        pb.font.color.rgb = SLATE_TEXT


def build_slide_15(prs):
    """Slide 15: Experimental Results Summary: Multi-Cohort Benchmark Performance Matrix."""
    slide = add_base_slide(prs, "14. Results Matrix", "Master Multi-Cohort Benchmark Performance Matrix (N = 165)", 15)

    # Master Table
    rows = 5
    cols = 9
    table_shape = slide.shapes.add_table(rows, cols, Inches(0.8), Inches(1.5), Inches(11.733), Inches(3.2))
    table = table_shape.table

    # Column widths
    col_widths = [Inches(2.6), Inches(1.15), Inches(1.15), Inches(1.15), Inches(1.15), Inches(1.15), Inches(1.15), Inches(1.15), Inches(1.1)]
    for idx, width in enumerate(col_widths):
        table.columns[idx].width = width

    headers = ["Evaluation Suite & Model", "Strict Prec", "Strict Rec", "Strict Spec", "Strict F1", "Len Prec", "Len Rec", "Len Spec", "Len F1"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY_HEADER
        p = cell.text_frame.paragraphs[0]
        p.font.name = "Arial"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT

    data = [
        ("PharmaGuard (Core Showcase, n=15)", "1.0000", "0.8571 (6/7)", "1.0000", "0.9231", "0.8750", "1.0000 (7/7)", "0.8750", "0.9333"),
        ("Single-Shot LLM Baseline (n=15)", "0.8750", "1.0000 (7/7)", "0.8750", "0.9333", "0.7000", "1.0000 (7/7)", "0.6250", "0.8235"),
        ("PharmaGuard (Top Prescribed, n=50)", "1.0000", "0.4000 (10/25)", "1.0000", "0.5714", "0.9583", "0.9200 (23/25)", "0.9600", "0.9388"),
        ("PharmaGuard (OMOP Expanded, n=100)", "1.0000", "0.0600 (3/50)", "1.0000", "0.1132", "0.9333", "0.2800 (14/50)", "0.9800", "0.4308"),
    ]
    for i, row in enumerate(data):
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if i % 2 == 0 else BG_LIGHT
            p = cell.text_frame.paragraphs[0]
            p.font.name = "Arial"
            p.font.size = Pt(9.5)
            p.font.color.rgb = NAVY_DARK
            if j == 0:
                p.font.bold = True
                p.alignment = PP_ALIGN.LEFT
            else:
                p.alignment = PP_ALIGN.CENTER

    # Bottom Takeaway Card
    c_bot = add_card(slide, 0.8, 5.0, 11.7, 1.85)
    tf_b = c_bot.text_frame
    tf_b.word_wrap = True
    p = tf_b.paragraphs[0]
    p.text = "CORE BENCHMARK TAKEAWAYS ACROSS ALL 165 EVALUATED PAIRS"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT

    takeaways = [
        ("Flawless Strict Precision (1.0000):", "Zero false-positive high-priority escalations across all 165 pairs. The agent never issues an inappropriate regulatory alert on ungrounded controls."),
        ("High Boxed Warning Capture (92.0%):", "Captures 23 of 25 life-threatening Black Box Warnings in outpatient medications with 0.9388 Lenient F1."),
        ("Halving Clinician Alert Fatigue:", "Over-caution rate on negative controls cut to 4.0% on blockbusters and 2.0% on OMOP vs. 25.0% on single-shot baseline."),
    ]
    for h, b in takeaways:
        ph = tf_b.add_paragraph()
        ph.text = f"• {h} {b}"
        ph.font.size = Pt(10)
        ph.font.color.rgb = SLATE_TEXT
        ph.space_before = Pt(4)


def build_slide_16(prs):
    """Slide 16: Key Novelties & Scientific Contributions."""
    slide = add_base_slide(prs, "15. Contributions", "Key Scientific Contributions & Architectural Novelties", 16)
    pillars = [
        ("PILLAR 1: SCORING-INERT ARCHITECTURE", "Anti-Overfitting Design Pattern", BLUE_ACCENT, [
            ("Decoupling Clinical Context:", "Separates high-dimensional clinical context from fragile numerical confidence scoring."),
            ("Preserving Mathematical Truth:", "Alerts human reviewers to indication overlap without distorting underlying PRR calculations or overfitting benchmark thresholds."),
        ]),
        ("PILLAR 2: PUBLIC-API DISEASE REASONING", "Open-Data Causal Alternative", GREEN_ACCENT, [
            ("No Private Hospital Lock-In:", "Proves standardized WHO ATC codes resolved via ChEMBL API can contextualize indication bias without restricted EHRs."),
            ("Global Reproducibility:", "Democratizes advanced pharmacovigilance triage for safety boards globally without proprietary data licensing."),
        ]),
        ("PILLAR 3: TWO-ROUND CITATION AUDITING", "Eliminating Clinical AI Hallucinations", NAVY_HEADER, [
            ("Independent PubMed Grounding:", "Independently verified all 21 supporting clinical citations, correcting 13 historical publication errors."),
            ("Trial-Grounded Rules:", "Replaced over-extended editorial commentary with verified domain trials (Lapi 2013, Hernández-Díaz 2000)."),
        ]),
        ("PILLAR 4: REPRODUCIBILITY & DUAL-METRIC", "Rigorous Engineering & Evaluation", AMBER_ACCENT, [
            ("242 Automated Tests:", "Passing pytest test suite with frozen benchmark invariance proofs and persistent SHA-256 disk caching."),
            ("Dual-Metric Philosophy:", "Distinguishes regulatory ESCALATE from surveillance MONITOR, accurately characterizing uncertainty."),
        ]),
    ]
    for i, (tag, sub, color, items) in enumerate(pillars):
        col_idx = i % 2
        row_idx = i // 2
        left = 0.8 + col_idx * 5.95
        top = 1.5 + row_idx * 2.75
        c = add_card(slide, left, top, 5.75, 2.55)
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = tag
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = color
        ps = tf.add_paragraph()
        ps.text = sub
        ps.font.size = Pt(11.5)
        ps.font.bold = True
        ps.font.color.rgb = NAVY_DARK
        ps.space_before = Pt(3)
        for h, b in items:
            ph = tf.add_paragraph()
            ph.text = f"• {h}"
            ph.font.size = Pt(10)
            ph.font.bold = True
            ph.font.color.rgb = NAVY_DARK
            ph.space_before = Pt(5)
            pb = tf.add_paragraph()
            pb.text = b
            pb.font.size = Pt(9.5)
            pb.font.color.rgb = SLATE_TEXT


def build_slide_17(prs):
    """Slide 17: Limitations & Future Work."""
    slide = add_base_slide(prs, "16. Limitations & Roadmap", "Identified Project Limitations & Semester 8 Future Roadmap", 17)
    # Left Box: Limitations
    c1 = add_card(slide, 0.8, 1.5, 5.7, 5.3)
    tf1 = c1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "HONEST METHODOLOGICAL LIMITATIONS"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = AMBER_ACCENT

    lims = [
        ("Single-Curator Ground Truth (Core Benchmark):", "The 15-pair golden set was curated by a primary investigator; expanding to multi-center inter-rater consensus panels is required for formal regulatory submission."),
        ("Heuristic Linear Priors (0.40 / 0.40 / 0.20):", "Weights and escalation thresholds (0.70 / 0.35) reflect expert clinical priors rather than empirically optimized parameters."),
        ("Low Statistical Power on Holdout Discount (§37):", "Only 4 of 40 held-out pairs triggered concordance; evaluating on N ≥ 100 concordant pairs is necessary to establish statistical power for continuous discounting."),
        ("Single Primary Indication Simplification:", "WHO ATC codes classify primary labeled indications; off-label prescribing and multi-indication drugs (e.g., indomethacin for pain vs. patent ductus arteriosus) remain unmodeled."),
    ]
    for h, b in lims:
        ph = tf1.add_paragraph()
        ph.text = f"• {h}"
        ph.font.size = Pt(11.5)
        ph.font.bold = True
        ph.font.color.rgb = NAVY_DARK
        ph.space_before = Pt(10)
        pb = tf1.add_paragraph()
        pb.text = b
        pb.font.size = Pt(10.5)
        pb.font.color.rgb = SLATE_TEXT

    # Right Box: Future Roadmap
    c2 = add_card(slide, 6.8, 1.5, 5.7, 5.3)
    tf2 = c2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "SEMESTER 8 ROADMAP & PUBLICATION TARGETS"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT

    road = [
        ("Multi-Jurisdiction Pharmacovigilance Ingestion:", "Ingest international spontaneous reporting databases beyond US FDA FAERS: European EudraVigilance, Japanese JADER, and WHO VigiBase."),
        ("Automated MedDRA Hierarchical Roll-Up:", "Implement automated ontology expansion mapping Preferred Terms (PT) to High-Level Group Terms (HLGT) and System Organ Classes (SOC)."),
        ("Exposure-Adjusted Bayesian Gating:", "Develop Bayesian shrinkage gates conditioned on prescription volume to rescue chronic therapies from denominator dilution."),
        ("Conference Paper Submission:", "Complete 9-section conference paper manuscript drafted (docs/paper/PharmaGuard_Conference_Paper.md), targeting IEEE BIBM / ACM CHIL / JAMIA venues."),
    ]
    for h, b in road:
        ph = tf2.add_paragraph()
        ph.text = f"• {h}"
        ph.font.size = Pt(11.5)
        ph.font.bold = True
        ph.font.color.rgb = NAVY_DARK
        ph.space_before = Pt(10)
        pb = tf2.add_paragraph()
        pb.text = b
        pb.font.size = Pt(10.5)
        pb.font.color.rgb = SLATE_TEXT


def build_slide_18(prs):
    """Slide 18: Tech Stack & Engineering Rigor."""
    slide = add_base_slide(prs, "17. Engineering Rigor", "Production Tech Stack & Interactive Streamlit Dashboard", 18)
    # 4 Cards Layout
    items = [
        ("RUNTIME & CORE AGENT STACK", BLUE_ACCENT, [
            ("Core Python Environment:", "Python 3.13, Pandas, NumPy, Pydantic v2 data models."),
            ("Deterministic Orchestrator:", "FixedPipelineAgent enforcing sequential multi-stream execution and hard safety gates."),
            ("LangGraph ReAct Alternative:", "Autonomous tool-calling fallback for exploratory research."),
        ]),
        ("DUAL INFERENCE BACKENDS", GREEN_ACCENT, [
            ("Local Ollama Backend (qwen2.5:7b):", "100% offline, zero-cost, unmetered local inferencing with zero external token limits."),
            ("Cloud Google Gemini Alternative:", "Gemini Flash Lite backend via LangGraph ReAct for rapid cloud prototyping."),
            ("Persistent DiskCache Layer:", "Deterministic SHA-256 caching guarantees zero live network calls during evaluation runs."),
        ]),
        ("AUTOMATED TEST SUITE (242 TESTS)", NAVY_DARK, [
            ("Pytest Unit & Regression Suite:", "242 unit and integration tests passing in under 62 seconds."),
            ("Bytecode & Schema Invariance:", "Invariant assertion tests guarantee byte-identical outputs across repeated pipeline runs."),
            ("Continuous Integration Pipeline:", "Automated GitHub Actions CI running compileall, ruff linting, and full test suite."),
        ]),
        ("CLINICAL STREAMLIT DASHBOARD", AMBER_ACCENT, [
            ("Multi-Cohort Switcher:", "Instant top-bar toggling between Core [15], Blockbusters [50], and OMOP [100]."),
            ("Live Signal Triage Playground:", "Searchable selectbox with 151 benchmark presets and arbitrary drug-event triage."),
            ("Clinical Dossier Export:", "One-click generation and download of regulatory Clinical Safety Briefings (.md & .json)."),
        ]),
    ]
    for i, (tag, color, sub_items) in enumerate(items):
        col_idx = i % 2
        row_idx = i // 2
        left = 0.8 + col_idx * 5.95
        top = 1.5 + row_idx * 2.75
        c = add_card(slide, left, top, 5.75, 2.55)
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = tag
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = color
        for h, b in sub_items:
            ph = tf.add_paragraph()
            ph.text = f"• {h}"
            ph.font.size = Pt(10)
            ph.font.bold = True
            ph.font.color.rgb = NAVY_DARK
            ph.space_before = Pt(5)
            pb = tf.add_paragraph()
            pb.text = b
            pb.font.size = Pt(9.5)
            pb.font.color.rgb = SLATE_TEXT


def build_slide_19(prs):
    """Slide 19: Verified Academic & Clinical References."""
    slide = add_base_slide(prs, "18. References", "Independently Audited & Verified Academic Literature", 19)
    # Single Large Card with 2-Column Citations
    c1 = add_card(slide, 0.8, 1.5, 5.7, 5.3)
    tf1 = c1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "DISPROPORTIONALITY & BENCHMARKING"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT

    cites_left = [
        ("Evans, S. J. W., et al. (2001)", "Use of proportional reporting ratios (PRRs) for signal generation from spontaneous adverse drug reaction reports. Pharmacoepidemiol Drug Saf, 10(6), 483-486."),
        ("van Puijenbroek, E. P., et al. (2002)", "A comparison of methods used for detecting adverse drug reactions in spontaneous reporting systems. Br J Clin Pharmacol, 54(4), 414-421."),
        ("Bate, A., & Evans, S. J. W. (2009)", "Quantitative signal detection using spontaneous ADR reporting. Pharmacoepidemiol Drug Saf, 18(6), 427-436."),
        ("Ryan, P. B., et al. (2013)", "Defining a ground truth for pharmacovigilance signal detection: the OMOP labeled drug and adverse event test set. Drug Safety, 36(Suppl 1), S33-S47."),
        ("Coste, J., et al. (2023)", "Methods for drug safety signal detection using observational electronic health care data: A systematic review. Pharmacoepidemiol Drug Saf, 32(1), 28-43."),
    ]
    for auth, cit in cites_left:
        ph = tf1.add_paragraph()
        ph.text = f"• {auth}"
        ph.font.size = Pt(10.5)
        ph.font.bold = True
        ph.font.color.rgb = NAVY_DARK
        ph.space_before = Pt(8)
        pb = tf1.add_paragraph()
        pb.text = cit
        pb.font.size = Pt(9.5)
        pb.font.color.rgb = SLATE_TEXT

    c2 = add_card(slide, 6.8, 1.5, 5.7, 5.3)
    tf2 = c2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "EPIDEMIOLOGY, LLMS & CAUSAL GRAPHS"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = GREEN_ACCENT

    cites_right = [
        ("Omar, M., et al. (2025)", "Multi-model assurance analysis showing large language models are highly vulnerable to adversarial hallucination attacks. Communications Medicine, 5(1), 330."),
        ("Toonsi, S., et al. (2026)", "Causal knowledge graph analysis identifies adverse drug effects. Bioinformatics, 42(1), btaf661."),
        ("Walker, A. M. (1996)", "Confounding by indication. Epidemiology, 7(4), 335-336."),
        ("Psaty, B. M., et al. (1999)", "Channeling bias in observational studies of cardiovascular medications. J Am Geriatr Soc, 47(6), 749-754."),
        ("Schneeweiss, S., & Avorn, J. (2005)", "A review of uses of health care utilization databases for epidemiologic research on therapeutics. J Clin Epidemiol, 58(4), 323-337."),
    ]
    for auth, cit in cites_right:
        ph = tf2.add_paragraph()
        ph.text = f"• {auth}"
        ph.font.size = Pt(10.5)
        ph.font.bold = True
        ph.font.color.rgb = NAVY_DARK
        ph.space_before = Pt(8)
        pb = tf2.add_paragraph()
        pb.text = cit
        pb.font.size = Pt(9.5)
        pb.font.color.rgb = SLATE_TEXT


def build_slide_20(prs):
    """Slide 20: Conclusion & Committee Q&A (Dark Navy Finish)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = NAVY_DARK
    bg.line.color.rgb = NAVY_DARK

    # Badge
    badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(0.8), Inches(4.2), Inches(0.38))
    badge.fill.solid()
    badge.fill.fore_color.rgb = RGBColor(30, 58, 138)
    badge.line.color.rgb = BLUE_ACCENT
    tb_b = badge.text_frame
    p_b = tb_b.paragraphs[0]
    p_b.text = "DEFENSE CONCLUSION & COMMITTEE DISCUSSION"
    p_b.font.name = "Arial"
    p_b.font.size = Pt(10)
    p_b.font.bold = True
    p_b.font.color.rgb = RGBColor(191, 219, 254)
    p_b.alignment = PP_ALIGN.CENTER

    # Title
    tbox = slide.shapes.add_textbox(Inches(1.0), Inches(1.3), Inches(11.3), Inches(1.0))
    tf = tbox.text_frame
    p1 = tf.paragraphs[0]
    p1.text = "Summary of Capstone Achievements & Floor Open for Q&A"
    p1.font.name = "Arial"
    p1.font.size = Pt(26)
    p1.font.bold = True
    p1.font.color.rgb = WHITE

    # Left Summary Card
    c1 = add_card(slide, 1.0, 2.5, 7.2, 4.3, bg_color=NAVY_HEADER, border_color=RGBColor(51, 65, 85))
    tf1 = c1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "FOUR VERIFIED CAPSTONE ACHIEVEMENTS"
    p.font.name = "Arial"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT

    achs = [
        ("1. Evidence-Grounded Triage Funnel:", "Replaced hallucinated LLM self-reporting with deterministic tri-source evidence fusion (FAERS, ChEMBL, PubMed) and hard empirical safety gating."),
        ("2. Flawless Conservatism (100% Strict Precision):", "Zero false alarms across all 165 benchmark pairs, cutting alert fatigue to 2.0% on OMOP and 4.0% on blockbusters."),
        ("3. Public Disease-Context Reasoning:", "Resolved WHO ATC indication concordance via ChEMBL API, providing an accessible public alternative to restricted hospital EHR models."),
        ("4. Reproducibility & Publication Readiness:", "242 passing pytest tests, full conference paper draft, and a live Streamlit evaluation dashboard with instant clinical dossier exports."),
    ]
    for h, b in achs:
        ph = tf1.add_paragraph()
        ph.text = f"• {h}"
        ph.font.name = "Arial"
        ph.font.size = Pt(11.5)
        ph.font.bold = True
        ph.font.color.rgb = WHITE
        ph.space_before = Pt(8)
        pb = tf1.add_paragraph()
        pb.text = f"   {b}"
        pb.font.name = "Arial"
        pb.font.size = Pt(10.5)
        pb.font.color.rgb = RGBColor(148, 163, 184)

    # Right Card: Acknowledgments & Links
    c2 = add_card(slide, 8.45, 2.5, 3.88, 4.3, bg_color=NAVY_HEADER, border_color=RGBColor(51, 65, 85))
    tf2 = c2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "ACKNOWLEDGMENTS & REPOSITORY"
    p.font.name = "Arial"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = RGBColor(52, 211, 153)

    p_sup = tf2.add_paragraph()
    p_sup.text = "Dr. Nikhilanand Arya"
    p_sup.font.name = "Arial"
    p_sup.font.size = Pt(13)
    p_sup.font.bold = True
    p_sup.font.color.rgb = WHITE
    p_sup.space_before = Pt(8)

    p_sub = tf2.add_paragraph()
    p_sub.text = "Assistant Professor\nDepartment of Information Technology\nIIIT Allahabad\nSupervisor & Evaluator"
    p_sub.font.name = "Arial"
    p_sub.font.size = Pt(10.5)
    p_sub.font.color.rgb = RGBColor(148, 163, 184)

    p_repo_h = tf2.add_paragraph()
    p_repo_h.text = "OPEN REPOSITORY"
    p_repo_h.font.name = "Arial"
    p_repo_h.font.size = Pt(10)
    p_repo_h.font.bold = True
    p_repo_h.font.color.rgb = BLUE_ACCENT
    p_repo_h.space_before = Pt(14)

    p_url = tf2.add_paragraph()
    p_url.text = "github.com/Krishna200608/PharmaGuard"
    p_url.font.name = "Arial"
    p_url.font.size = Pt(10.5)
    p_url.font.bold = True
    p_url.font.color.rgb = RGBColor(191, 219, 254)

    p_qa = tf2.add_paragraph()
    p_qa.text = "Thank you! Floor is open for questions and committee feedback."
    p_qa.font.name = "Arial"
    p_qa.font.size = Pt(11)
    p_qa.font.bold = True
    p_qa.font.color.rgb = RGBColor(52, 211, 153)
    p_qa.space_before = Pt(14)


def main():
    print("Building PharmaGuard Capstone Defense Slide Deck...")
    prs = create_deck()

    # Build all 20 slides
    build_slide_1(prs)
    build_slide_2(prs)
    build_slide_3(prs)
    build_slide_4(prs)
    build_slide_5(prs)
    build_slide_6(prs)
    build_slide_7(prs)
    build_slide_8(prs)
    build_slide_9(prs)
    build_slide_10(prs)
    build_slide_11(prs)
    build_slide_12(prs)
    build_slide_13(prs)
    build_slide_14(prs)
    build_slide_15(prs)
    build_slide_16(prs)
    build_slide_17(prs)
    build_slide_18(prs)
    build_slide_19(prs)
    build_slide_20(prs)

    out_dir = Path("docs/presentation")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "PharmaGuard_Defense_Deck.pptx"
    prs.save(str(out_path))
    print(f"Successfully generated 20-slide presentation deck: {out_path.resolve()}")


if __name__ == "__main__":
    main()
