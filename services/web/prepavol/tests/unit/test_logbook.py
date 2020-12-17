# *_* coding: utf-8 *_*

"""Test logbook module
"""

import unittest
from unittest import mock
from datetime import datetime, timedelta
import pandas as pd
import pytest
from prepavol.logbook import FlightLog


class LogBookTestCase(unittest.TestCase):
    """ "Testing FlightLog."""

    @classmethod
    def test_get_log(cls, **kwargs):
        """Mock FlightLog.get_log to stub connection to aerogest"""
        test_dict = {
            "date": {
                0: (datetime.now() - timedelta(days=60)).strftime("%d/%m/%Y"),
                1: (datetime.now() - timedelta(days=50)).strftime("%d/%m/%Y"),
                2: (datetime.now() - timedelta(days=40)).strftime("%d/%m/%Y"),
                3: (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y"),
                4: (datetime.now() - timedelta(days=20)).strftime("%d/%m/%Y"),
            },
            "dep(UTC)": {
                0: "07:50:00",
                1: "15:45:00",
                2: "06:20:00",
                3: "10:40:00",
                4: "17:00:00",
            },
            "arr(UTC)": {
                0: "08:22:00",
                1: "16:58:00",
                2: "07:26:00",
                3: "11:39:00",
                4: "18:25:00",
            },
            "immat": {
                0: "F-GGXD",
                1: "F-HAAC",
                2: "F-BUPS",
                3: "F-HAAC",
                4: "F-GGXD",
            },
            "nature": {
                0: "VFR JOUR",
                1: "VFR JOUR",
                2: "VFR JOUR",
                3: "VFR JOUR",
                4: "VFR JOUR",
            },
            "type": {
                0: "TDP",
                1: "LOCAL",
                2: "LOCAL",
                3: "NAVIGATION",
                4: "NAVIGATION",
            },
            "mode": {0: "CDB", 1: "CDB", 2: "CDB", 3: "CDB", 4: "CDB"},
            "heures": {
                0: "00:32:00",
                1: "01:13:00",
                2: "01:06:00",
                3: "00:59:00",
                4: "01:25:00",
            },
        }
        test_data = pd.DataFrame.from_dict(test_dict)
        # we do care about the log_format argument
        if "log_format" in kwargs.keys():
            test_data = test_data.to_json()
        return test_data

    @pytest.mark.timeout(60)
    def test_failed_login_and_log_format(self):
        """Test a failed login to aerogest"""
        instance = FlightLog({"username": "any", "password": "some"}, log_format="json")
        print(instance)
        _ = instance.log_agg()
        _ = instance.last_quarter()
        self.assertFalse(instance.is_logged)

    def test_log_agg(self):
        """Test log_agg method using json log_format"""
        with mock.patch.object(FlightLog, "get_log", new=self.test_get_log):
            instance = FlightLog({"username": "any", "password": "any"})
            returned = instance.log_agg()[0].loc["Total", "heures"]
            expected = "05h15"
            self.assertEqual(returned, expected)

    def test_last_quarter(self):
        """Test log_agg method"""
        with mock.patch.object(FlightLog, "get_log", new=self.test_get_log):
            instance = FlightLog({"username": "any", "password": "any"})
            returned = instance.last_quarter().loc["Total", "heures"]
            expected = "05h15"
            self.assertEqual(returned, expected)
