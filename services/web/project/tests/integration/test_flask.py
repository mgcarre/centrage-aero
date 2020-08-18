import project
import unittest

class WebAppTestCase(unittest.TestCase):

    def setUp(self):
        app = project.create_app()
        app.testing = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.app = app.test_client()

    def test_home(self):
        """Read root page
        """
        result = self.app.get("/")
        self.assertEqual(result.status_code, 200)

    def test_static(self):
        """Read favicon over the static URL
        """
        result = self.app.get("/static/favicon.ico")
        self.assertEqual(result.status_code, 200)

    def test_fleet(self):
        """Read fleet page
        """
        result = self.app.get("/fleet")
        self.assertEqual(result.status_code, 200)

    def test_form_missing_pax0(self):
        """Generate an error when pax0 weight is missing
        """
        self.plane = project.planes.WeightBalance("FHAAC")
        #self.planeperf = project.planes.PlanePerf(self.plane.planetype, self.plane.auw, 1200, 25, 1010)
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
            "ldqnh": 1013
        }
        result = self.app.post("/", data=data)
        self.assertIn(b'This field is required.', result.data)

if __name__ == "__main__":
    unittest.main()