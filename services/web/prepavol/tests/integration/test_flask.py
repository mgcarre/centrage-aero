# *_* coding: utf-8 *_*

"""End to end tests.
"""

import os
import unittest

from PythonMETAR.metar import NOAAServError
import prepavol
import prepavol.planes as planes
from pytest import raises

class WebAppTestCase(unittest.TestCase):
    """ "Testing the web pages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callsign = "F-GTZR"
        self.plane = planes.WeightBalance(self.callsign)
        self.pilotname = "PILOTATOR"

    def setUp(self):
        os.environ["FLASK_ENV"] = "testing"
        app = prepavol.create_app()
        app.testing = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.app = app.test_client()

    def test_home(self):
        """Read root page"""
        result = self.app.get("/")
        self.assertEqual(result.status_code, 200)

    def test_static(self):
        """Read favicon over the static URL"""
        result = self.app.get("/favicon.ico")
        self.assertEqual(result.status_code, 200)

    def test_fleet(self):
        """Read fleet page"""
        result = self.app.get("/fleet")
        self.assertEqual(result.status_code, 200)

    def test_fuel_page(self):
        result = self.app.get("/carburant")
        self.assertEqual(result.status_code, 200)

    def test_oil_100_LL(self):
        result = self.app.get("/essence?type=100LL")
        self.assertEqual(result.status_code, 200)
    def test_no_oil_type(self):
        with raises(Exception) as excinfo:
            self.app.get("/essence?type=")
        assert "Valid oil names are" in str(excinfo.value)
    def test_no_oil(self):
        result = self.app.get("/essence")
        self.assertEqual(result.status_code, 404)

    def test_ad(self):
        result = self.app.get("/ad")
        self.assertEqual(result.status_code, 404)
    def test_ad_no_value(self):
        with raises(Exception) as excinfo:
            self.app.get("/ad?code=")
        assert "No such AD name" in str(excinfo.value)
    def test_ad_ok(self):
        result = self.app.get("/ad?code=lfpo")
        self.assertEqual(result.status_code, 200)
    def test_ad_nok(self):
        with raises(Exception) as excinfo:
            self.app.get("/ad?code=abcdef")
        assert "No such AD name" in str(excinfo.value)
        
    def test_form_missing_pax0(self):
        """Generate an error when pax0 weight is missing"""

        data = {
            "callsign": self.plane.callsign,
            "pax0": None,
            "pax1": self.plane.pax1,
            "pax2": self.plane.pax2,
            "pax3": self.plane.pax3,
            "baggage": self.plane.baggage,
            "mainfuel": self.plane.mainfuel,
            "leftwingfuel": self.plane.leftwingfuel,
            "rightwingfuel": self.plane.rightwingfuel,
            "auxfuel": self.plane.auxfuel,
            "tkalt": 0,
            "ldalt": 0,
            "tktemp": 15,
            "ldtemp": 15,
            "tkqnh": 1013,
            "ldqnh": 1013,
        }
        result = self.app.post("/devis", data=data)        
        self.assertIn(b"This field is required.", result.data)


    def test_api_form_field_validation(self):
        """Generate an error on required field validation"""

        data = {
            "callsign": "",
            "pax0": 0,
            "pax1": self.plane.pax1,
            "pax2": self.plane.pax2,
            "pax3": self.plane.pax3,
            "baggage": self.plane.baggage,
            "mainfuel": self.plane.mainfuel,
            "leftwingfuel": self.plane.leftwingfuel,
            "rightwingfuel": self.plane.rightwingfuel,
            "auxfuel": self.plane.auxfuel,
            "tkalt": 0,
            "ldalt": 0,
            "tktemp": 15,
            "ldtemp": 15,
            "tkqnh": 1013,
            "ldqnh": 1013,
        }
        result = self.app.post("/validate", data=data)
        self.assertEqual(result.status_code, 422)

    def test_cg_out_of_envelope(self):
        """Generate a balance error when cg is out the envelope.
        Full tank and weight at the back seats.
        """
        self.plane.pax0 = 100
        self.plane.pax2, self.plane.pax3 = 2 * [100]
        self.plane.mainfuel = self.plane.maxmainfuel
        data = {
            "pilot_name": "essai",
            "callsign": self.plane.callsign,
            "pax0": self.plane.pax0,
            "pax1": self.plane.pax1,
            "pax2": self.plane.pax2,
            "pax3": self.plane.pax3,
            "baggage": self.plane.baggage,
            "baggage2": self.plane.baggage2,
            "mainfuel": self.plane.mainfuel,
            "leftwingfuel": self.plane.leftwingfuel,
            "rightwingfuel": self.plane.rightwingfuel,
            "auxfuel": self.plane.auxfuel,
            "tkalt": 0,
            "ldalt": 0,
            "tktemp": 15,
            "ldtemp": 15,
            "tkqnh": 1013,
            "ldqnh": 1013,
            "rvt": "dur"
        }
        result = self.app.post("/devis", data=data)
        self.assertIn(b"Chargement invalide", result.data)

    def test_form_ok(self):
        """Generate a balance report when the form is valid."""
        self.plane.pax0 = 70
        self.plane.pax1 = 70
        self.plane.baggage = 20
        self.plane.mainfuel = self.plane.maxmainfuel
        data = {
            "pilot_name": self.pilotname,
            "callsign": self.plane.callsign,
            "pax0": self.plane.pax0,
            "pax1": self.plane.pax1,
            "pax2": self.plane.pax2,
            "pax3": self.plane.pax3,
            "baggage": self.plane.baggage,
            "baggage2": self.plane.baggage2,
            "mainfuel": self.plane.mainfuel,
            "leftwingfuel": self.plane.leftwingfuel,
            "rightwingfuel": self.plane.rightwingfuel,
            "auxfuel": self.plane.auxfuel,
            "tkalt": 400,
            "ldalt": 500,
            "tktemp": 2,
            "ldtemp": 2,
            "tkqnh": 1025,
            "ldqnh": 1027,
            "submit": "Valider",
            "rvt": "dur"
        }
        result = self.app.post("/devis", data=data)
        self.assertIn(b"Autonomie", result.data)

    def test_logout(self):
        """Cover the logout view"""
        result = self.app.get("/logout")
        # self.assertEqual(result.status_code, 302) deactivated route
        self.assertEqual(result.status_code, 400)

    def test_nonlogged_profile(self):
        """Cover the profile view without login"""
        result = self.app.get("/profile")
        # self.assertEqual(result.status_code, 302) deactivated route
        self.assertEqual(result.status_code, 400)

    def test_nonlogged_stats(self):
        """Cover the stats view without login"""
        result = self.app.get("/stats")
        # self.assertEqual(result.status_code, 302) deactivated route
        self.assertEqual(result.status_code, 400)

    def test_metar_nothing(self):
        result = self.app.get("/metar")
        self.assertEqual(result.status_code, 404)
    def test_metar_ok(self):
        result = self.app.get("/metar/lfpo")
        self.assertEqual(result.status_code, 200)
    def test_metar_nok(self):
        result = self.app.get("/metar/abcdef")
        self.assertEqual(result.status_code, 403)

    def test_form_carburant_fields_missing(self):
        data = {
            "pilot_name": self.pilotname,
            "callsign": "F-GGHJ",
            "type_vol": "TDP",
            "nb_branches": 0,
            "branches-0-distance": 5,
            "branches-0-vent": 0,
            "branches-1-distance": 5,
            "branches-1-vent": 0,
            "branches-2-distance": 5,
            "branches-2-vent": 0,
            "branches-3-distance": 5,
            "branches-3-vent": 0,
            "branches-4-distance": 5,
            "branches-4-vent": 0,
            "branches-5-distance": 5,
            "branches-5-vent": 0,
            "degagement-distance": 5,
            "degagement-vent": 0,
            "marge": 0,
            "mainfuel": 0,
            "leftwingfuel": 0,
            "rightwingfuel": 0,
            "auxfuel": 0,
            "submit": "Valider"
        }
        result = self.app.post("/carburant", data=data)
        self.assertIn(b"nombre de branche doit", result.data)
        self.assertIn(b"La marge est comprise", result.data)
        self.assertIn(b"est vide", result.data)

    def test_form_carburant_valid(self):
        data = {
            "pilot_name": self.pilotname,
            "callsign": "F-GGHJ",
            "type_vol": "NAV",
            "nb_branches": 1,
            "branches-0-distance": 5,
            "branches-0-vent": +10,
            "branches-1-distance": 5,
            "branches-1-vent": 0,
            "branches-2-distance": 5,
            "branches-2-vent": 0,
            "branches-3-distance": 5,
            "branches-3-vent": 0,
            "branches-4-distance": 5,
            "branches-4-vent": 0,
            "branches-5-distance": 5,
            "branches-5-vent": 0,
            "degagement-distance": 5,
            "degagement-vent": 0,
            "marge": 10,
            "mainfuel": 50,
            "leftwingfuel": 0,
            "rightwingfuel": 0,
            "auxfuel": 50,
            "submit": "Valider"
        }
        result = self.app.post("/carburant", data=data)
        self.assertIn(b"BON VOL", result.data)

    def test_form_carburant_invalid(self):
        data = {
            "pilot_name": self.pilotname,
            "callsign": "F-GGHJ",
            "type_vol": "NAV",
            "nb_branches": 6,
            "branches-0-distance": 5,
            "branches-0-vent": +10,
            "branches-1-distance": 5,
            "branches-1-vent": -10,
            "branches-2-distance": 25,
            "branches-2-vent": -10,
            "branches-3-distance": 15,
            "branches-3-vent": -20,
            "branches-4-distance": 35,
            "branches-4-vent": +20,
            "branches-5-distance": 55,
            "branches-5-vent": +10,
            "degagement-distance": 5,
            "degagement-vent": 0,
            "marge": 20,
            "mainfuel": 10,
            "leftwingfuel": 0,
            "rightwingfuel": 0,
            "auxfuel": 10,
            "submit": "Valider"
        }
        result = self.app.post("/carburant", data=data)
        self.assertIn(b"compl\xc3\xa9ment de carburant", result.data)

    def test_connexion_not_test(self):
        data = {
            "pilot_name": "test",
            "submit": "Valider"
        }
        result = self.app.post("/connexion", data=data)
        self.assertIn(b"t, e, s, t", result.data)

    def test_connexion_required(self):
        data = {
            "pilot_name": "",
            "submit": "Valider"
        }
        result = self.app.post("/connexion", data=data)
        self.assertIn(b"This field is required.", result.data)

    def test_connexion_ok(self):
        data = {
            "pilot_name": self.pilotname,
            "submit": "Valider"
        }
        result = self.app.post("/connexion", data=data)
        self.assertEqual(result.status_code, 302)

if __name__ == "__main__":
    unittest.main()
