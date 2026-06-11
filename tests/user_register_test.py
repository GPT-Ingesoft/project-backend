import unittest
from unittest.mock import MagicMock
from tests.user_conf_test import UserServices, make_user

class TestValidateUserData(unittest.TestCase):

    def test_validate_user_data(self):
        cases = [
            # ── valid fields ─────────────────────────────────────────────────────────
            ({"name": "Carlos", "email": "c@uni.edu", "role": "docente"},  {"name","email","role"},  False, None  ),
            ({"name": "Ana",    "email": "a@uni.edu", "role": "tecnico"},  {"name","email","role"},  False, None  ),

            # ── missing field ────────────────────────────────────────────────────────
            ({"name": "Carlos", "email": "c@uni.edu"},                     {"name","email","role"},  True, "role" ),
            ({"email": "c@uni.edu", "role": "docente"},                    {"name","email","role"},  True, "name" ),
            ({},                                                            {"name","email","role"},  True, None   ),

            # ── empty or whitespace-only field ───────────────────────────────────────
            ({"name": "",    "email": "c@uni.edu", "role": "docente"},     {"name","email","role"},  True, "name"  ),
            ({"name": "   ", "email": "c@uni.edu", "role": "docente"},     {"name","email","role"},  True, None    ),
            ({"name": "Ana", "email": "",           "role": "docente"},    {"name","email","role"},  True, "email" ),
        ]

        for data, fields, raises, match in cases:
            with self.subTest(data=data):
                if raises:
                    with self.assertRaises(ValueError) as cm:
                        UserServices.validate_user_data(data, fields)
                    if match:
                        self.assertIn(match, str(cm.exception))
                else:
                    UserServices.validate_user_data(data, fields)

class TestRegisterUser(unittest.TestCase):

    def _service(self, email_exists=False, role="docente"):
        repo = MagicMock()
        repo.email_exists.return_value      = email_exists
        repo.create_user.return_value       = make_user(rol=role)
        repo.create_technician.return_value = MagicMock()
        svc  = UserServices()
        svc.user_repository = repo
        return svc, repo

    # ── successful cases ─────────────────────────────────────────────────────
    def test_successful_registration(self):
        cases = [
            ({"name": "Mary Garcia",  "email": "m@uni.edu", "role": "docente"},        "docente"      ),
            ({"name": "John Smith",   "email": "j@uni.edu", "role": "laboratorista"},  "laboratorista"),
            ({"name": "Peter Clark",  "email": "p@uni.edu", "role": "tecnico",
              "specialty": "Networks", "contact": "555-0001"},                         "tecnico"      ),
        ]

        for data, expected_role in cases:
            with self.subTest(role=expected_role):
                svc, repo = self._service(role=expected_role)
                result = svc.register_user(data)
                self.assertEqual(result["role"], expected_role)
                repo.create_user.assert_called_once()

    # ── error cases ──────────────────────────────────────────────────────────
    def test_invalid_registration(self):
        cases = [
            ({"name": "X",      "email": "x@uni.edu", "role": "docente"},     False, "Name"       ),
            ({"name": "Alice",  "email": "a@uni.edu", "role": "superadmin"},  False, "superadmin" ),
            ({"name": "Alice",  "email": "a@uni.edu", "role": "admin"},       False, "admin"      ),
            ({"name": "Alice",  "email": "dup@uni.edu", "role": "docente"},   True,  "dup@uni.edu"),
            ({"name": "Robert", "email": "r@uni.edu", "role": "tecnico",
              "contact": "555"},                                               False, "specialty"  ),
            ({"name": "Robert", "email": "r@uni.edu", "role": "tecnico",
              "specialty": "Networks"},                                        False, "contact"    ),
        ]

        for data, email_exists, match in cases:
            with self.subTest(data=data):
                svc, _ = self._service(email_exists=email_exists)
                with self.assertRaises(ValueError) as cm:
                    svc.register_user(data)
                self.assertIn(match, str(cm.exception))

    # ── email normalization ───────────────────────────────────────────────────
    def test_email_normalized(self):
        cases = [
            ("  CLEAN@UNI.EDU  ",  "clean@uni.edu" ),
            ("USER@GMAIL.COM",     "user@gmail.com"),
            ("  Mixed@Case.IO",    "mixed@case.io" ),
        ]

        for email_input, expected_email in cases:
            with self.subTest(email=email_input):
                svc, repo = self._service()
                svc.register_user({"name": "Test", "email": email_input, "role": "docente"})
                self.assertEqual(repo.create_user.call_args.kwargs["email"], expected_email)

class TestFormatUserData(unittest.TestCase):

    def test_format_user_data(self):
        cases = [
            ("Mary Garcia",   "mary@uni.edu",    "docente",        True   ),
            ("John Smith",    "john@uni.edu",    "laboratorista",  False  ),
            ("Peter Clark",   "peter@uni.edu",   "tecnico",        True   ),
        ]

        for nombre, correo, rol, activo in cases:
            with self.subTest(rol=rol):
                user   = make_user(nombre=nombre, correo=correo, rol=rol)
                user.activo = activo
                result = UserServices.format_user_data(user)

                self.assertEqual(result["name"],   nombre)
                self.assertEqual(result["email"],  correo)
                self.assertEqual(result["role"],   rol)
                self.assertEqual(result["active"], activo)
                self.assertIn("id",         result)
                self.assertIn("created_at", result)

class TestRoleHelpers(unittest.TestCase):

    def test_is_lab_technician(self):
        cases = [
            ("laboratorista",   True  ),
            ("docente",         False ),
            ("tecnico",         False ),
        ]

        for rol, expected in cases:
            with self.subTest(rol=rol):
                self.assertEqual(UserServices.is_lab_technician(make_user(rol=rol)), expected)

    def test_is_teacher(self):
        cases = [
            ("docente",         True  ),
            ("laboratorista",   False ),
            ("tecnico",         False ),
        ]

        for rol, expected in cases:
            with self.subTest(rol=rol):
                self.assertEqual(UserServices.is_teacher(make_user(rol=rol)), expected)

    def test_is_technician(self):
        cases = [
            ("tecnico",         True  ),
            ("docente",         False ),
            ("laboratorista",   False ),
        ]

        for rol, expected in cases:
            with self.subTest(rol=rol):
                self.assertEqual(UserServices.is_technician(make_user(rol=rol)), expected)

if __name__ == "__main__":
    unittest.main(verbosity=2)
