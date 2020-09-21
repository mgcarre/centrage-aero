# *_* coding: utf-8 *_*

"""End to end tests.
"""

import os
import unittest
import prepavol
import prepavol.planes as planes


class WebAppTestCase(unittest.TestCase):
    """ "Testing the web pages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plane = planes.WeightBalance("FHAAC")

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

    def test_form_missing_pax0(self):
        """Generate an error when pax0 weight is missing"""

        data = {
            "callsign": self.plane.callsign,
            "pax0": self.plane.pax0,
            "pax1": self.plane.pax1,
            "pax2": self.plane.pax2,
            "pax3": self.plane.pax3,
            "baggage": self.plane.baggage,
            "fuel_gauge": self.plane.fuel_gauge,
            "auxfuel_gauge": self.plane.auxfuel_gauge,
            "tkalt": 0,
            "ldalt": 0,
            "tktemp": 15,
            "ldtemp": 15,
            "tkqnh": 1013,
            "ldqnh": 1013,
        }
        result = self.app.post("/", data=data)
        self.assertIn(b"This field is required.", result.data)

    def test_cg_out_of_envelope(self):
        """Generate a balance error when cg is out the envelope.
        Full tank and weight at the back seats.
        """
        self.plane.pax0 = 10
        self.plane.pax2, self.plane.pax3 = 2 * [100]
        self.plane.fuel_gauge = 4
        data = {
            "callsign": self.plane.callsign,
            "pax0": self.plane.pax0,
            "pax1": self.plane.pax1,
            "pax2": self.plane.pax2,
            "pax3": self.plane.pax3,
            "baggage": self.plane.baggage,
            "fuel_gauge": self.plane.fuel_gauge,
            "auxfuel_gauge": self.plane.auxfuel_gauge,
            "tkalt": 0,
            "ldalt": 0,
            "tktemp": 15,
            "ldtemp": 15,
            "tkqnh": 1013,
            "ldqnh": 1013,
        }
        result = self.app.post("/", data=data)
        self.assertIn(b"Balance out of cg envelope", result.data)

    def test_form_ok(self):
        """Generate a balance report when the form is valid."""
        self.plane.pax0 = 70
        self.plane.pax1 = 70
        self.plane.baggage = 20
        self.plane.fuel_gauge = 4
        data = {
            "callsign": self.plane.callsign,
            "pax0": self.plane.pax0,
            "pax1": self.plane.pax1,
            "pax2": self.plane.pax2,
            "pax3": self.plane.pax3,
            "baggage": self.plane.baggage,
            "fuel_gauge": self.plane.fuel_gauge,
            "auxfuel_gauge": self.plane.auxfuel_gauge,
            "tkalt": 0,
            "ldalt": 0,
            "tktemp": 15,
            "ldtemp": 15,
            "tkqnh": 1013,
            "ldqnh": 1013,
        }
        result = self.app.post("/", data=data)
        self.assertIn(b"Autonomie 4h20", result.data)

    def test_logout(self):
        """Cover the logout view"""
        result = self.app.get("/logout")
        self.assertEqual(result.status_code, 302)

    def test_nonlogged_profile(self):
        """Cover the profile view without login"""
        result = self.app.get("/profile")
        self.assertEqual(result.status_code, 302)

    def test_nonlogged_stats(self):
        """Cover the stats view without login"""
        result = self.app.get("/stats")
        self.assertEqual(result.status_code, 302)


if __name__ == "__main__":
    unittest.main()
