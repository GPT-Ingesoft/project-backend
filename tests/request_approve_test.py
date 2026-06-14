import unittest
from unittest.mock import MagicMock
from tests.request_conf_test import RequestServices, make_request, make_user


class TestApproveRequest(unittest.TestCase):
    """
    RF_35: Cuando se aprueba una solicitud, el módulo de gestión de
    solicitudes debe actualizar automáticamente el estado a 'En proceso'.
    """

    def _service(self, solicitud=None):
        repo = MagicMock()
        repo.get_by_id.return_value = solicitud

        # Simula que el repositorio persiste el cambio y devuelve la
        # solicitud ya actualizada a 'en_proceso'.
        if solicitud is not None:
            def approve(sol, usuario):
                sol.estado = "en_proceso"
                return sol
            repo.approve.side_effect = aprobar

        svc = RequestServices()
        svc.repo = repo
        return svc, repo

    # ── Caso exitoso ───────────────────────────────────────────────────────

    def test_approve_pending_request_changes_status_to_in_progress(self):
        solicitud = make_request(id=10, estado="pendiente")
        usuario = make_user(rol="laboratorista")
        svc, repo = self._service(solicitud)

        result = svc.approve_request(10, usuario)

        self.assertEqual(result["estado"], "en_proceso")
        self.assertEqual(result["id"], 10)
        repo.get_by_id.assert_called_once_with(10)
        repo.approve.assert_called_once_with(solicitud, usuario)

    def test_approve_request_returns_formatted_data(self):
        solicitud = make_request(id=5, estado="pendiente", descripcion="Pantalla rota")
        usuario = make_user()
        svc, _ = self._service(solicitud)

        result = svc.approve_request(5, usuario)

        for key in ("id", "estado", "prioridad", "descripcion", "equipo", "usuario", "created_at"):
            self.assertIn(key, result)
        self.assertEqual(result["descripcion"], "Pantalla rota")

    # ── Casos límite / de error ───────────────────────────────────────────

    def test_approve_nonexistent_request_raises_error(self):
        svc, repo = self._service(solicitud=None)

        with self.assertRaises(ValueError) as cm:
            svc.approve_request(999, make_user())

        self.assertIn("no encontrada", str(cm.exception))
        repo.approve.assert_not_called()

    def test_approve_request_already_in_progress_raises_error(self):
        solicitud = make_request(id=1, estado="en_proceso")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.approve_request(1, make_user())

        self.assertIn("pendiente", str(cm.exception))
        repo.approve.assert_not_called()

    def test_approve_completed_request_raises_error(self):
        solicitud = make_request(id=2, estado="completada")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError):
            svc.approve_request(2, make_user())

        repo.approve.assert_not_called()

    def test_approve_cancelled_request_raises_error(self):
        solicitud = make_request(id=3, estado="cancelada")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError):
            svc.approve_request(3, make_user())

        repo.approve.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
