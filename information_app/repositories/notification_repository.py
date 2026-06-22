from information_app.models import Notificacion, NotificacionUsuario
from information_app.repositories.repository_utils import BaseRepository


class NotificationRepository(BaseRepository):
    def get_model(self):
        return Notificacion

    @staticmethod
    def create_notification(*, message, notification_type, recipients, request=None):
        notification = Notificacion.objects.create(
            mensaje=message,
            tipo=notification_type,
            solicitud=request,
        )
        NotificacionUsuario.objects.bulk_create([
            NotificacionUsuario(notificacion=notification, usuario=user)
            for user in recipients
        ])
        return notification
