import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from information_app.models import (
    Adjunto,
    Asignacion,
    Equipo,
    Notificacion,
    Solicitud,
    Tecnico,
    Usuario,
)
from information_app.services.auth_services import AuthServices


class BackendRequirementsIntegrationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create(
            nombre='Laboratorista',
            correo='laboratorista.requisitos@unal.edu.co',
            rol='laboratorista',
        )
        cls.teacher = Usuario.objects.create(
            nombre='Docente',
            correo='docente.requisitos@unal.edu.co',
            rol='docente',
        )
        cls.technician_user = Usuario.objects.create(
            nombre='Técnico asignado',
            correo='tecnico.requisitos@unal.edu.co',
            rol='tecnico',
        )
        cls.other_technician_user = Usuario.objects.create(
            nombre='Técnico no asignado',
            correo='otro.tecnico.requisitos@unal.edu.co',
            rol='tecnico',
        )
        cls.technician = Tecnico.objects.create(
            usuario=cls.technician_user,
            especialidad='Electrónica',
            contacto='3000000000',
        )
        Tecnico.objects.create(
            usuario=cls.other_technician_user,
            especialidad='Redes',
            contacto='3111111111',
        )
        cls.equipment = Equipo.objects.create(
            nombre='Microscopio',
            codigo_inventario='REQ-001',
            modelo='M-1',
            marca='SysLab',
            numero_serie='REQ-SERIE-001',
            ubicacion='Laboratorio 1',
        )

    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()

    def tearDown(self):
        self.media_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    @staticmethod
    def authenticated_client(user):
        client = APIClient()
        token = AuthServices.generate_access_token(user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return client

    def test_assigned_technician_can_upload_valid_evidence(self):
        request = Solicitud.objects.create(
            descripcion='Reparación en curso',
            estado='en_proceso',
            usuario=self.teacher,
            equipo=self.equipment,
        )
        Asignacion.objects.create(solicitud=request, tecnico=self.technician)
        evidence = SimpleUploadedFile(
            'diagnostico.pdf',
            b'%PDF-1.4 evidencia',
            content_type='application/pdf',
        )

        response = self.authenticated_client(self.technician_user).post(
            f'/api/solicitudes/{request.id}/adjuntos/',
            {
                'archivo': evidence,
                'tipo': 'documento',
                'descripcion': 'Diagnóstico del daño encontrado',
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Adjunto.objects.count(), 1)
        self.assertEqual(response.data['adjunto']['solicitud_id'], request.id)

    def test_attachment_rejects_invalid_format_and_unassigned_technician(self):
        request = Solicitud.objects.create(
            descripcion='Reparación en curso',
            estado='en_proceso',
            usuario=self.teacher,
            equipo=self.equipment,
        )
        invalid_file = SimpleUploadedFile(
            'evidencia.exe',
            b'contenido',
            content_type='application/octet-stream',
        )

        invalid_response = self.authenticated_client(self.technician_user).post(
            f'/api/solicitudes/{request.id}/adjuntos/',
            {
                'archivo': invalid_file,
                'descripcion': 'Formato inválido',
            },
            format='multipart',
        )
        valid_file = SimpleUploadedFile(
            'evidencia.png',
            b'imagen',
            content_type='image/png',
        )
        unassigned_response = self.authenticated_client(
            self.other_technician_user
        ).post(
            f'/api/solicitudes/{request.id}/adjuntos/',
            {
                'archivo': valid_file,
                'tipo': 'imagen',
                'descripcion': 'Sin asignación',
            },
            format='multipart',
        )

        self.assertEqual(invalid_response.status_code, 400)
        self.assertIn('formato', invalid_response.data['error'].lower())
        self.assertEqual(unassigned_response.status_code, 403)
        self.assertIn('asignado', unassigned_response.data['error'].lower())
        self.assertEqual(Adjunto.objects.count(), 0)

    def test_notification_detail_includes_reason_and_recipient_roles(self):
        request = Solicitud.objects.create(
            descripcion='Equipo sin encender',
            usuario=self.teacher,
            equipo=self.equipment,
        )
        notification = Notificacion.objects.create(
            mensaje='Motivo: se asignó la atención de la solicitud.',
            tipo='asignacion_tecnico',
            solicitud=request,
        )
        notification.destinatarios.add(self.teacher, self.technician_user)

        response = self.authenticated_client(self.admin).get(
            f'/api/admin/notificaciones/{notification.id}/'
        )

        self.assertEqual(response.status_code, 200)
        data = response.data['notificacion']
        self.assertEqual(data['motivo'], notification.mensaje)
        self.assertEqual(
            {recipient['rol'] for recipient in data['destinatarios']},
            {'docente', 'tecnico'},
        )
        self.assertTrue(
            all(recipient['rol_nombre'] for recipient in data['destinatarios'])
        )

    def test_request_dashboard_lists_pending_and_orders_active_by_priority(self):
        for priority, state in (
            ('baja', 'pendiente'),
            ('alta', 'en_proceso'),
            ('media', 'pendiente'),
            ('alta', 'completada'),
        ):
            Solicitud.objects.create(
                descripcion=f'Solicitud {priority} {state}',
                prioridad=priority,
                estado=state,
                usuario=self.teacher,
                equipo=self.equipment,
            )

        response = self.authenticated_client(self.admin).get(
            '/api/panel/solicitudes/'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_pendientes'], 2)
        self.assertEqual(
            [item['prioridad'] for item in response.data['solicitudes_activas']],
            ['alta', 'media', 'baja'],
        )
        self.assertTrue(
            all(
                {'fecha_creacion', 'prioridad', 'estado'} <= set(item)
                for item in response.data['solicitudes_pendientes']
            )
        )
