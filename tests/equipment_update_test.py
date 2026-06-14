import unittest
from unittest.mock import MagicMock
from tests.equipment_conf_test import EquipmentServices, make_equipment


class TestUpdateEquipment(unittest.TestCase):

    def _service(
        self,
        inventory_code_exists_for_other=False,
        equipment_found=True,
        estado="operativo",
    ):
        repo = MagicMock()
        repo.get_by_id.return_value = make_equipment(estado=estado) if equipment_found else None
        repo.inventory_code_exists_for_other.return_value = inventory_code_exists_for_other
        repo.update.return_value = make_equipment()

        svc = EquipmentServices()
        svc.equipment_repository = repo
        return svc, repo


    def test_serial_number_cannot_be_modified(self):
        cases = [
            {"serial_number": "SN-NEW-001"},
            {"serial_number": "SN-XYZ-001"},           
            {"serial_number": ""},                      
            {"name": "Nuevo", "serial_number": "SN-9"}, 
        ]

        for data in cases:
            with self.subTest(data=data):
                svc, repo = self._service()
                with self.assertRaises(ValueError) as cm:
                    svc.update_equipment(1, data)
                self.assertIn("serial_number", str(cm.exception))
                repo.get_by_id.assert_not_called()  

    def test_successful_update_each_field_individually(self):
        cases = [
            {"name":           "Nuevo Nombre"       },
            {"inventory_code": "INV-999"            },
            {"model":          "Nuevo Modelo"       },
            {"brand":          "Nueva Marca"        },
            {"location":       "Lab 999"            },
            {"status":         "en_mantenimiento"   },
            {"status":         "fuera_de_servicio"  },
            {"status":         "operativo"          },
            {"criticality":    "alta"               },
            {"criticality":    "baja"               },
            {"criticality":    "media"              },
        ]

        for data in cases:
            with self.subTest(data=data):
                svc, repo = self._service()
                result = svc.update_equipment(1, data)
                repo.get_by_id.assert_called_once_with(1)
                repo.update.assert_called_once()
                self.assertIn("id", result)

    def test_successful_update_multiple_fields(self):
        data = {
            "name":           "Microscopio Mejorado",
            "inventory_code": "INV-002",
            "model":          "CX25",
            "brand":          "Nikon",
            "location":       "Lab 402",
            "status":         "en_mantenimiento",
            "criticality":    "alta",
        }

        svc, repo = self._service()
        result = svc.update_equipment(1, data)
        repo.update.assert_called_once()
        self.assertIn("id", result)

    def test_api_fields_mapped_to_db_columns(self):
        cases = [
            ({"name":           "Nombre"},      "nombre",            "Nombre"           ),
            ({"inventory_code": "INV-X"},       "codigo_inventario", "INV-X"            ),
            ({"model":          "Modelo"},      "modelo",            "Modelo"           ),
            ({"brand":          "Marca"},       "marca",             "Marca"            ),
            ({"location":       "Lab X"},       "ubicacion",         "Lab X"            ),
            ({"status":         "operativo"},   "estado",            "operativo"        ),
            ({"criticality":    "alta"},        "criticidad",        "alta"             ),
        ]

        for data, db_field, expected_value in cases:
            with self.subTest(data=data):
                svc, repo = self._service()
                svc.update_equipment(1, data)
                fields_dict = repo.update.call_args.args[1]
                self.assertEqual(fields_dict[db_field], expected_value)

    def test_decommissioned_equipment_cannot_be_modified(self):
        svc, repo = self._service(estado="dado_de_baja")

        with self.assertRaises(ValueError) as cm:
            svc.update_equipment(1, {"name": "Nuevo"})

        self.assertIn("decommissioned", str(cm.exception))
        repo.update.assert_not_called()

    def test_rejects_empty_string_fields(self):
        cases = [
            ({"name":           ""},  "name"           ),
            ({"inventory_code": ""},  "inventory_code" ),
            ({"model":          ""},  "model"          ),
            ({"brand":          ""},  "brand"          ),
            ({"location":       ""},  "location"       ),
        ]

        for data, match in cases:
            with self.subTest(field=match):
                svc, repo = self._service()
                with self.assertRaises(ValueError) as cm:
                    svc.update_equipment(1, data)
                self.assertIn(match, str(cm.exception))
                repo.update.assert_not_called()

    def test_rejects_whitespace_only_fields(self):
        cases = [
            {"name":           "   "},
            {"inventory_code": "   "},
            {"model":          "   "},
            {"brand":          "   "},
            {"location":       "   "},
        ]

        for data in cases:
            with self.subTest(data=data):
                svc, repo = self._service()
                with self.assertRaises(ValueError):
                    svc.update_equipment(1, data)
                repo.update.assert_not_called()

    def test_rejects_invalid_status_values(self):
        cases = [
            ({"status": "dado_de_baja"}, "dado_de_baja"),  
            ({"status": "roto"},         "roto"        ),
            ({"status": "activo"},       "activo"      ),
            ({"status": "disponible"},   "disponible"  ),
        ]

        for data, match in cases:
            with self.subTest(status=match):
                svc, repo = self._service()
                with self.assertRaises(ValueError) as cm:
                    svc.update_equipment(1, data)
                self.assertIn(match, str(cm.exception))
                repo.update.assert_not_called()

    def test_rejects_invalid_criticality_values(self):
        cases = [
            ({"criticality": "critica"},  "critica"  ),
            ({"criticality": "urgente"},  "urgente"  ),
            ({"criticality": "normal"},   "normal"   ),
        ]

        for data, match in cases:
            with self.subTest(criticality=match):
                svc, repo = self._service()
                with self.assertRaises(ValueError) as cm:
                    svc.update_equipment(1, data)
                self.assertIn(match, str(cm.exception))
                repo.update.assert_not_called()

    def test_rejects_duplicate_inventory_code(self):
        svc, repo = self._service(inventory_code_exists_for_other=True)

        with self.assertRaises(ValueError) as cm:
            svc.update_equipment(1, {"inventory_code": "INV-OTRO"})

        self.assertIn("INV-OTRO", str(cm.exception))
        repo.update.assert_not_called()

    # ── normalización ─────────────────────────────────────────────────────────

    def test_status_and_criticality_lowercased_and_stripped(self):
        cases = [
            ("OPERATIVO",          "ALTA",    "operativo",         "alta"  ),
            ("  en_mantenimiento", "  Media", "en_mantenimiento",  "media" ),
            ("FUERA_DE_SERVICIO",  "BAJA",    "fuera_de_servicio", "baja"  ),
            ("  Operativo  ",      "Alta  ",  "operativo",         "alta"  ),
        ]

        for status_in, criticality_in, expected_status, expected_criticality in cases:
            with self.subTest(status=status_in):
                svc, repo = self._service()
                svc.update_equipment(1, {"status": status_in, "criticality": criticality_in})
                fields_dict = repo.update.call_args.args[1]
                self.assertEqual(fields_dict["estado"],    expected_status)
                self.assertEqual(fields_dict["criticidad"], expected_criticality)

    def test_string_fields_stripped(self):
        cases = [
            ("name",           "  Microscopio  ", "nombre",            "Microscopio" ),
            ("inventory_code", "  INV-001  ",     "codigo_inventario", "INV-001"     ),
            ("model",          "  CX23  ",        "modelo",            "CX23"        ),
            ("brand",          "  Olympus  ",     "marca",             "Olympus"     ),
            ("location",       "  Lab 301  ",     "ubicacion",         "Lab 301"     ),
        ]

        for field, raw_value, db_field, expected_value in cases:
            with self.subTest(field=field):
                svc, repo = self._service()
                svc.update_equipment(1, {field: raw_value})
                fields_dict = repo.update.call_args.args[1]
                self.assertEqual(fields_dict[db_field], expected_value)


if __name__ == "__main__":
    unittest.main(verbosity=2)