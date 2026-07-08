from dataclasses import dataclass
from html import escape
from io import BytesIO
from time import perf_counter

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from information_app.services.admin_services import AdminServices


SYSLAB_BLUE = colors.HexColor('#04325E')
SYSLAB_GREEN = colors.HexColor('#68A645')
SYSLAB_LIGHT_BLUE = colors.HexColor('#EAF1F7')
SYSLAB_BORDER = colors.HexColor('#D7DEE5')
SYSLAB_TEXT = colors.HexColor('#26313D')


@dataclass(frozen=True)
class ReportDefinition:
    title: str
    filename: str
    columns: tuple
    widths: tuple


REPORT_DEFINITIONS = {
    'fallas': ReportDefinition(
        title='Reporte de fallas',
        filename='reporte-fallas.pdf',
        columns=(
            ('nombre', 'Equipo'),
            ('codigo_inventario', 'Código'),
            ('ubicacion', 'Ubicación'),
            ('estado', 'Estado'),
            ('total_fallas', 'Fallas'),
        ),
        widths=(58 * mm, 35 * mm, 58 * mm, 38 * mm, 24 * mm),
    ),
    'tiempos-reparacion': ReportDefinition(
        title='Reporte de tiempos de reparación',
        filename='reporte-tiempos-reparacion.pdf',
        columns=(
            ('nombre', 'Equipo'),
            ('codigo_inventario', 'Código'),
            ('ubicacion', 'Ubicación'),
            ('promedio_horas_reparacion', 'Promedio (h)'),
        ),
        widths=(68 * mm, 42 * mm, 68 * mm, 35 * mm),
    ),
    'fuera-de-servicio': ReportDefinition(
        title='Reporte de equipos fuera de servicio',
        filename='reporte-fuera-de-servicio.pdf',
        columns=(
            ('nombre', 'Equipo'),
            ('codigo_inventario', 'Código'),
            ('ubicacion', 'Ubicación'),
            ('dias_inactivo', 'Días'),
            ('motivo_baja', 'Motivo'),
        ),
        widths=(48 * mm, 32 * mm, 48 * mm, 22 * mm, 63 * mm),
    ),
}


class ReportExportServices:
    def __init__(self, admin_services=None):
        self.admin_services = admin_services or AdminServices()

    def generate_pdf(self, report_type: str, threshold_days=None) -> dict:
        definition = self._get_definition(report_type)
        started_at = perf_counter()
        generated_at = timezone.localtime()

        # The database is queried here, immediately before rendering. The API never
        # accepts report rows from the browser, so exported data reflects server state.
        rows, details = self._get_report_data(report_type, threshold_days)
        pdf = self._render_pdf(definition, rows, generated_at, details)

        return {
            'content': pdf,
            'filename': definition.filename,
            'generated_at': generated_at.isoformat(),
            'duration_seconds': round(perf_counter() - started_at, 4),
            'record_count': len(rows),
        }

    def _get_report_data(self, report_type: str, threshold_days):
        if report_type == 'fallas':
            return self.admin_services.get_failure_report(), None
        if report_type == 'tiempos-reparacion':
            return self.admin_services.get_repair_time_report(), None

        result = self.admin_services.get_out_of_service_equipment_report(threshold_days)
        return result['equipos'], f"Umbral aplicado: {result['umbral_dias']} días"

    @staticmethod
    def _get_definition(report_type: str) -> ReportDefinition:
        definition = REPORT_DEFINITIONS.get(report_type)
        if not definition:
            valid_types = ', '.join(REPORT_DEFINITIONS)
            raise ValueError(
                f"Tipo de reporte '{report_type}' no válido. Opciones: {valid_types}."
            )
        return definition

    def _render_pdf(self, definition, rows, generated_at, details):
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=14 * mm,
            leftMargin=14 * mm,
            topMargin=18 * mm,
            bottomMargin=15 * mm,
            title=definition.title,
            author='SysLab',
            pageCompression=0,
        )
        styles = self._get_styles()
        story = [
            Paragraph(definition.title, styles['ReportTitle']),
            Paragraph(
                f"Generado: {generated_at.strftime('%d/%m/%Y %H:%M:%S')}",
                styles['Metadata'],
            ),
        ]
        if details:
            story.append(Paragraph(escape(details), styles['Metadata']))
        story.extend((Spacer(1, 5 * mm), self._build_table(definition, rows, styles)))
        document.build(
            story,
            onFirstPage=self._draw_page_footer,
            onLaterPages=self._draw_page_footer,
        )
        return buffer.getvalue()

    def _build_table(self, definition, rows, styles):
        data = [
            [Paragraph(escape(label), styles['TableHeader']) for _, label in definition.columns]
        ]
        if rows:
            data.extend(
                [
                    [self._format_cell(row.get(field), styles) for field, _ in definition.columns]
                    for row in rows
                ]
            )
        else:
            data.append([
                Paragraph('No hay registros para este reporte.', styles['EmptyState']),
                *['' for _ in definition.columns[1:]],
            ])

        table = Table(data, colWidths=definition.widths, repeatRows=1, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), SYSLAB_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), (colors.white, SYSLAB_LIGHT_BLUE)),
            ('GRID', (0, 0), (-1, -1), 0.35, SYSLAB_BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('SPAN', (0, 1), (-1, 1)) if not rows else ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        return table

    @staticmethod
    def _format_cell(value, styles):
        if value is None or value == '':
            value = 'Sin dato'
        return Paragraph(escape(str(value)), styles['TableCell'])

    @staticmethod
    def _get_styles():
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=SYSLAB_BLUE,
            alignment=TA_LEFT,
            spaceAfter=5,
        ))
        styles.add(ParagraphStyle(
            name='Metadata',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=SYSLAB_TEXT,
        ))
        styles.add(ParagraphStyle(
            name='TableHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=TA_LEFT,
        ))
        styles.add(ParagraphStyle(
            name='TableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.5,
            leading=9.5,
            textColor=SYSLAB_TEXT,
            alignment=TA_LEFT,
        ))
        styles.add(ParagraphStyle(
            name='EmptyState',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=9,
            textColor=SYSLAB_TEXT,
            alignment=TA_CENTER,
        ))
        return styles

    @staticmethod
    def _draw_page_footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(SYSLAB_GREEN)
        canvas.setLineWidth(1)
        canvas.line(14 * mm, 11 * mm, landscape(A4)[0] - 14 * mm, 11 * mm)
        canvas.setFillColor(SYSLAB_TEXT)
        canvas.setFont('Helvetica', 8)
        canvas.drawString(14 * mm, 7 * mm, 'SysLab · Sistema de gestión de laboratorios')
        canvas.drawRightString(
            landscape(A4)[0] - 14 * mm,
            7 * mm,
            f'Página {document.page}',
        )
        canvas.restoreState()
