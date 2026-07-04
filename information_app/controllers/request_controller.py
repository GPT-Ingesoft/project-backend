from rest_framework.response import Response
from rest_framework import status
from information_app.repositories.user_repository import UserRepository
from information_app.services.request_services import RequestServices
from information_app.controllers.controller_utils import (
    handle_exceptions,
    require_field,
    ValidationError,
    BaseAPIView,
)

class RequestTechnicianReassignmentView(BaseAPIView):
    @handle_exceptions
    def patch(self, request, request_id):
        self.get_lab_technician(request)
        result = RequestServices().reassign_technicians(request_id, self.get_json_data(request))
        return Response(
            {'message': 'Technicians reassigned successfully.', 'assignment': result},
            status=status.HTTP_200_OK,
        )


class RequestCreateView(BaseAPIView):
    @handle_exceptions
    def post(self, request):
        usuario = self.get_lab_technician(request)
        result = RequestServices().create_request(
            self.get_json_data(request),
            usuario,
        )
        return Response(
            {'message': 'Solicitud creada correctamente.', 'solicitud': result},
            status=status.HTTP_201_CREATED,
        )


class RequestDetailView(BaseAPIView):
    @handle_exceptions
    def get(self, request, solicitud_id):
        usuario = self.get_user(request)
        result = RequestServices().get_request(solicitud_id, usuario)
        return Response({'solicitud': result}, status=status.HTTP_200_OK)


class AvailableTechniciansView(BaseAPIView):
    @handle_exceptions
    def get(self, request, solicitud_id):
        self.get_lab_technician(request)
        technicians = RequestServices().get_available_technicians(solicitud_id)
        return Response(
            {'total': len(technicians), 'tecnicos': technicians},
            status=status.HTTP_200_OK,
        )


class RequestApproveView(BaseAPIView):
    @handle_exceptions
    def patch(self, request, solicitud_id):
        usuario = self.get_lab_technician(request)
        solicitud = RequestServices().approve_request(solicitud_id, usuario)
        return Response(
            {
                'message': 'Solicitud aprobada. Estado actualizado a En proceso.',
                'solicitud': solicitud
            },
            status=status.HTTP_200_OK,
        )

class LabScheduleView(BaseAPIView):
    @handle_exceptions
    def get(self, request):
        self.get_user(request)
        laboratorio = request.query_params.get('laboratorio', '').strip()
        srv = RequestServices()
        if not laboratorio:
            return Response(
                {'laboratorios': srv.get_available_laboratories()},
                status=status.HTTP_200_OK
            )
        return Response(
            {'laboratorio': laboratorio, 'horarios': srv.get_lab_schedule(laboratorio)},
            status=status.HTTP_200_OK,
        )

class RequestStatusView(BaseAPIView):
    @handle_exceptions
    def patch(self, request, solicitud_id):
        usuario = self.get_user(request)
        data = {
            'estado': require_field(request.data, 'estado').strip(),
            'motivo': require_field(request.data, 'motivo').strip(),
        }
        solicitud = RequestServices().change_status_manually(solicitud_id, data, usuario)
        return Response(
            {'message': f"Estado actualizado a '{data['estado']}'.", 'solicitud': solicitud},
            status=status.HTTP_200_OK,
        )

class RequestAttachmentView(BaseAPIView):
    @handle_exceptions
    def post(self, request, solicitud_id):
        usuario = self.get_user(request)
        archivo = request.FILES.get('archivo')
        if not archivo:
            raise ValidationError("El campo 'archivo' es obligatorio.")
        adjunto = RequestServices().upload_attachment(
            solicitud_id=solicitud_id,
            data={
                'archivo':     archivo,
                'tipo':        request.data.get('tipo'),
                'nombre':      request.data.get('nombre_archivo', '') or archivo.name,
                'tamanio':     archivo.size,
                'descripcion': request.data.get('descripcion', ''),
            },
            usuario=usuario,
        )
        return Response(
            {'message': 'Archivo adjunto cargado correctamente.', 'adjunto': adjunto},
            status=status.HTTP_201_CREATED,
        )

# ── Debug endpoints ─────────────────────────────────────────────────────────

class RequestCreateDebugView(BaseAPIView):
    skip_auth = True

    @handle_exceptions
    def post(self, request):
        data = self.get_json_data(request)
        user_id = data.pop('user_id', None)
        if not user_id:
            raise ValidationError("Field 'user_id' is required for debug mode.")

        usuario = UserRepository().get_by_id(user_id)
        if not usuario:
            raise ValidationError(f"Usuario con id {user_id} no encontrado.")

        result = RequestServices().create_request(data, usuario)
        return Response(
            {'message': 'Solicitud creada correctamente.', 'solicitud': result},
            status=status.HTTP_201_CREATED,
        )

class RequestTechnicianReassignmentDebugView(RequestTechnicianReassignmentView):
    skip_auth = True

class RequestApproveDebugView(RequestApproveView):
    skip_auth = True

    @handle_exceptions
    def patch(self, request, solicitud_id):
        solicitud = RequestServices().approve_request(solicitud_id, usuario=None)
        return Response(
            {'message': 'Solicitud aprobada.', 'solicitud': solicitud},
            status=status.HTTP_200_OK,
        )

class RequestStatusDebugView(RequestStatusView):
    skip_auth = True

    @handle_exceptions
    def patch(self, request, solicitud_id):
        data = {
            'estado': require_field(request.data, 'estado').strip(),
            'motivo': require_field(request.data, 'motivo').strip(),
        }
        solicitud = RequestServices().change_status_manually(solicitud_id, data, usuario=None)
        return Response(
            {'message': f"Estado actualizado a '{data['estado']}'.", 'solicitud': solicitud},
            status=status.HTTP_200_OK,
        )

class RequestAttachmentDebugView(RequestAttachmentView):
    skip_auth = True

    @handle_exceptions
    def post(self, request, solicitud_id):
        archivo = request.FILES.get('archivo')
        if not archivo:
            raise ValidationError("El campo 'archivo' es obligatorio.")
        adjunto = RequestServices().upload_attachment(
            solicitud_id=solicitud_id,
            data={
                'archivo':     archivo,
                'tipo':        request.data.get('tipo'),
                'nombre':      request.data.get('nombre_archivo', '') or archivo.name,
                'tamanio':     archivo.size,
                'descripcion': request.data.get('descripcion', ''),
            },
            usuario=None,
        )
        return Response(
            {'message': 'Archivo adjunto cargado correctamente.', 'adjunto': adjunto},
            status=status.HTTP_201_CREATED,
        )

class LabScheduleDebugView(LabScheduleView):
    skip_auth = True
