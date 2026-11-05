from datetime import date
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Drawing, Line, Rect, String


PURPLE = colors.HexColor('#6555E8')
BLUE = colors.HexColor('#4C7CF3')
INK = colors.HexColor('#24263A')
MUTED = colors.HexColor('#72758A')
PALE = colors.HexColor('#F4F5FB')
PALE_BLUE = colors.HexColor('#EEF3FF')
PALE_PURPLE = colors.HexColor('#F2F0FF')
GREEN = colors.HexColor('#21856E')
RED = colors.HexColor('#C64F63')
GRID = colors.HexColor('#E5E7F0')
PAGE_WIDTH, PAGE_HEIGHT = A4


def _safe_text(value):
    """Keep unusual user-entered Unicode from breaking ReportLab's core fonts."""
    value = str(value or '')
    for dash in ('\u2010', '\u2011', '\u2012', '\u2013', '\u2014', '\u2212'):
        value = value.replace(dash, '-')
    return value.encode('cp1252', errors='replace').decode('cp1252')


def _paragraph_text(value):
    return escape(_safe_text(value)).replace('\n', '<br/>')


def _money(value):
    value = Decimal(value or 0)
    return f'INR {value:,.2f}'


def _percent(value):
    return f'{Decimal(value or 0):.1f}%'


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='StatementTitle', parent=styles['Title'], fontName='Helvetica-Bold',
        fontSize=21, leading=25, textColor=INK, alignment=TA_LEFT, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name='StatementSubtitle', parent=styles['Normal'], fontName='Helvetica',
        fontSize=9, leading=13, textColor=MUTED,
    ))
    styles.add(ParagraphStyle(
        name='StatementSection', parent=styles['Heading2'], fontName='Helvetica-Bold',
        fontSize=12, leading=15, textColor=INK, spaceBefore=12, spaceAfter=7,
    ))
    styles.add(ParagraphStyle(
        name='StatementSmall', parent=styles['Normal'], fontName='Helvetica',
        fontSize=8, leading=11, textColor=MUTED,
    ))
    styles.add(ParagraphStyle(
        name='StatementCell', parent=styles['Normal'], fontName='Helvetica',
        fontSize=7.5, leading=10, textColor=INK, wordWrap='CJK',
    ))
    styles.add(ParagraphStyle(
        name='StatementCellRight', parent=styles['StatementCell'], alignment=TA_RIGHT,
    ))
    styles.add(ParagraphStyle(
        name='StatementCardLabel', parent=styles['Normal'], fontName='Helvetica',
        fontSize=7.5, leading=10, textColor=MUTED,
    ))
    styles.add(ParagraphStyle(
        name='StatementCardValue', parent=styles['Normal'], fontName='Helvetica-Bold',
        fontSize=11, leading=14, textColor=INK,
    ))
    return styles


def _p(text, style):
    return Paragraph(_paragraph_text(text), style)


def _table(data, widths, header=True, right_columns=()):
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign='LEFT')
    commands = [
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, GRID),
    ]
    if header:
        commands.extend([
            ('BACKGROUND', (0, 0), (-1, 0), PALE_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), INK),
        ])
        for column in right_columns:
            commands.append(('ALIGN', (column, 0), (column, -1), 'RIGHT'))
    table.setStyle(TableStyle(commands))
    return table


def _summary_cards(data, styles):
    cards = [
        ('Income in period', data.income_total, GREEN, PALE),
        ('Expenses in period', data.expense_total, RED, PALE),
        ('Investments in period', data.investment_total, BLUE, PALE),
        ('Balance at period end', data.available_balance, PURPLE, PALE_PURPLE),
    ]
    cells = []
    for label, amount, color, background in cards:
        cell = Table([
            [_p(label, styles['StatementCardLabel'])],
            [_p(_money(amount), ParagraphStyle(
                name=f'card-{label}', parent=styles['StatementCardValue'], textColor=color
            ))],
        ], colWidths=[122])
        cell.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), background),
            ('BOX', (0, 0), (-1, -1), 0.5, GRID),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        cells.append(cell)
    cards_table = Table([cells], colWidths=[128, 128, 128, 128])
    cards_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return cards_table


def _compact_amount(value):
    value = float(value or 0)
    if value >= 1_000_000:
        return f'{value / 1_000_000:.1f}m'
    if value >= 10_000:
        return f'{value / 1_000:.0f}k'
    if value >= 1_000:
        return f'{value / 1_000:.1f}k'
    return f'{value:,.0f}'


def _monthly_chart(monthly_spending):
    width, height = 495, 170
    left, right, bottom, top = 42, 8, 27, 12
    chart_width = width - left - right
    chart_height = height - bottom - top
    values = [float(row['amount']) for row in monthly_spending]
    maximum = max(values, default=0)
    scale = maximum or 1
    drawing = Drawing(width, height)
    for tick in range(5):
        y = bottom + chart_height * tick / 4
        value = scale * tick / 4
        drawing.add(Line(left, y, width - right, y, strokeColor=GRID, strokeWidth=0.6))
        drawing.add(String(
            left - 6, y - 2, _compact_amount(value),
            fontName='Helvetica', fontSize=6.5, fillColor=MUTED, textAnchor='end',
        ))
    slot = chart_width / max(len(monthly_spending), 1)
    bar_width = min(25, slot * 0.56)
    for index, row in enumerate(monthly_spending):
        x = left + index * slot + (slot - bar_width) / 2
        bar_height = chart_height * float(row['amount']) / scale if maximum else 0
        if bar_height:
            drawing.add(Rect(x, bottom, bar_width, bar_height, fillColor=PURPLE, strokeColor=None, rx=4, ry=4))
        label = row['short_label']
        if len(monthly_spending) <= 6:
            label = row['label']
        drawing.add(String(
            x + bar_width / 2, 9, _safe_text(label), fontName='Helvetica',
            fontSize=6.5 if len(monthly_spending) > 6 else 6, fillColor=MUTED, textAnchor='middle',
        ))
    return drawing


def _draw_header_footer(user_name, generated_date):
    safe_name = _safe_text(user_name)
    safe_date = generated_date.strftime('%d %b %Y')

    def draw(canvas, document):
        canvas.saveState()
        canvas.setFillColor(PURPLE)
        canvas.circle(42, PAGE_HEIGHT - 33, 11, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont('Helvetica-Bold', 11)
        canvas.drawCentredString(42, PAGE_HEIGHT - 37, 'S')
        canvas.setFillColor(INK)
        canvas.setFont('Helvetica-Bold', 11)
        canvas.drawString(60, PAGE_HEIGHT - 31, 'SmartSpend')
        canvas.setFillColor(MUTED)
        canvas.setFont('Helvetica', 7)
        canvas.drawString(60, PAGE_HEIGHT - 42, 'PERSONAL FINANCE')
        canvas.setFillColor(BLUE)
        canvas.setFont('Helvetica-Bold', 7)
        canvas.drawRightString(PAGE_WIDTH - 40, PAGE_HEIGHT - 34, 'FINANCIAL STATEMENT')
        canvas.setStrokeColor(GRID)
        canvas.setLineWidth(0.7)
        canvas.line(40, PAGE_HEIGHT - 51, PAGE_WIDTH - 40, PAGE_HEIGHT - 51)
        canvas.line(40, 37, PAGE_WIDTH - 40, 37)
        canvas.setFillColor(MUTED)
        canvas.setFont('Helvetica', 7)
        canvas.drawString(40, 25, f'Private statement for {safe_name} • Generated {safe_date}')
        canvas.drawRightString(PAGE_WIDTH - 40, 25, f'Page {document.page}')
        canvas.restoreState()

    return draw


def render_statement_pdf(user, data, generated_date=None):
    generated_date = generated_date or date.today()
    user_name = user.get_full_name().strip() or user.username
    styles = _styles()
    story = [
        Spacer(1, 2 * mm),
        _p('Financial statement', styles['StatementTitle']),
        _p(f'{data.report_scope_label}  •  {data.period_label}', styles['StatementSubtitle']),
        Spacer(1, 3 * mm),
        _p(f'Prepared for {_safe_text(user_name)}  •  Generated {generated_date.strftime("%d %B %Y")}', styles['StatementSmall']),
        Spacer(1, 5 * mm),
        _summary_cards(data, styles),
        Spacer(1, 2 * mm),
        _p('Statement totals cover the selected period. Available balance is calculated through the period end. Subscription and savings-goal figures show your active records when this report was generated.', styles['StatementSmall']),
        _p('Expense category breakdown', styles['StatementSection']),
    ]

    if data.category_breakdown:
        category_rows = [[
            _p('Category', styles['StatementCell']),
            _p('Expenses', styles['StatementCellRight']),
            _p('Share', styles['StatementCellRight']),
        ]]
        for row in data.category_breakdown:
            category_rows.append([
                _p(row['name'], styles['StatementCell']),
                _p(_money(row['amount']), styles['StatementCellRight']),
                _p(_percent(row['share']), styles['StatementCellRight']),
            ])
        story.append(_table(category_rows, [245, 150, 100], right_columns=(1, 2)))
    else:
        story.append(_p('No expenses were recorded in this period.', styles['StatementSmall']))

    story.extend([
        _p('Monthly spending', styles['StatementSection']),
        _p('Expense totals by month. For periods longer than 12 months, the chart shows the latest 12 months.', styles['StatementSmall']),
        Spacer(1, 2 * mm),
    ])
    if any(row['amount'] for row in data.monthly_spending):
        story.append(_monthly_chart(data.monthly_spending))
    else:
        story.append(_p('No monthly expense activity is available for this statement.', styles['StatementSmall']))

    story.append(_p(data.report_scope_label, styles['StatementSection']))
    if data.transactions:
        transaction_rows = [[
            _p('Date', styles['StatementCell']),
            _p('Description', styles['StatementCell']),
            _p('Type', styles['StatementCell']),
            _p('Category', styles['StatementCell']),
            _p('Payment', styles['StatementCell']),
            _p('Amount (INR)', styles['StatementCellRight']),
        ]]
        for transaction in data.transactions:
            transaction_rows.append([
                _p(transaction.date.strftime('%d/%m/%Y'), styles['StatementCell']),
                _p(transaction.description or transaction.get_kind_display(), styles['StatementCell']),
                _p(transaction.get_kind_display(), styles['StatementCell']),
                _p(transaction.category.name if transaction.category else 'Uncategorized', styles['StatementCell']),
                _p(transaction.get_payment_method_display() or '-', styles['StatementCell']),
                _p(_money(transaction.amount), styles['StatementCellRight']),
            ])
        story.append(_table(transaction_rows, [55, 123, 50, 90, 60, 117], right_columns=(5,)))
    else:
        story.append(_p('No transactions match this report selection.', styles['StatementSmall']))

    story.append(_p('Subscription summary', styles['StatementSection']))
    story.append(_p(
        f'{len(data.subscriptions)} active subscription(s) • Estimated monthly total: {_money(data.subscription_monthly_total)}',
        styles['StatementSmall'],
    ))
    if data.subscriptions:
        subscription_rows = [[
            _p('Service', styles['StatementCell']),
            _p('Billing cycle', styles['StatementCell']),
            _p('Next renewal', styles['StatementCell']),
            _p('Amount (INR)', styles['StatementCellRight']),
        ]]
        for subscription in data.subscriptions:
            subscription_rows.append([
                _p(subscription.name, styles['StatementCell']),
                _p(subscription.get_billing_cycle_display(), styles['StatementCell']),
                _p(subscription.next_renewal_date.strftime('%d %b %Y'), styles['StatementCell']),
                _p(_money(subscription.amount), styles['StatementCellRight']),
            ])
        story.append(_table(subscription_rows, [190, 105, 105, 95], right_columns=(3,)))

    story.append(_p('Budget and savings-goal summary', styles['StatementSection']))
    story.append(_p(
        f'{len(data.goals)} active savings goal(s) • Combined target: {_money(data.goal_target_total)} • Current saved: {_money(data.goal_current_total)}',
        styles['StatementSmall'],
    ))
    if data.goals:
        goal_rows = [[
            _p('Goal', styles['StatementCell']),
            _p('Target (INR)', styles['StatementCellRight']),
            _p('Saved (INR)', styles['StatementCellRight']),
            _p('Progress', styles['StatementCellRight']),
        ]]
        for goal in data.goals:
            goal_rows.append([
                _p(goal.name, styles['StatementCell']),
                _p(_money(goal.target_amount), styles['StatementCellRight']),
                _p(_money(goal.current_amount), styles['StatementCellRight']),
                _p(_percent(goal.progress_percentage), styles['StatementCellRight']),
            ])
        story.append(_table(goal_rows, [195, 100, 100, 100], right_columns=(1, 2, 3)))
    else:
        story.append(_p('No active savings goals are recorded.', styles['StatementSmall']))

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=65,
        bottomMargin=48,
        title=f'SmartSpend statement for {user_name}',
        author='SmartSpend',
        pageCompression=1,
    )
    page_callback = _draw_header_footer(user_name, generated_date)
    document.build(story, onFirstPage=page_callback, onLaterPages=page_callback)
    return buffer.getvalue()
