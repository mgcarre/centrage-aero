"""Unit tests of the emport carburant module
"""

from ntpath import join
import unittest

from prepavol.emport_carburant import EmportCarburant
from prepavol.emport_carburant_form import TypeVol

class EmportCarburantTest(unittest.TestCase):
    """Unit tests of emport carburant"""

    def setUp(self):
        self.callsign = "F-GTZR"
        self.bad_emport = EmportCarburant(
            self.callsign,
            [{"vent":+20, "distance":180}],
            "NAV",
            1,
            {"vent":+10, "distance":35},
            20,
            10,
            0,
            0,
            0
            )
        self.good_emport = EmportCarburant(
            self.callsign,
            [{"vent":+20, "distance":150}],
            "NAV",
            1,
            {"vent":+10, "distance":35},
            20,
            100,
            0,
            0,
            100
            )


    def emport_carburant_classinitiation(self):
        self.assertIsInstance(self.bad_emport, EmportCarburant)
        self.assertIsInstance(self.good_emport, EmportCarburant)

    def test_bad_reserve_time(self):
        self.assertIs(self.bad_emport.reserve_time, 30)

    def test_bad_fuel_quantity(self):
        resultat = self.bad_emport.sum_carburant_emporte
        self.assertEqual(resultat, 11)

    def test_bad_fuel_quantity_time(self):
        resultat = self.bad_emport.sum_carburant_emporte_time
        self.assertAlmostEqual(resultat, 2, delta=0.5)

    def test_get_bad_report(self):
        resultat = self.bad_emport.get_report[0]
        self.assertIn("Ce vol n'est pas autorisé", ''.join(resultat))
    
    def test_good_mainfuel_quantity(self):
        resultat = self.good_emport.sum_carburant_emporte
        self.assertEqual(resultat,160)

    def test_get_good_report(self):
        resultat = self.good_emport.get_report[0]
        self.assertIn("BON VOL", " ".join(resultat))