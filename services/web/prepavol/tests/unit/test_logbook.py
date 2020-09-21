# *_* coding: utf-8 *_*

"""Test logbook module
"""

import unittest
from unittest import mock
import pandas as pd
from prepavol.logbook import FlightLog


class LogBookTestCase(unittest.TestCase):
    """ "Testing FlightLog."""

    @classmethod
    def test_get_log(cls, **kwargs):
        """Mock FlightLog.get_log to stub connection to aerogest"""
        test_dict = {
            "Date": {
                0: "17/09/2020",
                1: "06/09/2020",
                2: "27/08/2020",
                3: "19/08/2020",
                4: "17/08/2020",
            },
            "H.Départ": {
                0: "07:50:00",
                1: "15:45:00",
                2: "06:20:00",
                3: "10:40:00",
                4: "17:00:00",
            },
            "H.Retour": {
                0: "08:22:00",
                1: "16:58:00",
                2: "07:26:00",
                3: "11:39:00",
                4: "18:25:00",
            },
            "Type": {
                0: "DR400-120",
                1: "DR400-120",
                2: "DR400-140B",
                3: "DR400-120",
                4: "DR400-120",
            },
            "Immat": {0: "F-GGXD", 1: "F-HAAC", 2: "F-BUPS", 3: "F-HAAC", 4: "F-GGXD"},
            "Vol": {
                0: "VFR JOUR",
                1: "VFR JOUR",
                2: "VFR JOUR",
                3: "VFR JOUR",
                4: "VFR JOUR",
            },
            "Départ": {0: "LFNG", 1: "LFNG", 2: "LFNG", 3: "LFNG", 4: "LFNG"},
            "Arrivée": {0: "LFNG", 1: "LFNG", 2: "LFNG", 3: "LFNB", 4: "LFNG"},
            "Type de vol": {
                0: "TDP",
                1: "LOCAL",
                2: "LOCAL",
                3: "NAVIGATION",
                4: "NAVIGATION",
            },
            "Mode": {0: "CDB", 1: "CDB", 2: "CDB", 3: "CDB", 4: "CDB"},
            "Heures": {0: "0:32", 1: "1:13", 2: "1:06", 3: "0:59", 4: "1:25"},
        }
        test_data = pd.DataFrame.from_dict(test_dict)
        # we do care about the log_format argument
        if "log_format" in kwargs.keys():
            test_data = test_data.to_json()
        return test_data

    def test_failed_login_and_log_format(self):
        """Test a failed login to aerogest"""
        instance = FlightLog({"username": "any", "password": "some"}, log_format="json")
        _ = instance.log_agg()
        _ = instance.last_quarter()
        self.assertFalse(instance.is_logged)

    def test_log_agg(self):
        """Test log_agg method using json log_format"""
        with mock.patch.object(FlightLog, "get_log", new=self.test_get_log):
            instance = FlightLog({"username": "any", "password": "any"})
            returned = instance.log_agg()[0].loc["Total", "Heures"]
            expected = "05h15"
            self.assertEqual(returned, expected)

    def test_last_quarter(self):
        """Test log_agg method"""
        with mock.patch.object(FlightLog, "get_log", new=self.test_get_log):
            instance = FlightLog({"username": "any", "password": "any"})
            returned = instance.last_quarter().loc["Total", "Heures"]
            expected = "05h15"
            self.assertEqual(returned, expected)
