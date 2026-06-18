import unittest
from unittest.mock import MagicMock
from tests.equipment_conf_test import (
    EquipmentServices,
    format_equipment_data,
    validate_required_fields,
    make_equipment,
)

class TestValidateEquipmentData(unittest.TestCase):

    def test_validate_equipment_data(self):
        fields = {"name", "inventory_code", "model", "brand", "serial_number", "location"}
        cases = [
            # ── valid fields ──────────────────────────────────────────────────
            (
                {"name": "Microscopio", "inventory_code": "INV-001", "model": "CX23",
                 "brand": "Olympus", "serial_number": "SN-001", "location": "Lab 301"},
                fields, False, None,
            ),
            (
                {"name": "Laptop", "inventory_code": "INV-002", "model": "ThinkPad",
                 "brand": "Lenovo", "serial_number": "SN-002", "location": "Lab 201"},
                fields , False, None,
            ),

            # ── missing field ─────────────────────────────────────────────────
            (
                {"inventory_code": "INV-001", "model": "CX23",
                 "brand": "Olympus", "serial_number": "SN-001", "location": "Lab 301"},
                fields, True, "name",
            ),
            (
                {"name": "Microscopio", "model": "CX23",
                 "brand": "Olympus", "serial_number": "SN-001", "location": "Lab 301"},
                fields, True, "inventory_code",
            ),
            (
                {"name": "Microscopio", "inventory_code": "INV-001", "model": "CX23",
                 "brand": "Olympus", "location": "Lab 301"},
                fields, True, "serial_number",
            ),
            ({}, fields, True, None),

            # ── empty or whitespace-only field ────────────────────────────────
            (
                {"name": "", "inventory_code": "INV-001", "model": "CX23",
                 "brand": "Olympus", "serial_number": "SN-001", "location": "Lab 301"},
                fields, True, "name",
            ),
            (
                {"name": "   ", "inventory_code": "INV-001", "model": "CX23",
                 "brand": "Olympus", "serial_number": "SN-001", "location": "Lab 301"},
                fields, True, None,
            ),
            (
                {"name": "Microscopio", "inventory_code": "INV-001", "model": "CX23",
                 "brand": "Olympus", "serial_number": "", "location": "Lab 301"},
                fields, True, "serial_number",
            ),
            (
                {"name": "Microscopio", "inventory_code": "INV-001", "model": "CX23",
                 "brand": "Olympus", "serial_number": "SN-001", "location": "  "},
                fields, True, None,
            ),
        ]

        for data, fields, raises, match in cases:
            with self.subTest(data=data):
                if raises:
                    with self.assertRaises(ValueError) as cm:
                        validate_required_fields(data, fields)
                    if match:
                        self.assertIn(match, str(cm.exception))
                else:
                    validate_required_fields(data, fields)

class TestRegisterEquipment(unittest.TestCase):

    def _service(self, inventory_code_exists=False, serial_number_exists=False,
                 estado="operativo", criticidad="media"):
        repo = MagicMock()
        repo.inventory_code_exists.return_value = inventory_code_exists
        repo.serial_number_exists.return_value  = serial_number_exists
        repo.create.return_value                = make_equipment(estado=estado, criticidad=criticidad)
        svc  = EquipmentServices()
        svc.equipment_repository = repo
        return svc, repo

    def _base_data(self, **overrides):
        data = {
            "name":             "Microscopio",
            "inventory_code":   "INV-001",
            "model":            "CX23",
            "brand":            "Olympus",
            "serial_number":    "SN-001",
            "location":         "Lab 301",
        }
        data.update(overrides)
        return data

    # ── successful cases ─────────────────────────────────────────────────────
    def test_successful_registration(self):
        cases = [
            (self._base_data(),                                                "operativo",           "media"  ),
            (self._base_data(status="en_mantenimiento"),                       "en_mantenimiento",    "media"  ),
            (self._base_data(status="fuera_de_servicio"),                      "fuera_de_servicio",   "media"  ),
            (self._base_data(criticality="alta"),                              "operativo",           "alta"   ),
            (self._base_data(criticality="baja"),                              "operativo",           "baja"   ),
            (self._base_data(status="en_mantenimiento", criticality="alta"),   "en_mantenimiento",    "alta"   ),
            (self._base_data(status="fuera_de_servicio", criticality="baja"),   "fuera_de_servicio",   "baja"   ),
        ]

        for data, expected_status, expected_criticality in cases:
            with self.subTest(status=expected_status, criticality=expected_criticality):
                svc, repo = self._service(estado=expected_status, criticidad=expected_criticality)
                result    = svc.register_equipment(data)
                self.assertEqual(result["status"],      expected_status)
                self.assertEqual(result["criticality"], expected_criticality)
                repo.create.assert_called_once()

    # ── error cases ──────────────────────────────────────────────────────────
    def test_invalid_registration(self):
        cases = [

            (self._base_data(status="dado_de_baja"),            False, False, "dado_de_baja"  ),
            (self._base_data(status="roto"),                    False, False, "roto"          ),
            (self._base_data(status="activo"),                  False, False, "activo"        ),
            (self._base_data(status="disponible"),              False, False, "disponible"    ),
            (self._base_data(criticality="critica"),            False, False, "critica"       ),
            (self._base_data(criticality="urgente"),            False, False, "urgente"       ),
            (self._base_data(criticality="normal"),             False, False, "normal"        ),
            (self._base_data(),                                 True,  False, "INV-001"       ),
            (self._base_data(),                                 False, True,  "SN-001"        ),

            ({k: v for k, v in self._base_data().items() if k != "name"},           False, False, "name"           ),
            ({k: v for k, v in self._base_data().items() if k != "inventory_code"}, False, False, "inventory_code" ),
            ({k: v for k, v in self._base_data().items() if k != "serial_number"},  False, False, "serial_number"  ),
            ({k: v for k, v in self._base_data().items() if k != "location"},       False, False, "location"       ),

            (self._base_data(name=""),             False, False, "name"           ),
            (self._base_data(inventory_code=""),   False, False, "inventory_code" ),
            (self._base_data(model=""),            False, False, "model"          ),
            (self._base_data(brand=""),            False, False, "brand"          ),
            (self._base_data(serial_number=""),    False, False, "serial_number"  ),
            (self._base_data(location=""),         False, False, "location"       ),
        ]

        for data, inv_exists, sn_exists, match in cases:
            with self.subTest(data=data, match=match):
                svc, _ = self._service(
                    inventory_code_exists=inv_exists,
                    serial_number_exists=sn_exists,
                )
                with self.assertRaises(ValueError) as cm:
                    svc.register_equipment(data)
                self.assertIn(match, str(cm.exception))

    def test_status_and_criticality_normalized(self):
        cases = [
            ("OPERATIVO",              "ALTA",             "operativo",           "alta"             ),
            ("  en_mantenimiento  ",   "  Media  ",        "en_mantenimiento",    "media"            ),
            ("FUERA_DE_SERVICIO",      "BAJA",             "fuera_de_servicio",   "baja"             ),
            ("  Operativo",            "Alta  ",           "operativo",           "alta"             ),
        ]

        for status_in, criticality_in, expected_status, expected_criticality in cases:
            with self.subTest(status=status_in, criticality=criticality_in):
                svc, repo = self._service()
                data = self._base_data(status=status_in, criticality=criticality_in)
                svc.register_equipment(data)
                call_kwargs = repo.create.call_args.kwargs
                self.assertEqual(call_kwargs["estado"],      expected_status)
                self.assertEqual(call_kwargs["criticidad"], expected_criticality)

    def test_string_fields_stripped(self):
        cases = [
            ("name",               "  Microscopio  ", "nombre",    "Microscopio"  ),
            ("inventory_code",     "  INV-001  ",     "codigo_inventario", "INV-001"      ),
            ("serial_number",      "  SN-001  ",      "numero_serie",    "SN-001"       ),
            ("location",           "  Lab 301  ",     "ubicacion",       "Lab 301"      ),
        ]

        for field, raw_value, db_field, expected_value in cases:
            with self.subTest(field=field):
                svc, repo = self._service()
                data = self._base_data(**{field: raw_value})
                svc.register_equipment(data)
                call_kwargs = repo.create.call_args.kwargs
                self.assertEqual(call_kwargs[db_field], expected_value)

class TestFormatEquipmentData(unittest.TestCase):

    def test_format_equipment_data(self):
        cases = [
            ("Microscopio",   "INV-001", "CX23",       "Olympus", "SN-001",  "Lab 301",  "operativo",         "media" ),
            ("Laptop",        "INV-002", "ThinkPad",   "Lenovo",  "SN-002",  "Lab 201",  "en_mantenimiento",  "alta"  ),
            ("Servidor",      "INV-003", "PowerEdge",  "Dell",    "SN-003",  "Lab 401",  "fuera_de_servicio", "baja"  ),
        ]

        for nombre, codigo, modelo, marca, serie, ubicacion, estado, criticidad in cases:
            with self.subTest(nombre=nombre):
                equipment = make_equipment(
                    nombre=nombre, codigo_inventario=codigo, modelo=modelo,
                    marca=marca, numero_serie=serie, ubicacion=ubicacion,
                    estado=estado, criticidad=criticidad,
                )
                result = format_equipment_data(equipment)

                self.assertEqual(result["name"],           nombre     )
                self.assertEqual(result["inventory_code"], codigo     )
                self.assertEqual(result["model"],          modelo     )
                self.assertEqual(result["brand"],          marca      )
                self.assertEqual(result["serial_number"],  serie      )
                self.assertEqual(result["location"],       ubicacion  )
                self.assertEqual(result["status"],         estado     )
                self.assertEqual(result["criticality"],    criticidad )
                self.assertIn("id",         result)
                self.assertIn("created_at", result)

if __name__ == "__main__":
    unittest.main(verbosity=2)
