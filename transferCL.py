import argparse
import json
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import date

def json_to_pdf(json_path, output_path):
    # === 1. 读取 JSON 文件 ===
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    applicant = data["applicant"]
    document = data["document"]

    # === 2. 确保输出目录存在 ===
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # === 3. 创建 PDF 文档 ===
    doc = SimpleDocTemplate(output_path, pagesize=LETTER,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Header', fontSize=12, leading=14, spaceAfter=6, textColor=colors.HexColor("#2E4053")))
    styles.add(ParagraphStyle(name='Body', fontSize=11, leading=16, spaceAfter=12))
    styles.add(ParagraphStyle(name='Closing', fontSize=11, leading=14, spaceBefore=24))

    story = []

    # === 4. Header ===
    story.append(Paragraph(f"<b>{applicant['name']}</b>", styles["Header"]))
    story.append(Paragraph(f"{applicant['email']} | {applicant['phone']}", styles["Header"]))
    story.append(Paragraph(f"<a href='{applicant['linkedin']}'>{applicant['linkedin']}</a> | "
                           f"<a href='{applicant['github']}'>{applicant['github']}</a>", styles["Header"]))
    story.append(Spacer(1, 0.2 * inch))

    # === 5. 日期与收件人 ===
    recipient = document["recipient"]
    today_str = date.today().strftime("%B %d, %Y")  # e.g. "November 9, 2025"
    story.append(Paragraph(today_str, styles["Body"]))
    story.append(Paragraph(f"Dear {recipient['title']},", styles["Body"]))
    story.append(Spacer(1, 0.1 * inch))

    # === 6. 正文 ===
    for paragraph in document["body"]:
        story.append(Paragraph(paragraph, styles["Body"]))

    # === 7. 结尾 ===
    closing = document["closing"]
    story.append(Paragraph(closing["signature"], styles["Closing"]))
    story.append(Paragraph(closing["name"], styles["Body"]))

    # === 8. 输出 PDF ===
    doc.build(story)
    print(f"✅ PDF generated successfully: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert JSON cover letter to PDF.")
    parser.add_argument("--json", required=True, help="Path to the input JSON file.")
    parser.add_argument("--out", required=True, help="Path to output PDF file.")
    args = parser.parse_args()

    json_to_pdf(args.json, args.out)
