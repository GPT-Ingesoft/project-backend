import unittest
from unittest.mock import MagicMock
from tests.user_conf_test import UserServices, make_user

class TestAssignRole(unittest.TestCase):

    def _service(self, user=None, found=True):
        repo = MagicMock()
        repo.get_by_id.return_value = user if found else None
        repo.update.return_value = user
        svc = UserServices()
        svc.user_repository = repo
        return svc, repo

    def test_successful_role_assignment(self):
        cases = [
            ("docente", "laboratorista"),
            ("laboratorista", "docente"),
            ("docente", "tecnico"),
        ]

        for current_role, new_role in cases:
            with self.subTest(current_role=current_role, new_role=new_role):
                user = make_user(rol=new_role)
                svc, repo = self._service(user=user)

                result = svc.assign_role(user_id=1, role=new_role)

                self.assertEqual(result["role"], new_role)
                repo.update.assert_called_once()
                call_kwargs = repo.update.call_args.kwargs
                self.assertEqual(call_kwargs["rol"], new_role)

    def test_invalid_role(self):
        invalid_roles = ["admin", "superadmin", "", "Docente"]

        for role in invalid_roles:
            with self.subTest(role=role):
                svc, repo = self._service(user=make_user())

                with self.assertRaises(ValueError):
                    svc.assign_role(user_id=1, role=role)

                repo.update.assert_not_called()

    def test_user_not_found(self):
        svc, repo = self._service(found=False)

        with self.assertRaises(ValueError) as cm:
            svc.assign_role(user_id=999, role="docente")

        self.assertIn("not found", str(cm.exception))
        repo.update.assert_not_called()

class TestChangeStatus(unittest.TestCase):

    def _service(self, user=None, found=True):
        repo = MagicMock()
        repo.get_by_id.return_value = user if found else None
        repo.update.return_value = user
        svc = UserServices()
        svc.user_repository = repo
        return svc, repo

    def test_deactivate_account(self):
        user = make_user()
        user.activo = False
        svc, repo = self._service(user=user)

        result = svc.change_status(user_id=1, active=False)

        self.assertFalse(result["active"])
        repo.update.assert_called_once()
        call_kwargs = repo.update.call_args.kwargs
        self.assertEqual(call_kwargs["activo"], False)

    def test_activate_account(self):
        user = make_user()
        user.activo = True
        svc, repo = self._service(user=user)

        result = svc.change_status(user_id=1, active=True)

        self.assertTrue(result["active"])
        repo.update.assert_called_once()
        call_kwargs = repo.update.call_args.kwargs
        self.assertEqual(call_kwargs["activo"], True)

    def test_user_not_found(self):
        svc, repo = self._service(found=False)

        with self.assertRaises(ValueError) as cm:
            svc.change_status(user_id=999, active=False)

        self.assertIn("not found", str(cm.exception))
        repo.update.assert_not_called()

class TestVerifyAccess(unittest.TestCase):

    def _service(self, user=None, found=True):
        repo = MagicMock()
        repo.get_by_id.return_value = user if found else None
        svc = UserServices()
        svc.user_repository = repo
        return svc, repo

    def test_active_user_can_access(self):
        user = make_user()
        user.activo = True
        svc, _ = self._service(user=user)

        result = svc.verify_access(user_id=1)

        self.assertEqual(result["id"], user.id)
        self.assertTrue(result["active"])

    def test_inactive_user_is_blocked(self):
        user = make_user()
        user.activo = False
        svc, _ = self._service(user=user)

        with self.assertRaises(PermissionError) as cm:
            svc.verify_access(user_id=1)

        self.assertIn("deactivated", str(cm.exception))

    def test_user_not_found(self):
        svc, _ = self._service(found=False)

        with self.assertRaises(ValueError) as cm:
            svc.verify_access(user_id=999)

        self.assertIn("not found", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
