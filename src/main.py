"""
Sales Data Report Generator
Professional, enterprise-inspired PDF report using the project's sample CSV.

Project structure:
Sales-Data-Report-Generator/
├── data/sales.csv
├── reports/
├── charts/
└── src/main.py

Run from PyCharm or terminal:
    python src/main.py

Required packages:
    pip install pandas matplotlib reportlab
"""

from pathlib import Path
from datetime import datetime

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    KeepTogether,
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


# ---------------------------------------------------------------------
# 1. PATHS AND DESIGN SYSTEM
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "sales.csv"
REPORT_DIR = PROJECT_ROOT / "reports"
CHART_DIR = PROJECT_ROOT / "charts"
OUTPUT_PDF = REPORT_DIR / "sales_report.pdf"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

# Enterprise-inspired palette from the supplied design specification.
NAVY = colors.HexColor("#0f2942")
SLATE = colors.HexColor("#f1f5f9")
SLATE_DARK = colors.HexColor("#64748b")
TEXT = colors.HexColor("#243447")
MUTED = colors.HexColor("#64748b")
GREEN = colors.HexColor("#15803d")
RED = colors.HexColor("#b91c1c")
WHITE = colors.white
BORDER = colors.HexColor("#dbe3eb")
GOLD = colors.HexColor("#b99a65")

NAVY_HEX = "#0f2942"
GREEN_HEX = "#15803d"
SLATE_HEX = "#64748b"
GOLD_HEX = "#b99a65"
GRID_HEX = "#e8edf2"

PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 18 * mm
RIGHT_MARGIN = 18 * mm
TOP_MARGIN = 18 * mm
BOTTOM_MARGIN = 18 * mm


# ---------------------------------------------------------------------
# 2. TYPOGRAPHY
# ---------------------------------------------------------------------

def register_fonts():
    """
    Uses DejaVu Sans when available; otherwise ReportLab's Helvetica.
    The report remains usable if the optional font files are unavailable.
    """
    possible_regular = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    possible_bold = [
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]

    regular = next((p for p in possible_regular if p.exists()), None)
    bold = next((p for p in possible_bold if p.exists()), None)

    if regular and bold:
        pdfmetrics.registerFont(TTFont("ReportSans", str(regular)))
        pdfmetrics.registerFont(TTFont("ReportSans-Bold", str(bold)))
        return "ReportSans", "ReportSans-Bold"

    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = register_fonts()


def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="Eyebrow",
        fontName=FONT_BOLD,
        fontSize=7.5,
        leading=10,
        textColor=GOLD,
        spaceAfter=5,
        tracking=1.1,
    ))
    styles.add(ParagraphStyle(
        name="ReportTitle",
        fontName=FONT_BOLD,
        fontSize=23,
        leading=27,
        textColor=NAVY,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="Subtitle",
        fontName=FONT,
        fontSize=9,
        leading=13,
        textColor=MUTED,
    ))
    styles.add(ParagraphStyle(
        name="Section",
        fontName=FONT_BOLD,
        fontSize=12,
        leading=15,
        textColor=NAVY,
        spaceBefore=7,
        spaceAfter=7,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="BodySmall",
        fontName=FONT,
        fontSize=8.2,
        leading=12,
        textColor=TEXT,
    ))
    styles.add(ParagraphStyle(
        name="MutedSmall",
        fontName=FONT,
        fontSize=7.2,
        leading=10,
        textColor=MUTED,
    ))
    styles.add(ParagraphStyle(
        name="KpiLabel",
        fontName=FONT_BOLD,
        fontSize=7,
        leading=9,
        textColor=MUTED,
    ))
    styles.add(ParagraphStyle(
        name="KpiValue",
        fontName=FONT_BOLD,
        fontSize=16,
        leading=19,
        textColor=NAVY,
    ))
    styles.add(ParagraphStyle(
        name="TableHeader",
        fontName=FONT_BOLD,
        fontSize=7,
        leading=9,
        textColor=NAVY,
    ))
    styles.add(ParagraphStyle(
        name="TableCell",
        fontName=FONT,
        fontSize=7.2,
        leading=9,
        textColor=TEXT,
    ))
    styles.add(ParagraphStyle(
        name="TableCellBold",
        fontName=FONT_BOLD,
        fontSize=7.2,
        leading=9,
        textColor=NAVY,
    ))
    styles.add(ParagraphStyle(
        name="Observation",
        fontName=FONT,
        fontSize=8,
        leading=11,
        textColor=TEXT,
    ))
    return styles


STYLES = build_styles()


# ---------------------------------------------------------------------
# 3. DATA INGESTION AND VALIDATION
# ---------------------------------------------------------------------

REQUIRED_COLUMNS = {
    "Order_ID", "Date", "Product", "Category",
    "Quantity", "Unit_Price", "Region"
}


def load_and_prepare_data():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Could not find {DATA_FILE}. Make sure sales.csv is inside the data folder."
        )

    df = pd.read_csv(DATA_FILE)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            "Your CSV is missing required column(s): "
            + ", ".join(sorted(missing))
        )

    df = df.copy()
    df = df.drop_duplicates()

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["Unit_Price"] = pd.to_numeric(df["Unit_Price"], errors="coerce")

    df = df.dropna(
        subset=["Order_ID", "Date", "Product", "Quantity", "Unit_Price", "Region"]
    )

    df = df[(df["Quantity"] >= 0) & (df["Unit_Price"] >= 0)]
    if df.empty:
        raise ValueError("No valid sales records remain after data cleaning.")

    df["Revenue"] = df["Quantity"] * df["Unit_Price"]
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    return df


# ---------------------------------------------------------------------
# 4. BUSINESS METRICS
# ---------------------------------------------------------------------

def calculate_metrics(df):
    total_revenue = float(df["Revenue"].sum())
    total_orders = int(df["Order_ID"].nunique())
    total_units = int(df["Quantity"].sum())
    average_order_value = total_revenue / total_orders if total_orders else 0

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "total_units": total_units,
        "average_order_value": average_order_value,
        "first_date": df["Date"].min(),
        "last_date": df["Date"].max(),
    }


def format_inr(value):
    return f"₹{value:,.0f}"


def format_inr_decimal(value):
    return f"₹{value:,.2f}"


def format_number(value):
    return f"{value:,.0f}"


def get_monthly_summary(df):
    return (
        df.groupby("Month", as_index=False)["Revenue"]
        .sum()
        .sort_values("Month")
    )


def get_product_summary(df):
    result = (
        df.groupby("Product", as_index=False)
        .agg(
            Units=("Quantity", "sum"),
            Revenue=("Revenue", "sum"),
            Orders=("Order_ID", "nunique"),
        )
        .sort_values("Revenue", ascending=False)
    )
    total = result["Revenue"].sum()
    result["Contribution"] = (
        result["Revenue"] / total * 100 if total else 0
    )
    return result


def get_region_summary(df):
    result = (
        df.groupby("Region", as_index=False)
        .agg(
            Orders=("Order_ID", "nunique"),
            Units=("Quantity", "sum"),
            Revenue=("Revenue", "sum"),
        )
        .sort_values("Revenue", ascending=False)
    )
    total = result["Revenue"].sum()
    result["Share"] = result["Revenue"] / total * 100 if total else 0
    return result


# ---------------------------------------------------------------------
# 5. CHART GENERATION
# ---------------------------------------------------------------------

def apply_chart_style(ax):
    ax.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GRID_HEX)
    ax.spines["bottom"].set_color(GRID_HEX)
    ax.tick_params(axis="both", labelsize=8, colors=SLATE_HEX)
    ax.grid(axis="y", color=GRID_HEX, linewidth=0.8)
    ax.set_axisbelow(True)


def create_monthly_chart(df):
    monthly = get_monthly_summary(df)

    fig, ax = plt.subplots(figsize=(9.2, 3.0), dpi=180)
    bars = ax.bar(
        monthly["Month"],
        monthly["Revenue"],
        color=NAVY_HEX,
        width=0.56,
        zorder=3,
    )

    apply_chart_style(ax)
    ax.set_title(
        "Monthly Revenue Trend",
        loc="left",
        fontsize=12,
        fontweight="bold",
        color=NAVY_HEX,
        pad=14,
    )
    ax.set_ylabel("Revenue (₹)", fontsize=8, color=SLATE_HEX)
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda x, _: f"₹{x/1000:,.0f}k")
    )
    ax.tick_params(axis="x", rotation=0)

    for bar, value in zip(bars, monthly["Revenue"]):
        ax.annotate(
            f"₹{value/1000:,.0f}k",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            fontsize=7,
            color=NAVY_HEX,
        )

    ax.margins(x=0.12, y=0.22)
    fig.tight_layout()
    path = CHART_DIR / "monthly_revenue.png"
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def create_product_chart(df):
    products = get_product_summary(df).sort_values("Revenue", ascending=True)

    fig, ax = plt.subplots(figsize=(5.0, 2.55), dpi=180)
    ax.barh(products["Product"], products["Revenue"], color=GOLD_HEX, height=0.55)

    apply_chart_style(ax)
    ax.set_title(
        "Revenue by Product",
        loc="left",
        fontsize=10,
        fontweight="bold",
        color=NAVY_HEX,
        pad=10,
    )
    ax.xaxis.set_major_formatter(
        FuncFormatter(lambda x, _: f"₹{x/1000:,.0f}k")
    )
    ax.tick_params(axis="y", labelsize=7)
    ax.tick_params(axis="x", labelsize=7)
    ax.grid(axis="x", color=GRID_HEX, linewidth=0.7)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    path = CHART_DIR / "product_revenue.png"
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def create_region_chart(df):
    regions = get_region_summary(df).sort_values("Revenue", ascending=True)

    fig, ax = plt.subplots(figsize=(5.0, 2.55), dpi=180)
    ax.barh(regions["Region"], regions["Revenue"], color=NAVY_HEX, height=0.55)

    apply_chart_style(ax)
    ax.set_title(
        "Revenue by Region",
        loc="left",
        fontsize=10,
        fontweight="bold",
        color=NAVY_HEX,
        pad=10,
    )
    ax.xaxis.set_major_formatter(
        FuncFormatter(lambda x, _: f"₹{x/1000:,.0f}k")
    )
    ax.tick_params(axis="y", labelsize=7)
    ax.tick_params(axis="x", labelsize=7)
    ax.grid(axis="x", color=GRID_HEX, linewidth=0.7)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    path = CHART_DIR / "region_revenue.png"
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------
# 6. PDF COMPONENTS
# ---------------------------------------------------------------------

def make_kpi_card(label, value, note, width):
    content = [
        Paragraph(label.upper(), STYLES["KpiLabel"]),
        Spacer(1, 5),
        Paragraph(value, STYLES["KpiValue"]),
        Spacer(1, 3),
        Paragraph(note, STYLES["MutedSmall"]),
    ]
    card = Table([[content]], colWidths=[width], rowHeights=[67])
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SLATE),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return card


def make_data_table(headers, rows, col_widths, total_row=False):
    header_cells = [Paragraph(str(x), STYLES["TableHeader"]) for x in headers]
    body = [header_cells]

    for row in rows:
        body.append([
            cell if isinstance(cell, Paragraph)
            else Paragraph(str(cell), STYLES["TableCell"])
            for cell in row
        ])

    table = Table(
        body,
        colWidths=col_widths,
        repeatRows=1,
        hAlign="LEFT",
    )

    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), SLATE),
        ("TEXTCOLOR", (0, 0), (-1, 0), NAVY),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, BORDER),
        ("LINEBELOW", (0, 1), (-1, -1), 0.35, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]

    for row_index in range(1, len(body)):
        if row_index % 2 == 0:
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), colors.HexColor("#fbfcfd")))

    if total_row and len(body) > 1:
        commands.extend([
            ("BACKGROUND", (0, -1), (-1, -1), SLATE),
            ("LINEABOVE", (0, -1), (-1, -1), 0.8, NAVY),
        ])

    table.setStyle(TableStyle(commands))
    return table


def build_observations(df, metrics):
    monthly = get_monthly_summary(df)
    products = get_product_summary(df)
    regions = get_region_summary(df)

    best_product = products.iloc[0]
    best_region = regions.iloc[0]

    if len(monthly) >= 2:
        first = monthly.iloc[0]["Revenue"]
        last = monthly.iloc[-1]["Revenue"]
        if first:
            change = (last - first) / first * 100
            trend_text = (
                f"Revenue in the latest month was {abs(change):.1f}% "
                f"{'higher' if change >= 0 else 'lower'} than the first month."
            )
        else:
            trend_text = "Monthly revenue is available for the selected reporting period."
    else:
        trend_text = "The dataset contains one reporting month, so a month-to-month comparison is not available."

    return [
        f"<b>Leading product:</b> {best_product['Product']} generated "
        f"{format_inr(best_product['Revenue'])} in revenue "
        f"({best_product['Contribution']:.1f}% of total revenue).",
        f"<b>Leading region:</b> {best_region['Region']} contributed "
        f"{best_region['Share']:.1f}% of recorded revenue.",
        f"<b>Revenue trend:</b> {trend_text}",
    ]


def draw_page(canvas, doc):
    canvas.saveState()

    # Slim top rule.
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(2)
    canvas.line(LEFT_MARGIN, PAGE_HEIGHT - 10 * mm, PAGE_WIDTH - RIGHT_MARGIN, PAGE_HEIGHT - 10 * mm)

    # Running footer.
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(LEFT_MARGIN, 13 * mm, PAGE_WIDTH - RIGHT_MARGIN, 13 * mm)

    canvas.setFont(FONT, 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(
        LEFT_MARGIN,
        8.5 * mm,
        "SALES DATA REPORT  •  CONFIDENTIAL",
    )
    canvas.drawRightString(
        PAGE_WIDTH - RIGHT_MARGIN,
        8.5 * mm,
        f"PAGE {doc.page}",
    )
    canvas.restoreState()


# ---------------------------------------------------------------------
# 7. REPORT GENERATION
# ---------------------------------------------------------------------

def generate_pdf_report(df, metrics):
    monthly_chart = create_monthly_chart(df)
    product_chart = create_product_chart(df)
    region_chart = create_region_chart(df)

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        rightMargin=RIGHT_MARGIN,
        leftMargin=LEFT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title="Sales Performance Report",
        author="Sales Data Report Generator",
        subject="Automated sales performance summary",
    )

    usable_width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    story = []

    # ---------------- PAGE 1: EXECUTIVE SUMMARY ----------------
    story.append(Paragraph("COMMERCIAL PERFORMANCE  /  SALES INTELLIGENCE", STYLES["Eyebrow"]))
    story.append(Paragraph("Sales Performance Report", STYLES["ReportTitle"]))

    date_range = (
        f"{metrics['first_date']:%d %b %Y} — {metrics['last_date']:%d %b %Y}"
    )
    story.append(Paragraph(
        f"Reporting window: {date_range}  &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Currency: INR (₹)  &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Generated: {datetime.now():%d %b %Y}",
        STYLES["Subtitle"],
    ))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Executive Summary", STYLES["Section"]))

    gap = 7
    card_width = (usable_width - gap * 3) / 4
    kpis = [
        make_kpi_card("Total Revenue", format_inr(metrics["total_revenue"]), "Recorded sales value", card_width),
        make_kpi_card("Total Orders", format_number(metrics["total_orders"]), "Unique order IDs", card_width),
        make_kpi_card("Units Sold", format_number(metrics["total_units"]), "Total quantity", card_width),
        make_kpi_card("Average Order Value", format_inr(metrics["average_order_value"]), "Revenue ÷ orders", card_width),
    ]

    kpi_row = Table(
        [[kpis[0], kpis[1], kpis[2], kpis[3]]],
        colWidths=[card_width] * 4,
        hAlign="LEFT",
    )
    kpi_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), gap),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(kpi_row)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Revenue Performance", STYLES["Section"]))
    story.append(Paragraph(
        "Monthly revenue generated from the supplied transaction records.",
        STYLES["MutedSmall"],
    ))
    story.append(Spacer(1, 5))
    story.append(Image(str(monthly_chart), width=usable_width, height=usable_width * 0.34))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Key Observations", STYLES["Section"]))
    observations = build_observations(df, metrics)
    obs_rows = [[
        Paragraph(
            "<font color='#b99a65'><b>•</b></font> " + item,
            STYLES["Observation"],
        )
    ] for item in observations]
    obs_table = Table(obs_rows, colWidths=[usable_width])
    obs_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fbfcfd")),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("LINEBEFORE", (0, 0), (0, -1), 2, GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(obs_table)

    # ---------------- PAGE 2: PRODUCT AND REGION DETAIL ----------------
    story.append(PageBreak())
    story.append(Paragraph("PERFORMANCE BREAKDOWN  /  PRODUCT & REGION", STYLES["Eyebrow"]))
    story.append(Paragraph("Revenue Composition", STYLES["ReportTitle"]))
    story.append(Paragraph(
        "A comparative view of product contribution and regional sales performance.",
        STYLES["Subtitle"],
    ))
    story.append(Spacer(1, 13))

    # Charts side by side.
    chart_width = (usable_width - 10) / 2
    chart_row = Table(
        [[
            Image(str(product_chart), width=chart_width, height=chart_width * 0.53),
            Image(str(region_chart), width=chart_width, height=chart_width * 0.53),
        ]],
        colWidths=[chart_width, chart_width],
        hAlign="LEFT",
    )
    chart_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(chart_row)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Regional Performance", STYLES["Section"]))
    region_summary = get_region_summary(df)
    region_rows = []
    for _, row in region_summary.iterrows():
        region_rows.append([
            row["Region"],
            format_number(row["Orders"]),
            format_number(row["Units"]),
            format_inr(row["Revenue"]),
            f"{row['Share']:.1f}%",
        ])

    region_rows.append([
        "Total",
        format_number(metrics["total_orders"]),
        format_number(metrics["total_units"]),
        format_inr(metrics["total_revenue"]),
        "100.0%",
    ])

    region_table = make_data_table(
        ["Region", "Orders", "Units", "Revenue", "Revenue Share"],
        region_rows,
        [usable_width * 0.25, usable_width * 0.13, usable_width * 0.13,
         usable_width * 0.27, usable_width * 0.22],
        total_row=True,
    )
    story.append(KeepTogether([region_table]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Product Performance", STYLES["Section"]))
    product_summary = get_product_summary(df)
    product_rows = []
    for _, row in product_summary.iterrows():
        product_rows.append([
            row["Product"],
            format_number(row["Orders"]),
            format_number(row["Units"]),
            format_inr(row["Revenue"]),
            f"{row['Contribution']:.1f}%",
        ])

    product_table = make_data_table(
        ["Product", "Orders", "Units Sold", "Revenue", "Contribution"],
        product_rows,
        [usable_width * 0.25, usable_width * 0.13, usable_width * 0.15,
         usable_width * 0.25, usable_width * 0.22],
    )
    story.append(KeepTogether([product_table]))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "<b>Methodology:</b> Revenue is calculated as Quantity × Unit Price. "
        "Orders are counted using unique Order_ID values. Product and regional "
        "contribution are calculated as a share of total recorded revenue. "
        "This report reflects only the fields available in the supplied CSV.",
        STYLES["MutedSmall"],
    ))

    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    return OUTPUT_PDF


# ---------------------------------------------------------------------
# 8. MAIN
# ---------------------------------------------------------------------

def main():
    print("Loading sales data...")
    df = load_and_prepare_data()

    print("Calculating performance metrics...")
    metrics = calculate_metrics(df)

    print("\nSALES SUMMARY")
    print("-" * 40)
    print(f"Total Revenue       : {format_inr_decimal(metrics['total_revenue'])}")
    print(f"Total Orders        : {metrics['total_orders']}")
    print(f"Total Units Sold    : {metrics['total_units']}")
    print(f"Average Order Value : {format_inr_decimal(metrics['average_order_value'])}")
    print("-" * 40)

    print("\nGenerating charts and PDF report...")
    pdf_path = generate_pdf_report(df, metrics)

    print("\nReport generated successfully.")
    print(f"PDF location: {pdf_path}")


if __name__ == "__main__":
    main()
