import time
from datetime import timedelta
from unittest.mock import Mock

from django.test import SimpleTestCase

from information_app.services.report_export_services import ReportExportServices


class ReportExportServicesTests(SimpleTestCase):
    @staticmethod
    def make_rows(total):
        return [
            {
                'id': index,
                'nombre': f'Equipo {index}',
                'codigo_inventario': f'EQ-{index:04d}',
                'ubicacion': 'Laboratorio de pruebas',
                'estado': 'operativo',
                'total_fallas': index % 8,
            }
            for index in range(total)
        ]

    def test_pdf_uses_fresh_data_from_report_service(self):
        admin_services = Mock()
        admin_services.get_failure_report.return_value = self.make_rows(1)

        result = ReportExportServices(admin_services).generate_pdf('fallas')

        admin_services.get_failure_report.assert_called_once_with()
        self.assertTrue(result['content'].startswith(b'%PDF-'))
        self.assertIn(b'Equipo 0', result['content'])
        self.assertEqual(result['record_count'], 1)

    def test_pdf_with_1000_records_is_generated_in_less_than_five_seconds(self):
        admin_services = Mock()
        admin_services.get_failure_report.return_value = self.make_rows(1000)
        service = ReportExportServices(admin_services)

        started_at = time.perf_counter()
        result = service.generate_pdf('fallas')
        elapsed = time.perf_counter() - started_at

        self.assertLess(elapsed, 5)
        self.assertEqual(result['record_count'], 1000)
        self.assertTrue(result['content'].startswith(b'%PDF-'))

    def test_out_of_service_pdf_includes_applied_threshold(self):
        admin_services = Mock()
        admin_services.get_out_of_service_equipment_report.return_value = {
            'umbral_dias': 30,
            'equipos': [],
        }

        result = ReportExportServices(admin_services).generate_pdf(
            'fuera-de-servicio', 30
        )

        admin_services.get_out_of_service_equipment_report.assert_called_once_with(30)
        self.assertIn(b'Umbral aplicado: 30', result['content'])

    def test_invalid_report_type_is_rejected(self):
        with self.assertRaises(ValueError):
            ReportExportServices(Mock()).generate_pdf('desconocido')
