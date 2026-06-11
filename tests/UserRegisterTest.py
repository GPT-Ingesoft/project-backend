import unittest
from unittest.mock import MagicMock
from UserConfTest import UserServices, make_user

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

class TestValidateProfileData(unittest.TestCase):

    def test_validate_profile_data(self):
        cases = [
            ("Martin Botina", "martin@test.com", False, None),
            ("Ana Torres", "ana@unal.edu.co", False, None),

            ("", "martin@test.com", True, "name"),
            ("   ", "martin@test.com", True, "name"),

            ("Martin", "", True, "email"),

            ("A", "martin@test.com", True, "Name"),

            ("Martin", "martin", True, "Email"),
            ("Martin", "martin@", True, "Email"),
            ("Martin", "martin@test", True, "Email"),
        ]

        for name, email, raises, match in cases:
            data = {"name": name,"email": email}
            with self.subTest(name=name, email=email):
                if raises:
                    with self.assertRaises(ValueError) as cm:
                        UserServices.validate_profile_data(data)

                    self.assertIn(match, str(cm.exception))
                else:
                    UserServices.validate_profile_data(data)

class TestUpdateOwnProfile(unittest.TestCase):

    def _service(self, duplicated_email=False):
        repo = MagicMock()
        repo.email_exists_for_other_user.return_value = duplicated_email
        repo.update_profile.return_value = make_user(
            nombre="Martin Actualizado",
            correo="martin.actualizado@test.com",
            rol="docente"
        )

        svc = UserServices()
        svc.user_repository = repo

        user = make_user(
            nombre="Martin Botina",
            correo="martin@test.com",
            rol="docente"
        )

        return svc, repo, user

    def test_update_own_profile_successfully(self):
        svc, repo, user = self._service()

        result = svc.update_own_profile(
            user,
            {
                "name": "Martin Actualizado",
                "email": "martin.actualizado@test.com"
            }
        )

        self.assertEqual(result["name"], "Martin Actualizado")
        self.assertEqual(result["email"], "martin.actualizado@test.com")

        repo.email_exists_for_other_user.assert_called_once_with(
            "martin.actualizado@test.com",
            user.id
        )

        repo.update_profile.assert_called_once_with(
            user=user,
            name="Martin Actualizado",
            email="martin.actualizado@test.com"
        )

    def test_update_own_profile_rejects_duplicated_email(self):
        svc, repo, user = self._service(duplicated_email=True)

        with self.assertRaises(ValueError) as cm:
            svc.update_own_profile(
                user,
                {
                    "name": "Martin Actualizado",
                    "email": "duplicado@test.com"
                }
            )

        self.assertIn("duplicado@test.com", str(cm.exception))
        repo.update_profile.assert_not_called()

    def test_update_own_profile_rejects_invalid_data(self):
        svc, repo, user = self._service()

        with self.assertRaises(ValueError):
            svc.update_own_profile(
                user,
                {
                    "name": "",
                    "email": "martin@test.com"
                }
            )

        repo.email_exists_for_other_user.assert_not_called()
        repo.update_profile.assert_not_called()

if __name__ == "__main__":
    unittest.main(verbosity=2)