import unittest
from unittest.mock import MagicMock
from tests.request_conf_test import RequestServices, make_request, make_user, make_attachment

class TestUploadAttachment(unittest.TestCase):

    def _service(self, solicitud=None, adjunto=None):
        repo = MagicMock()
        repo.get_by_id.return_value = solicitud
        repo.create_attachment.return_value = adjunto or make_attachment()
        repo.is_user_assigned.return_value = True

        svc = RequestServices()
        svc.request_repository = repo
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

        result = svc.upload_attachment(
            solicitud_id=7,
            data={
                "archivo": self._archivo(),
                "tipo": "documento",
                "nombre": "diagnostico.pdf",
                "tamanio": 2048,
                "descripcion": "Foto del daño",
            },
            usuario=make_user(),
        )

        self.assertEqual(result["solicitud_id"], 7)
        self.assertEqual(result["nombre_archivo"], "diagnostico.pdf")
        repo.create_attachment.assert_called_once()

    def test_attachment_upload_records_upload_date(self):
        solicitud = make_request(id=1, estado="pendiente")
        adjunto = make_attachment()
        svc, _ = self._service(solicitud, adjunto)

        result = svc.upload_attachment(
            solicitud_id=1,
            data={
                "archivo": self._archivo(nombre="foto.png"),
                "tipo": "imagen",
                "nombre": "foto.png",
                "tamanio": 1024,
                "descripcion": "Evidencia del problema",
            },
            usuario=make_user(),
        )

        self.assertIn("fecha_carga", result)
        self.assertEqual(result["fecha_carga"], adjunto.fecha_carga.isoformat())

    def test_unspecified_type_uses_default_other(self):
        solicitud = make_request(id=1, estado="pendiente")
        adjunto = make_attachment(tipo="otro")
        svc, repo = self._service(solicitud, adjunto)

        svc.upload_attachment(
            solicitud_id=1,
            data={
                "archivo": self._archivo(nombre="evidencia.zip"),
                "nombre": "evidencia.zip",
                "tamanio": 10,
                "descripcion": "Sin tipo especificado",
            },
            usuario=make_user(),
        )

        _, kwargs = repo.create_attachment.call_args
        attachment = kwargs["attachment"]
        self.assertEqual(attachment.tipo, "otro")

    def test_name_and_description_are_trimmed(self):
        solicitud = make_request(id=1, estado="pendiente")
        svc, repo = self._service(solicitud, make_attachment())

        svc.upload_attachment(
            solicitud_id=1,
            data={
                "archivo": self._archivo(),
                "tipo": "documento",
                "nombre": "  reporte.pdf  ",
                "tamanio": 10,
                "descripcion": "  Informe técnico  ",
            },
            usuario=make_user(),
        )

        _, kwargs = repo.create_attachment.call_args
        attachment = kwargs["attachment"]
        self.assertEqual(attachment.nombre, "reporte.pdf")
        self.assertEqual(attachment.descripcion, "Informe técnico")
    # ── Casos límite / de error ───────────────────────────────────────────

    def test_missing_file_raises_error(self):
        solicitud = make_request(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.upload_attachment(
                solicitud_id=1,
                data={
                    "archivo": None,
                    "tipo": "documento",
                    "nombre": "archivo.pdf",
                    "tamanio": 10,
                    "descripcion": "desc",
                },
                usuario=make_user(),
            )

        self.assertIn("archivo", str(cm.exception).lower())
        repo.create_attachment.assert_not_called()

    def test_empty_file_name_raises_error(self):
        solicitud = make_request(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.upload_attachment(
                solicitud_id=1,
                data={
                    "archivo": self._archivo(),
                    "tipo": "documento",
                    "nombre": "   ",
                    "tamanio": 10,
                    "descripcion": "desc",
                },
                usuario=make_user(),
            )

        self.assertIn("nombre_archivo", str(cm.exception))
        repo.create_attachment.assert_not_called()

    def test_empty_description_raises_error(self):
        solicitud = make_request(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.upload_attachment(
                solicitud_id=1,
                data={
                    "archivo": self._archivo(),
                    "tipo": "documento",
                    "nombre": "archivo.pdf",
                    "tamanio": 10,
                    "descripcion": "",
                },
                usuario=make_user(),
            )

        self.assertIn("descripcion", str(cm.exception))
        repo.create_attachment.assert_not_called()

    def test_invalid_type_raises_error(self):
        solicitud = make_request(id=1, estado="pendiente")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.upload_attachment(
                solicitud_id=1,
                data={
                    "archivo": self._archivo(nombre="archivo.pdf"),
                    "tipo": "audio",
                    "nombre": "archivo.mp3",
                    "tamanio": 10,
                    "descripcion": "desc",
                },
                usuario=make_user(),
            )

        self.assertIn("audio", str(cm.exception))
        repo.create_attachment.assert_not_called()

    def test_unsupported_file_format_raises_error(self):
        solicitud = make_request(id=1, estado="en_proceso")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.upload_attachment(
                solicitud_id=1,
                data={
                    "archivo": self._archivo(nombre="programa.exe"),
                    "nombre": "programa.exe",
                    "tamanio": 10,
                    "descripcion": "Formato no permitido",
                },
                usuario=make_user(),
            )

        self.assertIn("formato", str(cm.exception).lower())
        repo.create_attachment.assert_not_called()

    def test_file_larger_than_ten_mb_raises_error(self):
        solicitud = make_request(id=1, estado="en_proceso")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.upload_attachment(
                solicitud_id=1,
                data={
                    "archivo": self._archivo(
                        nombre="evidencia.pdf",
                        tamanio=(10 * 1024 * 1024) + 1,
                    ),
                    "nombre": "evidencia.pdf",
                    "tamanio": (10 * 1024 * 1024) + 1,
                    "descripcion": "Archivo demasiado grande",
                },
                usuario=make_user(),
            )

        self.assertIn("10 MB", str(cm.exception))
        repo.create_attachment.assert_not_called()

    def test_unassigned_technician_cannot_upload_evidence(self):
        solicitud = make_request(id=1, estado="en_proceso")
        svc, repo = self._service(solicitud)
        repo.is_user_assigned.return_value = False

        with self.assertRaises(PermissionError) as cm:
            svc.upload_attachment(
                solicitud_id=1,
                data={
                    "archivo": self._archivo(nombre="evidencia.png"),
                    "tipo": "imagen",
                    "nombre": "evidencia.png",
                    "tamanio": 10,
                    "descripcion": "Evidencia del trabajo",
                },
                usuario=make_user(rol="tecnico"),
            )

        self.assertIn("asignado", str(cm.exception).lower())
        repo.create_attachment.assert_not_called()

    def test_nonexistent_request_raises_error(self):
        svc, repo = self._service(solicitud=None)

        with self.assertRaises(ValueError) as cm:
            svc.upload_attachment(
                solicitud_id=999,
                data={
                    "archivo": self._archivo(),
                    "tipo": "documento",
                    "nombre": "archivo.pdf",
                    "tamanio": 10,
                    "descripcion": "desc",
                },
                usuario=make_user(),
            )

        self.assertIn("Request not found", str(cm.exception))
        repo.create_attachment.assert_not_called()

    def test_cannot_attach_to_completed_request(self):
        solicitud = make_request(id=1, estado="completada")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError) as cm:
            svc.upload_attachment(
                solicitud_id=1,
                data={
                    "archivo": self._archivo(),
                    "tipo": "documento",
                    "nombre": "archivo.pdf",
                    "tamanio": 10,
                    "descripcion": "desc",
                },
                usuario=make_user(),
            )

        self.assertIn("completada", str(cm.exception))
        repo.create_attachment.assert_not_called()

    def test_cannot_attach_to_cancelled_request(self):
        solicitud = make_request(id=1, estado="cancelada")
        svc, repo = self._service(solicitud)

        with self.assertRaises(ValueError):
            svc.upload_attachment(
                solicitud_id=1,
                data={
                    "archivo": self._archivo(),
                    "tipo": "documento",
                    "nombre": "archivo.pdf",
                    "tamanio": 10,
                    "descripcion": "desc",
                },
                usuario=make_user(),
            )

        repo.create_attachment.assert_not_called()

if __name__ == "__main__":
    unittest.main(verbosity=2)
