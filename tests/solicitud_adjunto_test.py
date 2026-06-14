import unittest
from unittest.mock import MagicMock
from tests.solicitud_conf_test import SolicitudServices, make_solicitud, make_usuario, make_adjunto


class TestSubirAdjunto(unittest.TestCase):
    """
    RF_38: El sistema debe asociar los archivos adjuntos a la solicitud
    correspondiente y registrar su fecha y hora de carga.
    """

    def _service(self, solicitud=None, adjunto=None):
        repo = MagicMock()
        repo.get_by_id.return_value = solicitud
        repo.crear_adjunto.return_value = adjunto or make_adjunto()

        svc = SolicitudServices()
        svc.repo = repo
        return svc, repo

    def _archivo(self, nombre="diagnostico.pdf", tamanio=2048):
        archivo = MagicMock()
        archivo.name = nombre
        archivo.size = tamanio
        return archivo

    # ── Caso exitoso ───────────────────────────────────────────────────────

    def test_subir_adjunto_exitoso_queda_asociado_a_la_solicitud(self):
        solicitud = make_solicitud(id=7, estado="en_proceso")
        adjunto = make_adjunto(solicitud_id=7)
        svc, repo = self._service(solicitud, adjunto)

        result = svc.subir_adjunto(
            solicitud_id=7,
            archivo=self._archivo(),
            tipo="documento",
            nombre="diagnostico.pdf",
            tamanio=2048,
            descripcion="Foto del daño",
            usuario=make_usuario(),
        )

        self.assertEqual(result["solicitud_id"], 7)
        self.assertEqual(result["nombre_archivo"], "diagnostico.pdf")
        repo.crear_adjunto.assert_called_once()

    def test_subir_adjunto_registra_fecha_de_carga(self):
        solicitud = make_solicitud(id=1, estado="pendiente")
        adjunto = make_adjunto()
        svc, _ = self._service(solicitud, adjunto)

        result = svc.subir_adjunto(
            solicitud_id=1,
            archivo=self._archivo(),
            tipo="imagen",
            nombre="foto.png",
            tamanio=1024,
            descripcion="Evidencia del problema",
            usuario=make_usuario(),
        )

        self.assertIn("fecha_carga", result)
        self.assertEqual(result["fecha_carga"], adjunto.fecha_carga.isoformat())

    def test_tipo_no_especificado_usa_otro_por_defecto(self):
        solicitud = make_solicitud(id=1, estado="pendiente")
        adjunto = make_adjunto(tipo="otro")
        svc, repo = self._service(solicitud, adjunto)

        svc.subir_adjunto(
            solicitud_id=1,
            archivo=self._archivo(),
            tipo=None,
            nombre="archivo.bin",
            tamanio=10,
            descripcion="Sin tipo especificado",
            usuario=make_usuario(),
        )

        _, kwargs = repo.crear_adjunto.call_args
        self.assertEqual(kwargs["tipo"], "otro")

    def test_nombre_y_descripcion_se_recortan(self):
        solicitud = make_solicitud(id=1, estado="pendiente")
        svc, repo = self._service(solicitud, make_adjunto())

        svc.subir_adjunto(
            solicitud_id=1,
            archivo=self._archivo(),
            tipo="documento",
            nombre="  reporte.pdf  ",
            tamanio=10,
            descripcion="  Informe técnico  ",
            usuario=make_usuario(),
        )

        _, kwargs = repo.crear_adjunto.call_args
        self.assertEqual(kwargs["nombre"], "reporte.pdf")
        self.assertEqual(kwargs["descripcion"], "Informe técnico")

    # ── Casos límite / de error ───────────────────────────────────────────

    def test_archivo_faltante_lanza_error(self):
        solicitud = make_solicitud(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.subir_adjunto(
                solicitud_id=1, archivo=None, tipo="documento",
                nombre="archivo.pdf", tamanio=10,
                descripcion="desc", usuario=make_usuario(),
            )

        self.assertIn("archivo", str(cm.exception).lower())
        repo.crear_adjunto.assert_not_called()

    def test_nombre_archivo_vacio_lanza_error(self):
        solicitud = make_solicitud(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.subir_adjunto(
                solicitud_id=1, archivo=self._archivo(), tipo="documento",
                nombre="   ", tamanio=10,
                descripcion="desc", usuario=make_usuario(),
            )

        self.assertIn("nombre_archivo", str(cm.exception))
        repo.crear_adjunto.assert_not_called()

    def test_descripcion_vacia_lanza_error(self):
        solicitud = make_solicitud(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.subir_adjunto(
                solicitud_id=1, archivo=self._archivo(), tipo="documento",
                nombre="archivo.pdf", tamanio=10,
                descripcion="", usuario=make_usuario(),
            )

        self.assertIn("descripcion", str(cm.exception))
        repo.crear_adjunto.assert_not_called()

    def test_tipo_invalido_lanza_error(self):
        solicitud = make_solicitud(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.subir_adjunto(
                solicitud_id=1, archivo=self._archivo(), tipo="audio",
                nombre="archivo.mp3", tamanio=10,
                descripcion="desc", usuario=make_usuario(),
            )

        self.assertIn("audio", str(cm.exception))
        repo.crear_adjunto.assert_not_called()

    def test_solicitud_inexistente_lanza_error(self):
        svc, repo = self._service(solicitud=None)

        with self.assertRaises(ValueError) as cm:
            svc.subir_adjunto(
                solicitud_id=999, archivo=self._archivo(), tipo="documento",
                nombre="archivo.pdf", tamanio=10,
                descripcion="desc", usuario=make_usuario(),
            )

        self.assertIn("no encontrada", str(cm.exception))
        repo.crear_adjunto.assert_not_called()

    def test_no_se_puede_adjuntar_a_solicitud_completada(self):
        solicitud = make_solicitud(id=1, estado="completada")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.subir_adjunto(
                solicitud_id=1, archivo=self._archivo(), tipo="documento",
                nombre="archivo.pdf", tamanio=10,
                descripcion="desc", usuario=make_usuario(),
            )

        self.assertIn("completada", str(cm.exception))
        repo.crear_adjunto.assert_not_called()

    def test_no_se_puede_adjuntar_a_solicitud_cancelada(self):
        solicitud = make_solicitud(id=1, estado="cancelada")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError):
            svc.subir_adjunto(
                solicitud_id=1, archivo=self._archivo(), tipo="documento",
                nombre="archivo.pdf", tamanio=10,
                descripcion="desc", usuario=make_usuario(),
            )

        repo.crear_adjunto.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
