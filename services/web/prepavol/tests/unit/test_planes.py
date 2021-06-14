"""Unit tests of the planes module
"""

import unittest
import pandas

from prepavol import planes


class WeightBalanceTestCase(unittest.TestCase):
    """Unit tests of WeightBalance"""

    def setUp(self):
        self.plane = planes.WeightBalance("FHAAC")

    def test_nonexistent_callsign(self):
        """Unknown call sign should raise an exception"""
        self.assertRaises(Exception, planes.WeightBalance, "FXXX")

    def test_basic(self):
        """Ensure plane is duly instantiated"""
        self.assertIsInstance(self.plane, planes.WeightBalance)

    def test_mtow_exceeded(self):
        """All-up weight above MTOW should make is_ready_to_fly False"""
        self.plane.pax0, self.plane.pax1, self.plane.pax2, self.plane.pax3 = 4 * [100]
        # Required to update properties
        _ = self.plane.auw
        self.assertFalse(self.plane.is_ready_to_fly)

    def test_cg_out_of_envelope(self):
        """Balance out of envelope should make is_ready_to_fly False"""
        self.plane.pax2, self.plane.pax3 = 2 * [140]
        self.plane.mainfuel_gauge = 4
        # Required to update properties
        _ = self.plane.cg
        self.assertFalse(self.plane.is_ready_to_fly)

    def test_plot_balance(self):
        """Test the plot_balance method"""
        self.plane.pax0 = 100
        self.plane.mainfuel_gauge = 4
        self.assertTrue(self.plane.plot_balance(encode=True))


class PlanePerfTestCase(unittest.TestCase):
    """Unit tests of PlanePerf"""

    def setUp(self):
        self.plane = planes.WeightBalance("FHAAC")
        self.plane.pax0, self.plane.pax1 = 2 * [70]
        self.plane.mainfuel_gauge = 4
        _ = self.plane.cg
        self.planeperf = planes.PlanePerf(
            self.plane.planetype, self.plane.auw, 1200, 25, 1010
        )

    def test_planeperf_instantiation(self):
        """Validate PlanePerf class instantiation"""
        self.assertIsInstance(self.planeperf, planes.PlanePerf)

    def test_planeperf_density_altitude(self):
        """Validate density altitude property"""
        self.assertIsNotNone(self.planeperf.Zd)

    def test_planeperf_takeoff_prediction(self):
        """Validate takeoff distance prediction"""
        self.assertIsInstance(self.planeperf.predict("takeoff"), pandas.DataFrame)

    def test_planeperf_landing_prediction(self):
        """Validate landing distance prediction"""
        self.assertIsInstance(self.planeperf.predict("landing"), pandas.DataFrame)

    def test_plot_performance(self):
        """Test plot_performance method"""
        self.assertTrue(self.planeperf.plot_performance("takeoff", encode=True))


if __name__ == "__main__":
    unittest.main()
