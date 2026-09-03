"""
PDF Report Generator for UdyamAI.
Uses ReportLab to render professional, formatted feasibility & business plan reports.
"""

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def create_feasibility_pdf(report_data: dict[str, Any], output_path: str | None = None) -> bytes:
    """
    Generates a PDF document for an UdyamAI Feasibility Analysis Report.

    :param report_data: Dictionary containing report metrics, financial summaries, SWOT, schemes, etc.
    :param output_path: Optional file path to write the PDF directly.
    :return: PDF bytes content.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        output_path if output_path else buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#475569"),
        spaceAfter=15,
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=14,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )
    bold_body_style = ParagraphStyle(
        "BoldBodyText",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#0F172A"),
    )

    story = []

    # Title Banner
    title_text = report_data.get("title", "UdyamAI Business Feasibility & Report")
    story.append(Paragraph(title_text, title_style))

    loc_name = report_data.get("location_name", "Specified Location")
    cat_name = report_data.get("category_name", "Enterprise")
    date_str = report_data.get("generated_at", "2026")
    story.append(
        Paragraph(
            f"<b>Category:</b> {cat_name} | <b>Location:</b> {loc_name} | <b>Date:</b> {date_str}",
            subtitle_style,
        )
    )
    story.append(
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=15)
    )

    # Executive Summary & Overall Feasibility Score
    overall_score = float(report_data.get("overall_score") or 0.0)
    summary_text = str(report_data.get("summary") or "Feasibility analysis complete.")
    recommendation = str(report_data.get("recommendation") or "Proceed with plan.")

    score_color = (
        "#16A34A" if overall_score >= 70 else "#D97706" if overall_score >= 50 else "#DC2626"
    )

    score_box_data = [
        [
            Paragraph(
                "<b>Overall Feasibility Index</b>",
                ParagraphStyle("WhiteText", parent=bold_body_style, textColor=colors.white),
            ),
            Paragraph(
                f"<b>{overall_score:.1f}%</b>",
                ParagraphStyle(
                    "ScoreText",
                    parent=bold_body_style,
                    fontSize=24,
                    leading=28,
                    textColor=colors.white,
                    alignment=1,
                ),
            ),
        ],
        [
            Paragraph(
                f"<b>Recommendation:</b> {recommendation}",
                ParagraphStyle("RecText", parent=body_style, textColor=colors.white),
            ),
            Paragraph(
                "High Potential" if overall_score >= 70 else "Moderate Viability",
                ParagraphStyle("SubText", parent=body_style, textColor=colors.white, alignment=1),
            ),
        ],
    ]

    score_table = Table(score_box_data, colWidths=[380, 150])
    score_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(score_color)),
                ("PADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROUNDEDCORNERS", [4, 4, 4, 4]),
            ]
        )
    )
    story.append(score_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Executive Summary", h1_style))
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 10))

    # Score Breakdown Table
    story.append(Paragraph("Feasibility Sub-Score Breakdown", h1_style))

    m_score = float(report_data.get("market_score") or 0.0)
    f_score = float(report_data.get("financial_score") or 0.0)
    c_score = float(report_data.get("competition_score") or 0.0)
    i_score = float(report_data.get("infrastructure_score") or 0.0)
    r_score = float(report_data.get("risk_score") or 0.0)

    breakdown_data = [
        [
            Paragraph("<b>Domain Dimension</b>", bold_body_style),
            Paragraph("<b>Score</b>", bold_body_style),
            Paragraph("<b>Assessment</b>", bold_body_style),
        ],
        [
            Paragraph("Market Demand & Reach", body_style),
            Paragraph(f"{m_score:.1f}%", body_style),
            Paragraph("Strong" if m_score >= 70 else "Moderate", body_style),
        ],
        [
            Paragraph("Financial Viability & ROI", body_style),
            Paragraph(f"{f_score:.1f}%", body_style),
            Paragraph("Strong" if f_score >= 70 else "Moderate", body_style),
        ],
        [
            Paragraph("Competition Threat Level", body_style),
            Paragraph(f"{c_score:.1f}%", body_style),
            Paragraph("Low Risk" if c_score >= 70 else "Moderate Risk", body_style),
        ],
        [
            Paragraph("Infrastructure & Logistics", body_style),
            Paragraph(f"{i_score:.1f}%", body_style),
            Paragraph("Adequate" if i_score >= 60 else "Constrained", body_style),
        ],
        [
            Paragraph("Risk Resilience", body_style),
            Paragraph(f"{r_score:.1f}%", body_style),
            Paragraph("High Resilience" if r_score >= 70 else "Needs Mitigation", body_style),
        ],
    ]

    table = Table(breakdown_data, colWidths=[240, 100, 190])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 15))

    # Financial Scenario & Capital
    fin_summary = report_data.get("financial_summary", {})
    if fin_summary and isinstance(fin_summary, dict):
        story.append(Paragraph("Financial Model Summary", h1_style))
        p_cost = float(fin_summary.get("project_cost") or 0.0)
        a_cap = float(fin_summary.get("available_capital") or 0.0)
        l_amt = float(fin_summary.get("loan_amount") or 0.0)
        m_sur = float(fin_summary.get("monthly_surplus") or 0.0)
        m_emi = float(fin_summary.get("monthly_emi") or 0.0)
        n_sur = float(fin_summary.get("net_monthly_surplus") or 0.0)

        fin_data = [
            [
                Paragraph("<b>Metric</b>", bold_body_style),
                Paragraph("<b>Amount (Rs.) / Value</b>", bold_body_style),
            ],
            [
                Paragraph("Total Estimated Project Cost", body_style),
                Paragraph(f"Rs. {p_cost:,.2f}", body_style),
            ],
            [
                Paragraph("Available Capital (Equity)", body_style),
                Paragraph(f"Rs. {a_cap:,.2f}", body_style),
            ],
            [
                Paragraph("Recommended Bank Loan", body_style),
                Paragraph(f"Rs. {l_amt:,.2f}", body_style),
            ],
            [
                Paragraph("Estimated Monthly Surplus", body_style),
                Paragraph(f"Rs. {m_sur:,.2f}", body_style),
            ],
            [
                Paragraph("Estimated Monthly EMI", body_style),
                Paragraph(f"Rs. {m_emi:,.2f}", body_style),
            ],
            [
                Paragraph("Net Monthly Surplus", body_style),
                Paragraph(f"Rs. {n_sur:,.2f}", body_style),
            ],
        ]
        fin_table = Table(fin_data, colWidths=[300, 230])
        fin_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(fin_table)
        story.append(Spacer(1, 15))

    # Recommended Government Schemes
    schemes = report_data.get("schemes", [])
    if schemes:
        story.append(Paragraph("Eligible Government Subsidy & Credit Schemes", h1_style))
        sch_rows = [
            [
                Paragraph("<b>Scheme Name</b>", bold_body_style),
                Paragraph("<b>Subsidy %</b>", bold_body_style),
                Paragraph("<b>Status</b>", bold_body_style),
            ]
        ]
        for sch in schemes:
            name = str(sch.get("name", "Scheme"))
            sub_pct = sch.get("subsidy_percentage", "N/A")
            sub_str = f"{sub_pct}%" if isinstance(sub_pct, (int, float)) else str(sub_pct)
            status = str(sch.get("match_status", "Potential Match")).replace("_", " ").title()
            sch_rows.append(
                [
                    Paragraph(name, body_style),
                    Paragraph(sub_str, body_style),
                    Paragraph(status, body_style),
                ]
            )

        sch_table = Table(sch_rows, colWidths=[280, 110, 140])
        sch_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFF6FF")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BFDBFE")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(sch_table)
        story.append(Spacer(1, 15))

    # SWOT Analysis Box
    swot = report_data.get("swot", {})
    if swot and isinstance(swot, dict):
        story.append(Paragraph("SWOT Matrix & Strategic Insights", h1_style))

        def fmt_list(lst: list) -> str:
            if not lst:
                return "• Standard operating model"
            return "<br/>".join([f"• {item}" for item in lst[:3]])

        strengths = fmt_list(swot.get("strengths", []))
        weaknesses = fmt_list(swot.get("weaknesses", []))
        opportunities = fmt_list(swot.get("opportunities", []))
        threats = fmt_list(swot.get("threats", []))

        swot_table_data = [
            [
                Paragraph(f"<b>Strengths</b><br/>{strengths}", body_style),
                Paragraph(f"<b>Weaknesses</b><br/>{weaknesses}", body_style),
            ],
            [
                Paragraph(f"<b>Opportunities</b><br/>{opportunities}", body_style),
                Paragraph(f"<b>Threats</b><br/>{threats}", body_style),
            ],
        ]
        swot_table = Table(swot_table_data, colWidths=[260, 270])
        swot_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#F0FDF4")),
                    ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#FEF2F2")),
                    ("BACKGROUND", (0, 1), (0, 1), colors.HexColor("#EFF6FF")),
                    ("BACKGROUND", (1, 1), (1, 1), colors.HexColor("#FFFBEB")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("PADDING", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(swot_table)
        story.append(Spacer(1, 15))

    # Strategic Action Steps
    next_steps = report_data.get("next_steps", [])
    if next_steps:
        story.append(Paragraph("Recommended Implementation Roadmap", h1_style))
        for idx, step in enumerate(next_steps, 1):
            story.append(Paragraph(f"<b>{idx}.</b> {step}", body_style))
        story.append(Spacer(1, 10))

    # Footer note
    story.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.HexColor("#94A3B8"),
            spaceBefore=15,
            spaceAfter=10,
        )
    )
    story.append(
        Paragraph(
            "<i>Generated by UdyamAI Intelligence Platform. Official Feasibility & Detailed Project Report for Banking & Government Schemes.</i>",
            ParagraphStyle(
                "FooterNote",
                parent=body_style,
                fontSize=8,
                leading=10,
                textColor=colors.HexColor("#64748B"),
                alignment=1,
            ),
        )
    )

    doc.build(story)

    if output_path:
        with open(output_path, "rb") as f:
            return f.read()
    else:
        buffer.seek(0)
        return buffer.getvalue()
