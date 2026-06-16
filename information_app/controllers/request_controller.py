from rest_framework.response import Response
from rest_framework import status

from information_app.services.request_services import RequestServices
from information_app.controllers.controller_utils import (
    handle_exceptions,
    require_field,
    ValidationError,
    BaseAPIView
)

class RequestTechnicianReassignmentView(BaseAPIView):

    @handle_exceptions
    def patch(self, request, request_id):
        self.get_lab_technician(request)
        data   = self.get_json_data(request)
        result = RequestServices().reassign_technicians(request_id, data)
        return Response(
            {'message': 'Technicians reassigned successfully.', 'assignment': result},
            status=status.HTTP_200_OK,
        )

class RequestApproveView(BaseAPIView):

    @handle_exceptions
    def patch(self, request, solicitud_id):
        usuario   = self.get_lab_technician(request)
        solicitud = RequestServices().approve_request(solicitud_id, usuario)
        return Response(
            {
                'message': 'Solicitud aprobada. Estado actualizado a En proceso.',
                'solicitud': solicitud,
            },
            status=status.HTTP_200_OK,
        )

class LabScheduleView(BaseAPIView):

    @handle_exceptions
    def get(self, request):
        self.get_user(request)
        laboratorio = request.query_params.get('laboratorio', '').strip()
        srv         = RequestServices()

        if not laboratorio:
            return Response(
                {'laboratorios': srv.get_available_laboratories()},
                status=status.HTTP_200_OK,
            )

        horarios = srv.get_lab_schedule(laboratorio)
        return Response(
            {'laboratorio': laboratorio, 'horarios': horarios},
            status=status.HTTP_200_OK,
        )

class RequestStatusView(BaseAPIView):

    @handle_exceptions
    def patch(self, request, solicitud_id):
        usuario      = self.get_user(request)

        data = {
            'estado': require_field(request.data, 'estado').strip(),
            'motivo': require_field(request.data, 'motivo').strip(),
        }

        solicitud = RequestServices().change_status_manually(
            solicitud_id, data, usuario
        )

        return Response(
            {'message': f"Estado actualizado a '{data['estado']}'.", 'solicitud': solicitud},
            status=status.HTTP_200_OK,
        )

class RequestAttachmentView(BaseAPIView):

    @handle_exceptions
    def post(self, request, solicitud_id):
        usuario     = self.get_user(request)
        archivo     = request.FILES.get('archivo')

        if not archivo:
            raise ValidationError("El campo 'archivo' es obligatorio.")

        data = {
            'archivo':     archivo,
            'tipo':        request.data.get('tipo', 'otro'),
            'nombre':      request.data.get('nombre_archivo', '') or archivo.name,
            'tamanio':     archivo.size,
            'descripcion': request.data.get('descripcion', ''),
        }

        adjunto = RequestServices().upload_attachment(
            solicitud_id=solicitud_id,
            data=data,
            usuario=usuario,
        )

        return Response(
            {'message': 'Archivo adjunto cargado correctamente.', 'adjunto': adjunto},
            status=status.HTTP_201_CREATED,
        )

#################### DEBUG ####################

class RequestApproveDebugView(BaseAPIView):

    @handle_exceptions
    def patch(self, request, solicitud_id):
        solicitud = RequestServices().approve_request(solicitud_id, usuario=None)
        return Response(
            {'message': 'Solicitud aprobada.', 'solicitud': solicitud},
            status=status.HTTP_200_OK,
        )

class RequestStatusDebugView(BaseAPIView):

    @handle_exceptions
    def patch(self, request, solicitud_id):
        data = {
            'estado': require_field(request.data, 'estado').strip(),
            'motivo': require_field(request.data, 'motivo').strip(),
        }

        solicitud = RequestServices().change_status_manually(
            solicitud_id, data, usuario=None
        )

        return Response(
            {'message': f"Estado actualizado a '{data['estado']}'.", 'solicitud': solicitud},
            status=status.HTTP_200_OK,
        )

class RequestAttachmentDebugView(BaseAPIView):

    @handle_exceptions
    def post(self, request, solicitud_id):
        archivo     = request.FILES.get('archivo')
        if not archivo:
            raise ValidationError("El campo 'archivo' es obligatorio.")

        data = {
            'archivo':     archivo,
            'tipo':        request.data.get('tipo', 'otro'),
            'nombre':      request.data.get('nombre_archivo', '') or archivo.name,
            'tamanio':     archivo.size,
            'descripcion': request.data.get('descripcion', ''),
        }

        adjunto = RequestServices().upload_attachment(
            solicitud_id=solicitud_id,
            data=data,
            usuario=None,
        )

        return Response(
            {'message': 'Archivo adjunto cargado correctamente.', 'adjunto': adjunto},
            status=status.HTTP_201_CREATED,
        )

class LabScheduleDebugView(BaseAPIView):

    @handle_exceptions
    def get(self, request):
        laboratorio = request.query_params.get('laboratorio', '').strip()
        srv         = RequestServices()

        if not laboratorio:
            return Response(
                {'laboratorios': srv.get_available_laboratories()},
                status=status.HTTP_200_OK,
            )

        horarios = srv.get_lab_schedule(laboratorio)
        return Response(
            {'laboratorio': laboratorio, 'horarios': horarios},
            status=status.HTTP_200_OK,
        )
