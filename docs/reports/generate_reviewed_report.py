"""
generate_reviewed_report.py
===========================
Generates the reviewed, publication-grade implementation report for
ClinGap-NLP: Clinical Decision Gap Intelligence System.

Output:
  clinngap_nlp/docs/reports/ClinGap_NLP_Detailed_Implementation_Report_Reviewed.pdf
"""

import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and display total page count.
    Adds a sleek professional header and footer on every page except the cover.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            # Minimal subtle footer on cover page
            self.saveState()
            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(42, 25, "CLINGAP-NLP  •  CLINICAL DECISION GAP INTELLIGENCE SYSTEM")
            self.setFont("Helvetica", 7.5)
            self.drawRightString(A4[0] - 42, 25, "TECHNICAL IMPLEMENTATION REPORT (REVIEWED EDITION)  •  v1.0.0")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(42, 36, A4[0] - 42, 36)
            self.restoreState()
            return

        self.saveState()
        # Top Running Header
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#1E3A8A"))
        self.drawString(42, A4[1] - 28, "CLINGAP-NLP: CLINICAL DECISION GAP INTELLIGENCE SYSTEM")
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawRightString(A4[0] - 42, A4[1] - 28, "SYSTEM IMPLEMENTATION & ARCHITECTURAL VERIFICATION (REVIEWED)")

        # Top rule line
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(42, A4[1] - 32, A4[0] - 42, A4[1] - 32)

        # Bottom rule line & Running Footer
        self.line(42, 36, A4[0] - 42, 36)
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#475569"))
        self.drawString(42, 24, "RESEARCH & QA PROTOTYPE  •  NOT FOR DIRECT AUTONOMOUS CLINICAL DIAGNOSIS")
        self.setFont("Helvetica", 7.5)
        self.drawRightString(A4[0] - 42, 24, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def create_report(output_path):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Document setup: A4 with 42pt margins (width=595.28, printable=511.28)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=42,
        rightMargin=42,
        topMargin=42,
        bottomMargin=44
    )

    PW = 508.0  # Safe printable width

    styles = getSampleStyleSheet()

    # Palette
    c_primary = colors.HexColor("#0F172A")    # Slate 900
    c_navy = colors.HexColor("#1E3A8A")       # Navy 800
    c_blue = colors.HexColor("#1D4ED8")       # Blue 700
    c_teal = colors.HexColor("#0D9488")       # Teal 600
    c_teal_dark = colors.HexColor("#0F766E")  # Teal 700
    c_text = colors.HexColor("#1E293B")       # Slate 800
    c_muted = colors.HexColor("#475569")      # Slate 600
    c_border = colors.HexColor("#CBD5E1")     # Slate 300
    c_bg_light = colors.HexColor("#F8FAFC")   # Slate 50
    c_bg_callout = colors.HexColor("#EFF6FF") # Blue 50
    c_bg_warn = colors.HexColor("#FFFBEB")    # Amber 50
    c_warn_border = colors.HexColor("#FCD34D")

    # Typography Styles
    cover_title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=c_primary,
        alignment=0,
        spaceAfter=6
    )

    cover_subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=16,
        textColor=c_teal_dark,
        alignment=0,
        spaceAfter=12
    )

    cover_desc_style = ParagraphStyle(
        'CoverDesc',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=c_muted,
        alignment=0,
        spaceAfter=15
    )

    ch_title_style = ParagraphStyle(
        'ChapterTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=17,
        textColor=c_navy,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=c_teal_dark,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'Heading3_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.8,
        leading=11.5,
        textColor=c_primary,
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=11.5,
        textColor=c_text,
        spaceAfter=4.5
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.0,
        leading=11.0,
        textColor=c_text,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.2,
        leading=9.2,
        textColor=colors.HexColor("#0F172A")
    )

    callout_text = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.0,
        leading=11.0,
        textColor=colors.HexColor("#1E3A8A")
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=10,
        textColor=colors.white
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10.0,
        textColor=c_text
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10.0,
        textColor=c_text
    )

    table_cell_code = ParagraphStyle(
        'TableCellCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=6.8,
        leading=8.8,
        textColor=colors.HexColor("#0F172A")
    )

    meta_label = ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=10,
        textColor=c_navy
    )

    meta_val = ParagraphStyle(
        'MetaVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=10,
        textColor=c_text
    )

    story = []

    # Helper functions for UI blocks
    def make_callout(text, bg_color=c_bg_callout, border_color=c_blue, title="NOTE"):
        content = [
            Paragraph(f"<b>[{title}]</b> {text}", callout_text)
        ]
        t = Table([[content]], colWidths=[PW])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg_color),
            ('BOX', (0,0), (-1,-1), 1, border_color),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        return t

    def make_code_box(code_str):
        p = Paragraph(code_str.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style)
        t = Table([[p]], colWidths=[PW])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
            ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor("#CBD5E1")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        return t

    def make_section_divider():
        return HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#E2E8F0"), spaceBefore=8, spaceAfter=8)

    # =========================================================================
    # COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 15))
    tag_table = Table([[
        Paragraph("<b>CLINICAL NLP & DECISION INTELLIGENCE MONOGRAPH — REVIEWED EDITION</b>", ParagraphStyle('Tag', fontName='Helvetica-Bold', fontSize=8, textColor=colors.white))
    ]], colWidths=[330])
    tag_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_navy),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(tag_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("ClinGap-NLP", cover_title_style))
    story.append(Paragraph("Clinical Decision Gap Intelligence System", cover_subtitle_style))
    story.append(Paragraph(
        "A Comprehensive System Architecture, Implementation, and Software Verification Report documenting "
        "an end-to-end clinical NLP pipeline integrating Transformer-based Biomedical NER, clausal negation "
        "scoping, proximity-aware medication regimen parsing, deterministic guideline matching, and "
        "decision gap detection with a modern React 18 / FastAPI Single Page Application.",
        cover_desc_style
    ))

    story.append(HRFlowable(width="100%", thickness=1.5, color=c_teal, spaceBefore=4, spaceAfter=12))

    # Metadata Panel Table (Updated with accurate runtime status)
    meta_data = [
        [Paragraph("Project Title", meta_label), Paragraph("ClinGap-NLP — Clinical Decision Gap Intelligence System", meta_val)],
        [Paragraph("System Role", meta_label), Paragraph("Explainable Clinical Documentation Review & Quality Assurance Prototype", meta_val)],
        [Paragraph("Backend Architecture", meta_label), Paragraph("FastAPI 0.115+ (Python 3.13.3) ASGI on Port 8001 via Uvicorn", meta_val)],
        [Paragraph("Frontend Architecture", meta_label), Paragraph("React 18.3.1 + Vite 6 Single Page Application on Port 3001 with Tailwind CSS 3.4", meta_val)],
        [Paragraph("Primary NER (Active)", meta_label), Paragraph("Hugging Face d4data/biomedical-ner-all (Token Classification, CPU, Stride=128)", meta_val)],
        [Paragraph("Secondary NER (Status)", meta_label), Paragraph("spaCy en_ner_bc5cdr_md (<b>Unavailable in environment; dictionary fallback active</b>)", meta_val)],
        [Paragraph("Lexicons & Patterns", meta_label), Paragraph("Active: Curated dictionaries (diseases, symptoms, meds, tests) + Regex patterns", meta_val)],
        [Paragraph("Context Embeddings", meta_label), Paragraph("Bio_ClinicalBERT (768-dim loaded from cache; numerical vector only; TF-IDF fallback ready)", meta_val)],
        [Paragraph("Guideline Engine", meta_label), Paragraph("Configured Prototype Rules (knowledge_base/guidelines.json, Rules R1, R2, R3)", meta_val)],
        [Paragraph("Dataset Integration", meta_label), Paragraph("MTSamples Cleaned Corpus (4,966 records across 40 medical specialties)", meta_val)],
        [Paragraph("Software Verification", meta_label), Paragraph("<b>56 / 56 Pytest Software Tests Passing (27.44s)</b> | Vite Production Build Verified (15.07s)", meta_val)],
        [Paragraph("Monograph Status", meta_label), Paragraph("Academic Review Edition — Factually Audited against Active Codebase", meta_val)],
    ]
    meta_table = Table(meta_data, colWidths=[130, PW - 130])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_light),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 14))
    story.append(make_callout(
        "<b>RESEARCH PROTOTYPE & REGULATORY SAFETY DISCLAIMER:</b> ClinGap-NLP is an educational, research, "
        "and documentation quality assurance prototype designed to assist healthcare professionals in auditing clinical "
        "narratives. It does NOT diagnose patients, formulate therapeutic plans, or serve as an autonomous medical device. "
        "Configured guideline rules in this prototype are demonstration models and must not be used as clinical directives. "
        "All flagged documentation gaps and guideline recommendations must be evaluated and verified by a licensed "
        "physician prior to clinical intervention.",
        bg_color=c_bg_warn, border_color=c_warn_border, title="SAFETY NOTICE"
    ))

    story.append(PageBreak())

    # =========================================================================
    # TABLE OF CONTENTS & EXECUTIVE SUMMARY
    # =========================================================================
    story.append(Paragraph("Table of Contents & Executive Summary", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph("<b>Document Organization & Chapter Index</b>", h2_style))
    story.append(Paragraph(
        "This reviewed report is organized into 19 formal technical chapters structured according to academic and industrial "
        "software engineering documentation standards:",
        body_style
    ))

    toc_data = [
        [Paragraph("<b>Ch.</b>", table_header), Paragraph("<b>Chapter Title</b>", table_header), Paragraph("<b>Primary Scope & Focus Area</b>", table_header)],
        [Paragraph("1", table_cell_bold), Paragraph("Introduction", table_cell_bold), Paragraph("Clinical NLP background, cognitive burden, motivation, research scope", table_cell)],
        [Paragraph("2", table_cell_bold), Paragraph("Problem Statement", table_cell_bold), Paragraph("Unstructured narrative challenges, omission vs malpractice distinction", table_cell)],
        [Paragraph("3", table_cell_bold), Paragraph("Proposed System & Objectives", table_cell_bold), Paragraph("Hybrid NLP solution, prototype boundaries, functional scope", table_cell)],
        [Paragraph("4", table_cell_bold), Paragraph("Requirements & System Design", table_cell_bold), Paragraph("FR-01 to FR-10, non-functional criteria, division of responsibilities", table_cell)],
        [Paragraph("5", table_cell_bold), Paragraph("Technology Stack", table_cell_bold), Paragraph("Verified component matrix, library roles, active vs fallback models", table_cell)],
        [Paragraph("6", table_cell_bold), Paragraph("Project Folder Structure", table_cell_bold), Paragraph("Exhaustive file tree across 4 subsystems, directory responsibilities", table_cell)],
        [Paragraph("7", table_cell_bold), Paragraph("System Architecture", table_cell_bold), Paragraph("Multi-tier topology, vector architectural diagram, data contracts", table_cell)],
        [Paragraph("8", table_cell_bold), Paragraph("End-to-End Workflow", table_cell_bold), Paragraph("11-stage pipeline execution sequence, process flow diagram", table_cell)],
        [Paragraph("9", table_cell_bold), Paragraph("Detailed Module Implementation", table_cell_bold), Paragraph("Algorithms, signatures, edge cases across modules A through N", table_cell)],
        [Paragraph("10", table_cell_bold), Paragraph("Clinical NLP & Rule Reasoning", table_cell_bold), Paragraph("Probabilistic NER vs deterministic reasoning, status lifecycle", table_cell)],
        [Paragraph("11", table_cell_bold), Paragraph("Frontend-Backend Integration", table_cell_bold), Paragraph("REST API matrix, dual-dispatch client, single-source state sync", table_cell)],
        [Paragraph("12", table_cell_bold), Paragraph("Database & Data Management", table_cell_bold), Paragraph("SQLAlchemy ORM models, SQLite storage, MTSamples indexing", table_cell)],
        [Paragraph("13", table_cell_bold), Paragraph("Sample Case & Demonstration", table_cell_bold), Paragraph("Synthetic multi-morbidity note trace, step-by-step audit output", table_cell)],
        [Paragraph("14", table_cell_bold), Paragraph("User Interface & Views", table_cell_bold), Paragraph("Detailed breakdown & layout wireframes of all 8 SPA modules", table_cell)],
        [Paragraph("15", table_cell_bold), Paragraph("Testing & Verification", table_cell_bold), Paragraph("56 backend unit/regression tests, Vite build verification, history", table_cell)],
        [Paragraph("16", table_cell_bold), Paragraph("Results & Discussion", table_cell_bold), Paragraph("Observed behavior, software verification vs clinical validation", table_cell)],
        [Paragraph("17", table_cell_bold), Paragraph("Limitations & Future Scope", table_cell_bold), Paragraph("Syntactic edge cases, SNOMED/RxNorm roadmap, FHIR compliance", table_cell)],
        [Paragraph("18", table_cell_bold), Paragraph("Conclusion", table_cell_bold), Paragraph("Synthesis of contributions, responsible clinical AI principles", table_cell)],
        [Paragraph("19", table_cell_bold), Paragraph("References & Appendices", table_cell_bold), Paragraph("Verified official citations, technical glossary, local setup guide", table_cell)],
    ]
    toc_table = Table(toc_data, colWidths=[24, 155, PW - 179])
    toc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_navy),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0,0), (-1,-1), 2.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.8),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(toc_table)

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Executive Summary</b>", h2_style))
    story.append(Paragraph(
        "Modern healthcare delivery generates massive volumes of unstructured narrative documentation. While electronic health "
        "records (EHRs) capture rich clinical nuances, vital information—such as diagnostic prerequisites, ordered versus completed "
        "investigations, and exact medication regimens—frequently remains trapped in free text. Clinicians and quality auditors facing "
        "severe cognitive overload can inadvertently miss documentation omissions or delayed laboratory follow-ups. "
        "<b>ClinGap-NLP</b> addresses this challenge by providing an explainable, dual-paradigm intelligence system that marries "
        "probabilistic deep-learning entity extraction with deterministic, criteria-based clinical reasoning.",
        body_style
    ))
    story.append(Paragraph(
        "Rather than relying on black-box generative models that can hallucinate clinical guidelines, ClinGap-NLP utilizes a transparent "
        "hybrid pipeline: a 4-tier Named Entity Recognition (NER) architecture (combining Hugging Face's <i>d4data/biomedical-ner-all</i> "
        "BioBERT token classifier, spaCy models, curated medical lexicons, and regex patterns), clausal bidirectional negation detection, "
        "token-distance medication-regimen reconstruction, and an explicit investigation lifecycle state machine. Extracted patient findings "
        "are evaluated against deterministic prototype guideline rules to surface missing diagnostic evaluations and documentation gaps. "
        "The system features a reactive React 18 Single Page Application and a high-throughput FastAPI backend, verified by 56 passing "
        "automated regression tests.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 1: INTRODUCTION
    # =========================================================================
    story.append(Paragraph("Chapter 1: Introduction", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph("1.1 Natural Language Processing in Healthcare", h2_style))
    story.append(Paragraph(
        "Natural Language Processing (NLP) has emerged as an indispensable technology for unlocking structured knowledge from clinical "
        "narratives. Over 80% of healthcare documentation exists in unstructured formats, including physician progress notes, admission summaries, "
        "discharge instructions, and radiology reports. Clinical NLP models must process medical jargon, non-standard acronyms, complex syntactic "
        "structures, and temporal dependencies while maintaining strict clinical fidelity.",
        body_style
    ))

    story.append(Paragraph("1.2 Cognitive and Operational Challenges in Clinical Note Review", h2_style))
    story.append(Paragraph(
        "Manual chart review is labor-intensive, error-prone, and unsustainable given escalating patient volumes. Healthcare practitioners "
        "experience documented cognitive fatigue when cross-referencing multi-page clinical histories against evolving evidence-based "
        "protocols. Critical data points—such as whether a glycated hemoglobin (HbA1c) test was ordered, performed, or merely recommended—often "
        "become buried under voluminous narratives. This fragmentation can lead to diagnostic delays, unnecessary repeat testing, and quality audit failures.",
        body_style
    ))

    story.append(Paragraph("1.3 Project Motivation: The ClinGap-NLP Vision", h2_style))
    story.append(Paragraph(
        "The ClinGap-NLP project was conceived to bridge the gap between complex unstructured text and actionable clinical documentation review. "
        "Its primary motivation is to empower healthcare documentation auditors, clinical quality officers, and research fellows with an "
        "automated, explainable tool that extracts vital clinical entities, tracks investigation lifecycles, and highlights potential "
        "documentation omissions without disrupting existing clinical workflows.",
        body_style
    ))

    story.append(Paragraph("1.4 Dual-Paradigm Architecture: Structured Extraction & Rule-Based Reasoning", h2_style))
    story.append(Paragraph(
        "A central design tenet of ClinGap-NLP is the strict decoupling of <b>probabilistic extraction</b> from <b>deterministic reasoning</b>. "
        "Machine learning models excel at recognizing linguistic surface forms of diseases, symptoms, and medications across varied phrasing. "
        "However, clinical protocol enforcement must remain 100% auditable and reproducible. By feeding normalized entities into a deterministic "
        "criteria engine, ClinGap-NLP guarantees that every flagged gap is anchored to an explicit rule and clear textual justification.",
        body_style
    ))

    story.append(Paragraph("1.5 Target Audience and Research Scope", h2_style))
    story.append(Paragraph(
        "The system is tailored for clinical informatics researchers, medical coding auditors, healthcare quality assurance committees, and "
        "students of clinical NLP. The prototype provides an interactive sandbox for exploring how biomedical transformers, rule-based "
        "reasoners, and modern web architectures converge to enhance documentation integrity. Configured guideline rules within this "
        "prototype are designed to demonstrate system capabilities and test pipeline behavior rather than serve as universally binding clinical standards.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 2: PROBLEM STATEMENT
    # =========================================================================
    story.append(Paragraph("Chapter 2: Problem Statement", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph("2.1 The Unstructured Narrative Dilemma", h2_style))
    story.append(Paragraph(
        "In routine clinical practice, documentation is recorded in freeform narrative prose. A single paragraph may contain diagnoses, "
        "patient-reported symptoms, explicit negations, active medication dosages, and laboratory orders. Traditional keyword matching "
        "fails catastrophically in this domain because it cannot distinguish between active pathology and negated findings (e.g., 'patient "
        "has cough' versus 'patient denies cough').",
        body_style
    ))

    story.append(Paragraph("2.2 Multi-Entity Interdependence and Syntactic Ambiguity", h2_style))
    story.append(Paragraph(
        "Clinical entities do not exist in isolation. A medication mention is clinically incomplete without its dosage strength, unit, and "
        "administration frequency. When multiple medications appear in proximity, naive parsers cross-pair dosages (assigning 500 mg to an "
        "inhaler rather than an antibiotic). Similarly, laboratory values (e.g., 'glucose 218 mg/dL') share identical units (mg) with medication "
        "strengths (e.g., 'metformin 500 mg'), creating high risk of false-positive medication extractions.",
        body_style
    ))

    story.append(Paragraph("2.3 Investigation Lifecycle Tracking", h2_style))
    story.append(Paragraph(
        "Diagnostic investigations undergo a dynamic lifecycle: they may be <i>unmentioned</i>, <i>ordered/pending</i>, <i>actively in progress</i>, "
        "<i>completed/performed</i>, or <i>explicitly cancelled/not performed</i>. Existing documentation tools frequently treat any mention "
        "of a test as completed, or conversely flag pending tests as missing. A robust system must model these distinct states.",
        body_style
    ))

    story.append(Paragraph("2.4 Formal Problem Formulation", h2_style))
    story.append(Paragraph(
        "<b>Given:</b> An unstructured clinical text document <i>D</i> consisting of sentences <i>s<sub>1</sub>, s<sub>2</sub>, ..., s<sub>n</sub></i>.<br/>"
        "<b>Extract:</b> A tuple set <i>E = {(t<sub>i</sub>, y<sub>i</sub>, v<sub>i</sub>, c<sub>i</sub>, n<sub>i</sub>, st<sub>i</sub>)}</i> where "
        "<i>t<sub>i</sub></i> is entity surface text, <i>y<sub>i</sub> &in; {DISEASE, SYMPTOM, MEDICATION, INVESTIGATION, DOSAGE, FREQUENCY}</i>, "
        "<i>v<sub>i</sub></i> is normalized canonical form, <i>c<sub>i</sub> &in; [0,1]</i> is confidence, <i>n<sub>i</sub> &in; {True, False}</i> is negation, "
        "and <i>st<sub>i</sub> &in; {ordered, pending, completed, not performed}</i> is status.<br/>"
        "<b>Reconstruct:</b> Regimens <i>R = {(m<sub>k</sub>, d<sub>k</sub>, f<sub>k</sub>)}</i> associating each medication with its nearest valid dosage and frequency.<br/>"
        "<b>Audit:</b> A set of guideline rules <i>G = {g<sub>j</sub>}</i> to detect potential documentation gaps <i>&Delta; = {&delta;<sub>m</sub>}</i> where "
        "required diagnostic actions are absent or noted as unperformed.",
        body_style
    ))

    story.append(Paragraph("2.5 Essential Clinical Boundary: Documentation Omission vs Medical Error", h2_style))
    story.append(Paragraph(
        "<b>Critical Distinction:</b> ClinGap-NLP identifies <i>documentation and follow-up gaps</i> within the provided text record. A missing "
        "mention of an HbA1c test in a clinic note indicates that the test was not documented in that visit; it does <b>NOT</b> prove that the "
        "treating physician committed medical negligence or that the test was never performed at an external facility. The system serves as a "
        "documentation audit assistant, not a medico-legal adjudicator.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 3: PROPOSED SYSTEM AND OBJECTIVES
    # =========================================================================
    story.append(Paragraph("Chapter 3: Proposed System and Objectives", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph("3.1 Proposed Solution Overview", h2_style))
    story.append(Paragraph(
        "ClinGap-NLP introduces a complete, runnable client-server architecture designed to ingest multi-format clinical documentation, "
        "execute a 4-tier hybrid NLP pipeline, evaluate deterministic clinical guidelines, track diagnostic lifecycles, and present "
        "explainable audit findings through a rich, interactive React 18 dashboard. The system integrates deep transformer representations "
        "for contextual fidelity while guaranteeing 100% deterministic, explainable rule evaluation.",
        body_style
    ))

    story.append(Paragraph("3.2 Expected Inputs and Supported Outputs", h2_style))
    story.append(Paragraph(
        "<b>Supported Inputs:</b><br/>"
        "• Plain text clinical narratives (.txt) typed directly or loaded via demo presets.<br/>"
        "• Uploaded digital documents (.pdf, .docx, .txt) parsed without external runtime binaries.<br/>"
        "• Standardized clinical dataset records from the MTSamples corpus (4,966 records across 40 specialties).<br/>"
        "<b>Generated Outputs:</b><br/>"
        "• Structured clinical entities with canonical normalization and clausal negation tags.<br/>"
        "• Proximity-reconstructed medication regimens (medication, dosage strength, dosing frequency).<br/>"
        "• Diagnostic investigation lifecycle states (Ordered / Pending, Pending Results, Performed, Not performed).<br/>"
        "• Evaluated guideline rule activations and flagged documentation gaps (MISSING_INVESTIGATION).<br/>"
        "• Mathematical confidence scores and structured explainability trees linking gaps to rules.<br/>"
        "• Reconstructed chronological clinical timeline with categorized condition, regimen, and lab views.",
        body_style
    ))

    story.append(Paragraph("3.3 Core System Objectives", h2_style))
    story.append(Paragraph(
        "1. <b>Multi-Tier Extraction Robustness:</b> Achieve robust entity extraction across diseases, symptoms, medications, and labs "
        "by combining biomedical transformers with multi-layer fallback dictionaries and regular expressions.<br/>"
        "2. <b>Clausal Negation Awareness:</b> Accurately scope negations across sentence clauses without falsely negating active orders.<br/>"
        "3. <b>Disambiguation Fidelity:</b> Distinguish numeric laboratory measurements (e.g., 218 mg/dL) from medication dosages (500 mg).<br/>"
        "4. <b>Deterministic Auditability:</b> Ensure guideline matching is transparent, repeatable, and directly inspectable.<br/>"
        "5. <b>Modern Full-Stack Integration:</b> Deliver a sub-second reactive user experience connecting a React 18 SPA to a FastAPI backend.",
        body_style
    ))

    story.append(Paragraph("3.4 Operational Scope & Prototype Boundaries", h2_style))
    story.append(Paragraph(
        "The current implementation represents a functional research prototype. Implemented capabilities include multi-tier NER, negation scoping, "
        "regimen reconstruction, file parsing (.txt/.pdf/.docx), MTSamples dataset search, guideline evaluation, and persistent SQLite storage. "
        "Future enhancements outside current scope include direct HL7/FHIR hospital EHR integration, ICD-10/SNOMED automated billing coding, "
        "and multi-lingual clinical processing.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 4: REQUIREMENTS AND SYSTEM DESIGN
    # =========================================================================
    story.append(Paragraph("Chapter 4: Requirements and System Design", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph("4.1 Functional Requirements Specification", h2_style))
    fr_data = [
        [Paragraph("<b>Req ID</b>", table_header), Paragraph("<b>Requirement Name</b>", table_header), Paragraph("<b>Detailed Functional Specification</b>", table_header)],
        [Paragraph("FR-01", table_cell_bold), Paragraph("Multi-Format Ingestion", table_cell), Paragraph("Ingest text via manual input, preset selection, or file upload (.txt, .pdf, .docx) with automatic text extraction.", table_cell)],
        [Paragraph("FR-02", table_cell_bold), Paragraph("Hybrid NER Extraction", table_cell), Paragraph("Extract entities across 6 categories using Hugging Face BioBERT, spaCy fallback, lexicons, and regex patterns.", table_cell)],
        [Paragraph("FR-03", table_cell_bold), Paragraph("Clausal Negation Scoping", table_cell), Paragraph("Identify pre- and post-negation phrases within clauses; mark negated entities; preserve active pending tests.", table_cell)],
        [Paragraph("FR-04", table_cell_bold), Paragraph("Prescription Parsing", table_cell), Paragraph("Pair medications with nearest following dosage and frequency; filter noise words; prevent cross-pairing.", table_cell)],
        [Paragraph("FR-05", table_cell_bold), Paragraph("Lab Unit Disambiguation", table_cell), Paragraph("Reject clinical lab values (mg/dL, g/dL, mmHg, °C) from being classified as medication dosages or drug names.", table_cell)],
        [Paragraph("FR-06", table_cell_bold), Paragraph("Investigation Lifecycle", table_cell), Paragraph("Classify tests into: ORDERED/PENDING, pending, completed/performed, or not performed; suppress false gaps.", table_cell)],
        [Paragraph("FR-07", table_cell_bold), Paragraph("Guideline Rule Matching", table_cell), Paragraph("Match non-negated patient entities against deterministic rules in guidelines.json; record activated rule IDs.", table_cell)],
        [Paragraph("FR-08", table_cell_bold), Paragraph("Decision Gap Detection", table_cell), Paragraph("Emit MISSING_INVESTIGATION gaps for guideline recommendations absent from note or noted as cancelled/unperformed.", table_cell)],
        [Paragraph("FR-09", table_cell_bold), Paragraph("Timeline Reconstruction", table_cell), Paragraph("Synthesize a chronological event sequence with categorized condition, regimen, and test lifecycle cards.", table_cell)],
        [Paragraph("FR-10", table_cell_bold), Paragraph("Dataset Record Browser", table_cell), Paragraph("Provide searchable, paginated access to 4,966 MTSamples clinical records with one-click editor population.", table_cell)],
    ]
    fr_table = Table(fr_data, colWidths=[38, 115, PW - 153])
    fr_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_navy),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(fr_table)

    story.append(Paragraph("4.2 Non-Functional Considerations", h2_style))
    story.append(Paragraph(
        "• <b>Auditability & Determinism:</b> Identical clinical input text must produce identical entity, rule, and gap results across multiple runs.<br/>"
        "• <b>Resilience & Graceful Degradation:</b> If heavyweight models encounter environment limits, the system "
        "must seamlessly fall back to dictionary and regex tiers without raising 500 server errors.<br/>"
        "• <b>Performance & Responsiveness:</b> Sub-second analysis response for standard clinical notes (<1,000 words); optimized pagination for large datasets.<br/>"
        "• <b>Thread Safety:</b> SQLite database configured with check_same_thread=False and scoped SQLAlchemy sessions for concurrent request safety.",
        body_style
    ))

    story.append(Paragraph("4.3 Division of Responsibilities", h2_style))
    story.append(Paragraph(
        "The architecture enforces strict separation of concerns. The <b>React 18 frontend</b> manages user interaction, UI routing across 8 modules, "
        "local state persistence via AnalysisContext, file upload packaging, and result visualization. The <b>FastAPI backend</b> handles document parsing, "
        "NLP pipeline orchestration, knowledge base querying, SQLite transactions, and structured JSON serialization.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 5: TECHNOLOGY STACK
    # =========================================================================
    story.append(Paragraph("Chapter 5: Technology Stack", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph(
        "Every technology incorporated into ClinGap-NLP was selected to fulfill a specific operational requirement. "
        "The table below documents the verified technology stack based on active source code inspection and runtime status verification:",
        body_style
    ))

    tech_data = [
        [Paragraph("<b>Technology</b>", table_header), Paragraph("<b>Role & Runtime Status</b>", table_header), Paragraph("<b>Operational Implementation & Usage</b>", table_header), Paragraph("<b>Key Source File / Config</b>", table_header)],
        [Paragraph("Python 3.13.3", table_cell_bold), Paragraph("Backend Runtime<br/>(<b>Active</b>)", table_cell), Paragraph("Core execution engine for ASGI server, NLP processing, and data services.", table_cell), Paragraph("clinngap_nlp/backend/*", table_cell_code)],
        [Paragraph("FastAPI 0.115+", table_cell_bold), Paragraph("REST API Framework<br/>(<b>Active</b>)", table_cell), Paragraph("Asynchronous web server providing endpoints for analysis, uploads, dataset browsing, and health checks.", table_cell), Paragraph("backend/main.py<br/>backend/api/*", table_cell_code)],
        [Paragraph("Uvicorn (Standard)", table_cell_bold), Paragraph("ASGI Web Server<br/>(<b>Active</b>)", table_cell), Paragraph("Production ASGI HTTP server hosting FastAPI on port 8001 with hot reload.", table_cell), Paragraph("backend/main.py", table_cell_code)],
        [Paragraph("React 18.3.1", table_cell_bold), Paragraph("Frontend UI Library<br/>(<b>Active</b>)", table_cell), Paragraph("Single Page Application managing component lifecycle, state, and routing across 8 modules.", table_cell), Paragraph("frontend-react/src/App.jsx", table_cell_code)],
        [Paragraph("Vite 6.1.0 / 6.4.3", table_cell_bold), Paragraph("Frontend Build Tool<br/>(<b>Active</b>)", table_cell), Paragraph("Modern build engine providing instant HMR development server (Port 3001) and optimized production bundles.", table_cell), Paragraph("frontend-react/vite.config.js<br/>package.json", table_cell_code)],
        [Paragraph("Tailwind CSS 3.4.17", table_cell_bold), Paragraph("UI Styling System<br/>(<b>Active</b>)", table_cell), Paragraph("Utility-first CSS framework defining clinical theme tokens, responsive layouts, badges, and cards.", table_cell), Paragraph("frontend-react/tailwind.config.js<br/>src/index.css", table_cell_code)],
        [Paragraph("Lucide React 0.475", table_cell_bold), Paragraph("Iconography Library<br/>(<b>Active</b>)", table_cell), Paragraph("Clean clinical iconography for navigation, alert statuses, entity tags, and actions.", table_cell), Paragraph("frontend-react/package.json", table_cell_code)],
        [Paragraph("Axios 1.7.9", table_cell_bold), Paragraph("HTTP Client<br/>(<b>Active</b>)", table_cell), Paragraph("Primary REST client communicating with FastAPI backend; paired with native Fetch fallback.", table_cell), Paragraph("frontend-react/src/services/api.js", table_cell_code)],
        [Paragraph("Hugging Face Transformers", table_cell_bold), Paragraph("Primary Biomedical NER<br/>(<b>Active on CPU</b>)", table_cell), Paragraph("Runs token classification using d4data/biomedical-ner-all (CPU pipeline with 128-token overlap stride).", table_cell), Paragraph("backend/services/ner_service.py", table_cell_code)],
        [Paragraph("Bio_ClinicalBERT", table_cell_bold), Paragraph("Context Embeddings<br/>(<b>Active from Cache</b>)", table_cell), Paragraph("Generates 768-dim contextual text embeddings via emilyalsentzer/Bio_ClinicalBERT; TF-IDF fallback ready.", table_cell), Paragraph("backend/services/context_service.py<br/>model_manager.py", table_cell_code)],
        [Paragraph("spaCy / scispaCy", table_cell_bold), Paragraph("Secondary NER Layer<br/>(<b>Unavailable / Fallback</b>)", table_cell), Paragraph("en_ner_bc5cdr_md is not installed in the environment; ModelManager logs fallback to dictionaries.", table_cell), Paragraph("backend/services/model_manager.py", table_cell_code)],
        [Paragraph("Curated Lexicons", table_cell_bold), Paragraph("Tertiary Clinical Dicts<br/>(<b>Active</b>)", table_cell), Paragraph("JSON dictionaries for diseases, symptoms, medications, and investigations with canonical normalization.", table_cell), Paragraph("knowledge_base/*.json<br/>backend/services/ner_service.py", table_cell_code)],
        [Paragraph("Python re (Regex)", table_cell_bold), Paragraph("Pattern Extraction<br/>(<b>Active</b>)", table_cell), Paragraph("Quaternary layer extracting medication dosages, frequencies, and lab measurement boundary guards.", table_cell), Paragraph("backend/services/ner_service.py<br/>prescription_service.py", table_cell_code)],
        [Paragraph("SQLAlchemy 2.0+", table_cell_bold), Paragraph("Database ORM<br/>(<b>Active</b>)", table_cell), Paragraph("Object-relational mapping defining Patient, Document, and ClinicalEntity schemas.", table_cell), Paragraph("backend/database.py<br/>backend/models/*", table_cell_code)],
        [Paragraph("SQLite 3", table_cell_bold), Paragraph("Relational Storage<br/>(<b>Active</b>)", table_cell), Paragraph("Embedded database storage hosting clinngap.db for patient notes and extracted clinical records.", table_cell), Paragraph("clinngap.db", table_cell_code)],
        [Paragraph("PyMuPDF / pypdf", table_cell_bold), Paragraph("PDF Document Extraction<br/>(<b>Active</b>)", table_cell), Paragraph("Extracts text streams from clinical PDF files without external runtime binaries via fitz (PyMuPDF 1.27.2).", table_cell), Paragraph("backend/services/document_parser.py", table_cell_code)],
        [Paragraph("zipfile / xml.etree", table_cell_bold), Paragraph("DOCX Text Extraction<br/>(<b>Active</b>)", table_cell), Paragraph("Pure standard-library OpenXML parser extracting clinical text from Word (.docx) files.", table_cell), Paragraph("backend/services/document_parser.py", table_cell_code)],
        [Paragraph("Pandas 2.2+", table_cell_bold), Paragraph("Dataset Indexing<br/>(<b>Active</b>)", table_cell), Paragraph("Loads, caches, and filters 4,966 MTSamples clinical transcriptions across 40 specialties.", table_cell), Paragraph("backend/services/dataset_service.py", table_cell_code)],
        [Paragraph("Pytest 9.1.1", table_cell_bold), Paragraph("Automated Testing<br/>(<b>Active</b>)", table_cell), Paragraph("Executes 56 unit, integration, and regression test cases verifying clinical extraction and reasoning.", table_cell), Paragraph("clinngap_nlp/tests/*", table_cell_code)],
    ]
    tech_table = Table(tech_data, colWidths=[85, 95, PW - 290, 110])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_navy),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(tech_table)

    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Detailed Fallback Architecture Verification</b>", h3_style))
    story.append(Paragraph(
        "<b>ModelManager Resilience:</b> In the actual development environment, external transformer models and specialized spaCy packages "
        "(such as <code>en_ner_bc5cdr_md</code>) may experience network constraints or package incompatibilities. The <code>ModelManager</code> "
        "class explicitly catches import/load exceptions and gracefully logs: <i>'Falling back to dictionary based NER'</i> and <i>'Falling back "
        "to TF-IDF'</i>. Crucially, the <code>ClinicalPipeline</code> is engineered so that guideline matching and gap detection remain "
        "100% deterministic and functional even when running in fallback mode.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 6: PROJECT FOLDER STRUCTURE
    # =========================================================================
    story.append(Paragraph("Chapter 6: Project Folder Structure", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph(
        "The ClinGap-NLP codebase adheres to a modular, decoupled architectural layout separating the FastAPI backend, "
        "the React 18 SPA frontend, standalone clinical pipeline utilities, knowledge base dictionaries, and automated test suites. "
        "The complete file hierarchy is documented below across four structured functional subsystems:",
        body_style
    ))

    story.append(Paragraph("6.1 Backend API, Services, and Persistence Subsystem (backend/)", h2_style))
    backend_tree = (
        "clinngap_nlp/backend/\n"
        "├── api/                      # REST Route Handlers\n"
        "│   ├── __init__.py           # Package marker\n"
        "│   ├── analysis.py           # POST /api/analyze (Pipeline execution & schema response)\n"
        "│   ├── dataset.py            # GET /api/dataset/mtsamples/* (Search, specialties, & records)\n"
        "│   ├── health.py             # GET /api/health (Liveness probe)\n"
        "│   └── upload.py             # POST /api/upload (.txt, .pdf, .docx ingestion & extraction)\n"
        "├── models/                   # SQLAlchemy Relational Models\n"
        "│   ├── __init__.py           # Model exports\n"
        "│   ├── clinical_entity.py    # ClinicalEntity model (document_id, text, type, conf, negated)\n"
        "│   ├── document.py           # Document model (patient_id, title, content, type, created_at)\n"
        "│   └── patient.py            # Patient model (id, name, documents relationship)\n"
        "├── services/                 # Core Business & Clinical NLP Services\n"
        "│   ├── clinical_pipeline.py  # Master pipeline orchestrator (NER, negation, guidelines, gaps)\n"
        "│   ├── confidence_service.py # Weighted confidence computation formula\n"
        "│   ├── context_service.py    # Bio_ClinicalBERT & TF-IDF text embedding\n"
        "│   ├── dataset_service.py    # MTSamples CSV query, specialty filtering, & DataFrame caching\n"
        "│   ├── document_parser.py    # Multi-format parser (.txt, .pdf, .docx without external binaries)\n"
        "│   ├── explainability_service.py # Structured audit explanation tree generator\n"
        "│   ├── gap_detection.py      # Missing & unperformed investigation auditor\n"
        "│   ├── guideline_service.py  # Deterministic criteria matcher against guidelines.json\n"
        "│   ├── model_manager.py      # Lazy model loader with dictionary & TF-IDF fallbacks\n"
        "│   ├── negation_service.py   # Clausal bidirectional negation detection & investigation scoping\n"
        "│   ├── ner_service.py        # 4-Tier Hybrid NER (BioBERT, spaCy, Dicts, Regex, lab guards)\n"
        "│   └── prescription_service.py # Regimen proximity reconstructor with unit disambiguation\n"
        "├── database.py               # SQLite engine, SessionLocal, Base declarative setup\n"
        "└── main.py                   # FastAPI ASGI entrypoint, CORS middleware & router binding\n"
    )
    story.append(make_code_box(backend_tree))
    story.append(Spacer(1, 6))

    story.append(Paragraph("6.2 Frontend Single Page Application Subsystem (frontend-react/)", h2_style))
    frontend_tree = (
        "clinngap_nlp/frontend-react/\n"
        "├── src/\n"
        "│   ├── components/           # Reusable UI Primitives & Layout Containers\n"
        "│   │   ├── common/           # Button, Card, Badge, Modal reusable components\n"
        "│   │   └── layout/           # Header, Sidebar, Layout master shell\n"
        "│   ├── context/              # Central State Providers\n"
        "│   │   └── AnalysisContext.jsx # Single-source state provider & localStorage synchronizer\n"
        "│   ├── pages/                # 8 Interactive Functional Module Views\n"
        "│   │   ├── AboutPage.jsx     # System architecture overview & clinical safety disclaimer\n"
        "│   │   ├── ClinicalInputPage.jsx # Text editor, Presets, File Upload, MTSamples Explorer\n"
        "│   │   ├── DashboardPage.jsx # Statistical overview, gap metrics, & quick action cards\n"
        "│   │   ├── EntityExtractionPage.jsx # Extracted entity viewer with filtering & confidence badges\n"
        "│   │   ├── GapDetectionPage.jsx # Missing investigation gap audit & severity views\n"
        "│   │   ├── GuidelineMatchingPage.jsx # Activated guideline rule inspector & criteria viewer\n"
        "│   │   ├── PrescriptionPage.jsx # Reconstructed medication regimen table & lab guards\n"
        "│   │   └── TimelinePage.jsx  # Chronological clinical event & test lifecycle tracker\n"
        "│   ├── services/             # Frontend Network Client\n"
        "│   │   └── api.js            # Axios client with automatic native Fetch fallback\n"
        "│   ├── App.jsx               # Tab-based router and root provider wrapper\n"
        "│   ├── index.css             # Tailwind CSS directives & custom clinical styling tokens\n"
        "│   └── main.jsx              # React DOM entrypoint (strict mode)\n"
        "├── package.json              # React 18, Vite 6, Tailwind CSS 3.4 dependencies\n"
        "└── vite.config.js            # Vite configuration & React plugin setup\n"
    )
    story.append(make_code_box(frontend_tree))
    story.append(Spacer(1, 6))

    story.append(Paragraph("6.3 Standalone Pipeline & Medical Knowledge Base (pipeline/ & knowledge_base/)", h2_style))
    pipeline_tree = (
        "clinngap_nlp/\n"
        "├── pipeline/                 # Standalone / Modular Clinical NLP Package\n"
        "│   ├── confidence.py         # Weighted confidence metric formula\n"
        "│   ├── context_analysis.py   # Context model metadata injector\n"
        "│   ├── gap_detection.py      # Standalone decision gap detector\n"
        "│   ├── guideline_engine.py   # Standalone guideline rule matcher\n"
        "│   ├── hybrid_ner.py         # Standalone NER runner\n"
        "│   ├── investigation_extractor.py # Standalone investigation keyword extractor\n"
        "│   ├── negation.py           # Standalone clausal negation handler\n"
        "│   ├── preprocess.py         # Whitespace & character normalization\n"
        "│   ├── prescription_parser.py# Standalone prescription parser\n"
        "│   ├── run.py                # Standalone end-to-end pipeline runner\n"
        "│   ├── text_processor.py     # Regex baseline text processor\n"
        "│   └── timeline.py           # Chronological timeline & summary generator\n"
        "├── knowledge_base/           # Curated Medical Knowledge Dictionaries\n"
        "│   ├── diseases.json         # Canonical disease terms, synonyms, & categories (HTN, DM, Asthma)\n"
        "│   ├── guidelines.json       # Clinical guideline rules (R1, R2, R3)\n"
        "│   ├── investigations.json   # Diagnostic tests & synonyms (CBC, HbA1c, Chest X-ray)\n"
        "│   ├── medications.json      # Pharmaceutical names (metformin, lisinopril, salbutamol, etc.)\n"
        "│   └── symptoms.json         # Symptom terminology (chest pain, dizziness, cough, fever)\n"
    )
    story.append(make_code_box(pipeline_tree))
    story.append(Spacer(1, 6))

    story.append(Paragraph("6.4 Corpus Datasets, Benchmarks, Scripts, and Automated Tests", h2_style))
    misc_tree = (
        "clinngap_nlp/\n"
        "├── data/\n"
        "│   ├── datasets/mtsamples_clean.csv # 4,966 Cleaned MTSamples clinical records (40 specialties)\n"
        "│   └── demo/case1.txt        # Benchmark clinical note for automated testing & seeding\n"
        "├── tests/                    # Automated Pytest Suite (56 Passing Tests)\n"
        "│   ├── test_clinical_extraction_fixes.py # 33 Regression tests (units, statuses, scope)\n"
        "│   ├── test_ner.py           # 9 NER tests (HF, dictionaries, regex, deduplication)\n"
        "│   ├── test_pipeline_case1.py# 1 End-to-end pipeline integration test\n"
        "│   ├── test_prescription.py  # 3 Prescription parsing tests\n"
        "│   └── test_prescription_end_to_end.py # 10 Regimen proximity pairing tests\n"
        "├── scripts/                  # Utility Scripts\n"
        "│   └── seed_database.py      # SQLite database schema creation & demo seeding\n"
        "├── clinngap.db               # Active SQLite relational database\n"
        "├── config.py                 # Environment variable configuration loader\n"
        "└── requirements.txt          # Backend Python dependencies\n"
    )
    story.append(make_code_box(misc_tree))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 7: SYSTEM ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("Chapter 7: System Architecture", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph("7.1 Multi-Tier Architectural Topology", h2_style))
    story.append(Paragraph(
        "ClinGap-NLP is structured around a decoupled, 5-tier architecture that guarantees clean boundaries between presentation, "
        "API orchestration, NLP extraction, deterministic reasoning, and data persistence:",
        body_style
    ))

    # Architecture Vector Block Diagram (Rendered as styled table)
    arch_diagram_data = [
        [Paragraph("<b>PRESENTATION LAYER: React 18 + Vite SPA (Port 3001)</b>", table_header)],
        [Paragraph(
            "<b>Interactive Pages:</b> DashboardPage • ClinicalInputPage • EntityExtractionPage • GuidelineMatchingPage • "
            "GapDetectionPage • PrescriptionPage • TimelinePage • AboutPage<br/>"
            "<b>State & Client:</b> AnalysisContext (Single-Source State & LocalStorage Sync) • api.js (Axios Client with Fetch Fallback)",
            table_cell
        )],
        [Paragraph("<b>&darr;&nbsp;&nbsp;HTTP / REST over JSON (CORS Enabled, Ports 3001 &harr; 8001)&nbsp;&nbsp;&darr;</b>", ParagraphStyle('Arrow', fontName='Helvetica-Bold', fontSize=7.5, textColor=c_navy, alignment=1))],
        [Paragraph("<b>API & SERVICE ORCHESTRATION LAYER: FastAPI ASGI (Port 8001)</b>", table_header)],
        [Paragraph(
            "<b>Entrypoint:</b> backend/main.py (Uvicorn Worker, CORS Middleware, Error Handlers)<br/>"
            "<b>Endpoints:</b> /api/analyze (Pipeline) • /api/upload (Multi-Format Parser) • /api/dataset/mtsamples/* (Search/Records) • /api/health<br/>"
            "<b>Pipeline Coordinator:</b> backend/services/clinical_pipeline.py (Master Execution Orchestrator)",
            table_cell
        )],
        [Paragraph("<b>&darr;&nbsp;&nbsp;In-Memory Data Pipeline Objects (Entities, Spans, Regimens)&nbsp;&nbsp;&darr;</b>", ParagraphStyle('Arrow', fontName='Helvetica-Bold', fontSize=7.5, textColor=c_navy, alignment=1))],
        [Paragraph("<b>CLINICAL NLP PIPELINE LAYER: 4-Tier Hybrid NER & Context Services</b>", table_header)],
        [Paragraph(
            "<b>Tier 1 (Primary - Active):</b> Hugging Face <i>d4data/biomedical-ner-all</i> Token Classification (BioBERT, CPU, Stride=128)<br/>"
            "<b>Tier 2 (Secondary - Status):</b> spaCy Model via ModelManager (en_ner_bc5cdr_md, Unavailable in environment; fallback active)<br/>"
            "<b>Tier 3 (Lexical - Active):</b> Curated Clinical Dictionaries (Diseases, Symptoms, Medications, Investigations)<br/>"
            "<b>Tier 4 (Regex - Active):</b> Pattern Matchers (Dosage Regex, Frequency Regex, Lab Measurement Exclusion Guards)<br/>"
            "<b>Context & Negation:</b> negation_service.py (Clausal Scope) • context_service.py (Bio_ClinicalBERT 768-dim Embeddings)",
            table_cell
        )],
        [Paragraph("<b>&darr;&nbsp;&nbsp;Normalized Entities & Lifecycle States&nbsp;&nbsp;&darr;</b>", ParagraphStyle('Arrow', fontName='Helvetica-Bold', fontSize=7.5, textColor=c_navy, alignment=1))],
        [Paragraph("<b>REASONING & AUDIT LAYER: Deterministic Clinical Logic & Prescription Studio</b>", table_header)],
        [Paragraph(
            "<b>Guideline Matcher:</b> guideline_service.py (Evaluates Non-Negated Entities against prototype guidelines.json)<br/>"
            "<b>Gap Detection Auditor:</b> gap_detection.py (Detects Missing Investigations & Flags Explicitly Cancelled Tests)<br/>"
            "<b>Regimen Reconstructor:</b> prescription_service.py (Clause Proximity Associator for Medication, Dose, & Frequency)<br/>"
            "<b>Scoring & Explainability:</b> confidence_service.py (Weighted Confidence) • explainability_service.py (Audit Trees)",
            table_cell
        )],
        [Paragraph("<b>&darr;&nbsp;&nbsp;Persistence, Caching, & Model Weights&nbsp;&nbsp;&darr;</b>", ParagraphStyle('Arrow', fontName='Helvetica-Bold', fontSize=7.5, textColor=c_navy, alignment=1))],
        [Paragraph("<b>DATA & PERSISTENCE LAYER: SQLite Database & Clinical Lexicons</b>", table_header)],
        [Paragraph(
            "<b>Relational Storage:</b> SQLite (clinngap.db via SQLAlchemy: patients, documents, clinical_entities)<br/>"
            "<b>Knowledge Base:</b> JSON Dictionaries (diseases.json, guidelines.json, investigations.json, medications.json, symptoms.json)<br/>"
            "<b>Corpus Repository:</b> data/datasets/mtsamples_clean.csv (4,966 records indexed via Pandas)",
            table_cell
        )],
    ]
    arch_table = Table(arch_diagram_data, colWidths=[PW])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_navy),
        ('BACKGROUND', (0,1), (-1,1), c_bg_light),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#F1F5F9")),
        ('BACKGROUND', (0,3), (-1,3), c_teal_dark),
        ('BACKGROUND', (0,4), (-1,4), c_bg_light),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor("#F1F5F9")),
        ('BACKGROUND', (0,6), (-1,6), c_blue),
        ('BACKGROUND', (0,7), (-1,7), c_bg_light),
        ('BACKGROUND', (0,8), (-1,8), colors.HexColor("#F1F5F9")),
        ('BACKGROUND', (0,9), (-1,9), c_navy),
        ('BACKGROUND', (0,10), (-1,10), c_bg_light),
        ('BACKGROUND', (0,11), (-1,11), colors.HexColor("#F1F5F9")),
        ('BACKGROUND', (0,12), (-1,12), colors.HexColor("#334155")),
        ('BACKGROUND', (0,13), (-1,13), c_bg_light),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(arch_table)

    story.append(Spacer(1, 6))
    story.append(Paragraph("7.2 Inter-Tier Data Flow and Communication Protocols", h2_style))
    story.append(Paragraph(
        "Communication between the React frontend and FastAPI backend is strictly stateless and REST-compliant. When a user enters "
        "a clinical note or selects a preset, the frontend dispatches a <code>POST /api/analyze</code> payload containing <code>patient_id</code>, "
        "<code>document_id</code>, and the clinical <code>text</code>. The backend executes the pipeline synchronously on CPU with singleton model caching "
        "and responds with a fully populated JSON document containing extracted entities, clausal negation flags, reconstructed regimens, "
        "investigation lifecycle statuses, guideline activations, and detected documentation gaps.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 8: END-TO-END WORKFLOW
    # =========================================================================
    story.append(Paragraph("Chapter 8: End-to-End Workflow", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph(
        "The complete execution lifecycle of ClinGap-NLP progresses through 11 distinct processing stages, spanning user ingestion "
        "to interactive dashboard rendering:",
        body_style
    ))

    workflow_steps = [
        ("Stage 1: Document Ingestion", "User provides clinical text via manual input, preset selection, or file upload (.txt, .pdf, .docx). Uploaded files are decoded into UTF-8 text via document_parser.py."),
        ("Stage 2: Text Preprocessing", "Text undergoes whitespace normalization, sentence boundary detection, and special character sanitization while preserving vital clinical punctuation (e.g., blood pressure slashes and decimal points)."),
        ("Stage 3: Hybrid 4-Tier NER Extraction", "The text is evaluated sequentially across the 4-tier NER architecture: (1) Hugging Face BioBERT token classifier, (2) spaCy model if available, (3) clinical dictionaries, and (4) dosage/frequency regex patterns."),
        ("Stage 4: Unit Disambiguation & Guarding", "Extracted candidates undergo lab measurement filtering. Numeric laboratory units (e.g., 218 mg/dL, 148/92 mmHg, 38.2°C) are rejected from being classified as medication dosages or drug names."),
        ("Stage 5: Clausal Negation Scoping", "Sentence clauses are parsed for bidirectional negation triggers (e.g., 'denies', 'no', 'without', 'not performed'). Target entities are marked with negated=True; active orders are preserved."),
        ("Stage 6: Investigation Lifecycle Resolution", "Every diagnostic test mention is classified into one of four lifecycle states: ORDERED/PENDING, pending, completed/performed, or not performed based on clausal modal verbs and results."),
        ("Stage 7: Proximity Regimen Reconstruction", "Medications are mapped against dosage and frequency spans. A directional proximity search pairs each drug with its nearest following dose and frequency within sentence boundaries."),
        ("Stage 8: Contextual Embedding Computation", "A 768-dimensional contextual vector is generated via Bio_ClinicalBERT (or TF-IDF fallback) to capture holistic semantic document representation for downstream auditing."),
        ("Stage 9: Deterministic Guideline Evaluation", "Non-negated patient entities (diseases, symptoms) are matched against prerequisite criteria in guidelines.json. Matched rules and their diagnostic recommendations are compiled."),
        ("Stage 10: Decision Gap Audit & Scoring", "The gap auditor checks whether recommended investigations are present and completed. Missing or cancelled tests emit MISSING_INVESTIGATION gaps. A mathematical confidence score is calculated."),
        ("Stage 11: Reactive Dashboard Rendering", "FastAPI returns the composite JSON payload. React's AnalysisContext updates all global state and persists to localStorage. Results instantly populate all 8 interactive tabs."),
    ]

    wf_table_data = [[Paragraph("<b>Stage & Sequence</b>", table_header), Paragraph("<b>Detailed Processing Logic & Operational Behavior</b>", table_header)]]
    for s_title, s_desc in workflow_steps:
        wf_table_data.append([Paragraph(f"<b>{s_title}</b>", table_cell_bold), Paragraph(s_desc, table_cell)])

    wf_table = Table(wf_table_data, colWidths=[130, PW - 130])
    wf_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_navy),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(wf_table)

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 9: DETAILED MODULE-WISE IMPLEMENTATION
    # =========================================================================
    story.append(Paragraph("Chapter 9: Detailed Module-Wise Implementation", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph(
        "This chapter provides an exhaustive, code-level examination of each core module implemented in ClinGap-NLP. "
        "All specifications reflect active source code in <code>clinngap_nlp/</code>.",
        body_style
    ))

    # 9.1 Document Parser
    story.append(Paragraph("9.1 Multi-Format Document Parser (document_parser.py & upload.py)", h2_style))
    story.append(Paragraph(
        "<b>Purpose:</b> Ingests clinical notes and prescriptions in plain text (.txt), PDF (.pdf), and Microsoft Word (.docx) formats, "
        "extracting clean textual streams without requiring external runtime binaries or cloud APIs.<br/>"
        "<b>Source Path:</b> <code>backend/services/document_parser.py</code> and <code>backend/api/upload.py</code>.<br/>"
        "<b>Implementation Logic:</b><br/>"
        "• <i>Plain Text (.txt):</i> Decodes raw bytes using an encoding cascade: UTF-8 &rarr; Latin-1 &rarr; CP1252 &rarr; ASCII with replace fallback.<br/>"
        "• <i>PDF Documents (.pdf):</i> Utilizes <code>fitz</code> (PyMuPDF) stream opening to iterate over pages and concatenate text streams. "
        "If PyMuPDF encounters an issue, it falls back to <code>pypdf.PdfReader</code>.<br/>"
        "• <i>DOCX Documents (.docx):</i> Directly unzips the OpenXML package in memory via <code>zipfile.ZipFile</code>, parses <code>word/document.xml</code> "
        "via <code>xml.etree.ElementTree</code>, and extracts text within paragraph <code>&lt;w:p&gt;</code> and text <code>&lt;w:t&gt;</code> nodes with regex fallback.<br/>"
        "<b>API Contract:</b> <code>POST /api/upload</code> accepts multipart/form-data and returns JSON: "
        "<code>{filename, file_type, text, char_count, word_count, preview}</code>.",
        body_style
    ))

    # 9.2 Text Preprocessor
    story.append(Paragraph("9.2 Text Preprocessing and Normalization (preprocess.py & text_processor.py)", h2_style))
    story.append(Paragraph(
        "<b>Purpose:</b> Normalizes raw clinical text to ensure uniform whitespace, standard line breaks, and consistent encoding "
        "while rigorously preserving clinical numerals, units, and punctuation.<br/>"
        "<b>Source Path:</b> <code>pipeline/preprocess.py</code> and <code>pipeline/text_processor.py</code>.<br/>"
        "<b>Implementation Logic:</b> Executes <code>' '.join(text.split()).strip()</code> to collapse redundant spaces and tab characters. "
        "Guarantees that vital clinical compound expressions such as <code>148/92 mmHg</code>, <code>38.2°C</code>, and <code>218 mg/dL</code> "
        "remain intact for downstream tokenization.",
        body_style
    ))

    # 9.3 Hybrid NER Service
    story.append(Paragraph("9.3 Hybrid 4-Tier Named Entity Recognition (ner_service.py)", h2_style))
    story.append(Paragraph(
        "<b>Purpose:</b> Extracts clinical entities across six categories (DISEASE, SYMPTOM, MEDICATION, INVESTIGATION, DOSAGE, FREQUENCY) "
        "using a prioritized four-layer hybrid architecture.<br/>"
        "<b>Source Path:</b> <code>backend/services/ner_service.py</code>.<br/>"
        "<b>Four-Layer Architecture:</b><br/>"
        "1. <b>Layer 1 (Hugging Face Transformer - Active):</b> Loads <code>d4data/biomedical-ner-all</code> via a lazy singleton pipeline "
        "(token-classification, aggregation_strategy='simple', CPU device=-1). Uses a 128-token overlapping stride to handle long documents "
        "without boundary truncation. Maps model labels (Disease_disorder &rarr; DISEASE, Medication &rarr; MEDICATION, etc.) with a minimum "
        "confidence threshold of 0.60.<br/>"
        "2. <b>Layer 2 (spaCy via ModelManager - Fallback):</b> Invokes <code>ModelManager.load_ner()</code> to run <code>en_ner_bc5cdr_md</code>. "
        "In the current execution environment, spaCy is not installed, so the service logs a fallback message and delegates to Layers 3 and 4.<br/>"
        "3. <b>Layer 3 (Curated Dictionaries - Active):</b> Performs regex exact matching against sorted lexicon keys (longest match first) from "
        "<code>knowledge_base/</code> for diseases, symptoms, medications, and investigations. Overlapping spans are skipped.<br/>"
        "4. <b>Layer 4 (Regex Patterns - Active):</b> Matches dosage patterns (<code>DOSAGE_PATTERN</code>) and frequencies (<code>FREQ_PATTERN</code>).<br/>"
        "<b>Disambiguation & Deduplication:</b><br/>"
        "• <i>Noise Token Filtering:</i> Generic stop words, WordPiece stubs ('##ing'), and document header words are stripped.<br/>"
        "• <i>Nested Entity Suppression:</i> If a shorter entity is strictly nested within a longer entity of the same category throughout the text "
        "(e.g., 'tension' inside 'hypertension'), the shorter entity is suppressed.<br/>"
        "• <i>Lab Measurement Guard:</i> Calls <code>_is_lab_measurement_or_non_medication()</code> to ensure terms matching lab patterns (e.g. 218 mg/dL) "
        "are never tagged as medications or dosages.",
        body_style
    ))

    # 9.4 Negation Service
    story.append(Paragraph("9.4 Clausal Negation Detection (negation_service.py)", h2_style))
    story.append(Paragraph(
        "<b>Purpose:</b> Scopes negation triggers within sentence clauses to accurately determine whether clinical findings are asserted or denied.<br/>"
        "<b>Source Path:</b> <code>backend/services/negation_service.py</code>.<br/>"
        "<b>Implementation Logic:</b><br/>"
        "• <i>Sentence/Clause Splitting:</i> Splits text on sentence and clause boundaries (<code>[.\\n;]</code>).<br/>"
        "• <i>Prefix Regex (pattern_pre):</i> Matches negation cues (<code>no, without, absence of, denies, denied, not, never</code>) "
        "occurring up to 8 tokens before the entity: <code>\\b(?:...)\\b(?:[\\s,/-]+[\\w-]+){0,8}\\s*\\b{ent_text}\\b</code>.<br/>"
        "• <i>Suffix Regex (pattern_post):</i> Matches post-entity cues (<code>not performed, was not performed, negative, absent</code>) "
        "occurring up to 6 tokens after the entity: <code>\\b{ent_text}\\b(?:\\s*\\([^)]*\\))?(?:[\\s,/-]+[\\w-]+){0,6}\\s*\\b(?:...)\\b</code>.<br/>"
        "• <i>Compound Scoping:</i> Accurately handles coordinated symptoms across conjunctions (e.g., 'denies chest pain and dizziness' marks both "
        "chest pain and dizziness as negated).<br/>"
        "• <i>Investigation Overrides:</i> For investigations, delegates to <code>extract_investigation_status()</code>. If status is "
        "<code>ORDERED/PENDING</code>, <code>pending</code>, <code>ordered</code>, or <code>completed/performed</code>, the entity's negated flag is "
        "strictly forced to <code>False</code> to prevent false-positive missing gaps.",
        body_style
    ))

    # 9.5 Prescription Service
    story.append(Paragraph("9.5 Prescription Parsing & Regimen Reconstruction (prescription_service.py)", h2_style))
    story.append(Paragraph(
        "<b>Purpose:</b> Reconstructs structured medication regimens, associating each distinct pharmaceutical agent with its valid dosage "
        "strength and dosing frequency while avoiding cross-pairing across clauses.<br/>"
        "<b>Source Path:</b> <code>backend/services/prescription_service.py</code>.<br/>"
        "<b>Implementation Logic:</b><br/>"
        "• <i>Medication Collection:</i> Extracts distinct medications from NER entities (or falls back to <code>medications.json</code>). "
        "Filters out clinical noise terms (e.g., 'medication', 'pill', 'tablet').<br/>"
        "• <i>Span Extraction:</i> Locates character start/end spans for all medication occurrences, dosage matches (via <code>DOSAGE_REGEX</code>), "
        "and frequency matches (via <code>FREQ_REGEX</code>).<br/>"
        "• <i>Proximity Directional Pairing:</i> For each medication, computes forward distance to dosage spans (within 120 chars) and frequency "
        "spans (within 150 chars). Backward distances are penalized by a factor of 2.0 to enforce forward reading order.<br/>"
        "• <i>Output Schema:</i> Returns a list of dicts: <code>[{'medication': str, 'dosage': Optional[str], 'frequency': Optional[str]}]</code>.",
        body_style
    ))

    story.append(PageBreak())

    # 9.6 Investigation Status Extractor
    story.append(Paragraph("9.6 Investigation Status Lifecycle Analysis (ner_service.py::extract_investigation_status)", h2_style))
    story.append(Paragraph(
        "<b>Purpose:</b> Implements a deterministic state machine to classify diagnostic test mentions into four clinical lifecycle states.<br/>"
        "<b>Source Path:</b> <code>backend/services/ner_service.py</code> (lines 131–205).<br/>"
        "<b>Lifecycle State Rules:</b><br/>"
        "1. <b>ORDERED/PENDING:</b> Clause contains ordering verbs (<i>was ordered, is ordered, requested, scheduled for</i>) AND explicit "
        "unperformed/pending indicators (<i>not yet performed, yet to be done, awaiting performance</i>). Example: 'Chest X-ray has been requested "
        "but has not yet been performed.'<br/>"
        "2. <b>pending:</b> Clause indicates results are awaited (<i>not yet available, results pending, awaiting results, in progress</i>). "
        "Example: 'CBC was ordered but the result is not yet available.'<br/>"
        "3. <b>not performed:</b> Entity is negated or clause contains cancellation/omission keywords (<i>was not performed, declined, refused, "
        "cancelled, discontinued</i>). Example: 'Urine test was cancelled and not performed.'<br/>"
        "4. <b>completed/performed:</b> Clause contains completion cues (<i>completed, was performed, performed, showed, reveals, result was</i>) "
        "or explicit numeric lab values. Example: 'HbA1c was performed and showed 8.1%.'",
        body_style
    ))

    # 9.7 Timeline Generator
    story.append(Paragraph("9.7 Clinical Timeline Generation (timeline.py)", h2_style))
    story.append(Paragraph(
        "<b>Purpose:</b> Synthesizes chronological clinical trajectories and structured summaries categorizing conditions, regimens, and investigations.<br/>"
        "<b>Source Path:</b> <code>pipeline/timeline.py</code>.<br/>"
        "<b>Implementation Logic:</b><br/>"
        "• <code>format_investigation_timeline_status()</code> maps raw statuses to clean display badges: 'Ordered / Pending', 'Pending Results', "
        "'Performed', 'Not performed'.<br/>"
        "• <code>build_timeline_summary()</code> integrates reconstructed regimens from <code>prescription_service</code>, guaranteeing that each "
        "medication's dosage and frequency stay bound to that specific drug (eliminating array-index mismatch bugs).",
        body_style
    ))

    # 9.8 Guideline Service
    story.append(Paragraph("9.8 Guideline Matching Engine (guideline_service.py & guidelines.json)", h2_style))
    story.append(Paragraph(
        "<b>Purpose:</b> Deterministically evaluates non-negated patient entities against configured prototype rules.<br/>"
        "<b>Source Path:</b> <code>backend/services/guideline_service.py</code> and <code>knowledge_base/guidelines.json</code>.<br/>"
        "<b>Matching Algorithm:</b><br/>"
        "Loads prototype rule definitions from JSON. Extracts all non-negated entity types: <code>{e['entity_type'] for e in entities if not e.get('negated')}</code>. "
        "For each rule, verifies if required entity types form a subset of active patient types: "
        "<code>if required.issubset(entity_types) and rule.get('recommendation'): matches.append(rule)</code>.<br/>"
        "• <i>Rule R1:</i> Criteria: <code>['SYMPTOM']</code> &rarr; Recommends: <code>INVESTIGATION: CBC</code>.<br/>"
        "• <i>Rule R2:</i> Criteria: <code>['DISEASE']</code> &rarr; Recommends: <code>INVESTIGATION: HbA1c</code>.<br/>"
        "• <i>Rule R3:</i> Criteria: <code>[]</code> &rarr; Recommends: <code>None</code> (Educational no-gap benchmark).",
        body_style
    ))

    # 9.9 Gap Detection Service
    story.append(Paragraph("9.9 Decision Gap Detection Auditor (gap_detection.py)", h2_style))
    story.append(Paragraph(
        "<b>Purpose:</b> Audits clinical documentation to detect missing or unperformed investigations against matched prototype recommendations.<br/>"
        "<b>Source Path:</b> <code>backend/services/gap_detection.py</code>.<br/>"
        "<b>Auditing Logic:</b><br/>"
        "1. <b>Guideline Recommendation Gaps:</b> For each matched rule recommending an investigation, checks if that investigation exists in extracted "
        "entities with active status. If absent, negated, or marked 'not performed', emits a <code>MISSING_INVESTIGATION</code> gap with <code>rule_id</code>.<br/>"
        "2. <b>Explicitly Negated Gaps:</b> Scans all investigation entities. If any specific test is explicitly negated or marked 'not performed' "
        "(and NOT ordered/pending or completed), emits a <code>MISSING_INVESTIGATION</code> gap reflecting it was noted as not performed.<br/>"
        "3. <b>False-Positive Suppression:</b> Tests with status <code>ORDERED/PENDING</code>, <code>pending</code>, <code>ordered</code>, or "
        "<code>completed/performed</code> never emit false gaps.<br/>"
        "4. <b>Generic Word Guard:</b> Generic nouns ('test', 'investigation', 'procedure') are suppressed from creating standalone gaps.<br/>"
        "5. <b>Deduplication:</b> Gaps sharing identical <code>(gap_type, canonical_entity)</code> are deduplicated.",
        body_style
    ))

    # 9.10 Confidence & Explainability
    story.append(Paragraph("9.10 Confidence Scoring & Explainability (confidence_service.py & explainability_service.py)", h2_style))
    story.append(Paragraph(
        "<b>Purpose:</b> Computes an auditable confidence score and constructs structured explanation trees linking gaps to clinical rules.<br/>"
        "<b>Source Path:</b> <code>backend/services/confidence_service.py</code> and <code>backend/services/explainability_service.py</code>.<br/>"
        "<b>Scoring Formula:</b><br/>"
        "<code>entity_score = min(1.0, len(entities) / 20) * 0.35</code><br/>"
        "<code>gap_score = (1 - len(gaps) / 5) * 0.30</code><br/>"
        "<code>confidence = round((entity_score + gap_score) * 100, 2)</code><br/>"
        "<b>Explainability Tree:</b> Returns a dictionary containing all extracted entities, detected gaps, computed confidence score, and "
        "activated <code>matched_rules</code> list for complete transparent human audit.",
        body_style
    ))

    # 9.11 FastAPI Orchestration
    story.append(Paragraph("9.11 FastAPI Orchestration & ASGI Pipeline (main.py & clinical_pipeline.py)", h2_style))
    story.append(Paragraph(
        "<b>Purpose:</b> Coordinates all microservices into an asynchronous REST pipeline exposed via FastAPI.<br/>"
        "<b>Source Path:</b> <code>backend/main.py</code> and <code>backend/services/clinical_pipeline.py</code>.<br/>"
        "<b>Execution Flow:</b> In <code>ClinicalPipeline.run(db, patient_id, document_id, text)</code>:<br/>"
        "1. Resolves input text (from request payload or SQLite document table).<br/>"
        "2. Executes <code>hybrid_ner(content)</code> &rarr; 3. Runs <code>detect_negations(content, entities)</code> &rarr;<br/>"
        "4. Computes Bio_ClinicalBERT text embedding &rarr; 5. Matches guidelines via <code>guideline_engine.match(entities)</code> &rarr;<br/>"
        "6. Detects gaps via <code>detect_gaps(entities, rule_matches)</code> &rarr; 7. Reconstructs regimens via <code>reconstruct_regimens(content)</code> &rarr;<br/>"
        "8. Compiles and returns composite response dictionary.",
        body_style
    ))

    # 9.12 React Single Page App
    story.append(Paragraph("9.12 React Single Page Application & State Provider (AnalysisContext.jsx)", h2_style))
    story.append(Paragraph(
        "<b>Purpose:</b> Manages global analysis state, tab routing, API client dispatches, and persistent caching in the React 18 frontend.<br/>"
        "<b>Source Path:</b> <code>frontend-react/src/context/AnalysisContext.jsx</code> and <code>frontend-react/src/App.jsx</code>.<br/>"
        "<b>Implementation Features:</b><br/>"
        "• <i>Single Source of Truth:</i> Maintains <code>analysisResult</code>, <code>patientId</code>, <code>documentId</code>, and <code>rawText</code>.<br/>"
        "• <i>Dual Dispatch Transport:</i> Calls <code>apiService.analyzeClinicalText</code> using Axios with an automatic native Fetch fallback.<br/>"
        "• <i>Persistent Storage:</i> Automatically synchronizes analysis results to <code>localStorage</code> under <code>clingap_nlp_current_analysis</code>, "
        "ensuring data persists across browser reloads and navigation.<br/>"
        "• <i>Liveness Polling:</i> Periodically checks <code>/api/health</code> every 15 seconds to display real-time backend connection status.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 10: CLINICAL NLP AND RULE-BASED REASONING
    # =========================================================================
    story.append(Paragraph("Chapter 10: Clinical NLP and Rule-Based Reasoning", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph("10.1 Probabilistic Information Extraction vs Deterministic Clinical Reasoning", h2_style))
    story.append(Paragraph(
        "In healthcare artificial intelligence, a fundamental tension exists between flexibility and auditability. Deep learning models "
        "(such as BioBERT and BioClinicalBERT) are inherently probabilistic; they excel at generalizing across diverse phrasing, spelling variations, "
        "and contextual nuances. However, medical guidelines require strict deterministic consistency. ClinGap-NLP resolves this dilemma "
        "through a dual-paradigm pipeline: probabilistic models perform entity extraction, while deterministic rules perform clinical audit reasoning.",
        body_style
    ))

    story.append(Paragraph("10.2 Disambiguation across Clinical Phrasing Scenarios", h2_style))
    story.append(Paragraph(
        "The table below illustrates how the combined NLP and rule-based logic handles diverse clinical linguistic scenarios:",
        body_style
    ))

    case_reasoning_data = [
        [Paragraph("<b>Clinical Input Sentence</b>", table_header), Paragraph("<b>NER & Status Resolution</b>", table_header), Paragraph("<b>Guideline Evaluation</b>", table_header), Paragraph("<b>Audit Gap Outcome & Clinical Justification</b>", table_header)],
        [
            Paragraph("“Chest pain is present.”", table_cell_bold),
            Paragraph("SYMPTOM: chest pain<br/>negated: False", table_cell),
            Paragraph("Matches Rule R1 (Symptom present &rarr; Recommend CBC)", table_cell),
            Paragraph("<b>Gap Emitted:</b> MISSING_INVESTIGATION: CBC.<br/>Chest pain is an active symptom triggering prototype baseline rule.", table_cell)
        ],
        [
            Paragraph("“The patient denies chest pain.”", table_cell_bold),
            Paragraph("SYMPTOM: chest pain<br/>negated: True", table_cell),
            Paragraph("No rule matches (Negated symptoms excluded from R1 criteria)", table_cell),
            Paragraph("<b>No Gap Emitted.</b><br/>Symptom is explicitly denied; prototype criteria are not triggered.", table_cell)
        ],
        [
            Paragraph("“A complete blood count was performed.”", table_cell_bold),
            Paragraph("INVESTIGATION: CBC<br/>status: completed/performed<br/>negated: False", table_cell),
            Paragraph("Evaluates against R1 recommendation", table_cell),
            Paragraph("<b>No Gap Emitted.</b><br/>Recommended investigation is present and documented as completed.", table_cell)
        ],
        [
            Paragraph("“Urine testing was ordered; result pending.”", table_cell_bold),
            Paragraph("INVESTIGATION: urine test<br/>status: pending<br/>negated: False", table_cell),
            Paragraph("Evaluates against active orders", table_cell),
            Paragraph("<b>No Gap Emitted.</b><br/>Active pending orders do not constitute missing documentation.", table_cell)
        ],
        [
            Paragraph("“Patient has type 2 diabetes mellitus. Blood glucose 218 mg/dL.”", table_cell_bold),
            Paragraph("DISEASE: diabetes mellitus<br/>Lab: 218 mg/dL (dosage guard)<br/>HbA1c: Absent from note", table_cell),
            Paragraph("Matches Rule R2 (Disease present &rarr; Recommend HbA1c)", table_cell),
            Paragraph("<b>Gap Emitted:</b> MISSING_INVESTIGATION: HbA1c (Rule R2).<br/>Patient has diabetes mellitus with no documented glycemic monitoring test.", table_cell)
        ],
    ]
    case_reasoning_table = Table(case_reasoning_data, colWidths=[120, 110, 115, PW - 345])
    case_reasoning_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_navy),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0,0), (-1,-1), 2.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.8),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(case_reasoning_table)

    story.append(Spacer(1, 6))
    story.append(Paragraph("10.3 Distinguishing Absent Documentation from Explicit Non-Performance", h2_style))
    story.append(Paragraph(
        "A critical distinction implemented in ClinGap-NLP is the technical difference between an <b>unmentioned investigation</b> and an "
        "<b>explicitly negated or non-performed investigation</b>:<br/>"
        "• <b>Case A: Unmentioned / Absent Investigation (Guideline Omission):</b> When an investigation is completely absent from the clinical narrative "
        "(e.g., a diabetic note that never mentions HbA1c at all), <b>no entity is created</b> for HbA1c in the extraction layer. When the guideline "
        "engine evaluates Rule R2, it queries the extracted entity list; because no active HbA1c entity exists, the system detects a missing recommendation "
        "and emits a gap linked to the rule (<code>rule_id='R2'</code>) with description: <i>'The HbA1c investigation is missing from the record.'</i><br/>"
        "• <b>Case B: Explicit Non-Performance (Clinician Documented Non-Performance):</b> When the clinician explicitly documents that an investigation "
        "was not performed, refused, or cancelled (e.g., 'CBC was not performed' or 'No CBC was ordered'), the entity <b>is extracted</b>, and the "
        "clausal negation engine assigns <code>negated=True</code> and <code>status='not performed'</code>. In <code>gap_detection.py</code>, this triggers "
        "a gap reflecting that the test was documented as unperformed (<code>rule_id=None</code>) with description: <i>'The CBC investigation was noted as not performed.'</i><br/>"
        "This clear technical distinction prevents the system from confusing an omitted test with a test that was actively considered and declined.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 11: FRONTEND AND BACKEND INTEGRATION
    # =========================================================================
    story.append(Paragraph("Chapter 11: Frontend and Backend Integration", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph("11.1 Client-Server Communication Topology", h2_style))
    story.append(Paragraph(
        "ClinGap-NLP operates as a decoupled client-server web application. The frontend runs on <b>Port 3001</b> via Vite's development server "
        "(or preview server), while the backend runs on <b>Port 8001</b> via Uvicorn. Cross-Origin Resource Sharing (CORS) is enabled on FastAPI "
        "to permit seamless bidirectional JSON messaging.",
        body_style
    ))

    story.append(Paragraph("11.2 Implemented REST API Endpoint Reference", h2_style))
    api_data = [
        [Paragraph("<b>Endpoint</b>", table_header), Paragraph("<b>Method</b>", table_header), Paragraph("<b>Purpose</b>", table_header), Paragraph("<b>Request Schema / Input</b>", table_header), Paragraph("<b>Response Schema / Output</b>", table_header)],
        [
            Paragraph("<code>/api/health</code>", table_cell_code),
            Paragraph("GET", table_cell_bold),
            Paragraph("System health & liveness check", table_cell),
            Paragraph("None", table_cell),
            Paragraph("<code>{'status': 'ok'}</code>", table_cell_code)
        ],
        [
            Paragraph("<code>/api/analyze</code>", table_cell_code),
            Paragraph("POST", table_cell_bold),
            Paragraph("Executes clinical NLP pipeline", table_cell),
            Paragraph("<code>{patient_id: int, document_id: int, text: str}</code>", table_cell_code),
            Paragraph("<code>{entities: list, gaps: list, confidence: float, explanation: dict, regimens: list, context_info: dict}</code>", table_cell_code)
        ],
        [
            Paragraph("<code>/api/upload</code>", table_cell_code),
            Paragraph("POST", table_cell_bold),
            Paragraph("Multi-format document ingestion", table_cell),
            Paragraph("Multipart form: <code>file (.txt, .pdf, .docx)</code>", table_cell_code),
            Paragraph("<code>{filename, file_type, text, char_count, word_count, preview}</code>", table_cell_code)
        ],
        [
            Paragraph("<code>/api/dataset/mtsamples/specialties</code>", table_cell_code),
            Paragraph("GET", table_cell_bold),
            Paragraph("Retrieves MTSamples specialties", table_cell),
            Paragraph("None", table_cell),
            Paragraph("<code>List[str]</code> (40 unique medical specialties)", table_cell_code)
        ],
        [
            Paragraph("<code>/api/dataset/mtsamples/records</code>", table_cell_code),
            Paragraph("GET", table_cell_bold),
            Paragraph("Searchable paginated corpus query", table_cell),
            Paragraph("Query params: <code>q, specialty, limit, offset</code>", table_cell_code),
            Paragraph("<code>{records: list, total: int, limit: int, offset: int}</code>", table_cell_code)
        ],
        [
            Paragraph("<code>/api/dataset/mtsamples/{id}</code>", table_cell_code),
            Paragraph("GET", table_cell_bold),
            Paragraph("Retrieves full transcription record", table_cell),
            Paragraph("Path param: <code>id: int (0 to 4965)</code>", table_cell_code),
            Paragraph("<code>{id, sample_name, medical_specialty, transcription, ...}</code>", table_cell_code)
        ],
    ]
    api_table = Table(api_data, colWidths=[105, 45, 105, 120, PW - 375])
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_navy),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(api_table)

    story.append(Spacer(1, 6))
    story.append(Paragraph("11.3 Dual-Dispatch Client Resilience (api.js)", h2_style))
    story.append(Paragraph(
        "A critical engineering feature in <code>frontend-react/src/services/api.js</code> is the <b>dual-dispatch transport architecture</b>. "
        "Standard Axios HTTP requests are wrapped in a resilient try/catch block. In environments where strict browser proxy or CORS "
        "headers interrupt Axios requests, the client automatically executes an immediate fallback using the browser's native <code>fetch()</code> API. "
        "This ensures uninterrupted client-server communication across diverse runtime and browser environments.",
        body_style
    ))

    story.append(Paragraph("11.4 Single-Source-of-Truth State Management", h2_style))
    story.append(Paragraph(
        "The frontend implements React Context (<code>AnalysisContext.jsx</code>) as the single source of truth. When an analysis completes, "
        "the response object—containing entities, regimens, investigation statuses, and gap findings—is committed to central state and saved "
        "to browser <code>localStorage</code>. All 8 pages read reactively from this central context, ensuring that switching tabs never triggers "
        "unnecessary re-computation or data loss.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 12: DATABASE AND DATA MANAGEMENT
    # =========================================================================
    story.append(Paragraph("Chapter 12: Database and Data Management", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph("12.1 Database Technology & Engine Configuration", h2_style))
    story.append(Paragraph(
        "ClinGap-NLP utilizes an embedded <b>SQLite 3</b> database accessed through <b>SQLAlchemy 2.0</b> Object-Relational Mapping (ORM). "
        "The database file defaults to <code>clinngap.db</code> located in the project root. The SQLAlchemy engine is configured with "
        "<code>connect_args={'check_same_thread': False}</code> to permit thread-safe database session sharing across asynchronous FastAPI worker threads.",
        body_style
    ))

    story.append(Paragraph("12.2 Relational Data Models & Table Schemas", h2_style))
    story.append(Paragraph(
        "The relational schema defines three interconnected entities structured around patient documentation:",
        body_style
    ))

    schema_data = [
        [Paragraph("<b>Table Name</b>", table_header), Paragraph("<b>Primary Key</b>", table_header), Paragraph("<b>Foreign Keys</b>", table_header), Paragraph("<b>Columns & Data Types</b>", table_header), Paragraph("<b>ORM Relationship</b>", table_header)],
        [
            Paragraph("<code>patients</code>", table_cell_code),
            Paragraph("<code>id</code> (Integer)", table_cell),
            Paragraph("None", table_cell),
            Paragraph("<code>name</code>: String (nullable=False)", table_cell),
            Paragraph("<code>documents</code>: relationship('Document')", table_cell)
        ],
        [
            Paragraph("<code>documents</code>", table_cell_code),
            Paragraph("<code>id</code> (Integer)", table_cell),
            Paragraph("<code>patient_id &rarr; patients.id</code>", table_cell_code),
            Paragraph("<code>title</code>: String, <code>doc_type</code>: String, <code>content</code>: Text, <code>created_at</code>: DateTime", table_cell),
            Paragraph("<code>patient</code>: relationship('Patient')<br/><code>entities</code>: relationship('ClinicalEntity')", table_cell)
        ],
        [
            Paragraph("<code>clinical_entities</code>", table_cell_code),
            Paragraph("<code>id</code> (Integer)", table_cell),
            Paragraph("<code>document_id &rarr; documents.id</code>", table_cell_code),
            Paragraph("<code>entity_text</code>: String, <code>entity_type</code>: String, <code>normalized_value</code>: String, <code>confidence</code>: Float, <code>negated</code>: Boolean, <code>source</code>: String", table_cell),
            Paragraph("<code>document</code>: relationship('Document')", table_cell)
        ],
    ]
    schema_table = Table(schema_data, colWidths=[80, 70, 100, PW - 350, 100])
    schema_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_navy),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0,0), (-1,-1), 2.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(schema_table)

    story.append(Spacer(1, 6))
    story.append(Paragraph("12.3 Data Lifecycle: Transient Analysis vs Persistent Storage", h2_style))
    story.append(Paragraph(
        "<b>Architectural Operation:</b><br/>"
        "• <i>Transient Interactive Analysis:</i> When a user inputs text directly into the web UI, the pipeline processes the document in memory, "
        "returning real-time entity and gap objects without forcing immediate database writes. This guarantees ultra-low latency and privacy.<br/>"
        "• <i>Persisted Storage:</i> The database is initialized via <code>scripts/seed_database.py</code>, creating baseline demo records "
        "(e.g., Patient 'John Doe', Case 1 note). When <code>document_id</code> is supplied without text, the backend fetches content directly "
        "from SQLite (<code>SELECT content FROM documents WHERE id = :doc_id</code>).",
        body_style
    ))

    story.append(Paragraph("12.4 MTSamples Dataset Integration (4,966 Records)", h2_style))
    story.append(Paragraph(
        "To evaluate real-world clinical documentation, ClinGap-NLP embeds the MTSamples corpus located at <code>data/datasets/mtsamples_clean.csv</code>. "
        "The dataset contains 4,966 anonymized clinical transcriptions spanning 40 medical specialties (Cardiology, Surgery, Neurology, Pulmonary, etc.). "
        "The <code>dataset_service.py</code> module caches the Pandas DataFrame in memory, providing sub-millisecond keyword search and paginated "
        "retrieval that streams directly into the web editor.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 13: SAMPLE CASE AND DEMONSTRATION
    # =========================================================================
    story.append(Paragraph("Chapter 13: Sample Case and Demonstration", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph("13.1 Benchmark Clinical Scenario Specification", h2_style))
    story.append(Paragraph(
        "To demonstrate the complete end-to-end operation of ClinGap-NLP, we examine a multi-morbidity clinical note featuring "
        "co-occurring diagnoses, active medication regimens, lab values, ordered tests, and missing documentation:",
        body_style
    ))

    demo_note = (
        "A patient has type 2 diabetes and hypertension. The patient takes metformin 500 mg twice daily and "
        "lisinopril 10 mg once daily. Random blood glucose is 218 mg/dL. CBC was performed. Urine testing was "
        "ordered, and the result is pending. No HbA1c result is documented."
    )
    story.append(make_callout(demo_note, bg_color=c_bg_light, border_color=c_navy, title="INPUT CLINICAL NOTE"))
    story.append(Spacer(1, 6))

    story.append(Paragraph("13.2 Step-by-Step Processing Trace and Actual System Output", h2_style))
    story.append(Paragraph(
        "Executing this note through the ClinGap-NLP pipeline yields the following structured outputs across all analytical layers:",
        body_style
    ))

    trace_data = [
        [Paragraph("<b>Pipeline Stage</b>", table_header), Paragraph("<b>Extracted Finding / Classification</b>", table_header), Paragraph("<b>Internal Representation & Normalized Values</b>", table_header)],
        [
            Paragraph("1. Diagnoses", table_cell_bold),
            Paragraph("Type 2 diabetes<br/>Hypertension", table_cell),
            Paragraph("• entity_type: DISEASE, normalized_value: 'diabetes mellitus', negated: False<br/>• entity_type: DISEASE, normalized_value: 'hypertension', negated: False", table_cell)
        ],
        [
            Paragraph("2. Medications & Regimens", table_cell_bold),
            Paragraph("Metformin: 500 mg, twice daily<br/>Lisinopril: 10 mg, once daily", table_cell),
            Paragraph("• Reconstructed Regimen 1: {medication: 'metformin', dosage: '500 mg', frequency: 'twice daily'}<br/>• Reconstructed Regimen 2: {medication: 'lisinopril', dosage: '10 mg', frequency: 'once daily'}", table_cell)
        ],
        [
            Paragraph("3. Lab Disambiguation", table_cell_bold),
            Paragraph("218 mg/dL (Blood Glucose)", table_cell),
            Paragraph("• Rejected from DOSAGE and MEDICATION tiers via lab measurement guard (re.search matches 'mg/dL'). Correctly handled as lab value.", table_cell)
        ],
        [
            Paragraph("4. CBC Investigation", table_cell_bold),
            Paragraph("CBC was performed", table_cell),
            Paragraph("• entity_type: INVESTIGATION, normalized_value: 'cbc'<br/>• status: 'completed/performed', negated: False &rarr; <b>No gap emitted</b>", table_cell)
        ],
        [
            Paragraph("5. Urine Test Investigation", table_cell_bold),
            Paragraph("Urine testing was ordered; result pending", table_cell),
            Paragraph("• entity_type: INVESTIGATION, normalized_value: 'urine test'<br/>• status: 'ORDERED/PENDING', negated: False &rarr; <b>No gap emitted (active order)</b>", table_cell)
        ],
        [
            Paragraph("6. HbA1c Documentation<br/>(Explicit Statement)", table_cell_bold),
            Paragraph("“No HbA1c result is documented”", table_cell),
            Paragraph("• In this note, the sentence explicitly mentions HbA1c preceded by 'No'. Extracted entity: {entity_type: INVESTIGATION, normalized_value: 'hba1c', negated: True, status: 'not performed'}.<br/>"
                      "• <i>Contrast with Unmentioned Test:</i> If HbA1c were completely unmentioned, NO entity would exist, but Rule R2 would still flag it as missing.", table_cell)
        ],
        [
            Paragraph("7. Guideline Evaluation", table_cell_bold),
            Paragraph("Prototype Rule R2 Activated", table_cell),
            Paragraph("• Rule Criteria: DISEASE present ('type 2 diabetes') &rarr; Recommends: INVESTIGATION 'HbA1c'.", table_cell)
        ],
        [
            Paragraph("8. Gap Auditor Output", table_cell_bold),
            Paragraph("<b>MISSING_INVESTIGATION: HbA1c</b>", ParagraphStyle('RedText', fontName='Helvetica-Bold', fontSize=7.4, textColor=colors.HexColor("#B91C1C"))),
            Paragraph("• gap_type: 'MISSING_INVESTIGATION', entity: 'hba1c', rule_id: 'R2'<br/>• description: 'The HbA1c investigation is missing from the record.'", table_cell)
        ],
    ]
    trace_table = Table(trace_data, colWidths=[105, 140, PW - 245])
    trace_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_navy),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(trace_table)

    story.append(Spacer(1, 6))
    story.append(Paragraph("13.3 Clinical Audit Interpretation", h2_style))
    story.append(Paragraph(
        "<b>Documentation Audit Summary:</b> The system successfully identified both chronic conditions, correctly reconstructed "
        "both medication regimens without cross-pairing, distinguished blood glucose (218 mg/dL) from drug dosages, recognized the completed CBC, "
        "honored the pending urine test order without emitting a false gap, and flagged the missing HbA1c documentation against Rule R2. "
        "This demonstrates the power of ClinGap-NLP: flagging documentation follow-ups for human clinician review without generating distracting false positives.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 14: USER INTERFACE AND VIEWS
    # =========================================================================
    story.append(Paragraph("Chapter 14: User Interface and Component Views", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph("14.1 Frontend UI Architecture and Design Philosophy", h2_style))
    story.append(Paragraph(
        "The ClinGap-NLP frontend is built with React 18, Vite 6, and Tailwind CSS. The interface adopts a professional clinical "
        "design aesthetic featuring a deep slate/navy sidebar (<code>#0F172A</code>), crisp medical blue accent highlights (<code>#1E40AF</code>), "
        "and light slate content backgrounds (<code>#F8FAFC</code>). All 8 views are navigated via a persistent sidebar that displays "
        "real-time backend liveness badges (Connected / Offline) and quick statistics.",
        body_style
    ))

    ui_views = [
        ("View 1: Main Dashboard (DashboardPage.jsx)", [
            "• Top Metric Cards: Total Entities Extracted, Potential Gaps Flagged, Confidence Score %, Pipeline Liveness.",
            "• Visual Analytics Panels: Entity Distribution by Category, Gap Severity Breakdown, Matched Guideline Rules.",
            "• Quick Action Buttons: 'Load Case 1', 'Explore MTSamples', 'Review Gaps', with recent document summary preview."
        ]),
        ("View 2: Clinical Input Studio (ClinicalInputPage.jsx)", [
            "• Direct Clinical Note Editor: Real-time character/word counter with syntax-ready textarea.",
            "• Demo Presets Selector: Instant loading for Case 1 (Diabetes/HTN), Case 2 (Missing CBC), Case 3 (Respiratory).",
            "• Multi-Format File Uploader: Drag-and-drop or file picker accepting .txt, .pdf, and .docx documents.",
            "• MTSamples Dataset Explorer: Searchable, paginated browser across 4,966 records in 40 specialties with 1-click loading."
        ]),
        ("View 3: Entity Extraction (EntityExtractionPage.jsx)", [
            "• Categorized Filter Tabs: All Entities, Diseases, Symptoms, Medications, Investigations, Dosages, Frequencies.",
            "• Entity Card Grid: Displays entity text, normalized canonical form, extraction confidence badge, source tier.",
            "• Negation Indicators: Prominent red badges for negated entities ('negated=True') with clausal scope justification."
        ]),
        ("View 4: Guideline Matching Inspector (GuidelineMatchingPage.jsx)", [
            "• Active Rule Cards: Displays triggered rule IDs (R1, R2), rule descriptions, and required entity prerequisites.",
            "• Evidence Inspector: Shows matched patient findings that satisfied rule criteria (e.g., 'DISEASE &rarr; diabetes mellitus').",
            "• Diagnostic Recommendation Badges: Clear visual badges showing recommended clinical actions."
        ]),
        ("View 5: Decision Gap Detection Audit (GapDetectionPage.jsx)", [
            "• Actionable Gap Cards: Highlighting missing investigations with red alert styling and severity badges.",
            "• Rule Attribution: Explicitly links gaps to guideline rule IDs (or flags explicit clinician non-performance).",
            "• Clinical Rationale Panel: Contextual explanation clarifying why the omission was flagged for review."
        ]),
        ("View 6: Prescription & Regimen Studio (PrescriptionPage.jsx)", [
            "• Reconstructed Regimen Table: Dedicated 3-column table showing Medication Name, Dosage Strength, Dosing Frequency.",
            "• Proximity Association Inspector: Visualizes directional token distance pairing between drugs and dosages.",
            "• Lab Value Rejection Badge: Explicitly confirms that lab values (e.g. 218 mg/dL) were excluded from prescriptions."
        ]),
        ("View 7: Clinical Timeline & Investigation Tracker (TimelinePage.jsx)", [
            "• Chronological Event Flow: Step-by-step sequential event cards reconstructed from clinical narrative flow.",
            "• Active Condition & Regimen Summary: Dedicated summary cards pairing each drug with its exact dosage.",
            "• Investigation Lifecycle Grid: Categorized tracker displaying tests with real-time badges (Ordered/Pending, Performed, etc.)."
        ]),
        ("View 8: System Architecture & About (AboutPage.jsx)", [
            "• Architectural Overview: Detailed explanation of the 4-tier hybrid NER pipeline and dual-paradigm reasoning.",
            "• Technical Stack Specifications: Full documentation of FastAPI, React, BioBERT, SQLite, and Pytest components.",
            "• Regulatory Disclaimer: Full medical safety disclaimer clarifying research and QA boundary conditions."
        ]),
    ]

    ui_table_data = [[Paragraph("<b>Interface Module & Component</b>", table_header), Paragraph("<b>Layout Elements, Interactive Controls, & Visual Data Output</b>", table_header)]]
    for v_title, v_items in ui_views:
        ui_table_data.append([
            Paragraph(f"<b>{v_title}</b>", table_cell_bold),
            Paragraph("<br/>".join(v_items), table_cell)
        ])

    ui_table = Table(ui_table_data, colWidths=[150, PW - 150])
    ui_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_navy),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(ui_table)

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 15: TESTING AND VERIFICATION
    # =========================================================================
    story.append(Paragraph("Chapter 15: Testing and Verification", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph("15.1 Testing Strategy and Harness Execution", h2_style))
    story.append(Paragraph(
        "Quality assurance and verification in ClinGap-NLP are governed by an automated, non-destructive test suite. "
        "The test harness evaluates clinical entity extraction, unit disambiguation, clausal negation scoping, prescription pairing, "
        "investigation lifecycle states, and end-to-end pipeline execution.<br/>"
        "<b>Executed Command:</b> <code>python -m pytest tests</code> from <code>clinngap_nlp/</code>.<br/>"
        "<b>Verified Execution Result:</b> <b>56 passed, 3 warnings in 27.44s</b> (Python 3.13.3, Pytest 9.1.1, Win32).",
        body_style
    ))

    test_file_data = [
        [Paragraph("<b>Test Suite File</b>", table_header), Paragraph("<b>Passed</b>", table_header), Paragraph("<b>Scope of Verification & Covered Edge Cases</b>", table_header)],
        [
            Paragraph("<code>tests/test_clinical_extraction_fixes.py</code>", table_cell_code),
            Paragraph("<b>33</b>", table_cell_bold),
            Paragraph("• Separates medication dosages from lab units (218 mg/dL, 14.2 g/dL, mmHg, °C rejected from dosages).<br/>"
                      "• Coverage for respiratory drugs (salbutamol) and chronic conditions (asthma).<br/>"
                      "• Investigation lifecycle: ORDERED/PENDING, pending, completed/performed, not performed.<br/>"
                      "• Clausal negation scoping across coordinated symptoms (denies chest pain AND dizziness).<br/>"
                      "• Full clinical note evaluation: 3 medication regimens verified without index cross-pairing.<br/>"
                      "• False-positive gap suppression for active orders and generic words ('test').", table_cell)
        ],
        [
            Paragraph("<code>tests/test_ner.py</code>", table_cell_code),
            Paragraph("<b>9</b>", table_cell_bold),
            Paragraph("• Hybrid NER basic extraction across all 6 entity types.<br/>"
                      "• Demo clinical note entity validation and clausal negation assertions.<br/>"
                      "• Normalization and synonym mapping for HbA1c casing variants (hba1c, glycated hemoglobin).<br/>"
                      "• Word boundary validation and WordPiece subword fragment rejection.<br/>"
                      "• Deduplication keeping highest-confidence entities.", table_cell)
        ],
        [
            Paragraph("<code>tests/test_pipeline_case1.py</code>", table_cell_code),
            Paragraph("<b>1</b>", table_cell_bold),
            Paragraph("• Full end-to-end integration test validating pipeline output against Case 1 demo note.<br/>"
                      "• Asserts correct entity counts, rule matches, and gap detection.", table_cell)
        ],
        [
            Paragraph("<code>tests/test_prescription.py</code>", table_cell_code),
            Paragraph("<b>3</b>", table_cell_bold),
            Paragraph("• Legacy prescription parser verification against baseline regex.<br/>"
                      "• Extraction of dosages and frequencies from prescription strings.", table_cell)
        ],
        [
            Paragraph("<code>tests/test_prescription_end_to_end.py</code>", table_cell_code),
            Paragraph("<b>10</b>", table_cell_bold),
            Paragraph("• Case 1: amoxicillin 500 mg three times daily &rarr; exact pairing.<br/>"
                      "• Case 2: metformin 500 mg twice daily &rarr; exact pairing.<br/>"
                      "• Case 3: ibuprofen 400 mg every 8 hours &rarr; exact pairing.<br/>"
                      "• Case 4: paracetamol 500 mg as needed &rarr; PRN frequency pairing.<br/>"
                      "• Case 5: dosage without frequency (amoxicillin 250 mg &rarr; frequency=None).<br/>"
                      "• Case 6: frequency without dosage (metformin once daily &rarr; dosage=None).<br/>"
                      "• Case 7: multiple medications in single sentence with distinct frequencies.<br/>"
                      "• Cases 8–10: noise word filtering, multi-line notes, and complex clinical orders.", table_cell)
        ],
        [
            Paragraph("<b>TOTAL VERIFIED BACKEND TESTS</b>", table_cell_bold),
            Paragraph("<b>56 / 56</b>", table_cell_bold),
            Paragraph("<b>100% Pass Rate across all 5 test files in 27.44 seconds.</b>", table_cell_bold)
        ],
    ]
    test_table = Table(test_file_data, colWidths=[165, 45, PW - 210])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_navy),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, c_bg_light]),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#EFF6FF")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(test_table)

    story.append(Spacer(1, 6))
    story.append(Paragraph("15.2 Frontend Production Build Verification", h2_style))
    story.append(Paragraph(
        "<b>Executed Command:</b> <code>npm run build</code> inside <code>clinngap_nlp/frontend-react/</code>.<br/>"
        "<b>Build Output:</b> Vite v6.4.3 transformed 1,659 modules in <b>15.07 seconds</b> with 0 errors:<br/>"
        "• <code>dist/index.html</code> (1.28 kB | gzip: 0.70 kB)<br/>"
        "• <code>dist/assets/index-b5EL2gu1.css</code> (33.71 kB | gzip: 6.36 kB)<br/>"
        "• <code>dist/assets/index-BlDQL5Kt.js</code> (305.27 kB | gzip: 89.51 kB)<br/>"
        "This confirms that all React 18 components, hooks, Tailwind stylesheets, and Lucide icon imports compile cleanly into production bundles.",
        body_style
    ))

    story.append(Paragraph("15.3 Historical Regression Fixes and Verification Evidence", h2_style))
    story.append(Paragraph(
        "<b>1. Laboratory Measurement vs Dosage Collision:</b> Previously, expressions like 'glucose 218 mg/dL' were captured as 218 mg dosages. "
        "The negative lookahead regex and <code>_is_lab_measurement_or_non_medication()</code> guard completely eliminate this collision.<br/>"
        "<b>2. Medication Regimen Array-Index Mismatch:</b> In early prototypes, medications and dosages were stored in flat arrays, causing "
        "misalignments (e.g. assigning 100 mcg to amoxicillin). The proximity reconstructor associates each drug directly with its adjacent dosage.<br/>"
        "<b>3. Investigation Lifecycle False Positives:</b> Tests documented as 'ordered but not yet performed' previously triggered missing gaps. "
        "The 4-state lifecycle machine prevents pending orders from emitting false-positive gaps.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 16: RESULTS AND DISCUSSION
    # =========================================================================
    story.append(Paragraph("Chapter 16: Results and Discussion", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph("16.1 Qualitative and Quantitative Observations of System Behavior", h2_style))
    story.append(Paragraph(
        "Evaluation of ClinGap-NLP across synthetic benchmark notes, test suites, and the MTSamples corpus reveals robust, "
        "repeatable software behavior. The dual-paradigm architecture reliably addresses the primary failure modes of clinical text processing:",
        body_style
    ))

    results_data = [
        [Paragraph("<b>Capability Dimension</b>", table_header), Paragraph("<b>Observed Operational Performance & Verification Evidence</b>", table_header)],
        [
            Paragraph("Entity Recognition Fidelity", table_cell_bold),
            Paragraph("The 4-tier hybrid pipeline reliably captures multi-word clinical entities (e.g., 'type 2 diabetes mellitus', 'complete blood count') "
                      "while rejecting single-character tokenization artifacts. Nested entity deduplication prevents redundant fragment entries.", table_cell)
        ],
        [
            Paragraph("Regimen Proximity Accuracy", table_cell_bold),
            Paragraph("10 out of 10 automated test cases in test_prescription_end_to_end.py passed successfully during regression testing. "
                      "Medications in coordinated sentences are correctly associated with their following dosages with zero cross-pairing in test notes.", table_cell)
        ],
        [
            Paragraph("Investigation Status Discrimination", table_cell_bold),
            Paragraph("Successfully discriminates all four diagnostic states. Active pending tests ('urine test ordered') do not produce false gaps, "
                      "while unmentioned tests ('HbA1c') reliably trigger guideline-backed gap notifications.", table_cell)
        ],
        [
            Paragraph("Execution Latency (CPU)", table_cell_bold),
            Paragraph("Synchronous CPU execution on standard hardware runs smoothly without timeout. Singleton pipeline loading ensures "
                      "the transformer model is initialized once, avoiding repeated model loading overhead across requests.", table_cell)
        ],
        [
            Paragraph("Frontend React Responsiveness", table_cell_bold),
            Paragraph("Instantaneous sub-10ms UI tab switching driven by React Context single-source-of-truth state. Zero data loss across browser "
                      "reloads due to automatic localStorage synchronization.", table_cell)
        ],
    ]
    results_table = Table(results_data, colWidths=[140, PW - 140])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_navy),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0,0), (-1,-1), 2.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.8),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(results_table)

    story.append(Spacer(1, 6))
    story.append(Paragraph("16.2 Methodological Distinction: Software Verification vs Clinical Validation", h2_style))
    story.append(Paragraph(
        "<b>Rigorous Scientific Disclaimer:</b> The results documented in this report represent <b>software engineering verification metrics</b> "
        "(automated unit test passes, regression assertions, build completions, and latency profiling). They do <b>NOT</b> constitute formal "
        "prospective clinical trial efficacy metrics (such as prospective clinical diagnostic sensitivity, specificity, or patient outcome improvements). "
        "Formal clinical evaluation requires IRB-approved trials on annotated clinical datasets (such as MIMIC-IV or i2b2/n2c2) and blinded review "
        "by certified medical specialists.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 17: LIMITATIONS AND FUTURE SCOPE
    # =========================================================================
    story.append(Paragraph("Chapter 17: Limitations and Future Scope", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph("17.1 Current System Limitations", h2_style))
    story.append(Paragraph(
        "1. <b>Syntactic Ambiguity in Multi-Clause Sentences:</b> When three or more medications appear in complex parenthetical or passive structures "
        "(e.g., 'started on drug A after drug B was stopped due to drug C'), proximity pairing can face ambiguity.<br/>"
        "2. <b>Dictionary Coverage Boundaries:</b> The curated clinical dictionaries in <code>knowledge_base/</code> cover high-frequency conditions, "
        "medications, and investigations. Rare diseases or experimental therapeutics not present in the transformer or dictionaries may be missed.<br/>"
        "3. <b>Single-Visit Narrative Scope:</b> The current engine analyzes one clinical document at a time. It does not perform cross-encounter "
        "temporal reasoning to verify if an HbA1c was performed at a different clinic three weeks prior.<br/>"
        "4. <b>Local CPU Execution Constraints:</b> While CPU execution ensures portability, running large transformer models on very long notes "
        "(>5,000 words) exhibits noticeable latency compared to GPU-accelerated infrastructure.",
        body_style
    ))

    story.append(Paragraph("17.2 Future Scope & Technical Roadmap", h2_style))
    story.append(Paragraph(
        "• <b>SNOMED CT, RxNorm, & LOINC Ontology Integration:</b> Upgrade entity normalization from custom JSON lexicons to standardized "
        "medical ontologies (UMLS, SNOMED CT for diseases, RxNorm for medications, and LOINC for laboratory investigations).<br/>"
        "• <b>Temporal Event Relation Extraction:</b> Implement temporal relation extraction (e.g., TimeML / Clinical TempEval) to reconstruct "
        "absolute event timelines across longitudinal patient encounters.<br/>"
        "• <b>HL7 FHIR Interoperability:</b> Build bi-directional FHIR adapters (e.g., <code>DiagnosticReport</code>, <code>MedicationRequest</code>, "
        "<code>Condition</code> resources) to enable direct ingestion from commercial Hospital Information Systems.<br/>"
        "• <b>Multi-Hop Guideline Reasoning:</b> Expand the guideline engine to support multi-criteria conditional rules (e.g., age &gt; 65 AND "
        "eGFR &lt; 30 &rarr; dose reduction recommendations).<br/>"
        "• <b>GPU Acceleration & Quantized Inference:</b> Quantize BioBERT weights (via ONNX Runtime / INT8 quantization) to achieve sub-50ms inference times.",
        body_style
    ))

    story.append(Spacer(1, 4))

    # =========================================================================
    # CHAPTER 18: CONCLUSION
    # =========================================================================
    story.append(Paragraph("Chapter 18: Conclusion", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph(
        "The <b>ClinGap-NLP — Clinical Decision Gap Intelligence System</b> successfully demonstrates the viability of a dual-paradigm "
        "clinical intelligence architecture. By pairing modern deep learning token classification (Hugging Face BioBERT) with deterministic, "
        "auditable clinical guideline matching, the system resolves the fundamental tension between extraction flexibility and medical safety.",
        body_style
    ))
    story.append(Paragraph(
        "Through rigorous source-code inspection, architectural analysis, and automated testing, this monograph has established that:<br/>"
        "1. The 4-tier hybrid NER pipeline provides high-fidelity entity extraction with multi-layer fallback resilience.<br/>"
        "2. The clausal negation engine and 4-state investigation lifecycle model eliminate false-positive gap notifications for active orders.<br/>"
        "3. Directional proximity pairing reconstructs complete medication regimens while strictly separating lab units from drug strengths.<br/>"
        "4. The system is verified by <b>56 passing automated backend regression tests</b> and a validated React 18 production build.<br/>"
        "5. The application operates as an auditable documentation review tool, empowering clinicians and quality auditors to catch omissions "
        "without hallucinating clinical diagnoses.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 19: REFERENCES AND APPENDICES
    # =========================================================================
    story.append(Paragraph("Chapter 19: References and Appendices", ch_title_style))
    story.append(make_section_divider())

    story.append(Paragraph("19.1 Verified Technical & Library References", h2_style))
    refs = [
        "1. Alsentzer, E., Murphy, J. R., Boag, W., et al. (2019). 'Publicly Available Clinical BERT Embeddings.' Proceedings of the 2nd Clinical Natural Language Processing Workshop, NAACL 2019.",
        "2. d4data Team. (2022). 'Biomedical Named Entity Recognition All-in-One Model (d4data/biomedical-ner-all).' Hugging Face Model Hub. https://huggingface.co/d4data/biomedical-ner-all",
        "3. FastAPI Framework Documentation. (2024). Tiangolo / Sebastián Ramírez. https://fastapi.tiangolo.com/",
        "4. React 18 & Vite Build Tooling. (2024). Meta Open Source & Evan You. https://react.dev/ and https://vitejs.dev/",
        "5. MTSamples Medical Transcription Corpus. (2020). Cleaned Multi-Specialty Clinical Notes Dataset. MTSamples.com.",
        "6. SQLAlchemy 2.0 ORM Documentation. (2024). Michael Bayer. https://www.sqlalchemy.org/",
        "7. ReportLab Platypus Framework. (2024). ReportLab Europe Ltd. https://www.reportlab.com/",
    ]
    for r in refs:
        story.append(Paragraph(r, bullet_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("19.2 Technical Glossary", h2_style))
    glossary_data = [
        [Paragraph("<b>Term</b>", table_header), Paragraph("<b>Definition in the Context of ClinGap-NLP</b>", table_header)],
        [Paragraph("<b>NER</b>", table_cell_bold), Paragraph("Named Entity Recognition: Identifying spans of clinical text representing diseases, symptoms, drugs, or tests.", table_cell)],
        [Paragraph("<b>Clausal Negation</b>", table_cell_bold), Paragraph("Scoping negation words (e.g. 'denies') strictly within clause boundaries to avoid falsely negating separate findings.", table_cell)],
        [Paragraph("<b>Decision Gap</b>", table_cell_bold), Paragraph("A documented clinical situation where a guideline-recommended diagnostic evaluation is missing or noted as cancelled.", table_cell)],
        [Paragraph("<b>Regimen Reconstruction</b>", table_cell_bold), Paragraph("Proximity-based binding of a pharmaceutical agent with its valid dosage strength and dosing frequency.", table_cell)],
        [Paragraph("<b>Lifecycle State</b>", table_cell_bold), Paragraph("One of four states (ORDERED/PENDING, pending, completed/performed, not performed) tracking diagnostic progression.", table_cell)],
        [Paragraph("<b>Dual-Dispatch</b>", table_cell_bold), Paragraph("Frontend network client pattern attempting Axios first with an automatic native Fetch fallback.", table_cell)],
    ]
    glossary_table = Table(glossary_data, colWidths=[100, PW - 100])
    glossary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_navy),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(glossary_table)

    story.append(Spacer(1, 6))
    story.append(Paragraph("19.3 Local Execution & Reproduction Guide", h2_style))
    story.append(Paragraph(
        "To reproduce the application and verify all automated tests in a local Windows environment:",
        body_style
    ))
    run_cmds = (
        "# 1. Start FastAPI Backend (Port 8001):\n"
        "cd \"C:\\Desktop\\nlp project\\clinngap_nlp\"\n"
        "python -m uvicorn backend.main:app --reload --port 8001\n\n"
        "# 2. Start React 18 Frontend (Port 3001):\n"
        "cd \"C:\\Desktop\\nlp project\\clinngap_nlp\\frontend-react\"\n"
        "npm run dev -- --host 127.0.0.1 --port 3001\n\n"
        "# 3. Execute Automated Backend Test Suite (56 tests):\n"
        "cd \"C:\\Desktop\\nlp project\\clinngap_nlp\"\n"
        "python -m pytest tests\n\n"
        "# 4. Validate Production Frontend Build:\n"
        "cd \"C:\\Desktop\\nlp project\\clinngap_nlp\\frontend-react\"\n"
        "npm run build\n"
    )
    story.append(make_code_box(run_cmds))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Report generated successfully: {output_path}")

if __name__ == '__main__':
    target = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "ClinGap_NLP_Detailed_Implementation_Report_Reviewed.pdf"
    )
    if len(sys.argv) > 1:
        target = sys.argv[1]
    create_report(target)
