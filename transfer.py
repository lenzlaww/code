#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transfer.py
Turn a structured resume JSON into a clean PDF (1–2 page, ATS-friendly).

Usage:
  python transfer.py --json resume.json --out resume.pdf
"""

import json
import argparse
from typing import Dict, List, Any

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    ListFlowable, ListItem, HRFlowable
)

from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ---------------------------------------------------------------------
# Font
# ---------------------------------------------------------------------

# 以 Inter 为例：把 register_charter 改成通用 register_family
def register_family(font_dir: str,
                    family_name: str = "Inter",
                    filenames: dict | None = None):

    default_files = {
        "REG":        "Inter_18pt-Regular.ttf",        # 没有 Regular，用 Bold 代替
        "BOLD":       "Inter_18pt-Bold.ttf",
        "ITALIC":     "Inter_18pt-Italic.ttf",  # 没有 Italic，用 BoldItalic 代替
        "BOLDITALIC": "Inter_18pt-BoldItalic.ttf",}

    files = filenames or default_files
    base = Path(font_dir)

    def reg(post_name: str, fname_key: str):
        fpath = base / files[fname_key]
        if not fpath.exists():
            raise FileNotFoundError(f"Missing font file: {fpath}")
        pdfmetrics.registerFont(TTFont(post_name, str(fpath)))
        return post_name

    reg_name = reg(f"{family_name}",          "REG")
    b_name   = reg(f"{family_name}-Bold",     "BOLD")
    i_name   = reg(f"{family_name}-Italic",   "ITALIC")
    bi_name  = reg(f"{family_name}-BoldItalic","BOLDITALIC")

    return {
        "REG": reg_name,
        "BOLD": b_name,
        "ITALIC": i_name,
        "BOLDITALIC": bi_name,
    }


family = register_family("./font", family_name="Inter")
doc = SimpleDocTemplate(...)
avail_width = doc.width

# ---------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------
def make_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(name="Name",    fontName=family["BOLD"], fontSize=20, leading=24, alignment=TA_CENTER, spaceAfter=6))
    styles.add(ParagraphStyle(name="Contact",    fontName=family["ITALIC"], fontSize=9, leading=11, textColor=colors.grey, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="Section", fontName=family["BOLD"], fontSize=12, leading=14))
    styles.add(ParagraphStyle(name="Body",    fontName=family["REG"],  fontSize=10, leading=13))
    styles.add(ParagraphStyle(name="Meta",    fontName=family["ITALIC"], fontSize=9, leading=11))
    styles.add(ParagraphStyle(name="HeaderLine", parent=styles["Body"],          # 你已有的基础样式
    fontName=family["BOLD"],        # 左右都可用粗体；或拆成不同样式
    fontSize=11,
    leading=13,
    alignment=TA_LEFT))             # 段落整体左对齐)
    styles.add(ParagraphStyle(name="LeftCell",  parent=styles["Body"],  alignment=TA_LEFT,
                             fontName=family["BOLD"], fontSize=10, leading=13))
    styles.add(ParagraphStyle(name="RightCell", parent=styles["Body"], alignment=TA_RIGHT,
                             fontName=family["BOLD"], fontSize=10, leading=13))
    styles.add(ParagraphStyle(name="LeftCellR",  parent=styles["Body"],  alignment=TA_LEFT,
                             fontName=family["ITALIC"], fontSize=9, leading=13))
    styles.add(ParagraphStyle(name="RightCellR", parent=styles["Body"], alignment=TA_RIGHT,
                             fontName=family["ITALIC"], fontSize=9, leading=13))
    return styles

# ---------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------
def join_contact_line(basics: Dict[str, Any]) -> str:
    parts = []
    for key in ("email", "phone", "linkedin", "github"):
        v = basics.get(key, "")
        if v: parts.append(v)
    return " | ".join(parts)

def bullet_list(flowables: List[str], style: ParagraphStyle) -> ListFlowable:
    items = [ListItem(Paragraph(b, style)) for b in flowables if b and str(b).strip()]
    if not items:
        return ListFlowable([])
    return ListFlowable(items, bulletType="bullet", leftPadding=10)

def render_key_value_lines(data, styles, family, label_width=80, font_size=9, gap=2):
    """
    data: dict，如 {"Programming": ["Python","Java"], "Frameworks": ["Spark","Airflow"], ...}
    styles: 你的样式集合（含 Body）
    family: 你的字体家族映射（含 'REG'/'BOLD'）
    label_width: 左侧标签的“对齐宽度”（pt）。可调 70~120
    font_size: 行字号
    gap: 每行之间的垂直间距（pt）
    """
    line_style = ParagraphStyle(
        name="SkillLine",
        parent=styles["Body"],
        fontName=family["REG"],
        fontSize=font_size,
        leading=font_size + 2,
        # 悬挂缩进：第一行往左缩 label_width，后续行左缩进 label_width，从而整齐对齐
        leftIndent=label_width,
        firstLineIndent=-label_width,
        spaceAfter=gap,
    )

    elems = []
    heavy = family.get("HEAVY", family["BOLD"])
    for cat, vals in data.items():
        text = f'<font name="{heavy}">{cat}:</font> ' + ", ".join(vals)
        elems.append(Paragraph(text, line_style))
    return elems


def render_section_title(title: str, styles) -> List[Any]:
    return [Spacer(1, 2), Paragraph(title, styles["Section"]),
            HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey), Spacer(1, 2)]

def table_line(left, right, styles, Bold):
    if Bold:
        role_p = Paragraph(left or "", styles["LeftCell"])
        date_p = Paragraph(right or "", styles["RightCell"])
    else:
        role_p = Paragraph(left or "", styles["LeftCellR"])
        date_p = Paragraph(right or "", styles["RightCellR"])
    w1 = 0.85 * avail_width
    w2 = 0.40 * avail_width
    tbl = Table([[role_p, date_p]], colWidths=[w1,w2])
    tbl.hAlign = 'LEFT'
    tbl.setStyle(TableStyle([
        # ("BACKGROUND", (1,0), (1,0), colors.HexColor("#1F6FEB")),
        ("ALIGN", (0,0), (0,0), "LEFT"),
        ("ALIGN", (2,0), (2,0), "RIGHT"),
        ("FONTNAME", (0,0), (2,0), family["BOLD"]),
        ("FONTSIZE", (0,0), (2,0), 11),
        ("LEFTPADDING",  (0,0), (2,0), 0),
        ("RIGHTPADDING", (0,0), (2,0), 0),
        ("TOPPADDING",   (0,0), (2,0), 0),
        ("BOTTOMPADDING",(0,0), (2,0), 0),
    ]))

    return tbl

# ---------------------------------------------------------------------
# Main build function
# ---------------------------------------------------------------------
def build_pdf(resume: Dict[str, Any], out_path: str, pagesize=LETTER):
    styles = make_styles()
    story: List[Any] = []

    basics = resume.get("basics", {})
    name = basics.get("name", "")
    contact_line = join_contact_line(basics)
    status = basics.get("status","")

    # Header
    if name:
        story.append(Paragraph(name, styles["Name"]))
    if contact_line:
        story.append(Paragraph(contact_line, styles["Contact"]))
        story.append(Paragraph(status, styles["Contact"]))
    story.append(Spacer(1, 1))

    #Education
    edus = resume.get("education", [])
    if edus:
        story += render_section_title("Education", styles)
        for ed in edus:
            # In your JSON, "company" holds school name, "role" holds degree
            degree = ed.get("company", "")
            school = ed.get("role", "")
            location = ed.get("location","")
            dates = ed.get("dates","")

            story.append(table_line(school, dates, styles, True))
            story.append(table_line(degree, location, styles, False))

            story.append(Spacer(1, 1))

   
    # Experience
    exps = resume.get("experience", [])
    
    if exps:
        story += render_section_title("Experience", styles)
        for e in exps:
            role = e.get("role","")
            date = e.get("dates","")
            story.append(table_line(role, date, styles, True))
            
            location = e.get("location","")
            company = e.get("company","")
            story.append(table_line(company, location, styles, False))

            bullets = e.get("bullets", [])
            if bullets:
                story.append(bullet_list(bullets, styles["Body"]))
            story.append(Spacer(1, 1))

    # Projects
    projs = resume.get("projects", [])
    if projs:
        story += render_section_title("Projects", styles)
        for p in projs:
            title = p.get("title", "")
            dates = p.get("dates", "")
            story.append(table_line(title, dates, styles, True))

            bullets = p.get("bullets", [])
            if bullets:
                story.append(bullet_list(bullets, styles["Body"]))
            story.append(Spacer(1, 1))


    # Skills
    skills = resume.get("skills", {})
    if skills:
        story += render_section_title("Technical Skills", styles)
        story.extend(render_key_value_lines(resume["skills"], styles, family, label_width=80))

    

    # Build
    doc = SimpleDocTemplate(
        out_path,
        pagesize=pagesize,
        leftMargin=0.2*inch, rightMargin=0.2*inch,
        topMargin=0.1*inch, bottomMargin=0.1*inch
    )
    doc.build(story)

# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="Path to resume JSON (schema similar to resume.json)")
    parser.add_argument("--out", required=True, help="Output PDF path")
    args = parser.parse_args()

    with open(args.json, "r", encoding="utf-8") as f:
        resume = json.load(f)

    build_pdf(resume, args.out)
    print(f"✔ Generated: {args.out}")

if __name__ == "__main__":
    main()
