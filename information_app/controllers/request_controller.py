from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from information_app.services.request_services import RequestServices
from information_app.controllers.controller_utils import (
    handle_exceptions,
    ControllerMixin,
    require_field,
    ValidationError,
)

class RequestTechnicianReassignmentView(ControllerMixin, APIView):
    authentication_classes = []
    permission_classes     = []

    @handle_exceptions
    def patch(self, request, request_id):
        self.get_lab_technician(request)
        data   = self.get_json_data(request)
        result = RequestServices().reassign_technicians(request_id, data)
        return Response(
            {'message': 'Technicians reassigned successfully.', 'assignment': result},
            status=status.HTTP_200_OK,
        )

class RequestApproveView(ControllerMixin, APIView):
    authentication_classes = []
    permission_classes     = []

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

class LabScheduleView(ControllerMixin, APIView):
    authentication_classes = []
    permission_classes     = []

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

class RequestStatusView(ControllerMixin, APIView):
    authentication_classes = []
    permission_classes     = []

    @handle_exceptions
    def patch(self, request, solicitud_id):
        usuario      = self.get_user(request)
        nuevo_estado = require_field(request.data, 'estado').strip()
        motivo       = require_field(request.data, 'motivo').strip()

        solicitud = RequestServices().change_status_manually(
            solicitud_id, nuevo_estado, motivo, usuario
        )
        return Response(
            {'message': f"Estado actualizado a '{nuevo_estado}'.", 'solicitud': solicitud},
            status=status.HTTP_200_OK,
        )

class RequestAttachmentView(ControllerMixin, APIView):
    authentication_classes = []
    permission_classes     = []

    @handle_exceptions
    def post(self, request, solicitud_id):
        usuario     = self.get_user(request)
        archivo     = request.FILES.get('archivo')

        if not archivo:
            raise ValidationError("El campo 'archivo' es obligatorio.")

        tipo        = request.data.get('tipo', 'otro')
        nombre      = request.data.get('nombre_archivo', '') or archivo.name
        descripcion = request.data.get('descripcion', '')

        adjunto = RequestServices().upload_attachment(
            solicitud_id=solicitud_id,
            archivo=archivo,
            tipo=tipo,
            nombre=nombre,
            tamanio=archivo.size,
            descripcion=descripcion,
            usuario=usuario,
        )
        return Response(
            {'message': 'Archivo adjunto cargado correctamente.', 'adjunto': adjunto},
            status=status.HTTP_201_CREATED,
        )

#################### DEBUG ####################

class RequestApproveDebugView(APIView):
    authentication_classes = []
    permission_classes     = []

    @handle_exceptions
    def patch(self, request, solicitud_id):
        solicitud = RequestServices().approve_request(solicitud_id, usuario=None)
        return Response(
            {'message': 'Solicitud aprobada.', 'solicitud': solicitud},
            status=status.HTTP_200_OK,
        )

class RequestStatusDebugView(APIView):
    authentication_classes = []
    permission_classes     = []

    @handle_exceptions
    def patch(self, request, solicitud_id):
        nuevo_estado = require_field(request.data, 'estado').strip()
        motivo       = require_field(request.data, 'motivo').strip()

        solicitud = RequestServices().change_status_manually(
            solicitud_id, nuevo_estado, motivo, usuario=None
        )
        return Response(
            {'message': f"Estado actualizado a '{nuevo_estado}'.", 'solicitud': solicitud},
            status=status.HTTP_200_OK,
        )

class RequestAttachmentDebugView(APIView):
    authentication_classes = []
    permission_classes     = []

    @handle_exceptions
    def post(self, request, solicitud_id):
        archivo     = request.FILES.get('archivo')
        if not archivo:
            raise ValidationError("El campo 'archivo' es obligatorio.")

        tipo        = request.data.get('tipo', 'otro')
        nombre      = request.data.get('nombre_archivo', '') or archivo.name
        descripcion = request.data.get('descripcion', '')

        adjunto = RequestServices().upload_attachment(
            solicitud_id=solicitud_id,
            archivo=archivo,
            tipo=tipo,
            nombre=nombre,
            tamanio=archivo.size,
            descripcion=descripcion,
            usuario=None,
        )
        return Response(
            {'message': 'Archivo adjunto cargado correctamente.', 'adjunto': adjunto},
            status=status.HTTP_201_CREATED,
        )

class LabScheduleDebugView(APIView):
    authentication_classes = []
    permission_classes     = []

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
