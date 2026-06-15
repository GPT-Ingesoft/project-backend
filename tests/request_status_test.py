import unittest
from unittest.mock import MagicMock
from tests.request_conf_test import RequestServices, make_request, make_user


class TestManualStatusChange(unittest.TestCase):
    """
    RF_37: Si el estado de una solicitud es cambiado manualmente, el
    módulo de gestión de solicitudes debe garantizar que se especifique
    un motivo, el cual quedará asociado a la solicitud.
    """

    def _service(self, solicitud=None):
        repo = MagicMock()
        repo.get_by_id.return_value = solicitud

        if solicitud is not None:
            def change_status(sol, nuevo_estado, motivo, usuario):
                sol.estado = nuevo_estado
                return sol
            repo.change_status.side_effect = change_status
            
        svc = RequestServices()
        svc.repo = repo
        return svc, repo

    # ── Validación del motivo obligatorio ─────────────────────────────────

    def test_empty_reason_raises_error(self):
        solicitud = make_request(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.change_status_manually(1, "cancelada", "", make_user())

        self.assertIn("motivo", str(cm.exception).lower())
        repo.change_status.assert_not_called()

    def test_reason_with_only_spaces_raises_error(self):
        solicitud = make_request(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError):
            svc.change_status_manually(1, "cancelada", "   ", make_user())

        repo.change_status.assert_not_called()

    def test_none_reason_raises_error(self):
        solicitud = make_request(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError):
            svc.change_status_manually(1, "cancelada", None, make_user())

        repo.change_status.assert_not_called()

    def test_reason_is_trimmed_before_saving(self):
        solicitud = make_request(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        svc.change_status_manually(1, "cancelada", "  Equipo dado de baja  ", make_user())

        args, _ = repo.change_status.call_args
        self.assertEqual(args[2], "Equipo dado de baja")

    # ── Validación del estado destino ─────────────────────────────────────

    def test_invalid_status_raises_error(self):
        solicitud = make_request(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.change_status_manually(1, "archivada", "Motivo válido", make_user())

        self.assertIn("archivada", str(cm.exception))
        repo.change_status.assert_not_called()

    def test_nonexistent_request_raises_error(self):
        svc, repo = self._service(solicitud=None)

        with self.assertRaises(ValueError) as cm:
            svc.change_status_manually(999, "cancelada", "Motivo válido", make_user())

        self.assertIn("no encontrada", str(cm.exception))
        repo.change_status.assert_not_called()

    # ── Transiciones de estado permitidas / no permitidas ──────────────────

    def test_allowed_status_transitions_execute_successfully(self):
        casos = [
            ("pendiente", "en_proceso"),
            ("pendiente", "cancelada"),
            ("en_proceso", "completada"),
            ("en_proceso", "cancelada"),
        ]

        for estado_actual, nuevo_estado in casos:
            with self.subTest(de=estado_actual, a=nuevo_estado):
                solicitud = make_request(id=1, estado=estado_actual)
                svc, repo = self._service(solicitud)

                result = svc.change_status_manually(1, nuevo_estado, "Motivo justificado", make_user())

                self.assertEqual(result["estado"], nuevo_estado)
                repo.change_status.assert_called_once()

    def test_disallowed_status_transition_raises_error(self):
        # pendiente -> completada no está permitido directamente
        solicitud = make_request(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.change_status_manually(1, "completada", "Motivo justificado", make_user())

        self.assertIn("pendiente", str(cm.exception))
        self.assertIn("completada", str(cm.exception))
        repo.change_status.assert_not_called()

    def test_completed_request_does_not_allow_changes(self):
        solicitud = make_request(id=1, estado="completada")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.change_status_manually(1, "en_proceso", "Reabrir caso", make_user())

        self.assertIn("completada", str(cm.exception))
        repo.change_status.assert_not_called()

    def test_cancelled_request_does_not_allow_changes(self):
        solicitud = make_request(id=1, estado="cancelada")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError):
            svc.change_status_manually(1, "pendiente", "Reabrir caso", make_user())

        repo.change_status.assert_not_called()

    # ── El motivo queda asociado a la solicitud ────────────────────────────

    def test_reason_is_sent_to_repository_to_be_associated(self):
        solicitud = make_request(id=1, estado="en_proceso")
        usuario = make_user(rol="laboratorista")
        svc, repo = self._service(solicitud)

        svc.change_status_manually(1, "cancelada", "El usuario retiró la solicitud", usuario)

        repo.change_status.assert_called_once_with(
            solicitud, "cancelada", "El usuario retiró la solicitud", usuario
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
