import unittest
from unittest.mock import MagicMock
from tests.request_conf_test import RequestServices, make_request, make_user, make_attachment


class TestUploadAttachment(unittest.TestCase):
    """
    RF_38: El sistema debe asociar los archivos adjuntos a la solicitud
    correspondiente y registrar su fecha y hora de carga.
    """

    def _service(self, solicitud=None, adjunto=None):
        repo = MagicMock()
        repo.get_by_id.return_value = solicitud
        repo.crear_adjunto.return_value = adjunto or make_attachment()

        svc = RequestServices()
        svc.repo = repo
        return svc, repo

    def _archivo(self, nombre="diagnostico.pdf", tamanio=2048):
        archivo = MagicMock()
        archivo.name = nombre
        archivo.size = tamanio
        return archivo

    # ── Caso exitoso ───────────────────────────────────────────────────────

    def test_successful_attachment_upload_is_associated_with_request(self):
        solicitud = make_request(id=7, estado="en_proceso")
        adjunto = make_attachment(solicitud_id=7)
        svc, repo = self._service(solicitud, adjunto)

        result = svc.subir_adjunto(
            solicitud_id=7,
            archivo=self._archivo(),
            tipo="documento",
            nombre="diagnostico.pdf",
            tamanio=2048,
            descripcion="Foto del daño",
            usuario=make_user(),
        )

        self.assertEqual(result["solicitud_id"], 7)
        self.assertEqual(result["nombre_archivo"], "diagnostico.pdf")
        repo.crear_adjunto.assert_called_once()

    def test_attachment_upload_records_upload_date(self):
        solicitud = make_request(id=1, estado="pendiente")
        adjunto = make_attachment()
        svc, _ = self._service(solicitud, adjunto)

        result = svc.subir_adjunto(
            solicitud_id=1,
            archivo=self._archivo(),
            tipo="imagen",
            nombre="foto.png",
            tamanio=1024,
            descripcion="Evidencia del problema",
            usuario=make_user(),
        )

        self.assertIn("fecha_carga", result)
        self.assertEqual(result["fecha_carga"], adjunto.fecha_carga.isoformat())

    def test_unspecified_type_uses_default_other(self):
        solicitud = make_request(id=1, estado="pendiente")
        adjunto = make_attachment(tipo="otro")
        svc, repo = self._service(solicitud, adjunto)

        svc.subir_adjunto(
            solicitud_id=1,
            archivo=self._archivo(),
            tipo=None,
            nombre="archivo.bin",
            tamanio=10,
            descripcion="Sin tipo especificado",
            usuario=make_user(),
        )

        _, kwargs = repo.crear_adjunto.call_args
        self.assertEqual(kwargs["tipo"], "otro")

    def test_name_and_description_are_trimmed(self):
        solicitud = make_request(id=1, estado="pendiente")
        svc, repo = self._service(solicitud, make_attachment())

        svc.subir_adjunto(
            solicitud_id=1,
            archivo=self._archivo(),
            tipo="documento",
            nombre="  reporte.pdf  ",
            tamanio=10,
            descripcion="  Informe técnico  ",
            usuario=make_user(),
        )

        _, kwargs = repo.crear_adjunto.call_args
        self.assertEqual(kwargs["nombre"], "reporte.pdf")
        self.assertEqual(kwargs["descripcion"], "Informe técnico")

    # ── Casos límite / de error ───────────────────────────────────────────

    def test_missing_file_raises_error(self):
        solicitud = make_request(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.subir_adjunto(
                solicitud_id=1, archivo=None, tipo="documento",
                nombre="archivo.pdf", tamanio=10,
                descripcion="desc", usuario=make_user(),
            )

        self.assertIn("archivo", str(cm.exception).lower())
        repo.crear_adjunto.assert_not_called()

    def test_empty_file_name_raises_error(self):
        solicitud = make_request(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.subir_adjunto(
                solicitud_id=1, archivo=self._archivo(), tipo="documento",
                nombre="   ", tamanio=10,
                descripcion="desc", usuario=make_user(),
            )

        self.assertIn("nombre_archivo", str(cm.exception))
        repo.crear_adjunto.assert_not_called()

    def test_empty_description_raises_error(self):
        solicitud = make_request(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.subir_adjunto(
                solicitud_id=1, archivo=self._archivo(), tipo="documento",
                nombre="archivo.pdf", tamanio=10,
                descripcion="", usuario=make_user(),
            )

        self.assertIn("descripcion", str(cm.exception))
        repo.crear_adjunto.assert_not_called()

    def test_invalid_type_raises_error(self):
        solicitud = make_request(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.subir_adjunto(
                solicitud_id=1, archivo=self._archivo(), tipo="audio",
                nombre="archivo.mp3", tamanio=10,
                descripcion="desc", usuario=make_user(),
            )

        self.assertIn("audio", str(cm.exception))
        repo.crear_adjunto.assert_not_called()

    def test_nonexistent_request_raises_error(self):
        svc, repo = self._service(solicitud=None)

        with self.assertRaises(ValueError) as cm:
            svc.subir_adjunto(
                solicitud_id=999, archivo=self._archivo(), tipo="documento",
                nombre="archivo.pdf", tamanio=10,
                descripcion="desc", usuario=make_user(),
            )

        self.assertIn("no encontrada", str(cm.exception))
        repo.crear_adjunto.assert_not_called()

    def test_cannot_attach_to_completed_request(self):
        solicitud = make_request(id=1, estado="completada")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.subir_adjunto(
                solicitud_id=1, archivo=self._archivo(), tipo="documento",
                nombre="archivo.pdf", tamanio=10,
                descripcion="desc", usuario=make_user(),
            )

        self.assertIn("completada", str(cm.exception))
        repo.crear_adjunto.assert_not_called()

    def test_cannot_attach_to_cancelled_request(self):
        solicitud = make_request(id=1, estado="cancelada")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError):
            svc.subir_adjunto(
                solicitud_id=1, archivo=self._archivo(), tipo="documento",
                nombre="archivo.pdf", tamanio=10,
                descripcion="desc", usuario=make_user(),
            )

        repo.crear_adjunto.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
