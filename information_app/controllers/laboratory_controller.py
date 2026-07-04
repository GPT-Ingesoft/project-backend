from rest_framework import status
from rest_framework.response import Response

from information_app.controllers.controller_utils import BaseAPIView, handle_exceptions
from information_app.services.laboratory_services import LaboratoryServices


class LaboratoryListCreateView(BaseAPIView):
    @handle_exceptions
    def get(self, request):
        self.get_user(request)
        return Response(
            {'laboratories': LaboratoryServices().list_laboratories()},
            status=status.HTTP_200_OK,
        )

    @handle_exceptions
    def post(self, request):
        self.get_lab_technician(request)
        laboratory = LaboratoryServices().create_laboratory(self.get_json_data(request))
        return Response(
            {'message': 'Laboratory created successfully.', 'laboratory': laboratory},
            status=status.HTTP_201_CREATED,
        )


class LaboratoryDetailView(BaseAPIView):
    @handle_exceptions
    def get(self, request, laboratory_id):
        self.get_user(request)
        return Response(
            {'laboratory': LaboratoryServices().get_laboratory(laboratory_id)},
            status=status.HTTP_200_OK,
        )

    @handle_exceptions
    def patch(self, request, laboratory_id):
        self.get_lab_technician(request)
        laboratory = LaboratoryServices().update_laboratory(
            laboratory_id,
            self.get_json_data(request),
        )
        return Response(
            {'message': 'Laboratory updated successfully.', 'laboratory': laboratory},
            status=status.HTTP_200_OK,
        )

    @handle_exceptions
    def delete(self, request, laboratory_id):
        self.get_lab_technician(request)
        LaboratoryServices().delete_laboratory(laboratory_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ScheduleListCreateView(BaseAPIView):
    @handle_exceptions
    def get(self, request):
        self.get_user(request)
        laboratory_id = request.query_params.get('laboratory_id')
        if laboratory_id not in (None, ''):
            laboratory_id = int(laboratory_id)
        return Response(
            {'schedules': LaboratoryServices().list_schedules(laboratory_id)},
            status=status.HTTP_200_OK,
        )

    @handle_exceptions
    def post(self, request):
        self.get_lab_technician(request)
        schedule = LaboratoryServices().create_schedule(self.get_json_data(request))
        return Response(
            {'message': 'Schedule created successfully.', 'schedule': schedule},
            status=status.HTTP_201_CREATED,
        )


class ScheduleDetailView(BaseAPIView):
    @handle_exceptions
    def get(self, request, schedule_id):
        self.get_user(request)
        return Response(
            {'schedule': LaboratoryServices().get_schedule(schedule_id)},
            status=status.HTTP_200_OK,
        )

    @handle_exceptions
    def patch(self, request, schedule_id):
        self.get_lab_technician(request)
        schedule = LaboratoryServices().update_schedule(
            schedule_id,
            self.get_json_data(request),
        )
        return Response(
            {'message': 'Schedule updated successfully.', 'schedule': schedule},
            status=status.HTTP_200_OK,
        )

    @handle_exceptions
    def delete(self, request, schedule_id):
        self.get_lab_technician(request)
        LaboratoryServices().delete_schedule(schedule_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LaboratoryListCreateDebugView(LaboratoryListCreateView):
    skip_auth = True


class LaboratoryDetailDebugView(LaboratoryDetailView):
    skip_auth = True


class ScheduleListCreateDebugView(ScheduleListCreateView):
    skip_auth = True


class ScheduleDetailDebugView(ScheduleDetailView):
    skip_auth = True
