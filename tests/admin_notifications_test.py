import unittest
from datetime import timedelta
from unittest.mock import MagicMock

from tests.admin_conf_test import (
    NOW,
    make_notification,
    make_admin_service,
    load_request_repository,
)


class TestRequestDeletionProtection(unittest.TestCase):

    def _repo(self):
        return load_request_repository()

    def test_delete_raises_permission_error(self):
        repo = self._repo()
        with self.assertRaises(PermissionError):
            repo.delete_instance(MagicMock())

    def test_delete_error_message_references_requirement(self):
        repo = self._repo()
        with self.assertRaises(PermissionError) as cm:
            repo.delete_instance(MagicMock())
        self.assertIn('RF_36', str(cm.exception))

    def test_delete_does_not_call_orm_delete(self):
        repo = self._repo()
        fake_solicitud = MagicMock()
        try:
            repo.delete_instance(fake_solicitud)
        except PermissionError:
            pass
        fake_solicitud.delete.assert_not_called()


class TestNotificationHistory(unittest.TestCase):

    def test_returns_all_notifications(self):
        notifs = [
            make_notification(3, NOW),
            make_notification(2, NOW - timedelta(days=1)),
            make_notification(1, NOW - timedelta(days=2)),
        ]
        svc, _, _ = make_admin_service(notifications=notifs)
        result = svc.get_notification_history()
        self.assertEqual(len(result), 3)

    def test_preserves_descending_order_from_repository(self):
        notifs = [
            make_notification(10, NOW),
            make_notification(5,  NOW - timedelta(hours=3)),
            make_notification(1,  NOW - timedelta(days=7)),
        ]
        svc, _, _ = make_admin_service(notifications=notifs)
        ids = [n['id'] for n in svc.get_notification_history()]
        self.assertEqual(ids, [10, 5, 1])

    def test_response_includes_required_fields(self):
        notifs = [make_notification(1, NOW, tipo='cambio_estado', mensaje='Aprobada')]
        svc, _, _ = make_admin_service(notifications=notifs)
        item = svc.get_notification_history()[0]
        for field in ('id', 'tipo', 'mensaje', 'fecha_envio', 'destinatarios'):
            self.assertIn(field, item)

    def test_returns_empty_list_when_no_notifications_exist(self):
        svc, _, _ = make_admin_service(notifications=[])
        self.assertEqual(svc.get_notification_history(), [])

    def test_nonexistent_notification_raises_error(self):
        svc, repo, _ = make_admin_service()
        repo.get_notification_by_id.return_value = None
        with self.assertRaises(ValueError):
            svc.get_notification(999)


if __name__ == '__main__':
    unittest.main(verbosity=2)
