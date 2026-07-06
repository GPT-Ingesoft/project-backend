from django.http import HttpResponse

from information_app.controllers.controller_utils import BaseAPIView, handle_exceptions
from information_app.services.report_export_services import ReportExportServices


class ReportExportView(BaseAPIView):
    @handle_exceptions
    def get(self, request, report_type):
        self.get_lab_technician_or_technician(request)
        threshold_days = request.query_params.get('umbral_dias')
        result = ReportExportServices().generate_pdf(report_type, threshold_days)

        response = HttpResponse(result['content'], content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{result["filename"]}"'
        response['X-Report-Generated-At'] = result['generated_at']
        response['X-Report-Generation-Seconds'] = result['duration_seconds']
        response['X-Report-Record-Count'] = result['record_count']
        return response
