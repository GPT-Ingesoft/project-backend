import unittest
from unittest.mock import MagicMock
from tests.solicitud_conf_test import SolicitudServices, make_solicitud, make_usuario


class TestAprobarSolicitud(unittest.TestCase):
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
            def aprobar(sol, usuario):
                sol.estado = "en_proceso"
                return sol
            repo.aprobar.side_effect = aprobar

        svc = SolicitudServices()
        svc.repo = repo
        return svc, repo

    # ── Caso exitoso ───────────────────────────────────────────────────────

    def test_aprobar_solicitud_pendiente_cambia_estado_a_en_proceso(self):
        solicitud = make_solicitud(id=10, estado="pendiente")
        usuario = make_usuario(rol="laboratorista")
        svc, repo = self._service(solicitud)

        result = svc.aprobar_solicitud(10, usuario)

        self.assertEqual(result["estado"], "en_proceso")
        self.assertEqual(result["id"], 10)
        repo.get_by_id.assert_called_once_with(10)
        repo.aprobar.assert_called_once_with(solicitud, usuario)

    def test_aprobar_solicitud_retorna_datos_formateados(self):
        solicitud = make_solicitud(id=5, estado="pendiente", descripcion="Pantalla rota")
        usuario = make_usuario()
        svc, _ = self._service(solicitud)

        result = svc.aprobar_solicitud(5, usuario)

        for key in ("id", "estado", "prioridad", "descripcion", "equipo", "usuario", "created_at"):
            self.assertIn(key, result)
        self.assertEqual(result["descripcion"], "Pantalla rota")

    # ── Casos límite / de error ───────────────────────────────────────────

    def test_aprobar_solicitud_inexistente_lanza_error(self):
        svc, repo = self._service(solicitud=None)

        with self.assertRaises(ValueError) as cm:
            svc.aprobar_solicitud(999, make_usuario())

        self.assertIn("no encontrada", str(cm.exception))
        repo.aprobar.assert_not_called()

    def test_aprobar_solicitud_ya_en_proceso_lanza_error(self):
        solicitud = make_solicitud(id=1, estado="en_proceso")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.aprobar_solicitud(1, make_usuario())

        self.assertIn("pendiente", str(cm.exception))
        repo.aprobar.assert_not_called()

    def test_aprobar_solicitud_completada_lanza_error(self):
        solicitud = make_solicitud(id=2, estado="completada")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError):
            svc.aprobar_solicitud(2, make_usuario())

        repo.aprobar.assert_not_called()

    def test_aprobar_solicitud_cancelada_lanza_error(self):
        solicitud = make_solicitud(id=3, estado="cancelada")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError):
            svc.aprobar_solicitud(3, make_usuario())

        repo.aprobar.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
