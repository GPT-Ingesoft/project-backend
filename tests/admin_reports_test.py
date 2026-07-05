import unittest
from datetime import timedelta

from tests.admin_conf_test import (
    NOW,
    make_equipment,
    make_admin_service,
    UMBRAL_DIAS_DEFAULT,
)


class TestFailureReport(unittest.TestCase):

    def test_returns_equipment_list(self):
        equipos = [
            make_equipment(1, 'Osciloscopio', total_fallas=5),
            make_equipment(2, 'Microscopio',  total_fallas=2),
        ]
        svc, _, _ = make_admin_service(failure=equipos)
        self.assertEqual(len(svc.get_failure_report()), 2)

    def test_preserves_descending_order_from_repository(self):
        equipos = [
            make_equipment(1, 'A', total_fallas=10),
            make_equipment(2, 'B', total_fallas=4),
            make_equipment(3, 'C', total_fallas=1),
        ]
        svc, _, _ = make_admin_service(failure=equipos)
        fallas = [e['total_fallas'] for e in svc.get_failure_report()]
        self.assertEqual(fallas, sorted(fallas, reverse=True))

    def test_response_includes_total_fallas_field(self):
        equipos = [make_equipment(1, 'Equipo X', total_fallas=3)]
        svc, _, _ = make_admin_service(failure=equipos)
        result = svc.get_failure_report()
        self.assertIn('total_fallas', result[0])
        self.assertEqual(result[0]['total_fallas'], 3)

    def test_returns_empty_list_when_no_failures(self):
        svc, _, _ = make_admin_service(failure=[])
        self.assertEqual(svc.get_failure_report(), [])


class TestRepairTimeReport(unittest.TestCase):

    def test_average_duration_is_converted_to_hours(self):
        equipos = [make_equipment(1, 'Torno', promedio_horas=timedelta(hours=5))]
        svc, _, _ = make_admin_service(repair=equipos)
        result = svc.get_repair_time_report()
        self.assertEqual(result[0]['promedio_horas_reparacion'], 5.0)

    def test_returns_none_when_no_average_available(self):
        equipos = [make_equipment(1, 'Torno', promedio_horas=None)]
        svc, _, _ = make_admin_service(repair=equipos)
        self.assertIsNone(svc.get_repair_time_report()[0]['promedio_horas_reparacion'])

    def test_delegates_filtering_to_repository(self):
        svc, repo, _ = make_admin_service(repair=[])
        svc.get_repair_time_report()
        repo.get_repair_time_report.assert_called_once()

    def test_returns_empty_list_without_completed_requests(self):
        svc, _, _ = make_admin_service(repair=[])
        self.assertEqual(svc.get_repair_time_report(), [])


class TestOutOfServiceReport(unittest.TestCase):

    def test_uses_stored_threshold_when_no_parameter_given(self):
        svc, repo, _ = make_admin_service(threshold_stored='45', out_of_service=[])
        svc.get_out_of_service_equipment_report()
        repo.get_out_of_service_equipment.assert_called_once_with(45)

    def test_uses_default_when_no_threshold_is_stored(self):
        svc, repo, _ = make_admin_service(threshold_stored=None, out_of_service=[])
        svc.get_out_of_service_equipment_report()
        repo.get_out_of_service_equipment.assert_called_once_with(UMBRAL_DIAS_DEFAULT)

    def test_inline_parameter_overrides_stored_threshold(self):
        svc, repo, _ = make_admin_service(threshold_stored='45', out_of_service=[])
        svc.get_out_of_service_equipment_report(umbral_dias=10)
        repo.get_out_of_service_equipment.assert_called_once_with(10)

    def test_set_threshold_persists_value(self):
        svc, _, config_repo = make_admin_service()
        svc.set_out_of_service_threshold(60)
        config_repo.set_value.assert_called_once()
        self.assertEqual(config_repo.set_value.call_args[0][1], 60)

    def test_non_numeric_threshold_raises_error(self):
        svc, _, _ = make_admin_service()
        with self.assertRaises(ValueError):
            svc.get_out_of_service_equipment_report(umbral_dias='not_a_number')

    def test_negative_threshold_raises_error(self):
        svc, _, _ = make_admin_service()
        with self.assertRaises(ValueError):
            svc.get_out_of_service_equipment_report(umbral_dias=-5)

    def test_response_includes_threshold_used(self):
        svc, _, _ = make_admin_service(threshold_stored=None, out_of_service=[])
        result = svc.get_out_of_service_equipment_report(umbral_dias=20)
        self.assertEqual(result['umbral_dias'], 20)

    def test_response_includes_equipment_fields(self):
        fecha = NOW - timedelta(days=40)
        equipos = [make_equipment(
            1, 'Fresadora', estado='fuera_de_servicio',
            motivo_baja='Fallo crítico', fecha_baja=fecha, dias_inactivo=40,
        )]
        svc, _, _ = make_admin_service(out_of_service=equipos)
        item = svc.get_out_of_service_equipment_report(umbral_dias=30)['equipos'][0]
        self.assertEqual(item['motivo_baja'], 'Fallo crítico')
        self.assertIn('dias_inactivo', item)
        self.assertIn('fecha_baja', item)


if __name__ == '__main__':
    unittest.main(verbosity=2)